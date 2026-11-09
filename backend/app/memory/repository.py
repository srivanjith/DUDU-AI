"""
DODO Persistent Memory Repository
Handles CRUD, filtering, deduplication, conflict resolution, and persistence
across application restarts via BaseRepository and MongoDBManager fallback.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId

from backend.app.database.repositories.base_repository import BaseRepository
from backend.app.database.repositories.model_repository import AuditRepository
from backend.app.memory.models import MemoryCategory, MemoryItem
from backend.app.memory.security import memory_security

logger = logging.getLogger("dodo.memory.repository")


class PersistentMemoryRepository(BaseRepository):
    """Repository managing structured long-term memory records."""

    def __init__(self):
        super().__init__("memories")
        self.audit_repo = AuditRepository()

    def create_memory(
        self,
        content: str,
        category: str = MemoryCategory.CONVERSATION.value,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        importance: int = 3,
        tags: Optional[List[str]] = None,
        source: str = "user_input",
        is_verified: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Validates, sanitizes, deduplicates, and stores a memory item.
        Returns (memory_doc, status_message).
        """
        # 1. Validation & Privacy Check
        is_valid, reason = memory_security.validate_for_storage(content)
        if not is_valid:
            return None, f"Memory validation failed: {reason}"

        sanitized_content = memory_security.sanitize_content(content)

        # 2. Duplicate Detection
        existing = self.find_duplicate(sanitized_content, category, project_id)
        if existing:
            # Refresh timestamp and update importance if higher
            mem_id = existing["id"]
            new_importance = max(existing.get("importance", 3), importance)
            updates = {
                "importance": new_importance,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if metadata:
                merged_meta = dict(existing.get("metadata", {}))
                merged_meta.update(metadata)
                updates["metadata"] = merged_meta

            updated = self.update(mem_id, updates)
            logger.info(f"Refreshed existing duplicate memory [{mem_id}]")
            return updated, "duplicate_refreshed"

        # 3. Conflict Detection & Superseding
        conflict_id = self.detect_conflict(sanitized_content, category, project_id)
        superseded_id = None
        if conflict_id:
            logger.info(f"Conflict detected with memory [{conflict_id}]. Superseding older memory.")
            self.update(conflict_id, {
                "status": "superseded",
                "superseded_at": datetime.now(timezone.utc).isoformat(),
            })
            superseded_id = conflict_id

        # 4. Insert New Memory
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "content": sanitized_content,
            "category": category,
            "project_id": project_id,
            "conversation_id": conversation_id,
            "importance": max(1, min(5, importance)),
            "tags": tags or [],
            "source": source,
            "is_verified": is_verified,
            "supersedes_id": superseded_id,
            "status": "active",
            "metadata": metadata or {},
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        created = self.create(doc)

        self.audit_repo.log_event("memory_created", "system", {
            "memory_id": created["id"],
            "category": category,
            "project_id": project_id,
        })

        return created, "created"

    def find_duplicate(
        self,
        content: str,
        category: str,
        project_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Finds if identical or near-exact memory already exists."""
        q: Dict[str, Any] = {"category": category, "status": {"$ne": "superseded"}}
        if project_id:
            q["project_id"] = project_id

        candidates = self.find_all(filter_query=q, limit=100)
        norm_content = content.strip().lower()

        for c in candidates:
            c_norm = (c.get("content") or "").strip().lower()
            if c_norm == norm_content:
                return c
        return None

    def detect_conflict(
        self,
        new_content: str,
        category: str,
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Detects if new content directly contradicts or updates an existing project fact.
        e.g., 'Project framework is React' vs 'Project framework is Next.js'.
        """
        if category not in [MemoryCategory.PROJECT.value, MemoryCategory.PREFERENCE.value]:
            return None

        q: Dict[str, Any] = {"category": category, "status": "active"}
        if project_id:
            q["project_id"] = project_id

        candidates = self.find_all(filter_query=q, limit=50)
        new_lower = new_content.lower()

        # Keywords that denote key project configurations
        tech_keywords = ["framework", "technology stack", "tech stack", "database", "orm", "styling", "frontend", "backend"]
        for kw in tech_keywords:
            if kw in new_lower:
                for c in candidates:
                    c_text = (c.get("content") or "").lower()
                    if kw in c_text and c_text != new_lower:
                        return c["id"]
        return None

    def list_memories(
        self,
        category: Optional[str] = None,
        project_id: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Lists active memories with category, project, and substring filtering."""
        q: Dict[str, Any] = {"status": {"$ne": "superseded"}}
        if category:
            q["category"] = category
        if project_id:
            q["project_id"] = project_id

        docs = self.find_all(filter_query=q, limit=limit, skip=skip, sort=[("created_at", -1)])

        if search_query:
            sq = search_query.strip().lower()
            docs = [d for d in docs if sq in (d.get("content") or "").lower() or any(sq in t.lower() for t in d.get("tags", []))]

        return docs

    def count_by_category(self) -> Dict[str, int]:
        """Returns memory counts broken down by category."""
        counts = {cat.value: 0 for cat in MemoryCategory}
        all_docs = self.find_all(filter_query={"status": {"$ne": "superseded"}}, limit=1000)
        for d in all_docs:
            cat = d.get("category", MemoryCategory.CONVERSATION.value)
            if cat in counts:
                counts[cat] += 1
            else:
                counts[cat] = 1
        return counts

    def list_projects(self) -> List[str]:
        """Returns distinct project IDs that have stored memories."""
        all_docs = self.find_all(filter_query={"status": {"$ne": "superseded"}}, limit=1000)
        projects = set()
        for d in all_docs:
            pid = d.get("project_id")
            if pid:
                projects.add(str(pid))
        return sorted(list(projects))

    def clear_project_memories(self, project_id: str) -> int:
        """Deletes all memories associated with a specific project."""
        all_docs = self.find_all(filter_query={"project_id": project_id}, limit=1000)
        deleted = 0
        for d in all_docs:
            if self.delete(d["id"]):
                deleted += 1
        self.audit_repo.log_event("project_memories_cleared", "user", {
            "project_id": project_id,
            "deleted_count": deleted,
        })
        return deleted

    def clear_all_memories(self) -> int:
        """Deletes all memories in DODO."""
        all_docs = self.find_all(limit=5000)
        deleted = 0
        for d in all_docs:
            if self.delete(d["id"]):
                deleted += 1
        self.audit_repo.log_event("all_memories_cleared", "user", {"deleted_count": deleted})
        return deleted


memory_repo = PersistentMemoryRepository()

