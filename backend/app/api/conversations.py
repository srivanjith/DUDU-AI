import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.database.repositories.conversation_repository import ConversationRepository, MessageRepository
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_router import model_router

router = APIRouter(prefix="/conversations", tags=["Conversations"])

conv_repo = ConversationRepository()
msg_repo = MessageRepository()


class CreateConvRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    mode: Optional[str] = "assistant"
    project_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    model: Optional[str] = "auto"


@router.get("")
def list_conversations(limit: int = 50, project_id: Optional[str] = None):
    return conv_repo.list_recent(limit=limit, project_id=project_id)


@router.post("")
def create_conversation(req: CreateConvRequest):
    return conv_repo.create_conversation(
        title=req.title or "New Conversation",
        mode=req.mode or "assistant",
        project_id=req.project_id,
    )


@router.get("/{conv_id}")
def get_conversation(conv_id: str):
    conv = conv_repo.find_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = msg_repo.get_by_conversation(conv_id)
    return {"conversation": conv, "messages": messages}


@router.delete("/{conv_id}")
def delete_conversation(conv_id: str):
    msg_repo.delete_by_conversation(conv_id)
    success = conv_repo.delete(conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@router.post("/{conv_id}/messages")
async def send_message(conv_id: str, req: SendMessageRequest):
    """
    Saves user message, routes to optimal local model, and streams AI response tokens.
    """
    conv = conv_repo.find_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 1. Save user message
    msg_repo.add_message(conv_id, role="user", content=req.content)

    # 2. Route model
    route_result = await model_router.route(req.content, req.model)
    selected_model = route_result.selected_model

    # 3. Retrieve recent history for context
    past_messages = msg_repo.get_by_conversation(conv_id, limit=10)
    formatted_msgs = [{"role": m["role"], "content": m["content"]} for m in past_messages]

    async def stream_generator():
        accumulated_text = []
        async for chunk in ollama_client.chat_stream(selected_model, formatted_msgs):
            token = chunk.get("content", "")
            done = chunk.get("done", False)
            accumulated_text.append(token)

            data = {
                "token": token,
                "done": done,
                "model": selected_model,
                "routing_reason": route_result.reason,
            }
            yield f"data: {json.dumps(data)}\n\n"

            if done:
                # Save assistant response
                full_reply = "".join(accumulated_text)
                msg_repo.add_message(
                    conv_id,
                    role="assistant",
                    content=full_reply,
                    model_used=selected_model,
                )
                break

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

