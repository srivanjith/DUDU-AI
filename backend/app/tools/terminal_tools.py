import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.security import check_command_safety, validate_workspace_path
from backend.app.tools.registry import tool_registry, ToolDefinition, ToolParameter

RUNNING_PROCESSES: Dict[str, asyncio.subprocess.Process] = {}


@tool_registry.register(ToolDefinition(
    name="execute_terminal_command",
    description="Executes a controlled command within the authorized project workspace.",
    permission_level="controlled",
    parameters=[
        ToolParameter(name="command", type="string", description="Terminal command to execute"),
        ToolParameter(name="cwd", type="string", description="Working directory relative to workspace root", required=False, default=""),
        ToolParameter(name="timeout_seconds", type="integer", description="Maximum time in seconds to wait", required=False, default=60),
    ]
))
async def execute_terminal_command(command: str, cwd: str = "", timeout_seconds: int = 60) -> Dict[str, Any]:
    # Check command safety
    is_safe, perm_level, reason = check_command_safety(command)
    if not is_safe or perm_level == "prohibited":
        return {"error": f"Security Policy Violation: {reason}"}

    # Validate working directory
    valid, working_dir, err = validate_workspace_path(cwd)
    if not valid:
        return {"error": err}
    if not working_dir.exists():
        working_dir.mkdir(parents=True, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(working_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(timeout_seconds)
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            return {
                "command": command,
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "success": proc.returncode == 0,
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "command": command,
                "error": f"Command timed out after {timeout_seconds} seconds.",
                "exit_code": -1,
                "success": False,
            }
    except Exception as e:
        return {
            "command": command,
            "error": f"Failed to execute command: {str(e)}",
            "exit_code": -1,
            "success": False,
        }

