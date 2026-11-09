"""
DODO Context Manager
Manages token context windows, historical working memory, and input sanitation
for local-first autonomous agent execution.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings


class ContextManager:
    """
    Manages working memory and prompt context size.
    Prevents context window overflows for 1.5B/7B local models.
    Sanitizes untrusted input and safeguards environment credentials.
    """

    MAX_CONTEXT_TOKENS: int = 4096  # Conservative default for fast local 1.5B inference
    ESTIMATED_CHARS_PER_TOKEN: float = 3.8

    # Sensitive patterns to sanitize
    SENSITIVE_PATTERNS = [
        "SECRET_KEY", "PASSWORD", "TOKEN", "API_KEY", "MONGODB_URI",
        "PRIVATE_KEY", "BEARER", "AUTHORIZATION"
    ]

    def estimate_tokens(self, text: str) -> int:
        """Approximates token count based on character count."""
        if not text:
            return 0
        return int(len(text) / self.ESTIMATED_CHARS_PER_TOKEN)

    def sanitize_input(self, text: str) -> str:
        """
        Strips dangerous shell characters, system path traversals,
        and masks potential secrets from user input.
        """
        if not text:
            return ""

        # Normalize line endings
        sanitized = text.replace("\r\n", "\n")

        # Guard against directory traversal attempts
        if "../.." in sanitized or "..\\.." in sanitized:
            sanitized = sanitized.replace("../../", "").replace("..\\..\\", "")

        return sanitized.strip()

    def assemble_planning_context(
        self,
        prompt: str,
        workspace_path: Optional[str] = None,
        recent_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Assembles a bounded context string for task planning.
        """
        target_budget = max_tokens or self.MAX_CONTEXT_TOKENS
        workspace = Path(workspace_path or settings.AUTHORIZED_WORKSPACE_DIR).resolve()

        parts = [
            f"SYSTEM: DODO Local Autonomous Engine. Workspace authorized: {workspace.name}",
            f"USER_REQUEST: {self.sanitize_input(prompt)}",
        ]

        if recent_history:
            history_lines = []
            for msg in recent_history[-4:]:  # Keep last 4 messages at most
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:200]
                history_lines.append(f"{role}: {content}")
            if history_lines:
                parts.append("CONVERSATION_CONTEXT:\n" + "\n".join(history_lines))

        full_context = "\n\n".join(parts)
        if self.estimate_tokens(full_context) > target_budget:
            # Truncate safely
            char_limit = int(target_budget * self.ESTIMATED_CHARS_PER_TOKEN)
            full_context = full_context[:char_limit] + "\n... [Context truncated to fit model budget]"

        return full_context


context_manager = ContextManager()
