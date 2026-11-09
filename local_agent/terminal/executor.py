"""
DODO Local Agent Terminal Executor
Executes commands inside authorized workspace boundaries with real-time streaming,
timeout enforcement, process tree cleanup, secret redaction, and audit logging.
"""
import asyncio
import datetime
import logging
import os
import sys
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from local_agent.config import local_settings
from local_agent.security import (
    CommandCategory,
    PermissionRisk,
    classify_command,
    jail_path,
    redact_secrets,
)
from local_agent.terminal.manager import process_manager

logger = logging.getLogger("dodo.local_agent.executor")

MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MB maximum output limit


class ExecutionAuditRecord:
    def __init__(
        self,
        execution_id: str,
        command: str,
        category: str,
        cwd: str,
        success: bool,
        exit_code: int,
        duration_ms: float,
        error: Optional[str] = None,
    ):
        self.execution_id = execution_id
        self.command = command
        self.category = category
        self.cwd = cwd
        self.success = success
        self.exit_code = exit_code
        self.duration_ms = duration_ms
        self.error = error
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "command": self.command,
            "category": self.category,
            "cwd": self.cwd,
            "success": self.success,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class LocalTerminalExecutor:
    """Safely runs commands inside authorized workspaces with real-time output capture."""

    def __init__(self):
        self._running_tasks: Dict[str, asyncio.subprocess.Process] = {}
        self._audit_history: List[ExecutionAuditRecord] = []
        self._max_audit = 500

    def get_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [record.to_dict() for record in self._audit_history[-limit:]]

    def _record_audit(
        self,
        execution_id: str,
        command: str,
        category: str,
        cwd: str,
        success: bool,
        exit_code: int,
        duration_ms: float,
        error: Optional[str] = None,
    ):
        record = ExecutionAuditRecord(
            execution_id=execution_id,
            command=command,
            category=category,
            cwd=cwd,
            success=success,
            exit_code=exit_code,
            duration_ms=duration_ms,
            error=error,
        )
        self._audit_history.append(record)
        if len(self._audit_history) > self._max_audit:
            self._audit_history.pop(0)

    async def cancel(self, execution_id: str) -> bool:
        """Cancels a running execution by execution ID."""
        proc = self._running_tasks.get(execution_id)
        if not proc:
            return False

        logger.info(f"Cancelling execution {execution_id} (PID: {proc.pid})...")
        try:
            if proc.pid:
                await process_manager.kill_process(proc.pid)
            else:
                proc.kill()
        except Exception as e:
            logger.warning(f"Error terminating cancelled process: {e}")

        return True

    async def execute(
        self,
        command: str,
        cwd: str = "",
        workspace_root: Optional[str] = None,
        timeout: int = 60,
        approved: bool = False,
        execution_id: Optional[str] = None,
        on_output: Optional[Callable[[str, str], Any]] = None,
        is_dev_server: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes an approved terminal command.
        Returns execution results including stdout, stderr, and exit_code.
        """
        exec_id = execution_id or str(uuid.uuid4())
        start_time = time.perf_counter()

        # 1. Security Classification & Permission Check
        category, risk, reason = classify_command(command)
        if category == CommandCategory.PROHIBITED:
            err = f"Security Policy Violation: {reason}"
            self._record_audit(exec_id, command, category.value, cwd, False, -1, 0, err)
            return {
                "execution_id": exec_id,
                "command": command,
                "category": category.value,
                "success": False,
                "exit_code": -1,
                "error": err,
                "stdout": "",
                "stderr": err,
            }

        # Check approval requirement
        if risk == PermissionRisk.REQUIRES_APPROVAL and not approved:
            err = f"Approval Required: {reason}"
            return {
                "execution_id": exec_id,
                "command": command,
                "category": category.value,
                "risk_level": risk.value,
                "requires_approval": True,
                "reason": reason,
                "success": False,
                "exit_code": -1,
                "error": err,
                "stdout": "",
                "stderr": "",
            }

        # 2. Path Jail Validation
        valid, working_dir, path_err = jail_path(cwd, workspace_root)
        if not valid:
            err = f"Path Jail Violation: {path_err}"
            self._record_audit(exec_id, command, category.value, cwd, False, -1, 0, err)
            return {
                "execution_id": exec_id,
                "command": command,
                "category": category.value,
                "success": False,
                "exit_code": -1,
                "error": err,
                "stdout": "",
                "stderr": err,
            }

        # Ensure working directory exists
        working_dir.mkdir(parents=True, exist_ok=True)

        # 3. Duplicate Dev Server Prevention
        if is_dev_server or category == CommandCategory.DEV_SERVER:
            existing = process_manager.find_duplicate(command, str(working_dir))
            if existing:
                return {
                    "execution_id": exec_id,
                    "command": command,
                    "category": category.value,
                    "success": True,
                    "already_running": True,
                    "pid": existing.pid,
                    "status": "running",
                    "stdout": f"[DODO Dev Server] Process already running on PID {existing.pid}.\n",
                    "stderr": "",
                    "exit_code": 0,
                }

        # 4. Resolve python executable on Windows to ensure the valid interpreter is used
        effective_command = command
        if sys.platform == "win32":
            if effective_command.startswith("python ") or effective_command == "python":
                effective_command = f'"{sys.executable}" ' + effective_command[7:]
            elif effective_command.startswith("python3 ") or effective_command == "python3":
                effective_command = f'"{sys.executable}" ' + effective_command[8:]

        # 5. Spawn Subprocess
        try:
            logger.info(f"Executing [{exec_id}]: '{command}' in '{working_dir}' (timeout: {timeout}s)")
            proc = await asyncio.create_subprocess_shell(
                effective_command,
                cwd=str(working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._running_tasks[exec_id] = proc

            # If dev server, register and run log capture in background without blocking
            if is_dev_server or category == CommandCategory.DEV_SERVER:
                record = process_manager.register_process(
                    pid=proc.pid,
                    proc=proc,
                    execution_id=exec_id,
                    command=command,
                    cwd=str(working_dir),
                    category=category.value,
                )

                async def monitor_dev_server():
                    try:
                        while True:
                            line_b = await proc.stdout.readline()
                            if not line_b:
                                break
                            record.append_log(line_b.decode("utf-8", errors="replace"))
                    except Exception:
                        pass

                asyncio.create_task(monitor_dev_server())

                # Quick startup check (0.2s)
                try:
                    await asyncio.wait_for(proc.wait(), timeout=0.2)
                    if proc.returncode != 0:
                        stderr_b = await proc.stderr.read()
                        err_out = stderr_b.decode("utf-8", errors="replace")
                        return {
                            "execution_id": exec_id,
                            "command": command,
                            "category": category.value,
                            "success": False,
                            "exit_code": proc.returncode,
                            "error": f"Dev server failed on startup with code {proc.returncode}: {err_out}",
                            "stdout": "",
                            "stderr": err_out,
                        }
                except asyncio.TimeoutError:
                    pass

                self._record_audit(exec_id, command, category.value, str(working_dir), True, 0, 200, None)
                return {
                    "execution_id": exec_id,
                    "command": command,
                    "category": category.value,
                    "success": True,
                    "status": "running",
                    "is_dev_server": True,
                    "pid": proc.pid,
                    "stdout": f"[DODO Dev Server] Background server process started on PID {proc.pid}.\n",
                    "stderr": "",
                    "exit_code": 0,
                    "duration_ms": 200.0,
                }

            # Asynchronous Stream Reader
            stdout_lines: List[str] = []
            stderr_lines: List[str] = []
            total_bytes = 0

            async def read_stream(stream, is_stderr: bool):
                nonlocal total_bytes
                while True:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="replace")
                    line_redacted = redact_secrets(line)
                    total_bytes += len(line_bytes)

                    if is_stderr:
                        stderr_lines.append(line_redacted)
                    else:
                        stdout_lines.append(line_redacted)

                    if on_output:
                        try:
                            res = on_output("stderr" if is_stderr else "stdout", line_redacted)
                            if asyncio.iscoroutine(res):
                                await res
                        except Exception as e:
                            logger.debug(f"Error in on_output callback: {e}")

                    # Check output cap
                    if total_bytes > MAX_OUTPUT_BYTES:
                        msg = "\n[DODO Warning: Output limit of 1MB exceeded. Truncating...]\n"
                        stdout_lines.append(msg)
                        if on_output:
                            try:
                                res = on_output("stdout", msg)
                                if asyncio.iscoroutine(res):
                                    await res
                            except Exception:
                                pass
                        break

            # Run stream readers concurrently with process wait
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        read_stream(proc.stdout, False),
                        read_stream(proc.stderr, True),
                        proc.wait(),
                    ),
                    timeout=float(timeout),
                )
            except asyncio.TimeoutError:
                logger.warning(f"Execution {exec_id} timed out after {timeout}s. Terminating PID {proc.pid}...")
                if proc.pid:
                    await process_manager.kill_process(proc.pid)
                else:
                    proc.kill()
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                timeout_msg = f"\n[DODO Error: Execution timed out after {timeout} seconds.]\n"
                stderr_lines.append(timeout_msg)
                self._record_audit(exec_id, command, category.value, str(working_dir), False, -1, duration_ms, "Timed out")
                return {
                    "execution_id": exec_id,
                    "command": command,
                    "category": category.value,
                    "success": False,
                    "exit_code": -1,
                    "timed_out": True,
                    "error": f"Command timed out after {timeout}s",
                    "stdout": "".join(stdout_lines),
                    "stderr": "".join(stderr_lines),
                    "duration_ms": duration_ms,
                }

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            exit_code = proc.returncode if proc.returncode is not None else 0
            success = exit_code == 0
            stdout_text = "".join(stdout_lines)
            stderr_text = "".join(stderr_lines)

            self._record_audit(
                exec_id,
                command,
                category.value,
                str(working_dir),
                success,
                exit_code,
                duration_ms,
                None if success else f"Process exited with code {exit_code}",
            )

            return {
                "execution_id": exec_id,
                "command": command,
                "category": category.value,
                "success": success,
                "exit_code": exit_code,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            err_msg = str(e)
            self._record_audit(exec_id, command, category.value, str(working_dir), False, -1, duration_ms, err_msg)
            return {
                "execution_id": exec_id,
                "command": command,
                "category": category.value,
                "success": False,
                "exit_code": -1,
                "error": err_msg,
                "stdout": "",
                "stderr": err_msg,
                "duration_ms": duration_ms,
            }
        finally:
            self._running_tasks.pop(exec_id, None)


terminal_executor = LocalTerminalExecutor()
