from datetime import datetime
from typing import Any, Dict, List, Optional
from pymongo import DESCENDING
from backend.app.database.repositories.base_repository import BaseRepository
from backend.app.core.config import settings


class ModelRepository(BaseRepository):
    def __init__(self):
        super().__init__("model_configs")

    def seed_default_models(self):
        """Seeds default model configurations if empty."""
        if self.count() == 0:
            defaults = [
                {"model_name": settings.DEFAULT_GENERAL_MODEL, "role": "general", "context_length": 8192, "quantization": "4-bit", "is_active": True},
                {"model_name": settings.DEFAULT_CODING_MODEL, "role": "coding", "context_length": 16384, "quantization": "4-bit", "is_active": True},
                {"model_name": settings.DEFAULT_REASONING_MODEL, "role": "reasoning", "context_length": 16384, "quantization": "4-bit", "is_active": True},
                {"model_name": settings.DEFAULT_LIGHTWEIGHT_MODEL, "role": "lightweight", "context_length": 4096, "quantization": "4-bit", "is_active": True},
                {"model_name": settings.DEFAULT_EMBEDDING_MODEL, "role": "embedding", "context_length": 2048, "quantization": "fp16", "is_active": True},
            ]
            for m in defaults:
                self.create(m)

    def get_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"role": role, "is_active": True})
        return self._convert_id(doc)

    def record_metric(self, model_name: str, task_type: str, latency_ms: float, tokens_per_sec: float, prompt_tokens: int = 0, completion_tokens: int = 0):
        metric_doc = {
            "model_name": model_name,
            "task_type": task_type,
            "latency_ms": latency_ms,
            "tokens_per_second": tokens_per_sec,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "timestamp": datetime.utcnow(),
        }
        BaseRepository("model_metrics").create(metric_doc)


class MemoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("memories")

    def add_memory(self, content: str, category: str = "conversation", project_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        doc = {
            "content": content,
            "category": category,
            "project_id": project_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
        }
        return self.create(doc)

    def search_memories(self, query: str, project_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves relevant memories using text matching / keyword scoring.
        Atlas Vector Search is queried if vector index is enabled.
        """
        q = {}
        if project_id:
            q["project_id"] = project_id

        # Text score or substring fallback
        docs = list(self.find_all(filter_query=q, limit=50))
        # Simple relevance ranking
        keywords = query.lower().split()
        ranked = []
        for d in docs:
            text = (d.get("content") or "").lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                ranked.append((score, d))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in ranked[:limit]] if ranked else docs[:limit]


class ToolExecutionRepository(BaseRepository):
    def __init__(self):
        super().__init__("tool_executions")

    def log_execution(self, tool_name: str, parameters: Dict[str, Any], status: str, output: Optional[str] = None, error: Optional[str] = None, duration_ms: float = 0.0, task_id: Optional[str] = None) -> Dict[str, Any]:
        doc = {
            "task_id": task_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "status": status,
            "output": output,
            "error": error,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow(),
        }
        return self.create(doc)


class AuditRepository(BaseRepository):
    def __init__(self):
        super().__init__("audit_logs")

    def log_event(self, event_type: str, actor: str, details: Dict[str, Any]):
        doc = {
            "event_type": event_type,
            "actor": actor,
            "details": details,
            "timestamp": datetime.utcnow(),
        }
        return self.create(doc)

