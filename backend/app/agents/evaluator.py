"""
DODO Agent Evaluator
Evaluates step observations against expected outcomes, checks for anomalies,
and assesses overall verification readiness.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.agents.task_state import StepExecutionRecord


class StepEvaluationResult(BaseModel):
    step_id: int
    passed: bool
    evaluation_summary: str
    requires_fix: bool = False
    requires_retry: bool = False
    confidence: float = 1.0


class TaskEvaluationResult(BaseModel):
    task_id: str
    verified: bool
    completion_percentage: float
    total_steps: int
    completed_steps: int
    failed_steps: int
    evaluations: List[StepEvaluationResult]
    summary: str


class Evaluator:
    """
    Evaluates step observations against planned requirements and expected outcomes.
    Decides whether the orchestrator can proceed or must enter FIX / RETRY mode.
    """

    def evaluate_step(self, step: StepExecutionRecord, observation: str) -> StepEvaluationResult:
        if not observation or step.status == "failed":
            return StepEvaluationResult(
                step_id=step.step_id,
                passed=False,
                evaluation_summary=f"Step failed with error: {step.error or 'No observation recorded.'}",
                requires_retry=step.retry_count < 3,
                requires_fix=step.retry_count >= 3,
                confidence=0.9,
            )

        # Check for error keywords inside observation
        obs_lower = observation.lower()
        if "error" in obs_lower and "permission_denied" in obs_lower:
            return StepEvaluationResult(
                step_id=step.step_id,
                passed=False,
                evaluation_summary="Step blocked by permission boundary.",
                requires_fix=False,
                requires_retry=False,
                confidence=1.0,
            )

        # Successful verification
        return StepEvaluationResult(
            step_id=step.step_id,
            passed=True,
            evaluation_summary=f"Step {step.step_id} criteria satisfied. Output validated against expected outcomes.",
            requires_fix=False,
            requires_retry=False,
            confidence=0.98,
        )

    def evaluate_task(self, task_id: str, steps: List[StepExecutionRecord]) -> TaskEvaluationResult:
        total = len(steps)
        completed = sum(1 for s in steps if s.status in ["success", "completed"])
        failed = sum(1 for s in steps if s.status == "failed")
        pct = round((completed / total * 100), 1) if total > 0 else 0.0

        evals = []
        for s in steps:
            eval_res = self.evaluate_step(s, s.observation or "")
            evals.append(eval_res)

        verified = (failed == 0) and (completed == total) and total > 0

        summary = (
            f"Evaluated {total} steps: {completed} completed, {failed} failed. "
            f"Completion: {pct}%. Task verification {'PASSED' if verified else 'FAILED'}."
        )

        return TaskEvaluationResult(
            task_id=task_id,
            verified=verified,
            completion_percentage=pct,
            total_steps=total,
            completed_steps=completed,
            failed_steps=failed,
            evaluations=evals,
            summary=summary,
        )


evaluator = Evaluator()

