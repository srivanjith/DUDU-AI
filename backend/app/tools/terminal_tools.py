"""
DODO Terminal Execution Tools
Routes terminal execution requests to the authenticated Local Agent runtime with
permission checks and path jailing.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.tools.local_agent_client import local_agent_client
from backend.app.tools.registry import PermissionLevel, ToolDefinition, ToolParameter, tool_registry

logger = logging.getLogger("dodo.tools.terminal")


@tool_registry.register(ToolDefinition(
    name="execute_terminal_command",
    description="Executes an approved command inside the authorized workspace via the authenticated Local Agent.",
    permission_level="controlled",
    parameters=[
        ToolParameter(name="command", type="string", description="Terminal command to execute"),
        ToolParameter(name="cwd", type="string", description="Subdirectory relative to workspace root", required=False, default=""),
        ToolParameter(name="workspace_root", type="string", description="Explicit workspace directory path", required=False, default=None),
        ToolParameter(name="timeout_seconds", type="integer", description="Maximum time in seconds to wait", required=False, default=60),
        ToolParameter(name="approved", type="boolean", description="Whether explicit user approval was granted", required=False, default=False),
        ToolParameter(name="execution_id", type="string", description="Optional execution tracking ID", required=False, default=None),
        ToolParameter(name="is_dev_server", type="boolean", description="Whether to run command as monitored dev server", required=False, default=False),
    ]
))
async def execute_terminal_command(
    command: str,
    cwd: str = "",
    workspace_root: Optional[str] = None,
    timeout_seconds: int = 60,
    approved: bool = False,
    execution_id: Optional[str] = None,
    is_dev_server: bool = False,
) -> Dict[str, Any]:
    """
    Executes terminal commands through the secure Local Agent.
    """
    effective_root = workspace_root or settings.AUTHORIZED_WORKSPACE_DIR
    res = await local_agent_client.execute(
        command=command,
        cwd=cwd,
        workspace_root=effective_root,
        timeout=timeout_seconds,
        approved=approved,
        execution_id=execution_id,
        is_dev_server=is_dev_server,
    )
    return res
