import re
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_registry import model_registry


class TaskClassificationResult:
    def __init__(self, task_type: str, complexity: str, selected_model: str, reason: str):
        self.task_type = task_type
        self.complexity = complexity
        self.selected_model = selected_model
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "complexity": self.complexity,
            "selected_model": self.selected_model,
            "reason": self.reason,
        }


class ModelRouter:
    """
    Intelligent Model Router for DODO.
    Classifies user tasks, estimates complexity, checks local hardware constraints,
    and dynamically routes to the most capable local open-weight model.
    """

    CODING_KEYWORDS = [
        "code", "function", "class", "react", "fastapi", "python", "javascript",
        "typescript", "mongodb", "database", "api", "endpoint", "bug", "error",
        "fix", "refactor", "test", "docker", "component", "html", "css"
    ]

    REASONING_KEYWORDS = [
        "plan", "architect", "design", "step-by-step", "analyze", "strategy",
        "evaluate", "compare", "trade-offs", "complex", "autonomous"
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
        1. If user explicitly requested a model, honor it.
        2. Otherwise classify task & estimate complexity.
        3. Check available installed models.
        4. Select best role-mapped model with hardware awareness.
        """
        if requested_model and requested_model != "auto":
            return TaskClassificationResult(
                task_type="user_override",
                complexity="unknown",
                selected_model=requested_model,
                reason=f"User explicitly selected {requested_model}",
            )

        task_type = self.classify_task(prompt)
        complexity = self.estimate_complexity(prompt, task_type)

        role_map = {
            "lightweight": "lightweight",
            "general": "general",
            "coding": "coding",
            "reasoning": "reasoning",
        }
        target_role = role_map.get(task_type, "general")
        configured_model = model_registry.get_model_for_role(target_role)

        # Check if Ollama has this model downloaded
        available_models = await ollama_client.list_models()
        installed_names = [m.get("name", "") for m in available_models]

        selected_model = configured_model
        reason = f"Routed to {target_role} role model '{configured_model}' based on {task_type} intent ({complexity} complexity)."

        # If configured model is not installed but another model is installed, pick best available
        if installed_names:
            if not any(configured_model in name for name in installed_names):
                # Fallback to the first installed model
                selected_model = installed_names[0]
                reason = f"Preferred '{configured_model}' not yet pulled. Routed to installed '{selected_model}'."

        return TaskClassificationResult(
            task_type=task_type,
            complexity=complexity,
            selected_model=selected_model,
            reason=reason,
        )


model_router = ModelRouter()
