"""
DODO Cooperative Cancellation Token
Provides thread-safe and async-safe task cancellation signaling.
"""
import asyncio
from typing import Optional


class TaskCancelledException(Exception):
    """Raised when an active agent task execution is cancelled."""
    pass


class CancellationToken:
    """
    Cooperative cancellation mechanism for autonomous agent operations.
    Allows UI or API callers to signal cancellation cleanly to long-running loops.
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._is_cancelled = False
        self._reason: Optional[str] = None
        self._event = asyncio.Event()

    def cancel(self, reason: str = "Task cancelled by user."):
        """Sets the cancellation flag."""
        self._is_cancelled = True
        self._reason = reason
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def reason(self) -> str:
        return self._reason or "Cancelled"

    def check_cancelled(self):
        """Raises TaskCancelledException if cancelled."""
        if self._is_cancelled:
            raise TaskCancelledException(f"Task '{self.task_id}' was cancelled: {self.reason}")

    async def wait_until_cancelled(self):
        """Asynchronously waits until cancellation is triggered."""
        await self._event.wait()
