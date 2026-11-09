"""
DODO Retry Manager
Manages bounded step retries, loop detection, and error categorization
to prevent infinite execution cycles.
"""
import logging
from typing import Dict, List, Optional
from backend.app.core.config import settings

logger = logging.getLogger("dodo.agents.retry_manager")


class RetryDecision:
    def __init__(self, should_retry: bool, retry_count: int, reason: str, backoff_seconds: float = 0.0):
        self.should_retry = should_retry
        self.retry_count = retry_count
        self.reason = reason
        self.backoff_seconds = backoff_seconds


class RetryManager:
    """
    Controls retry policy for autonomous step execution.
    Guarantees strict bounds and prevents infinite loops.
    """

    MAX_RETRIES_PER_STEP: int = getattr(settings, "MAX_RETRIES_PER_STEP", 3)
    MAX_TOTAL_TASK_RETRIES: int = 6

    def __init__(self):
        # task_id -> step_id -> count
        self._retry_counts: Dict[str, Dict[int, int]] = {}
        # task_id -> list of error fingerprints
        self._error_history: Dict[str, List[str]] = {}

    def should_retry(self, task_id: str, step_id: int, error_message: str) -> RetryDecision:
        if task_id not in self._retry_counts:
            self._retry_counts[task_id] = {}
            self._error_history[task_id] = []

        step_counts = self._retry_counts[task_id]
        current_step_retries = step_counts.get(step_id, 0)
        total_task_retries = sum(step_counts.values())

        # 1. Non-retryable conditions
        fatal_indicators = ["permission denied", "cancelled", "security violation", "not found in registry"]
        err_lower = (error_message or "").lower()
        if any(fatal in err_lower for fatal in fatal_indicators):
            return RetryDecision(
                should_retry=False,
                retry_count=current_step_retries,
                reason=f"Error '{error_message}' is non-retryable / security fatal.",
            )

        # 2. Max retries per step check
        if current_step_retries >= self.MAX_RETRIES_PER_STEP:
            return RetryDecision(
                should_retry=False,
                retry_count=current_step_retries,
                reason=f"Step {step_id} reached maximum retry limit ({self.MAX_RETRIES_PER_STEP}).",
            )

        # 3. Total task retries check
        if total_task_retries >= self.MAX_TOTAL_TASK_RETRIES:
            return RetryDecision(
                should_retry=False,
                retry_count=current_step_retries,
                reason=f"Task reached maximum total retries ({self.MAX_TOTAL_TASK_RETRIES}).",
            )

        # 4. Infinite loop detection (repeated identical error)
        history = self._error_history[task_id]
        if history.count(error_message) >= 2:
            return RetryDecision(
                should_retry=False,
                retry_count=current_step_retries,
                reason=f"Loop detected: Identical failure repeated {history.count(error_message)} times.",
            )

        # Record retry
        step_counts[step_id] = current_step_retries + 1
        history.append(error_message)
        backoff = round(0.2 * (2 ** current_step_retries), 2)

        return RetryDecision(
            should_retry=True,
            retry_count=step_counts[step_id],
            reason=f"Retrying step {step_id} (attempt {step_counts[step_id]}/{self.MAX_RETRIES_PER_STEP}).",
            backoff_seconds=backoff,
        )

    def reset_task(self, task_id: str):
        """Cleans up retry tracking state for a task."""
        self._retry_counts.pop(task_id, None)
        self._error_history.pop(task_id, None)


retry_manager = RetryManager()

