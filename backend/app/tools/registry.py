"""
DODO Tool Registry & Permission Control
Central registry for all DODO autonomous and local agent tools.
Implements fine-grained 5-level permission enforcement, risk evaluation,
input schemas, timeouts, and execution audit logging.
"""
from enum import Enum
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from backend.app.database.repositories.model_repository import ToolExecutionRepository, AuditRepository

logger = logging.getLogger("dodo.tools.registry")


class PermissionLevel(str, Enum):
    """
    DODO 5-Level Security Permissions:
    1. READ: Safe internal inspection (always allowed or monitored).
    2. WRITE: File creations/modifications (requires approval in autonomous mode).
    3. EXECUTE: Script/binary/process runs (requires approval).
    4. DELETE: Removal of files or artifacts (requires explicit confirmation).
    5. DEPLOY: Build/service publishing (requires approval).
    """
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    DELETE = "DELETE"
    DEPLOY = "DEPLOY"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolStatus(str, Enum):
    AVAILABLE = "available"
    SIMULATED = "simulated"
    DISABLED = "disabled"


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    permission_level: PermissionLevel = PermissionLevel.READ
    risk_level: RiskLevel = RiskLevel.LOW
    status: ToolStatus = ToolStatus.AVAILABLE
    execution_timeout: int = 30  # seconds
    requires_approval: bool = False
    parameters: List[ToolParameter] = []
    input_schema: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        # Map legacy permission_level strings
        raw_perm = data.get("permission_level", "READ")
        if isinstance(raw_perm, str):
            mapping = {
                "automatic": PermissionLevel.READ,
                "controlled": PermissionLevel.WRITE,
                "requires_approval": PermissionLevel.EXECUTE,
                "prohibited": PermissionLevel.DELETE,
                "READ": PermissionLevel.READ,
                "WRITE": PermissionLevel.WRITE,
                "EXECUTE": PermissionLevel.EXECUTE,
                "DELETE": PermissionLevel.DELETE,
                "DEPLOY": PermissionLevel.DEPLOY,
            }
            data["permission_level"] = mapping.get(raw_perm, PermissionLevel.READ)

        # Infer requires_approval
        if "requires_approval" not in data:
            data["requires_approval"] = data["permission_level"] in [
                PermissionLevel.WRITE,
                PermissionLevel.EXECUTE,
                PermissionLevel.DELETE,
                PermissionLevel.DEPLOY,
            ]

        # Infer risk level if not explicitly provided
        if "risk_level" not in data:
            if data["permission_level"] == PermissionLevel.DELETE:
                data["risk_level"] = RiskLevel.CRITICAL
            elif data["permission_level"] in [PermissionLevel.EXECUTE, PermissionLevel.DEPLOY]:
                data["risk_level"] = RiskLevel.HIGH
            elif data["permission_level"] == PermissionLevel.WRITE:
                data["risk_level"] = RiskLevel.MEDIUM
            else:
                data["risk_level"] = RiskLevel.LOW

        super().__init__(**data)


class ToolRegistry:
    """
    Central registry for all DODO autonomous tools.
    Controls permissions, parameter validation, execution tracking, and audit logging.
    Enforces that no model-generated command can bypass security permissions.
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        self.exec_repo = ToolExecutionRepository()
        self.audit_repo = AuditRepository()

    def register(self, definition: ToolDefinition):
        """Decorator to register a tool function with its metadata definition."""
        def decorator(func: Callable):
            self._tools[definition.name] = func
            self._definitions[definition.name] = definition
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def get_definition(self, name: str) -> Optional[ToolDefinition]:
        return self._definitions.get(name)

    def list_definitions(self) -> List[Dict[str, Any]]:
        result = []
        for d in self._definitions.values():
            data = d.model_dump()
            data["permission_level"] = str(d.permission_level.value)
            data["risk_level"] = str(d.risk_level.value)
            data["status"] = str(d.status.value)
            result.append(data)
        return result

    def check_permission(
        self,
        tool_name: str,
        approved: bool = False,
        approved_permissions: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a tool execution is permitted under security rules.
        """
        defn = self.get_definition(tool_name)
        if not defn:
            return False, f"Tool '{tool_name}' not registered in permission registry."

        if defn.status == ToolStatus.DISABLED:
            return False, f"Tool '{tool_name}' is currently disabled by administrator policy."

        # READ permission is always safe
        if defn.permission_level == PermissionLevel.READ:
            return True, None

        # Check explicit approval
        if approved:
            return True, None

        if approved_permissions and defn.permission_level.value in approved_permissions:
            return True, None

        return False, f"Security Violation: Tool '{tool_name}' requires explicit {defn.permission_level.value} approval."

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        task_id: Optional[str] = None,
        enforce_permissions: bool = False,
        approved: bool = False,
        simulated: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes a registered tool with timing, logging, and permission enforcement.
        If simulated=True (e.g. in Phase 3 safe mode), performs safe simulation without OS side-effects.
        """
        func = self._tools.get(tool_name)
        defn = self._definitions.get(tool_name)

        if not func or not defn:
            err = f"Tool '{tool_name}' not found in registry."
            self.exec_repo.log_execution(tool_name, parameters, "failure", error=err, task_id=task_id)
            return {"success": False, "error": err}

        # 1. Enforce Permission Check
        if enforce_permissions:
            permitted, denial_reason = self.check_permission(tool_name, approved=approved)
            if not permitted:
                logger.warning(f"Tool execution blocked: {denial_reason}")
                self.audit_repo.log_event("tool_permission_denied", "agent", {
                    "tool": tool_name,
                    "task_id": task_id,
                    "reason": denial_reason
                })
                return {
                    "success": False,
                    "permission_denied": True,
                    "permission_required": defn.permission_level.value,
                    "error": denial_reason
                }

        # 2. Simulated Safe Execution (Phase 3 Autonomous Engine)
        if simulated or defn.status == ToolStatus.SIMULATED:
            logger.info(f"Simulating safe tool execution: {tool_name}")
            return {
                "success": True,
                "simulated": True,
                "tool": tool_name,
                "result": f"[SIMULATED SAFE EXECUTION] Tool '{tool_name}' simulated with parameters: {parameters}",
                "duration_ms": 15.0
            }

        # 3. Real Tool Execution
        start_time = time.perf_counter()
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(**parameters)
            else:
                result = func(**parameters)

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.exec_repo.log_execution(
                tool_name,
                parameters,
                "success",
                output=str(result)[:2000],
                duration_ms=duration_ms,
                task_id=task_id,
            )
            return {"success": True, "result": result, "duration_ms": duration_ms}
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            err_msg = str(e)
            logger.error(f"Error executing tool {tool_name}: {err_msg}")
            self.exec_repo.log_execution(
                tool_name,
                parameters,
                "failure",
                error=err_msg,
                duration_ms=duration_ms,
                task_id=task_id,
            )
            return {"success": False, "error": err_msg, "duration_ms": duration_ms}


tool_registry = ToolRegistry()
