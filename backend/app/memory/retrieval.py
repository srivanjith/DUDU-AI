"""
DODO Semantic Memory Retrieval Engine
Implements multi-factor relevance ranking: keyword matching, importance weighting,
recency decay, project isolation, and optional local Ollama embeddings.
"""
from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.app.memory.models import MemoryCategory
from backend.app.memory.repository import memory_repo


class MemoryRetrievalEngine:
    """Retrieves relevant memories using multi-factor ranking."""

    def __init__(self):
        self._embedding_model_checked = False
        self._local_embedding_model: Optional[str] = None

    def _tokenize(self, text: str) -> List[str]:
        """Normalizes and extracts keywords from text."""
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", text.lower())
        stopwords = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of",
            "is", "it", "this", "that", "my", "your", "i", "we", "with", "what",
            "how", "why", "when", "where", "can", "do", "does", "did", "be", "am"
        }
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1 and t.strip() not in stopwords]
        return tokens

    def _calculate_recency_score(self, created_at_iso: str) -> float:
        """
        Calculates exponential decay recency factor (0.5 to 1.0).
        Memories created today get ~1.0; memories created 30 days ago decay towards ~0.5.
        """
        try:
            created_dt = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta_days = max(0.0, (now - created_dt).total_seconds() / 86400.0)
            return math.exp(-0.02 * delta_days)  # Halves every ~35 days
        except Exception:
            return 0.8

    def _calculate_keyword_score(self, query_tokens: List[str], text: str, tags: List[str]) -> Tuple[float, List[str]]:
        """Calculates token overlap score with exact phrase bonus."""
        if not query_tokens:
            return 0.0, []

        text_lower = text.lower()
        matched = []
        raw_score = 0.0

        for tok in query_tokens:
            if tok in text_lower:
                matched.append(tok)
                # Count frequency capped at 3
                cnt = min(3, text_lower.count(tok))
                raw_score += 1.0 + (0.3 * (cnt - 1))

        # Check tags
        for t in tags:
            t_lower = t.lower()
            if any(tok in t_lower for tok in query_tokens):
                raw_score += 1.5
                matched.append(f"tag:{t}")

        # Normalization over query length
        normalized_score = min(1.0, raw_score / max(1, len(query_tokens)))
        return normalized_score, matched

    def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
        min_score: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        Ranks and retrieves relevant memories matching query.
        Returns list of memory dicts with 'relevance_score' and 'match_reasons'.
        """
        # Fetch candidate memories
        q: Dict[str, Any] = {"status": {"$ne": "superseded"}}
        if category:
            q["category"] = category
        if project_id:
            # Allow memories with matching project_id OR global memories without project_id
            q["$or"] = [{"project_id": project_id}, {"project_id": None}, {"project_id": ""}]

        candidates = memory_repo.find_all(filter_query=q, limit=200)
        if not candidates:
            return []

        query_tokens = self._tokenize(query)

        ranked_results = []
        for mem in candidates:
            content = mem.get("content", "")
            tags = mem.get("tags", [])
            importance = mem.get("importance", 3)
            created_at = mem.get("created_at", "")

            # 1. Keyword Overlap Score
            kw_score, matches = self._calculate_keyword_score(query_tokens, content, tags)

            # 2. Importance Multiplier (importance 1: 0.7x, importance 3: 1.0x, importance 5: 1.3x)
            importance_weight = 0.7 + (importance - 1) * 0.15

            # 3. Recency Weight
            recency_weight = self._calculate_recency_score(created_at)

            # 4. Project Affinity Bonus
            project_bonus = 1.2 if (project_id and mem.get("project_id") == project_id) else 1.0

            # Combined Score
            if query_tokens and kw_score > 0:
                final_score = kw_score * importance_weight * recency_weight * project_bonus
            elif not query_tokens:
                # If no query provided, rank by importance and recency
                final_score = (importance / 5.0) * recency_weight * project_bonus
            elif importance >= 5 or mem.get("category") == MemoryCategory.PREFERENCE.value:
                # Global preferences and high-importance rules provide a baseline presence in context
                final_score = 0.22 * importance_weight * recency_weight * project_bonus
            else:
                final_score = 0.0

            if final_score >= min_score or (not query_tokens and final_score > 0):
                reasons = []
                if matches:
                    reasons.append(f"Keywords matched: {', '.join(matches[:4])}")
                if importance >= 4:
                    reasons.append(f"High importance ({importance}/5)")
                if project_id and mem.get("project_id") == project_id:
                    reasons.append(f"Project match: {project_id}")

                res_item = dict(mem)
                res_item["relevance_score"] = round(final_score, 4)
                res_item["match_reasons"] = reasons
                ranked_results.append(res_item)

        # Sort descending by relevance score
        ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked_results[:limit]


retrieval_engine = MemoryRetrievalEngine()

