import logging
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.database.repositories.model_repository import ModelRepository
from backend.app.intelligence.ollama_client import ollama_client

logger = logging.getLogger("dodo.model_registry")

# Hardware specifications for local machine
HARDWARE_PROFILE = {
    "system_ram_gb": 16.0,
    "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
    "gpu_vram_gb": 4.0,
    "vram_headroom_gb": 3.2,  # usable VRAM excluding OS display buffer
    "recommended_quantization": "Q4_K_M (4-bit)",
}

# Verified capability matrix (do not claim tool calling unless verified)
MODEL_CAPABILITY_MATRIX = {
    "qwen2.5:7b": {
        "family": "Qwen",
        "parameters": "7.6B",
        "context_window": 32768,
        "supports_tools": True,
        "recommended_role": "general",
        "vram_required_gb": 4.7,
        "notes": "Fast general intelligence with partial GPU offload on 4GB VRAM.",
    },
    "qwen2.5-coder:7b": {
        "family": "Qwen",
        "parameters": "7.6B",
        "context_window": 32768,
        "supports_tools": True,
        "recommended_role": "coding",
        "vram_required_gb": 4.7,
        "notes": "State-of-the-art open-weight code generation and syntax comprehension.",
    },
    "deepseek-r1:8b": {
        "family": "DeepSeek",
        "parameters": "8.0B",
        "context_window": 32768,
        "supports_tools": False,  # R1 reasoning models output chain-of-thought, not function calls
        "recommended_role": "reasoning",
        "vram_required_gb": 4.9,
        "notes": "Specialized reasoning and multi-step architectural planning.",
    },
    "llama3.2:1b": {
        "family": "Llama",
        "parameters": "1.2B",
        "context_window": 8192,
        "supports_tools": False,
        "recommended_role": "lightweight",
        "vram_required_gb": 1.3,
        "notes": "Ultra-lightweight model that fits 100% inside 4GB VRAM (>60 tokens/sec).",
    },
    "llama3.2:3b": {
        "family": "Llama",
        "parameters": "3.2B",
        "context_window": 8192,
        "supports_tools": True,
        "recommended_role": "general",
        "vram_required_gb": 2.5,
        "notes": "Compact general assistant that fits 100% inside 4GB VRAM.",
    },
    "gemma2:2b": {
        "family": "Gemma",
        "parameters": "2.6B",
        "context_window": 8192,
        "supports_tools": False,
        "recommended_role": "lightweight",
        "vram_required_gb": 2.1,
        "notes": "Google open model, highly efficient for fast chat and summaries.",
    },
    "nomic-embed-text": {
        "family": "Nomic",
        "parameters": "137M",
        "context_window": 2048,
        "supports_tools": False,
        "recommended_role": "embedding",
        "vram_required_gb": 0.6,
        "notes": "Local dense embeddings for semantic code retrieval.",
    },
    "nvidia/nemotron-3-ultra-550b-a55b:free": {
        "family": "Nemotron",
        "provider": "OpenRouter",
        "type": "Cloud",
        "display_name": "NVIDIA Nemotron 3 Ultra",
        "parameters": "550B (MoE)",
        "context_window": 131072,
        "supports_tools": True,
        "recommended_role": "reasoning",
        "vram_required_gb": 0.0,
        "notes": "State-of-the-art 550B parameter cloud reasoning and coding model via OpenRouter.",
    },
    "nvidia/nemotron-super-vl": {
        "family": "Nemotron",
        "provider": "OpenRouter",
        "type": "Cloud",
        "display_name": "NVIDIA Nemotron Super VL",
        "parameters": "Vision-Language",
        "context_window": 131072,
        "supports_tools": True,
        "recommended_role": "vision",
        "vram_required_gb": 0.0,
        "notes": "Visual multimodal model for screenshot understanding and responsive UI layout validation.",
    },
}


class ModelRegistry:
    """
    Manages model roles, hardware compatibility checks, Ollama availability verification,
    and persistent configuration in MongoDB.
    """

    def __init__(self):
        self.repo = ModelRepository()
        self.repo.seed_default_models()

    def get_role_mapping(self) -> Dict[str, str]:
        """Returns the active model assigned to each role."""
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
        """Assigns an installed or target model to a specific role."""
        existing = self.repo.collection.find_one({"role": role})
        if existing:
            return self.repo.update(str(existing["_id"]), {"model_name": model_name, "is_active": True})
        else:
            return self.repo.create({"model_name": model_name, "role": role, "is_active": True})

    async def get_models_with_status(self) -> Dict[str, Any]:
        """
        Dynamically queries Ollama for installed models and cross-references
        with role mappings and hardware capability data.
        """
        installed = await ollama_client.list_models()
        installed_names = [m.get("name", "") for m in installed]
        role_map = self.get_role_mapping()

        # Build status for each configured role
        roles_status = {}
        for role, model_name in role_map.items():
            is_present = any(model_name in name or name.startswith(f"{model_name}:") for name in installed_names)
            cap = MODEL_CAPABILITY_MATRIX.get(model_name, {})
            roles_status[role] = {
                "assigned_model": model_name,
                "is_installed": is_present,
                "supports_tools": cap.get("supports_tools", False),
                "context_window": cap.get("context_window", 4096),
                "family": cap.get("family", "Unknown"),
            }

        from backend.app.intelligence.openrouter_client import openrouter_client, NEMOTRON_MODEL_ID, NEMOTRON_SUPER_VL_ID

        cloud_models = [
            {
                "id": NEMOTRON_MODEL_ID,
                "name": "NVIDIA Nemotron 3 Ultra",
                "display_name": "NVIDIA Nemotron 3 Ultra (Cloud • OpenRouter)",
                "provider": "OpenRouter",
                "type": "Cloud",
                "parameters": "550B (MoE)",
                "context_window": 131072,
                "supports_tools": True,
                "is_configured": openrouter_client.is_configured(),
                "is_free": True,
                "notes": "State-of-the-art 550B parameter cloud reasoning and coding model via OpenRouter.",
            },
            {
                "id": NEMOTRON_SUPER_VL_ID,
                "name": "NVIDIA Nemotron Super VL",
                "display_name": "NVIDIA Nemotron Super VL (Cloud • OpenRouter)",
                "provider": "OpenRouter",
                "type": "Cloud",
                "parameters": "Vision-Language",
                "context_window": 131072,
                "supports_tools": True,
                "is_configured": openrouter_client.is_configured(),
                "is_free": True,
                "notes": "Visual multimodal model for screenshot understanding and responsive UI layout validation.",
            }
        ]

        return {
            "installed_models": installed,
            "installed_count": len(installed),
            "cloud_models": cloud_models,
            "role_mapping": role_map,
            "roles_status": roles_status,
            "hardware_profile": HARDWARE_PROFILE,
            "recommended_models": MODEL_CAPABILITY_MATRIX,
        }

    def list_all_configs(self) -> List[Dict[str, Any]]:
        return self.repo.find_all()


model_registry = ModelRegistry()
