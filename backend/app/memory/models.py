"""
DODO Persistent Memory Models
Defines memory entities, categories, requests, and retrieval results.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    CONVERSATION = "conversation"
    PREFERENCE = "preference"
    PROJECT = "project"
    TASK_EXPERIENCE = "task_experience"
    KNOWLEDGE = "knowledge"


class MemoryItem(BaseModel):
    id: Optional[str] = None
    content: str
    category: MemoryCategory = MemoryCategory.CONVERSATION
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    importance: int = Field(default=3, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = "user_input"
    is_verified: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CreateMemoryRequest(BaseModel):
    content: str
    category: Optional[str] = "conversation"
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    importance: Optional[int] = 3
    tags: Optional[List[str]] = None
    source: Optional[str] = "user_input"
    is_verified: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None


class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    project_id: Optional[str] = None
    importance: Optional[int] = None
    tags: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class MemorySearchRequest(BaseModel):
    query: str = ""
    category: Optional[str] = None
    project_id: Optional[str] = None
    limit: int = 10
    min_score: float = 0.0


class SummarizeMemoryRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None
    category: Optional[str] = "conversation"

