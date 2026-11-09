"""
DODO Local Agent Service
Independent secure local runtime for autonomous development operations.
Handles authenticated execution requests, WebSocket streaming, process management,
and workspace isolation.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Security, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from local_agent.config import local_settings
from local_agent.security import verify_token, verify_token_string
from local_agent.filesystem.manager import fs_manager
from local_agent.terminal.executor import terminal_executor
from local_agent.terminal.manager import process_manager
from local_agent.browser.runner import browser_runner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("dodo.local_agent")

app = FastAPI(
    title="DODO Local Agent",
    description="Secure authenticated local runtime bridge for DODO development platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecRequest(BaseModel):
    command: str = Field(..., description="Terminal command to execute")
    cwd: Optional[str] = Field("", description="Subdirectory relative to workspace root")
    workspace_root: Optional[str] = Field(None, description="Explicit workspace root path")
    timeout: Optional[int] = Field(60, description="Execution timeout in seconds")
    approved: Optional[bool] = Field(False, description="Whether user explicitly approved execution")
    execution_id: Optional[str] = Field(None, description="Client-provided tracking ID")
    is_dev_server: Optional[bool] = Field(False, description="Whether this is a long-running dev server")


class CancelRequest(BaseModel):
    execution_id: str


class WriteFileRequest(BaseModel):
    path: str
    content: str


@app.get("/health")
def health():
    """Health and status of the DODO Local Agent."""
    active_procs = process_manager.list_processes(active_only=True)
    return {
        "status": "online",
        "agent": "DODO Local Agent",
        "version": "1.0.0",
        "host": local_settings.HOST,
        "port": local_settings.PORT,
        "authorized_workspace": local_settings.AUTHORIZED_WORKSPACE,
        "active_processes_count": len(active_procs),
        "audit_records_count": len(terminal_executor.get_audit_history(1000)),
    }


# ==============================================================================
# REST Terminal Execution & Process Endpoints
# ==============================================================================

@app.post("/api/exec", dependencies=[Depends(verify_token)])
async def execute_command(req: ExecRequest):
    """Executes an authorized command inside the workspace."""
    return await terminal_executor.execute(
        command=req.command,
        cwd=req.cwd or "",
        workspace_root=req.workspace_root,
        timeout=req.timeout or 60,
        approved=req.approved or False,
        execution_id=req.execution_id,
        is_dev_server=req.is_dev_server or False,
    )


@app.post("/api/cancel", dependencies=[Depends(verify_token)])
async def cancel_execution(req: CancelRequest):
    """Cancels a running command execution."""
    success = await terminal_executor.cancel(req.execution_id)
    return {"execution_id": req.execution_id, "cancelled": success}


@app.get("/api/processes", dependencies=[Depends(verify_token)])
def list_processes(active_only: bool = True):
    """Lists tracked background processes and dev servers."""
    return process_manager.list_processes(active_only=active_only)


@app.post("/api/processes/{pid}/kill", dependencies=[Depends(verify_token)])
async def kill_process(pid: int):
    """Terminates an active process tree."""
    success = await process_manager.kill_process(pid)
    if not success:
        raise HTTPException(status_code=404, detail=f"Process with PID {pid} not found.")
    return {"pid": pid, "killed": True}


@app.get("/api/history", dependencies=[Depends(verify_token)])
def get_execution_history(limit: int = 50):
    """Retrieves command audit history."""
    return terminal_executor.get_audit_history(limit=limit)


# ==============================================================================
# Filesystem Bridge Endpoints
# ==============================================================================

@app.get("/api/fs/list", dependencies=[Depends(verify_token)])
def list_files(subpath: str = ""):
    return fs_manager.list_files(subpath)


@app.get("/api/fs/read", dependencies=[Depends(verify_token)])
def read_file(path: str, start_line: int = 1, end_line: Optional[int] = None):
    return fs_manager.read(path, start_line, end_line)


@app.post("/api/fs/write", dependencies=[Depends(verify_token)])
def write_file(req: WriteFileRequest):
    return fs_manager.write(req.path, req.content)


@app.get("/api/browser/inspect", dependencies=[Depends(verify_token)])
async def browser_inspect(url: str):
    return await browser_runner.inspect(url)


# ==============================================================================
# Real-Time WebSocket Streaming Terminal
# ==============================================================================

@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    Secure WebSocket connection for live stdout/stderr streaming.
    Rejects unauthenticated connections immediately.
    """
    # 1. Authenticate token
    authenticated = verify_token_string(token)
    await websocket.accept()

    if not authenticated:
        # Wait for first message to be auth
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            msg = json.loads(raw)
            if msg.get("action") == "auth" and verify_token_string(msg.get("token")):
                authenticated = True
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": "Unauthorized: Invalid or missing DODO Local Agent authentication token."
                })
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Send welcome handshake
    await websocket.send_json({
        "type": "connected",
        "agent": "DODO Local Agent",
        "status": "ready",
        "workspace": local_settings.AUTHORIZED_WORKSPACE,
    })

    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "Invalid JSON payload."})
                continue

            action = data.get("action")

            if action == "exec":
                cmd = data.get("command", "")
                exec_id = data.get("execution_id", "")
                cwd = data.get("cwd", "")
                workspace_root = data.get("workspace_root")
                timeout = int(data.get("timeout", 60))
                approved = bool(data.get("approved", False))
                is_dev_server = bool(data.get("is_dev_server", False))

                async def stream_callback(stream_type: str, line: str):
                    try:
                        await websocket.send_json({
                            "type": "output",
                            "execution_id": exec_id,
                            "stream": stream_type,
                            "data": line,
                        })
                    except Exception:
                        pass

                # Start execution
                await websocket.send_json({
                    "type": "status",
                    "execution_id": exec_id,
                    "status": "running",
                    "command": cmd,
                })

                res = await terminal_executor.execute(
                    command=cmd,
                    cwd=cwd,
                    workspace_root=workspace_root,
                    timeout=timeout,
                    approved=approved,
                    execution_id=exec_id,
                    on_output=stream_callback,
                    is_dev_server=is_dev_server,
                )

                await websocket.send_json({
                    "type": "completed",
                    "execution_id": exec_id,
                    "result": res,
                })

            elif action == "cancel":
                exec_id = data.get("execution_id", "")
                cancelled = await terminal_executor.cancel(exec_id)
                await websocket.send_json({
                    "type": "status",
                    "execution_id": exec_id,
                    "status": "cancelled",
                    "cancelled": cancelled,
                })

            elif action == "kill":
                pid = int(data.get("pid", 0))
                killed = await process_manager.kill_process(pid)
                await websocket.send_json({
                    "type": "process_killed",
                    "pid": pid,
                    "success": killed,
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("Local terminal client disconnected.")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=local_settings.HOST, port=local_settings.PORT)
