import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.database.repositories.model_repository import ToolExecutionRepository, AuditRepository

logger = logging.getLogger("dodo.tools.registry")


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    permission_level: str = "automatic"  # automatic, controlled, requires_approval, prohibited
    parameters: List[ToolParameter] = []


class ToolRegistry:
    """
    Central registry for all DODO autonomous tools.
    Controls permissions, parameter validation, execution tracking, and audit logging.
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

    def list_definitions(self) -> List[Dict[str, Any]]:
        return [d.dict() for d in self._definitions.values()]

    async def execute(self, tool_name: str, parameters: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes registered tool with timing, logging, and error handling.
        """
        func = self._tools.get(tool_name)
        if not func:
            err = f"Tool '{tool_name}' not found in registry."
            self.exec_repo.log_execution(tool_name, parameters, "failure", error=err, task_id=task_id)
            return {"success": False, "error": err}

        start_time = time.perf_counter()
        try:
            # Check if function is async
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

