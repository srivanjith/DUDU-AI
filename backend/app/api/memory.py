"""
DODO Memory REST API Router
Exposes endpoints for creating, searching, updating, filtering, and managing
persistent long-term project context and user memories.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.memory.models import (
    CreateMemoryRequest,
    MemorySearchRequest,
    SummarizeMemoryRequest,
    UpdateMemoryRequest,
)
from backend.app.memory.manager import memory_manager
from backend.app.memory.repository import memory_repo
from backend.app.memory.retrieval import retrieval_engine

router = APIRouter(prefix="/api/memory", tags=["Memory"])


@router.get("", response_model=List[Dict[str, Any]])
def list_memories(
    category: Optional[str] = Query(None, description="Filter by memory category"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    q: Optional[str] = Query(None, description="Search keyword in memory content"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """Lists persistent memories with category, project, and substring filtering."""
    return memory_repo.list_memories(
        category=category,
        project_id=project_id,
        search_query=q,
        limit=limit,
        skip=skip,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_memory(req: CreateMemoryRequest):
    """Creates a new validated and sanitized persistent memory item."""
    mem, status_msg = memory_repo.create_memory(
        content=req.content,
        category=req.category or "conversation",
        project_id=req.project_id,
        conversation_id=req.conversation_id,
        importance=req.importance or 3,
        tags=req.tags or [],
        source=req.source or "user_input",
        is_verified=req.is_verified if req.is_verified is not None else True,
        metadata=req.metadata,
    )
    if not mem:
        raise HTTPException(status_code=400, detail=status_msg)
    return {"memory": mem, "status": status_msg}


@router.get("/categories")
def get_categories():
    """Returns total memory counts grouped by category."""
    counts = memory_repo.count_by_category()
    total = sum(counts.values())
    return {"total": total, "categories": counts}


@router.get("/projects")
def get_projects():
    """Returns distinct project IDs that have stored memories."""
    projects = memory_repo.list_projects()
    return {"projects": projects, "count": len(projects)}


@router.post("/search")
def search_memories(req: MemorySearchRequest):
    """Searches memories using multi-factor relevance ranking."""
    results = retrieval_engine.search(
        query=req.query,
        project_id=req.project_id,
        category=req.category,
        limit=req.limit,
        min_score=req.min_score,
    )
    return {"query": req.query, "count": len(results), "results": results}


@router.post("/summarize")
def summarize_memory(req: SummarizeMemoryRequest):
    """Condenses text and stores it as long-term conversation or project memory."""
    content = req.text.strip()
    if len(content) > 500:
        content = content[:497] + "..."
    summary_content = f"Summary: {content}"
    mem, msg = memory_repo.create_memory(
        content=summary_content,
        category=req.category or "conversation",
        project_id=req.project_id,
        conversation_id=req.conversation_id,
        importance=3,
        tags=["summary"],
        source="summarizer",
    )
    if not mem:
        raise HTTPException(status_code=400, detail=msg)
    return {"memory": mem, "status": msg}


@router.get("/{memory_id}")
def get_memory_by_id(memory_id: str):
    """Retrieves a single memory item by ID."""
    mem = memory_repo.find_by_id(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return mem


@router.put("/{memory_id}")
def update_memory_by_id(memory_id: str, req: UpdateMemoryRequest):
    """Updates an existing memory item."""
    existing = memory_repo.find_by_id(memory_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")

    updates: Dict[str, Any] = {}
    if req.content is not None:
        updates["content"] = req.content
    if req.category is not None:
        updates["category"] = req.category
    if req.project_id is not None:
        updates["project_id"] = req.project_id
    if req.importance is not None:
        updates["importance"] = max(1, min(5, req.importance))
    if req.tags is not None:
        updates["tags"] = req.tags
    if req.is_verified is not None:
        updates["is_verified"] = req.is_verified
    if req.metadata is not None:
        updates["metadata"] = req.metadata

    updated = memory_repo.update(memory_id, updates)
    return {"memory": updated, "success": True}


@router.delete("/project/{project_id}")
def clear_project_memories(project_id: str):
    """Deletes all memories associated with a specific project."""
    deleted_count = memory_repo.clear_project_memories(project_id)
    return {"project_id": project_id, "deleted_count": deleted_count, "success": True}


@router.delete("/clear")
def clear_all_memories(confirm: bool = Query(False, description="Explicit confirmation required")):
    """Deletes all memories across DODO."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Pass ?confirm=true to delete all persistent memories."
        )
    deleted_count = memory_repo.clear_all_memories()
    return {"deleted_count": deleted_count, "success": True}


@router.delete("/{memory_id}")
def delete_memory_by_id(memory_id: str):
    """Deletes a single memory item by ID."""
    deleted = memory_repo.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found.")
    return {"memory_id": memory_id, "success": True}
