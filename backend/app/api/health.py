import os
import platform
from typing import Any, Dict
from fastapi import APIRouter
import httpx
from backend.app.core.config import settings
from backend.app.database.mongodb import db_manager
from backend.app.intelligence.ollama_client import ollama_client

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def get_system_health() -> Dict[str, Any]:
    """Returns actual operational health of all DODO subsystems."""
    db_health = db_manager.check_health()
    ollama_health = await ollama_client.check_health()

    # Check local agent health
    local_agent_status = "offline"
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            res = await client.get(f"http://{settings.LOCAL_AGENT_HOST}:{settings.LOCAL_AGENT_PORT}/health")
            if res.status_code == 200:
                local_agent_status = "online"
    except Exception:
        pass

    return {
        "status": "healthy" if db_health["status"] in ["connected", "healthy_fallback"] else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
            "cpu_cores": os.cpu_count(),
        },
        "database": db_health,
        "inference_engine": ollama_health,
        "local_agent": {
            "status": local_agent_status,
            "host": settings.LOCAL_AGENT_HOST,
            "port": settings.LOCAL_AGENT_PORT,
            "authorized_workspace": settings.AUTHORIZED_WORKSPACE_DIR,
        },
    }

