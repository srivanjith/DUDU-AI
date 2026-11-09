from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pymongo import DESCENDING, ASCENDING
from backend.app.database.repositories.base_repository import BaseRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationRepository(BaseRepository):
    def __init__(self):
        super().__init__("conversations")

    def create_conversation(
        self,
        title: str = "New Conversation",
        mode: str = "assistant",
        project_id: Optional[str] = None,
        user_id: str = "default_local_user",
    ) -> Dict[str, Any]:
        now = utc_now()
        doc = {
            "title": title,
            "mode": mode,
            "project_id": project_id,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }
        return self.create(doc)

    def list_recent(
        self,
        limit: int = 50,
        skip: int = 0,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = {}
        if project_id:
            query["project_id"] = project_id
        if user_id:
            query["user_id"] = user_id
        return self.find_all(
            filter_query=query,
            limit=limit,
            skip=skip,
            sort=[("updated_at", DESCENDING)],
        )

    def touch(self, conv_id: str, increment_messages: bool = True):
        updates = {"updated_at": utc_now()}
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
        user_id: str = "default_local_user",
        generation_status: str = "completed",
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = utc_now()
        doc = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "thought_process": thought_process,
            "tool_calls": tool_calls or [],
            "tool_call_id": tool_call_id,
            "model_used": model_used,
            "generation_status": generation_status,
            "error_message": error_message,
            "created_at": now,
        }
        res = self.create(doc)
        # Update parent conversation
        ConversationRepository().touch(conversation_id, increment_messages=True)
        return res

    def get_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return self.find_all(
            filter_query={"conversation_id": conversation_id},
            skip=skip,
            limit=limit,
            sort=[("created_at", ASCENDING)],
        )

    def delete_by_conversation(self, conversation_id: str) -> int:
        res = self.collection.delete_many({"conversation_id": conversation_id})
        return res.deleted_count
