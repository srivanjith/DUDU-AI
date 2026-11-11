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

    VISION_KEYWORDS = [
        "screenshot", "visual", "ui inspection", "viewport", "layout defect",
        "responsive check", "image analysis", "visual bug", "visual analysis"
    ]

    COMPLEX_CODING_KEYWORDS = [
        "full-stack", "fullstack", "e-commerce", "ecommerce", "system architecture",
        "next.js", "architect", "multi-file", "complete application", "from scratch",
        "admin dashboard", "checkout workflow"
    ]

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
        """Classifies incoming task into vision, complex_architecture, reasoning, coding, or lightweight."""
        prompt_lower = prompt.lower().strip()

        if prompt_lower in self.LIGHTWEIGHT_EXACT or (len(prompt.split()) <= 2 and not any(kw in prompt_lower for kw in self.CODING_KEYWORDS)):
            return "lightweight"

        # 1. Vision & UI Screenshot Understanding
        if any(kw in prompt_lower for kw in self.VISION_KEYWORDS):
            return "vision"

        # 2. Complex Full-Stack Architecture & Planning
        if any(kw in prompt_lower for kw in self.COMPLEX_CODING_KEYWORDS):
            return "complex_architecture"

        # 3. Reasoning & Architecture Planning
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
        if task_type in ["complex_architecture", "reasoning"] or word_count > 60 or "full stack" in prompt.lower() or "from scratch" in prompt.lower():
            return "high"
        if task_type in ["coding", "vision"] or word_count > 25:
            return "medium"
        return "low"

    async def route(self, prompt: str, requested_model: Optional[str] = None) -> TaskClassificationResult:
        """
        Executes high-performance routing workflow:
        1. If user explicitly requested a cloud model, route directly to OpenRouter without touching Ollama.
        2. Visual screenshot understanding -> Nemotron Super VL (Cloud OpenRouter).
        3. Complex full-stack / architecture -> Nemotron 3 Ultra (Cloud OpenRouter).
        4. Simple coding / quick bug fixes -> Qwen2.5-Coder (Local Ollama).
        5. Preserves local-only mode and requires cloud consent.
        6. Accurately reports actual handled model and connectivity status.
        """
        from backend.app.intelligence.openrouter_client import (
            openrouter_client,
            NEMOTRON_MODEL_ID,
            NEMOTRON_SUPER_VL_ID,
        )

        # 1. Direct Cloud Route (Zero Ollama dependency)
        if requested_model and requested_model != "auto":
            if requested_model in [NEMOTRON_SUPER_VL_ID, "nemotron-super-vl"] or "super-vl" in requested_model.lower():
                is_cfg = openrouter_client.is_configured()
                return TaskClassificationResult(
                    task_type="visual_understanding",
                    complexity="high",
                    selected_model=NEMOTRON_SUPER_VL_ID,
                    role="vision",
                    reason="User explicitly selected NVIDIA Nemotron Super VL (Visual AI • Cloud).",
                    is_installed=is_cfg,
                    hardware_fit="Cloud Hosted (0% local VRAM)",
                    provider="OpenRouter",
                )

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

        # 2. Local Model Verification
        ollama_health = await ollama_client.check_health()
        is_ollama_online = ollama_health.get("status") == "online"
        installed_names = ollama_health.get("models", []) if is_ollama_online else []

        # Explicit user selection of a local model
        if requested_model and requested_model != "auto":
            is_present = is_ollama_online and any(
                requested_model in n or n.startswith(f"{requested_model}:") for n in installed_names
            )
            cap = MODEL_CAPABILITY_MATRIX.get(requested_model, {})
            vram_req = cap.get("vram_required_gb", 4.0)
            fit = "100% VRAM offload" if vram_req <= HARDWARE_PROFILE["vram_headroom_gb"] else "Hybrid GPU/RAM offload"
            reason = (
                f"User explicitly selected '{requested_model}'."
                if is_ollama_online
                else f"User selected '{requested_model}', but Ollama daemon is currently offline."
            )
            return TaskClassificationResult(
                task_type="user_override",
                complexity="user_defined",
                selected_model=requested_model,
                role="custom",
                reason=reason,
                is_installed=is_present,
                hardware_fit=fit,
                provider="Ollama",
            )

        task_type = self.classify_task(prompt)
        complexity = self.estimate_complexity(prompt, task_type)

        # Rule 1: Visual screenshot understanding -> Nemotron Super VL
        if task_type == "vision" and settings.ALLOW_CLOUD_INFERENCE and openrouter_client.is_configured():
            return TaskClassificationResult(
                task_type="vision",
                complexity=complexity,
                selected_model=NEMOTRON_SUPER_VL_ID,
                role="vision",
                reason="Auto-routed visual screenshot analysis to NVIDIA Nemotron Super VL.",
                is_installed=True,
                hardware_fit="Cloud Hosted (0% local VRAM)",
                provider="OpenRouter",
            )

        # Rule 2: Complex full-stack development & architecture planning -> Nemotron Ultra
        if task_type in ["complex_architecture", "reasoning"] and settings.ALLOW_CLOUD_INFERENCE and openrouter_client.is_configured():
            from backend.app.core.security import SECRET_PATTERNS
            has_secret = any(re.search(pat, prompt) for pat in SECRET_PATTERNS)
            if not has_secret and ".env" not in prompt:
                return TaskClassificationResult(
                    task_type=task_type,
                    complexity=complexity,
                    selected_model=NEMOTRON_MODEL_ID,
                    role="reasoning",
                    reason="Auto-routed complex full-stack / architecture task to NVIDIA Nemotron 3 Ultra (550B MoE).",
                    is_installed=True,
                    hardware_fit="Cloud Hosted (0% local VRAM)",
                    provider="OpenRouter",
                )

        # Rule 3: Simple coding tasks & quick bug fixes -> Qwen local
        role_map = {
            "lightweight": "lightweight",
            "general": "general",
            "coding": "coding",
            "reasoning": "coding",
            "complex_architecture": "coding",
            "vision": "general",
        }
        target_role = role_map.get(task_type, "coding")
        configured_model = model_registry.get_model_for_role(target_role)

        selected_model = configured_model
        is_installed = is_ollama_online and any(
            configured_model in name or name.startswith(f"{configured_model}:") for name in installed_names
        )
        if not is_ollama_online:
            reason = f"Auto-routed to {configured_model} (Local • Ollama), but Ollama daemon is offline."
        else:
            reason = f"Auto-routed to local {target_role} model '{configured_model}' ({complexity} complexity)."

        # If configured model is not installed but another model is installed, gracefully select best installed
        if is_ollama_online and not is_installed and installed_names:
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
            provider="Ollama",
        )


model_router = ModelRouter()
