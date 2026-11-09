"""
DODO Terminal & Local Agent API Endpoints
Provides endpoints for command execution, approval gating, cancellation, process monitoring,
audit history, and real-time streaming.
"""
import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.tools.local_agent_client import local_agent_client
from backend.app.tools.terminal_tools import execute_terminal_command

logger = logging.getLogger("dodo.api.terminal")

router = APIRouter(prefix="/api/terminal", tags=["Terminal & Local Agent"])

# In-memory registry of executions pending user approval
PENDING_APPROVALS: Dict[str, Dict[str, Any]] = {}
# Recent execution streams for SSE streaming
EXECUTION_STREAMS: Dict[str, asyncio.Queue] = {}


class TerminalRunRequest(BaseModel):
    command: str = Field(..., description="Terminal command to execute")
    cwd: Optional[str] = Field("", description="Subdirectory relative to workspace root")
    workspace_root: Optional[str] = Field(None, description="Explicit workspace root path")
    timeout_seconds: Optional[int] = Field(60, description="Execution timeout in seconds")
    approved: Optional[bool] = Field(False, description="Explicit user approval flag")
    is_dev_server: Optional[bool] = Field(False, description="Whether this command is a dev server")


class PairAgentRequest(BaseModel):
    secret_token: str = Field(..., description="Local Agent secret token to pair")


@router.get("/agent/status")
async def get_agent_status():
    """Returns the pairing and health status of the DODO Local Agent."""
    return await local_agent_client.get_status()


@router.post("/agent/pair")
async def pair_agent(req: PairAgentRequest):
    """Pairs the backend with the Local Agent using the provided token."""
    if req.secret_token != settings.LOCAL_AGENT_SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pairing failed: Invalid secret token."
        )
    status_info = await local_agent_client.get_status()
    return {"paired": True, "agent_status": status_info}


@router.post("/execute")
async def run_command(req: TerminalRunRequest):
    """
    Creates an execution request. If the command requires approval (e.g. dependency installation),
    returns requires_approval=True and pauses until approved.
    """
    exec_id = str(uuid.uuid4())
    res = await execute_terminal_command(
        command=req.command,
        cwd=req.cwd or "",
        workspace_root=req.workspace_root,
        timeout_seconds=req.timeout_seconds or 60,
        approved=req.approved or False,
        execution_id=exec_id,
        is_dev_server=req.is_dev_server or False,
    )

    if res.get("requires_approval") and not req.approved:
        # Register in pending approvals
        PENDING_APPROVALS[exec_id] = {
            "execution_id": exec_id,
            "command": req.command,
            "cwd": req.cwd or "",
            "workspace_root": req.workspace_root,
            "timeout_seconds": req.timeout_seconds or 60,
            "category": res.get("category", "UNKNOWN"),
            "reason": res.get("reason", "Action requires explicit user confirmation."),
            "is_dev_server": req.is_dev_server or False,
            "status": "pending_approval",
        }
        return {
            "execution_id": exec_id,
            "requires_approval": True,
            "command": req.command,
            "category": res.get("category"),
            "risk_level": res.get("risk_level", "requires_approval"),
            "reason": res.get("reason"),
            "message": "Explicit user approval required before executing this command.",
        }

    return res


@router.get("/pending-approvals")
def get_pending_approvals():
    """Lists commands currently paused awaiting user approval."""
    return list(PENDING_APPROVALS.values())


@router.post("/approve/{execution_id}")
async def approve_command(execution_id: str):
    """Approves and immediately executes a previously gated command."""
    pending = PENDING_APPROVALS.pop(execution_id, None)
    if not pending:
        raise HTTPException(status_code=404, detail=f"No pending execution with ID '{execution_id}' found.")

    res = await execute_terminal_command(
        command=pending["command"],
        cwd=pending["cwd"],
        workspace_root=pending["workspace_root"],
        timeout_seconds=pending["timeout_seconds"],
        approved=True,
        execution_id=execution_id,
        is_dev_server=pending.get("is_dev_server", False),
    )
    return res


@router.post("/cancel/{execution_id}")
async def cancel_command(execution_id: str):
    """Cancels a running command or pending approval."""
    PENDING_APPROVALS.pop(execution_id, None)
    success = await local_agent_client.cancel(execution_id)
    return {"execution_id": execution_id, "cancelled": success}


@router.get("/history")
async def get_command_history(limit: int = 50):
    """Retrieves command audit history."""
    return await local_agent_client.get_history(limit=limit)


@router.get("/processes")
async def list_processes(active_only: bool = True):
    """Lists running background processes and dev servers."""
    return await local_agent_client.list_processes(active_only=active_only)


@router.post("/processes/{pid}/kill")
async def kill_process(pid: int):
    """Terminates an active process tree."""
    success = await local_agent_client.kill_process(pid)
    if not success:
        raise HTTPException(status_code=404, detail=f"Process {pid} not found or already terminated.")
    return {"pid": pid, "killed": True}


@router.websocket("/ws")
async def terminal_websocket(websocket: WebSocket):
    """Interactive real-time terminal WebSocket for frontend xterm streaming."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "terminal_connected",
            "message": "Connected to DODO Real-time Terminal Hub",
        })
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            action = data.get("action")

            if action == "exec":
                cmd = data.get("command", "")
                exec_id = data.get("execution_id", str(uuid.uuid4()))
                cwd = data.get("cwd", "")
                timeout = int(data.get("timeout", 60))
                approved = bool(data.get("approved", False))

                await websocket.send_json({
                    "type": "status",
                    "execution_id": exec_id,
                    "status": "running",
                    "command": cmd,
                })

                res = await execute_terminal_command(
                    command=cmd,
                    cwd=cwd,
                    timeout_seconds=timeout,
                    approved=approved,
                    execution_id=exec_id,
                )

                if res.get("stdout"):
                    for line in res["stdout"].splitlines(keepends=True):
                        await websocket.send_json({
                            "type": "stdout",
                            "execution_id": exec_id,
                            "data": line,
                        })

                if res.get("stderr"):
                    for line in res["stderr"].splitlines(keepends=True):
                        await websocket.send_json({
                            "type": "stderr",
                            "execution_id": exec_id,
                            "data": line,
                        })

                await websocket.send_json({
                    "type": "completed",
                    "execution_id": exec_id,
                    "exit_code": res.get("exit_code", 0),
                    "success": res.get("success", False),
                    "error": res.get("error"),
                })

            elif action == "cancel":
                exec_id = data.get("execution_id", "")
                cancelled = await local_agent_client.cancel(exec_id)
                await websocket.send_json({
                    "type": "status",
                    "execution_id": exec_id,
                    "status": "cancelled",
                    "cancelled": cancelled,
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("Terminal WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"Terminal WebSocket exception: {e}")
