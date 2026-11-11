from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_registry import model_registry, HARDWARE_PROFILE, MODEL_CAPABILITY_MATRIX
from backend.app.database.repositories.base_repository import BaseRepository

router = APIRouter(tags=["Models"])


class SetRoleModelRequest(BaseModel):
    role: str = Field(..., description="Role: general, coding, reasoning, lightweight, embedding")
    model_name: str = Field(..., description="Model name e.g. qwen2.5:7b")


@router.get("/models")
@router.get("/api/models")
async def get_models():
    """Lists installed Ollama models, capability details, and role mappings."""
    return await model_registry.get_models_with_status()


@router.get("/models/status")
@router.get("/api/models/status")
async def get_models_status():
    """Returns actual operational connectivity to Ollama inference daemon and hardware capacity."""
    from backend.app.intelligence.openrouter_client import openrouter_client, NEMOTRON_MODEL_ID
    health = await ollama_client.check_health()
    return {
        "ollama": health,
        "openrouter": {
            "status": "configured" if openrouter_client.is_configured() else "unconfigured",
            "base_url": openrouter_client.base_url,
            "model": NEMOTRON_MODEL_ID,
            "display_name": "NVIDIA Nemotron 3 Ultra",
            "provider": "OpenRouter",
            "type": "Cloud",
            "is_free": True,
        },
        "hardware": HARDWARE_PROFILE,
        "recommended_models": MODEL_CAPABILITY_MATRIX,
    }


@router.get("/models/configs")
@router.get("/api/models/configs")
def get_model_configs():
    """Returns stored model configurations from MongoDB."""
    return model_registry.list_all_configs()


@router.post("/models/roles")
@router.post("/api/models/roles")
def set_model_role(req: SetRoleModelRequest):
    """Assigns an installed or preferred model to a role."""
    valid_roles = ["general", "coding", "reasoning", "lightweight", "embedding"]
    if req.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{req.role}'. Valid roles are: {valid_roles}"
        )
    return model_registry.set_model_for_role(req.role, req.model_name)


@router.get("/models/metrics")
@router.get("/api/models/metrics")
def get_model_metrics(limit: int = 50):
    """Retrieves latency and throughput metrics for models."""
    return BaseRepository("model_metrics").find_all(limit=limit, sort=[("timestamp", -1)])


@router.get("/models/ollama/health")
@router.get("/api/models/ollama/health")
@router.get("/api/ollama/health")
async def get_ollama_health(refresh: bool = False):
    """Returns actual operational connectivity to Ollama inference daemon."""
    from backend.app.intelligence.openrouter_client import openrouter_client, NEMOTRON_MODEL_ID, NEMOTRON_SUPER_VL_ID
    health = await ollama_client.check_health(force_refresh=refresh)
    return {
        **health,
        "openrouter": {
            "status": "configured" if openrouter_client.is_configured() else "unconfigured",
            "is_configured": openrouter_client.is_configured(),
            "models": [NEMOTRON_MODEL_ID, NEMOTRON_SUPER_VL_ID],
        },
    }


@router.post("/models/ollama/start")
@router.post("/api/models/ollama/start")
@router.post("/api/ollama/start")
async def start_ollama_daemon(timeout: int = 10):
    """
    Spawns the local Ollama background daemon on Windows/host if offline.
    Polls until responsive and returns health confirmation.
    """
    result = await ollama_client.start_daemon(timeout_seconds=timeout)
    return result
