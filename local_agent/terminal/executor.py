import asyncio
import logging
from typing import Any, Dict, Optional
from local_agent.security import jail_path
from local_agent.config import local_settings

logger = logging.getLogger("dodo.local_agent.terminal")


class LocalTerminalExecutor:
    """Safely runs commands inside the authorized workspace directory with timeout limits."""

    def __init__(self):
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}

    async def execute(self, command: str, cwd: str = "", timeout: int = 60) -> Dict[str, Any]:
        valid, working_dir, err = jail_path(cwd)
        if not valid:
            return {"error": err, "success": False, "exit_code": -1}

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(timeout)
            )
            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            return {"error": f"Execution timed out after {timeout}s", "success": False, "exit_code": -1}
        except Exception as e:
            return {"error": str(e), "success": False, "exit_code": -1}


terminal_executor = LocalTerminalExecutor()

