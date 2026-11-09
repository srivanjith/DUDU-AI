"""
DODO Local Agent Process & Dev Server Manager
Tracks process lifecycles, dev servers, background commands, prevents duplicates,
captures real-time output streams, and cleans up process trees.
"""
import asyncio
import datetime
import logging
import os
import signal
import subprocess
import sys
from typing import Any, Dict, List, Optional
from local_agent.security import redact_secrets

logger = logging.getLogger("dodo.local_agent.process_manager")


class ProcessRecord:
    def __init__(
        self,
        pid: int,
        execution_id: str,
        command: str,
        cwd: str,
        category: str = "DEV_SERVER",
        port: Optional[int] = None,
    ):
        self.pid = pid
        self.execution_id = execution_id
        self.command = command
        self.cwd = cwd
        self.category = category
        self.port = port
        self.status = "running"
        self.start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.end_time: Optional[str] = None
        self.exit_code: Optional[int] = None
        self.logs: List[str] = []
        self.max_log_lines = 1000

    def append_log(self, line: str):
        redacted = redact_secrets(line)
        self.logs.append(redacted)
        if len(self.logs) > self.max_log_lines:
            self.logs.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "execution_id": self.execution_id,
            "command": self.command,
            "cwd": self.cwd,
            "category": self.category,
            "port": self.port,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "exit_code": self.exit_code,
            "log_lines_count": len(self.logs),
            "recent_logs": self.logs[-20:],
        }


class ProcessManager:
    """
    Manages active dev servers and background processes.
    Prevents duplicate instances and enforces clean termination.
    """

    def __init__(self):
        self._processes: Dict[int, ProcessRecord] = {}
        self._async_procs: Dict[int, asyncio.subprocess.Process] = {}

    def get_process(self, pid: int) -> Optional[ProcessRecord]:
        return self._processes.get(pid)

    def list_processes(self, active_only: bool = True) -> List[Dict[str, Any]]:
        self._reap_finished()
        results = []
        for p in self._processes.values():
            if not active_only or p.status == "running":
                results.append(p.to_dict())
        return results

    def find_duplicate(self, command: str, cwd: str) -> Optional[ProcessRecord]:
        """Checks if a matching dev server / process is already running."""
        self._reap_finished()
        cmd_clean = command.strip().lower()
        for p in self._processes.values():
            if p.status == "running" and p.command.strip().lower() == cmd_clean:
                return p
        return None

    def register_process(
        self,
        pid: int,
        proc: asyncio.subprocess.Process,
        execution_id: str,
        command: str,
        cwd: str,
        category: str = "DEV_SERVER",
        port: Optional[int] = None,
    ) -> ProcessRecord:
        record = ProcessRecord(
            pid=pid,
            execution_id=execution_id,
            command=command,
            cwd=cwd,
            category=category,
            port=port,
        )
        self._processes[pid] = record
        self._async_procs[pid] = proc
        return record

    async def kill_process(self, pid: int) -> bool:
        """Terminates process and its child tree cleanly."""
        record = self._processes.get(pid)
        if not record:
            return False

        logger.info(f"Terminating process tree for PID {pid} ({record.command})...")
        try:
            if sys.platform == "win32":
                # Windows taskkill with /T (tree) and /F (force) ensures orphaned child workers are reaped
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception as e:
            logger.warning(f"Error terminating process tree for PID {pid}: {e}")

        # Try async proc terminate as well
        async_proc = self._async_procs.get(pid)
        if async_proc:
            try:
                async_proc.terminate()
            except Exception:
                pass

        record.status = "stopped"
        record.end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record.exit_code = -9
        return True

    def _reap_finished(self):
        """Checks for processes that exited independently."""
        for pid, record in list(self._processes.items()):
            if record.status == "running":
                async_proc = self._async_procs.get(pid)
                if async_proc and async_proc.returncode is not None:
                    record.status = "completed" if async_proc.returncode == 0 else "failed"
                    record.end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    record.exit_code = async_proc.returncode


process_manager = ProcessManager()

