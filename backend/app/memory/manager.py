"""
DODO Memory Lifecycle Manager
Orchestrates CAPTURE, CLASSIFICATION, VALIDATION, STORAGE, RETRIEVAL, and
CONTEXT INJECTION across DODO agents and conversational sessions.
"""
from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.app.memory.models import MemoryCategory, MemoryItem
from backend.app.memory.repository import memory_repo
from backend.app.memory.retrieval import retrieval_engine
from backend.app.memory.security import memory_security

logger = logging.getLogger("dodo.memory.manager")


class MemoryManager:
    """High-level autonomous memory lifecycle orchestrator."""

    def __init__(self):
        self.repo = memory_repo
        self.retrieval = retrieval_engine

    def capture_from_interaction(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyzes user input for memorable project facts, preferences, or error fixes,
        and autonomously captures structured memory.
        """
        msg_lower = user_message.lower().strip()

        # 1. Project Tech Stack & Architecture Declaration
        # e.g., "My current project uses React, FastAPI and MongoDB."
        stack_match = re.search(r"(?:my\s+(?:current\s+)?project\s+uses|we\s+are\s+using|built\s+with|stack\s+is)\s+([^.]+)", msg_lower)
        if stack_match:
            content = f"Project Tech Stack: {user_message.strip()}"
            mem, _ = self.repo.create_memory(
                content=content,
                category=MemoryCategory.PROJECT.value,
                project_id=project_id,
                conversation_id=conversation_id,
                importance=5,
                tags=["tech_stack", "architecture"],
                source="user_conversation",
            )
            return mem

        # 2. Error Fixes & Technical Decisions
        # e.g., "I fixed the authentication error by correcting the JWT configuration."
        fix_match = re.search(r"(?:i\s+fixed|the\s+fix\s+for|resolved\s+by|corrected\s+by)\s+([^.]+)", msg_lower)
        if fix_match:
            content = f"Verified Fix: {user_message.strip()}"
            mem, _ = self.repo.create_memory(
                content=content,
                category=MemoryCategory.TASK_EXPERIENCE.value,
                project_id=project_id,
                conversation_id=conversation_id,
                importance=4,
                tags=["fix", "solution", "troubleshooting"],
                source="user_conversation",
            )
            return mem

        # 3. User Preferences
        # e.g., "I prefer TypeScript over JavaScript" or "Always write Python with type hints"
        pref_match = re.search(r"(?:i\s+prefer|my\s+preference\s+is|always\s+use|prefer\s+to\s+write)\s+([^.]+)", msg_lower)
        if pref_match:
            content = f"User Preference: {user_message.strip()}"
            mem, _ = self.repo.create_memory(
                content=content,
                category=MemoryCategory.PREFERENCE.value,
                project_id=project_id,
                conversation_id=conversation_id,
                importance=4,
                tags=["preference", "workflow"],
                source="user_conversation",
            )
            return mem

        return None

    def record_task_experience(
        self,
        task_id: str,
        prompt: str,
        outcome_summary: str,
        verified: bool = True,
        project_id: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """Stores verified autonomous task outcome into task & experience memory."""
        content = f"Autonomous Task '{prompt[:80]}': Outcome verified={verified}. Summary: {outcome_summary[:200]}"
        mem, _ = self.repo.create_memory(
            content=content,
            category=MemoryCategory.TASK_EXPERIENCE.value,
            project_id=project_id,
            importance=4 if verified else 2,
            tags=["task_outcome", "agent_experience"],
            source="autonomous_orchestrator",
            is_verified=verified,
            metadata={"task_id": task_id, "duration_ms": duration_ms},
        )
        return mem

    def build_memory_prompt_injection(
        self,
        query: str,
        project_id: Optional[str] = None,
        max_tokens: int = 500,
    ) -> Tuple[str, List[str]]:
        """
        Retrieves relevant long-term memories and formats a bounded prompt section.
        Returns (formatted_text, list_of_contributing_categories).
        """
        results = self.retrieval.search(query=query, project_id=project_id, limit=4, min_score=0.15)
        if not results:
            return "", []

        lines = ["[RELEVANT LONG-TERM MEMORY]"]
        categories = set()
        estimated_chars = 0
        char_budget = int(max_tokens * 3.8)

        for res in results:
            cat = res.get("category", "general").upper()
            categories.add(res.get("category", "general"))
            content = res.get("content", "").strip()
            item_line = f"- [{cat}] {content}"

            if estimated_chars + len(item_line) > char_budget:
                lines.append("- ... [Additional memories truncated to preserve context budget]")
                break

            lines.append(item_line)
            estimated_chars += len(item_line)

        formatted_block = "\n".join(lines)
        return formatted_block, sorted(list(categories))


memory_manager = MemoryManager()

