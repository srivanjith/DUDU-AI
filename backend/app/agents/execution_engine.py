"""
DODO Safe Execution Engine
Executes controlled agent planning and simulation operations for Phase 3.
Guarantees that no arbitrary shell commands or real file modifications occur.
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from backend.app.agents.cancellation import CancellationToken
from backend.app.agents.task_state import StepExecutionRecord
from backend.app.tools.registry import PermissionLevel, tool_registry

logger = logging.getLogger("dodo.agents.execution_engine")


class StepExecutionResult:
    def __init__(
        self,
        step_id: int,
        success: bool,
        observation: str,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
        needs_approval: bool = False,
        permission_required: Optional[str] = None,
    ):
        self.step_id = step_id
        self.success = success
        self.observation = observation
        self.duration_ms = duration_ms
        self.error = error
        self.needs_approval = needs_approval
        self.permission_required = permission_required


class ExecutionEngine:
    """
    Executes discrete planning and simulated execution steps safely.
    Enforces security permissions and prevents unauthorized OS actions.
    """

    async def execute_step(
        self,
        step: StepExecutionRecord,
        task_id: str,
        workspace_path: str,
        completed_step_ids: List[int],
        cancellation_token: Optional[CancellationToken] = None,
        is_approved: bool = False,
    ) -> StepExecutionResult:
        start_time = time.perf_counter()

        # 1. Cancellation check
        if cancellation_token and cancellation_token.is_cancelled:
            return StepExecutionResult(
                step_id=step.step_id,
                success=False,
                observation="",
                error=f"Execution cancelled: {cancellation_token.reason}",
            )

        # 2. Dependency validation
        for dep in step.dependencies:
            if dep not in completed_step_ids:
                return StepExecutionResult(
                    step_id=step.step_id,
                    success=False,
                    observation="",
                    error=f"Dependency unmet: Step {dep} has not completed successfully.",
                )

        # 3. Approval Gate Check
        if step.approval_required and not is_approved:
            logger.info(f"Step {step.step_id} paused: explicit user approval required.")
            return StepExecutionResult(
                step_id=step.step_id,
                success=False,
                observation="",
                needs_approval=True,
                permission_required=step.risk_level.upper(),
                error=f"Step {step.step_id} requires explicit user approval before proceeding.",
            )

        # 4. Safe Execution: Tool or Simulated Planning
        if step.tool_name:
            params = dict(step.parameters or {})
            # Read-only tools can run if workspace exists, otherwise run safely simulated
            if step.tool_name == "list_workspace_files":
                params["subpath"] = params.get("subpath", "")
                params["depth"] = params.get("depth", 2)
                res = await tool_registry.execute(
                    step.tool_name,
                    params,
                    task_id=task_id,
                    enforce_permissions=True,
                    approved=is_approved,
                    simulated=False,
                )
            else:
                # In Phase 3, all WRITE/EXECUTE/DELETE operations run in SIMULATED mode
                res = await tool_registry.execute(
                    step.tool_name,
                    params,
                    task_id=task_id,
                    enforce_permissions=True,
                    approved=is_approved,
                    simulated=True,
                )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if res.get("success"):
                obs = f"[Observed] Tool '{step.tool_name}' executed: {res.get('result', '')}"
                return StepExecutionResult(step_id=step.step_id, success=True, observation=obs, duration_ms=duration_ms)
            else:
                err = res.get("error", "Unknown tool error")
                return StepExecutionResult(step_id=step.step_id, success=False, observation="", error=err, duration_ms=duration_ms)

        # 5. Analytical Planning Step Execution (Non-tool simulation)
        await asyncio.sleep(0.08)  # Controlled simulated execution time
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        outcomes_text = "; ".join(step.expected_outcomes) if step.expected_outcomes else "Completed."
        obs = f"[Planning Observation] {step.title} analyzed. Validated specifications: {outcomes_text}"

        return StepExecutionResult(
            step_id=step.step_id,
            success=True,
            observation=obs,
            duration_ms=duration_ms,
        )


execution_engine = ExecutionEngine()
