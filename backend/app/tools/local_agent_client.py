"""
DODO Local Agent Client
Backend HTTP/WebSocket bridge to communicate with the authenticated Local Agent runtime.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("dodo.tools.local_agent_client")


class LocalAgentClient:
    """Communicates with the external authenticated DODO Local Agent process."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        secret_token: Optional[str] = None,
    ):
        self.base_url = base_url or f"http://{settings.LOCAL_AGENT_HOST}:{settings.LOCAL_AGENT_PORT}"
        self.secret_token = secret_token or settings.LOCAL_AGENT_SECRET_TOKEN
        self.timeout = 120.0

    def _headers(self) -> Dict[str, str]:
        return {
            "X-DODO-Token": self.secret_token,
            "Content-Type": "application/json",
        }

    async def get_status(self) -> Dict[str, Any]:
        """Queries the Local Agent health endpoint."""
        url = f"{self.base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    data["paired"] = True
                    return data
                return {"status": "error", "paired": False, "code": res.status_code}
        except Exception as e:
            return {
                "status": "offline",
                "paired": False,
                "host": settings.LOCAL_AGENT_HOST,
                "port": settings.LOCAL_AGENT_PORT,
                "error": str(e),
            }

    async def execute(
        self,
        command: str,
        cwd: str = "",
        workspace_root: Optional[str] = None,
        timeout: int = 60,
        approved: bool = False,
        execution_id: Optional[str] = None,
        is_dev_server: bool = False,
    ) -> Dict[str, Any]:
        """Sends an execution request to the Local Agent."""
        url = f"{self.base_url}/api/exec"
        payload = {
            "command": command,
            "cwd": cwd,
            "workspace_root": workspace_root,
            "timeout": timeout,
            "approved": approved,
            "execution_id": execution_id,
            "is_dev_server": is_dev_server,
        }
        try:
            async with httpx.AsyncClient(timeout=float(timeout + 10)) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code == 401:
                    return {
                        "success": False,
                        "exit_code": -1,
                        "error": "Local Agent Authentication Failed: Invalid secret token.",
                    }
                return res.json()
        except Exception as e:
            logger.warning(f"Failed to communicate with Local Agent at {url}: {e}")
            # Fallback to internal terminal execution if local agent is not running
            from local_agent.terminal.executor import terminal_executor
            return await terminal_executor.execute(
                command=command,
                cwd=cwd,
                workspace_root=workspace_root,
                timeout=timeout,
                approved=approved,
                execution_id=execution_id,
                is_dev_server=is_dev_server,
            )

    async def cancel(self, execution_id: str) -> bool:
        """Sends cancellation request for execution."""
        url = f"{self.base_url}/api/cancel"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, headers=self._headers(), json={"execution_id": execution_id})
                if res.status_code == 200:
                    return res.json().get("cancelled", False)
                return False
        except Exception:
            from local_agent.terminal.executor import terminal_executor
            return await terminal_executor.cancel(execution_id)

    async def list_processes(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Lists running dev servers and background processes."""
        url = f"{self.base_url}/api/processes?active_only={str(active_only).lower()}"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url, headers=self._headers())
                if res.status_code == 200:
                    return res.json()
                return []
        except Exception:
            from local_agent.terminal.manager import process_manager
            return process_manager.list_processes(active_only=active_only)

    async def kill_process(self, pid: int) -> bool:
        """Kills a process tree."""
        url = f"{self.base_url}/api/processes/{pid}/kill"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, headers=self._headers())
                return res.status_code == 200
        except Exception:
            from local_agent.terminal.manager import process_manager
            return await process_manager.kill_process(pid)

    async def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches audit history."""
        url = f"{self.base_url}/api/history?limit={limit}"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url, headers=self._headers())
                if res.status_code == 200:
                    return res.json()
                return []
        except Exception:
            from local_agent.terminal.executor import terminal_executor
            return terminal_executor.get_audit_history(limit=limit)


local_agent_client = LocalAgentClient()

