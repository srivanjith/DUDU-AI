import os
import platform
import time
from typing import Any, Dict
from fastapi import APIRouter
import httpx

from backend.app.core.config import settings
from backend.app.database.mongodb import db_manager
from backend.app.intelligence.ollama_client import ollama_client

router = APIRouter(tags=["Health & Diagnostics"])

_START_TIME = time.time()


@router.get("/health")
@router.get("/api/health")
async def get_system_health() -> Dict[str, Any]:
    """Returns actual operational health of core DODO subsystems."""
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
        "uptime_seconds": round(time.time() - _START_TIME, 1),
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


@router.get("/diagnostics")
@router.get("/api/diagnostics")
async def get_unified_diagnostics() -> Dict[str, Any]:
    """
    Unified multi-subsystem diagnostic endpoint covering:
    Frontend, FastAPI Backend, Ollama, Database, Local Agent,
    Terminal, Browser Engine, Persistent Memory, and Agent Tasks.
    """
    health_base = await get_system_health()

    # 1. Frontend Check
    frontend_status = "offline"
    frontend_latency_ms = None
    try:
        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=1.5) as client:
            fe_res = await client.get("http://localhost:3000")
            if fe_res.status_code == 200:
                frontend_status = "online"
                frontend_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    except Exception:
        pass

    # 2. Browser Automation Status
    browser_diag = {
        "is_running": False,
        "open_tabs": 0,
        "console_errors_logged": 0,
        "network_errors_logged": 0,
    }
    try:
        from backend.app.browser.engine import browser_engine
        browser_diag["is_running"] = browser_engine.is_running()
        browser_diag["open_tabs"] = len(browser_engine._tabs)
        browser_diag["console_errors_logged"] = len(browser_engine.console_errors)
        browser_diag["network_errors_logged"] = len(browser_engine.network_failures)
    except Exception:
        pass

    # 3. Persistent Memory Status
    memory_diag = {"total_memories": 0, "categories": {}}
    try:
        from backend.app.memory.repository import memory_repo
        memory_diag["categories"] = memory_repo.count_by_category()
        memory_diag["total_memories"] = sum(memory_diag["categories"].values())
    except Exception:
        pass

    # 4. Agent Tasks Status
    tasks_diag = {"total": 0, "completed": 0, "failed": 0, "running": 0}
    try:
        from backend.app.database.repositories.project_repository import TaskRepository
        t_repo = TaskRepository()
        tasks = t_repo.find_all(limit=500)
        tasks_diag["total"] = len(tasks)
        tasks_diag["completed"] = sum(1 for t in tasks if t.get("status") == "completed")
        tasks_diag["failed"] = sum(1 for t in tasks if t.get("status") == "failed")
        tasks_diag["running"] = sum(1 for t in tasks if t.get("status") == "in_progress")
    except Exception:
        pass

    return {
        "status": health_base["status"],
        "timestamp": time.time(),
        "uptime_seconds": health_base["uptime_seconds"],
        "subsystems": {
            "frontend": {
                "status": frontend_status,
                "url": "http://localhost:3000",
                "latency_ms": frontend_latency_ms,
            },
            "backend": {
                "status": "online",
                "version": settings.VERSION,
                "pid": os.getpid(),
                "port": settings.PORT,
            },
            "database": health_base["database"],
            "inference_engine": health_base["inference_engine"],
            "local_agent": health_base["local_agent"],
            "browser_automation": browser_diag,
            "persistent_memory": memory_diag,
            "agent_tasks": tasks_diag,
        },
    }
