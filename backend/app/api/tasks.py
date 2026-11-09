"""
DODO Autonomous Agent Task Management API
Implements full task lifecycle management:
- POST /api/agent/tasks
- GET /api/agent/tasks
- GET /api/agent/tasks/{task_id}
- POST /api/agent/tasks/{task_id}/start
- POST /api/agent/tasks/{task_id}/cancel
- GET /api/agent/tasks/{task_id}/events
- POST /api/agent/tasks/{task_id}/approve
- GET /api/agent/tasks/{task_id}/stream
Also maintains backward-compatible aliases under /api/tasks and /tasks.
"""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.database.repositories.project_repository import TaskRepository

router = APIRouter(tags=["Agent Tasks"])
task_repo = TaskRepository()


class CreateTaskRequest(BaseModel):
    prompt: str = Field(..., max_length=65536, description="Autonomous development objective or request")
    workspace_path: Optional[str] = None
    project_id: Optional[str] = None
    mode: Optional[str] = "developer"


class ApproveStepRequest(BaseModel):
    step_id: int
    approved: bool = True
    comment: Optional[str] = None


# --------------------------------------------------------------------------
# 1. LIST TASKS
# --------------------------------------------------------------------------
@router.get("/api/agent/tasks")
@router.get("/api/tasks")
@router.get("/tasks")
def list_tasks(limit: int = Query(50, ge=1, le=200)):
    return task_repo.find_all(limit=limit, sort=[("created_at", -1)])


# --------------------------------------------------------------------------
# 2. CREATE TASK
# --------------------------------------------------------------------------
@router.post("/api/agent/tasks")
@router.post("/api/tasks")
@router.post("/tasks")
def create_task(req: CreateTaskRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Task prompt cannot be empty.")

    task = task_repo.create_task(
        prompt=req.prompt.strip(),
        project_id=req.project_id,
        workspace_path=req.workspace_path,
        mode=req.mode or "developer",
    )
    return task


# --------------------------------------------------------------------------
# 3. GET TASK DETAILS
# --------------------------------------------------------------------------
@router.get("/api/agent/tasks/{task_id}")
@router.get("/api/tasks/{task_id}")
@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


# --------------------------------------------------------------------------
# 4. START / RESUME TASK
# --------------------------------------------------------------------------
@router.post("/api/agent/tasks/{task_id}/start")
@router.post("/api/tasks/{task_id}/start")
def start_task(task_id: str):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    # Start or resume task
    state = agent_orchestrator.get_or_create_state(
        task_id=task_id,
        prompt=task.get("prompt", ""),
        workspace_path=task.get("workspace_path", "")
    )
    return {
        "success": True,
        "task_id": task_id,
        "status": state.status.value,
        "phase": state.phase.value,
        "message": "Task execution initiated."
    }


# --------------------------------------------------------------------------
# 5. CANCEL TASK
# --------------------------------------------------------------------------
@router.post("/api/agent/tasks/{task_id}/cancel")
@router.post("/api/tasks/{task_id}/cancel")
@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    success = agent_orchestrator.cancel_task(task_id)
    return {"success": success, "task_id": task_id, "status": "cancelled"}


# --------------------------------------------------------------------------
# 6. GET TASK EVENTS TIMELINE
# --------------------------------------------------------------------------
@router.get("/api/agent/tasks/{task_id}/events")
@router.get("/api/tasks/{task_id}/events")
def get_task_events(task_id: str):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    events = agent_orchestrator.get_task_events(task_id)
    return {
        "task_id": task_id,
        "total_events": len(events),
        "events": events
    }


# --------------------------------------------------------------------------
# 7. APPROVE STEP
# --------------------------------------------------------------------------
@router.post("/api/agent/tasks/{task_id}/approve")
@router.post("/api/tasks/{task_id}/approve")
def approve_step(task_id: str, req: ApproveStepRequest):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    if not req.approved:
        # User explicitly rejected
        agent_orchestrator.cancel_task(task_id, reason=f"User rejected approval for Step {req.step_id}: {req.comment or 'No comment'}")
        return {"success": True, "task_id": task_id, "step_id": req.step_id, "status": "rejected"}

    result = agent_orchestrator.approve_step(task_id, req.step_id)
    return result


# --------------------------------------------------------------------------
# 8. STREAM TASK PROGRESS (SSE)
# --------------------------------------------------------------------------
@router.get("/api/agent/tasks/{task_id}/stream")
@router.get("/api/tasks/{task_id}/stream")
@router.get("/tasks/{task_id}/stream")
async def stream_task_execution(task_id: str, resume: bool = False):
    """
    Streams live lifecycle progress events for an autonomous development task.
    Cycle: PLAN -> EXECUTE -> OBSERVE -> EVALUATE -> FIX -> VERIFY -> DELIVER
    """
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    async def event_generator():
        async for event in agent_orchestrator.execute_task_stream(task_id, resume=resume):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
