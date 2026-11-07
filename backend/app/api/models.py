from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_registry import model_registry
from backend.app.database.repositories.base_repository import BaseRepository

router = APIRouter(prefix="/models", tags=["Models"])


class SetRoleModelRequest(BaseModel):
    role: str
    model_name: str


@router.get("")
async def get_models():
    """Lists installed Ollama models and role mapping."""
    installed = await ollama_client.list_models()
    role_map = model_registry.get_role_mapping()
    return {
        "installed_models": installed,
        "role_mapping": role_map,
        "model_count": len(installed),
    }


@router.get("/configs")
def get_model_configs():
    return model_registry.list_all_configs()


@router.post("/roles")
def set_model_role(req: SetRoleModelRequest):
    return model_registry.set_model_for_role(req.role, req.model_name)


@router.get("/metrics")
def get_model_metrics(limit: int = 50):
    return BaseRepository("model_metrics").find_all(limit=limit, sort=[("timestamp", -1)])

