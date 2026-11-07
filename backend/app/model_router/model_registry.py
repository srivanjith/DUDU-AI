from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.database.repositories.model_repository import ModelRepository


class ModelRegistry:
    """
    Maintains the available model profiles, roles, hardware requirements,
    and configurations.
    """

    def __init__(self):
        self.repo = ModelRepository()
        self.repo.seed_default_models()

    def get_role_mapping(self) -> Dict[str, str]:
        """Returns the active model configured for each role."""
        configs = self.repo.find_all({"is_active": True})
        role_map = {
            "general": settings.DEFAULT_GENERAL_MODEL,
            "coding": settings.DEFAULT_CODING_MODEL,
            "reasoning": settings.DEFAULT_REASONING_MODEL,
            "lightweight": settings.DEFAULT_LIGHTWEIGHT_MODEL,
            "embedding": settings.DEFAULT_EMBEDDING_MODEL,
        }
        for cfg in configs:
            role = cfg.get("role")
            model_name = cfg.get("model_name")
            if role and model_name:
                role_map[role] = model_name
        return role_map

    def get_model_for_role(self, role: str) -> str:
        mapping = self.get_role_mapping()
        return mapping.get(role, settings.DEFAULT_GENERAL_MODEL)

    def set_model_for_role(self, role: str, model_name: str) -> Dict[str, Any]:
        existing = self.repo.collection.find_one({"role": role})
        if existing:
            return self.repo.update(str(existing["_id"]), {"model_name": model_name, "is_active": True})
        else:
            return self.repo.create({"model_name": model_name, "role": role, "is_active": True})

    def list_all_configs(self) -> List[Dict[str, Any]]:
        return self.repo.find_all()


model_registry = ModelRegistry()

