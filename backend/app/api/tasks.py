import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.database.repositories.project_repository import TaskRepository

router = APIRouter(prefix="/tasks", tags=["Tasks"])
task_repo = TaskRepository()


class CreateTaskRequest(BaseModel):
    prompt: str
    workspace_path: Optional[str] = None
    project_id: Optional[str] = None
    mode: Optional[str] = "developer"


@router.get("")
def list_tasks(limit: int = 50):
    return task_repo.find_all(limit=limit, sort=[("created_at", -1)])


@router.post("")
def create_task(req: CreateTaskRequest):
    return task_repo.create_task(
        prompt=req.prompt,
        project_id=req.project_id,
        workspace_path=req.workspace_path,
        mode=req.mode or "developer",
    )


@router.get("/{task_id}")
def get_task(task_id: str):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str):
    success = agent_orchestrator.cancel_task(task_id)
    return {"success": success, "task_id": task_id}


@router.get("/{task_id}/stream")
async def stream_task_execution(task_id: str):
    """
    Streams live lifecycle progress events for an autonomous development task.
    """
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        async for event in agent_orchestrator.execute_task_stream(task_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

