from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentPhase(str, Enum):
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    OBSERVE = "OBSERVE"
    EVALUATE = "EVALUATE"
    FIX = "FIX"
    VERIFY = "VERIFY"
    DELIVER = "DELIVER"


class StepExecutionRecord(BaseModel):
    step_id: int
    title: str
    tool_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, executing, success, failed, skipped
    observation: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


class AgentExecutionState(BaseModel):
    task_id: str
    prompt: str
    workspace_path: str
    phase: AgentPhase = AgentPhase.PLAN
    is_cancelled: bool = False
    step_records: List[StepExecutionRecord] = Field(default_factory=list)
    current_step_id: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    verification_passed: bool = False
    delivery_report: Optional[str] = None

