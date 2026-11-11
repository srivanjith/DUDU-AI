"""
DODO Task State Machine
Defines the stateful lifecycle, execution records, approval requests,
and event timelines for autonomous agent runs.
Lifecycle: PLAN -> EXECUTE -> OBSERVE -> EVALUATE -> FIX -> VERIFY -> DELIVER
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentPhase(str, Enum):
    UNDERSTAND = "UNDERSTAND"
    INSPECT = "INSPECT"
    PLAN = "PLAN"
    APPROVE = "APPROVE"
    EXECUTE = "EXECUTE"
    OBSERVE = "OBSERVE"
    DEBUG = "DEBUG"
    VERIFY = "VERIFY"
    DELIVER = "DELIVER"
    # Backwards compatibility aliases
    EVALUATE = "OBSERVE"
    FIX = "DEBUG"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    UNDERSTANDING = "understanding"
    INSPECTING = "inspecting"
    PLANNING = "planning"
    PLANNED = "planned"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    OBSERVING = "observing"
    DEBUGGING = "debugging"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    type: str  # "phase_change" | "step_start" | "observation" | "evaluation" | "approval_request" | "error" | "retry" | "completion"
    phase: AgentPhase
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    approval_id: str
    task_id: str
    step_id: int
    tool_name: str
    permission_level: str  # READ, WRITE, EXECUTE, DELETE, DEPLOY
    risk_level: str  # low, medium, high, critical
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, approved, rejected
    requested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None


class StepExecutionRecord(BaseModel):
    step_id: int
    title: str
    description: str = ""
    tool_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, awaiting_approval, in_progress, success, failed, skipped
    observation: Optional[str] = None
    evaluation: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    dependencies: List[int] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    risk_level: str = "low"
    approval_required: bool = False
    duration_ms: float = 0.0


class AgentExecutionState(BaseModel):
    task_id: str
    prompt: str
    workspace_path: str
    phase: AgentPhase = AgentPhase.PLAN
    status: TaskStatus = TaskStatus.QUEUED
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None
    step_records: List[StepExecutionRecord] = Field(default_factory=list)
    current_step_id: int = 0
    total_steps: int = 0
    completed_steps_count: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    events: List[ExecutionEvent] = Field(default_factory=list)
    pending_approval: Optional[ApprovalRequest] = None
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    verification_passed: bool = False
    delivery_report: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def record_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> ExecutionEvent:
        evt = ExecutionEvent(
            type=event_type,
            phase=self.phase,
            message=message,
            details=details or {},
        )
        self.events.append(evt)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return evt

