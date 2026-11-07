from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return str(v)


# --- CONVERSATION & MESSAGE SCHEMAS ---

class MessageCreate(BaseModel):
    role: str = Field(..., description="'user', 'assistant', 'system', or 'tool'")
    content: str
    thought_process: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    model_used: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    thought_process: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    model_used: Optional[str] = None
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    project_id: Optional[str] = None
    mode: str = "assistant"  # assistant, developer, computer


class ConversationResponse(BaseModel):
    id: str
    title: str
    mode: str
    project_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


# --- PROJECT SCHEMAS ---

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    workspace_path: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    workspace_path: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0


# --- AGENT TASK SCHEMAS ---

class TaskStep(BaseModel):
    step_id: int
    title: str
    description: str
    tool: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, in_progress, completed, failed, skipped
    result: Optional[str] = None
    error: Optional[str] = None


class TaskPlan(BaseModel):
    objective: str
    analysis: str
    estimated_steps: int
    steps: List[TaskStep]


class TaskCreate(BaseModel):
    prompt: str
    project_id: Optional[str] = None
    workspace_path: Optional[str] = None
    mode: str = "developer"  # developer, assistant, computer


class TaskResponse(BaseModel):
    id: str
    prompt: str
    project_id: Optional[str] = None
    workspace_path: str
    status: str = "queued"  # queued, planning, executing, evaluating, fixing, verified, completed, failed, cancelled
    plan: Optional[TaskPlan] = None
    current_step_index: int = 0
    created_at: datetime
    updated_at: datetime
    result_summary: Optional[str] = None
    verified: bool = False


# --- TOOL EXECUTION SCHEMAS ---

class ToolExecutionRecord(BaseModel):
    id: Optional[str] = None
    task_id: Optional[str] = None
    tool_name: str
    parameters: Dict[str, Any]
    status: str = "success"  # success, failure, denied
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- MODEL CONFIG SCHEMAS ---

class ModelConfigItem(BaseModel):
    model_name: str
    role: str  # general, coding, reasoning, lightweight, embedding
    context_length: int = 8192
    quantization: Optional[str] = "4-bit"
    is_active: bool = True
    parameters: Optional[Dict[str, Any]] = None


class ModelMetricRecord(BaseModel):
    model_name: str
    task_type: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- MEMORY SCHEMAS ---

class MemoryItem(BaseModel):
    id: Optional[str] = None
    project_id: Optional[str] = None
    category: str = "conversation"  # conversation, project, preference, codebase, execution
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

