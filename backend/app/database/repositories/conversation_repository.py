from datetime import datetime
from typing import Any, Dict, List, Optional
from pymongo import DESCENDING, ASCENDING
from backend.app.database.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository):
    def __init__(self):
        super().__init__("conversations")

    def create_conversation(self, title: str = "New Conversation", mode: str = "assistant", project_id: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "title": title,
            "mode": mode,
            "project_id": project_id,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }
        return self.create(doc)

    def list_recent(self, limit: int = 50, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if project_id:
            query["project_id"] = project_id
        return self.find_all(filter_query=query, limit=limit, sort=[("updated_at", DESCENDING)])

    def touch(self, conv_id: str, increment_messages: bool = True):
        updates = {"updated_at": datetime.utcnow()}
        conv = self.find_by_id(conv_id)
        if conv and increment_messages:
            updates["message_count"] = conv.get("message_count", 0) + 1
        return self.update(conv_id, updates)


class MessageRepository(BaseRepository):
    def __init__(self):
        super().__init__("messages")

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        thought_process: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        model_used: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "thought_process": thought_process,
            "tool_calls": tool_calls or [],
            "tool_call_id": tool_call_id,
            "model_used": model_used,
            "created_at": now,
        }
        res = self.create(doc)
        # Update parent conversation
        ConversationRepository().touch(conversation_id, increment_messages=True)
        return res

    def get_by_conversation(self, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.find_all(
            filter_query={"conversation_id": conversation_id},
            limit=limit,
            sort=[("created_at", ASCENDING)],
        )

    def delete_by_conversation(self, conversation_id: str) -> int:
        res = self.collection.delete_many({"conversation_id": conversation_id})
        return res.deleted_count

