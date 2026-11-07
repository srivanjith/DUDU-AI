from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.database.repositories.model_repository import MemoryRepository

router = APIRouter(prefix="/memory", tags=["Memory"])
mem_repo = MemoryRepository()


class CreateMemoryRequest(BaseModel):
    content: str
    category: Optional[str] = "conversation"
    project_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("")
def search_memories(q: str = "", project_id: Optional[str] = None, limit: int = 10):
    return mem_repo.search_memories(q, project_id=project_id, limit=limit)


@router.post("")
def add_memory(req: CreateMemoryRequest):
    return mem_repo.add_memory(
        content=req.content,
        category=req.category or "conversation",
        project_id=req.project_id,
        metadata=req.metadata,
    )


@router.delete("/{mem_id}")
def delete_memory(mem_id: str):
    return {"success": mem_repo.delete(mem_id)}

