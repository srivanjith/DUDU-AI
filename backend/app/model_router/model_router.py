import re
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_registry import model_registry, MODEL_CAPABILITY_MATRIX, HARDWARE_PROFILE


class TaskClassificationResult:
    def __init__(
        self,
        task_type: str,
        complexity: str,
        selected_model: str,
        role: str,
        reason: str,
        is_installed: bool = False,
        hardware_fit: str = "optimal",
        provider: str = "Ollama",
    ):
        self.task_type = task_type
        self.complexity = complexity
        self.selected_model = selected_model
        self.role = role
        self.reason = reason
        self.is_installed = is_installed
        self.hardware_fit = hardware_fit
        self.provider = provider

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "complexity": self.complexity,
            "selected_model": self.selected_model,
            "role": self.role,
            "reason": self.reason,
            "is_installed": self.is_installed,
            "hardware_fit": self.hardware_fit,
            "provider": self.provider,
        }


class ModelRouter:
    """
    Intelligent Model Router for DODO.
    Classifies user tasks, estimates complexity, checks local hardware constraints,
    verifies model availability in Ollama, and dynamically routes to the optimal model.
    Never silently falls back to cloud AI services.
    """

    CODING_KEYWORDS = [
        "code", "function", "class", "react", "fastapi", "python", "javascript",
        "typescript", "mongodb", "database", "api", "endpoint", "bug", "error",
        "fix", "refactor", "test", "docker", "component", "html", "css", "sql", "def ", "import "
    ]

    REASONING_KEYWORDS = [
        "plan", "architect", "design", "step-by-step", "analyze", "strategy",
        "evaluate", "compare", "trade-offs", "complex", "autonomous", "system design"
    ]

    LIGHTWEIGHT_EXACT = ["hi", "hello", "hey", "ping", "test", "ok", "yes", "no", "thanks", "thank you"]

    def classify_task(self, prompt: str) -> str:
        """Classifies incoming task into general, coding, reasoning, or lightweight."""
        prompt_lower = prompt.lower().strip()

        if prompt_lower in self.LIGHTWEIGHT_EXACT or (len(prompt.split()) <= 2 and not any(kw in prompt_lower for kw in self.CODING_KEYWORDS)):
            return "lightweight"

        # Check for complex planning / reasoning
        reasoning_score = sum(1 for kw in self.REASONING_KEYWORDS if kw in prompt_lower)
        coding_score = sum(1 for kw in self.CODING_KEYWORDS if kw in prompt_lower)

        if reasoning_score >= 2 or ("build" in prompt_lower and coding_score >= 2):
            return "reasoning"
        if coding_score >= 1 or re.search(r"```|[{}();=]", prompt):
            return "coding"
        return "general"

    def estimate_complexity(self, prompt: str, task_type: str) -> str:
        """Estimates task complexity: low, medium, or high."""
        word_count = len(prompt.split())
        if task_type == "reasoning" or word_count > 100 or "full stack" in prompt.lower() or "from scratch" in prompt.lower():
            return "high"
        if task_type == "coding" or word_count > 30:
            return "medium"
        return "low"

    async def route(self, prompt: str, requested_model: Optional[str] = None) -> TaskClassificationResult:
        """
        Executes routing workflow:
        1. If user explicitly requested a model, verify its presence.
        2. Otherwise classify task intent and estimate complexity.
        3. Match to configured role model.
        4. Cross-check against installed Ollama models.
        5. Evaluate hardware VRAM fit.
        """
        installed = await ollama_client.list_models()
        installed_names = [m.get("name", "") for m in installed]

        from backend.app.intelligence.openrouter_client import openrouter_client, NEMOTRON_MODEL_ID

        if requested_model and requested_model != "auto":
            if requested_model == NEMOTRON_MODEL_ID or "nemotron" in requested_model.lower():
                is_cfg = openrouter_client.is_configured()
                return TaskClassificationResult(
                    task_type="cloud_inference",
                    complexity="high",
                    selected_model=NEMOTRON_MODEL_ID,
                    role="reasoning",
                    reason="User explicitly selected NVIDIA Nemotron 3 Ultra (Cloud • OpenRouter).",
                    is_installed=is_cfg,
                    hardware_fit="Cloud Hosted (0% local VRAM)",
                    provider="OpenRouter",
                )

            is_present = any(requested_model in n or n.startswith(f"{requested_model}:") for n in installed_names)
            cap = MODEL_CAPABILITY_MATRIX.get(requested_model, {})
            vram_req = cap.get("vram_required_gb", 4.0)
            fit = "100% VRAM offload" if vram_req <= HARDWARE_PROFILE["vram_headroom_gb"] else "Hybrid GPU/RAM offload"
            return TaskClassificationResult(
                task_type="user_override",
                complexity="user_defined",
                selected_model=requested_model,
                role="custom",
                reason=f"User explicitly selected '{requested_model}'.",
                is_installed=is_present,
                hardware_fit=fit,
                provider="Ollama",
            )

        task_type = self.classify_task(prompt)
        complexity = self.estimate_complexity(prompt, task_type)

        # Cloud routing rule: Complex reasoning with explicit cloud permission
        if task_type == "reasoning" and settings.ALLOW_CLOUD_INFERENCE and openrouter_client.is_configured():
            from backend.app.core.security import SECRET_PATTERNS
            has_secret = any(re.search(pat, prompt) for pat in SECRET_PATTERNS)
            if not has_secret and ".env" not in prompt:
                return TaskClassificationResult(
                    task_type=task_type,
                    complexity=complexity,
                    selected_model=NEMOTRON_MODEL_ID,
                    role="reasoning",
                    reason="Auto-routed complex reasoning task to cloud NVIDIA Nemotron 3 Ultra (550B MoE).",
                    is_installed=True,
                    hardware_fit="Cloud Hosted (0% local VRAM)",
                    provider="OpenRouter",
                )

        role_map = {
            "lightweight": "lightweight",
            "general": "general",
            "coding": "coding",
            "reasoning": "reasoning",
        }
        target_role = role_map.get(task_type, "general")
        configured_model = model_registry.get_model_for_role(target_role)

        selected_model = configured_model
        is_installed = any(configured_model in name or name.startswith(f"{configured_model}:") for name in installed_names)
        reason = f"Routed to {target_role} model '{configured_model}' based on {task_type} intent ({complexity} complexity)."

        # If configured model is not installed but another model is installed, gracefully select best installed
        if not is_installed and installed_names:
            selected_model = installed_names[0]
            is_installed = True
            reason = f"Preferred '{configured_model}' is not downloaded. Dynamically routed to installed '{selected_model}'."

        cap = MODEL_CAPABILITY_MATRIX.get(selected_model, {})
        vram_req = cap.get("vram_required_gb", 4.0)
        fit = "100% VRAM offload" if vram_req <= HARDWARE_PROFILE["vram_headroom_gb"] else "Hybrid GPU/RAM offload"

        return TaskClassificationResult(
            task_type=task_type,
            complexity=complexity,
            selected_model=selected_model,
            role=target_role,
            reason=reason,
            is_installed=is_installed,
            hardware_fit=fit,
        )


model_router = ModelRouter()
