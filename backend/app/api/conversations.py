import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.app.database.repositories.conversation_repository import ConversationRepository, MessageRepository
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_router import model_router

router = APIRouter(tags=["Conversations"])

conv_repo = ConversationRepository()
msg_repo = MessageRepository()


class CreateConvRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    mode: Optional[str] = "assistant"
    project_id: Optional[str] = None
    user_id: Optional[str] = "default_local_user"


class SendMessageRequest(BaseModel):
    content: str = Field(..., max_length=65536)
    model: Optional[str] = "auto"
    user_id: Optional[str] = "default_local_user"


@router.get("/conversations")
@router.get("/api/conversations")
def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Lists conversations with pagination."""
    return conv_repo.list_recent(limit=limit, skip=skip, project_id=project_id, user_id=user_id)


@router.post("/conversations")
@router.post("/api/conversations")
def create_conversation(req: CreateConvRequest):
    """Creates a new conversation session."""
    return conv_repo.create_conversation(
        title=req.title or "New Conversation",
        mode=req.mode or "assistant",
        project_id=req.project_id,
        user_id=req.user_id or "default_local_user",
    )


@router.get("/conversations/{conv_id}")
@router.get("/api/conversations/{conv_id}")
def get_conversation(
    conv_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Retrieves conversation metadata and paginated message history."""
    conv = conv_repo.find_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = msg_repo.get_by_conversation(conv_id, skip=skip, limit=limit)
    return {
        "conversation": conv,
        "messages": messages,
        "count": len(messages),
        "skip": skip,
        "limit": limit,
    }


@router.delete("/conversations/{conv_id}")
@router.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    """Deletes conversation and associated message records."""
    deleted_messages = msg_repo.delete_by_conversation(conv_id)
    success = conv_repo.delete(conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "deleted_messages": deleted_messages, "conversation_id": conv_id}


@router.post("/conversations/{conv_id}/messages")
@router.post("/api/conversations/{conv_id}/messages")
async def send_message(conv_id: str, req: SendMessageRequest):
    """
    Saves user message, routes to optimal local model, and streams AI response tokens via SSE.
    """
    conv = conv_repo.find_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    prompt = req.content.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    # 1. Save user message
    msg_repo.add_message(
        conv_id,
        role="user",
        content=prompt,
        user_id=req.user_id or "default_local_user",
        generation_status="completed"
    )

    # 2. Route model
    route_result = await model_router.route(prompt, req.model)
    selected_model = route_result.selected_model

    # 3. Retrieve recent history for context
    past_messages = msg_repo.get_by_conversation(conv_id, limit=10)
    formatted_msgs = [{"role": m["role"], "content": m["content"]} for m in past_messages]

    async def stream_generator():
        accumulated_text = []
        has_error = False
        error_msg = None

        # Emit routing info first
        yield f"data: {json.dumps({'type': 'routing', 'model': selected_model, 'role': route_result.role, 'reason': route_result.reason, 'is_installed': route_result.is_installed})}\n\n"

        async for chunk in ollama_client.chat_stream(selected_model, formatted_msgs):
            if "error" in chunk:
                has_error = True
                error_msg = chunk["error"]
                yield f"data: {json.dumps({'type': 'error', 'token': f'⚠️ {error_msg}', 'done': True, 'model': selected_model, 'error': error_msg})}\n\n"
                break

            token = chunk.get("content", "")
            done = chunk.get("done", False)
            if token:
                accumulated_text.append(token)

            data = {
                "type": "token" if not done else "done",
                "token": token,
                "done": done,
                "model": selected_model,
                "routing_reason": route_result.reason,
            }
            yield f"data: {json.dumps(data)}\n\n"

            if done:
                break

        full_reply = "".join(accumulated_text)
        if has_error:
            msg_repo.add_message(
                conv_id,
                role="assistant",
                content=f"⚠️ {error_msg}",
                model_used=selected_model,
                user_id=req.user_id or "default_local_user",
                generation_status="error",
                error_message=error_msg,
            )
        else:
            msg_repo.add_message(
                conv_id,
                role="assistant",
                content=full_reply,
                model_used=selected_model,
                user_id=req.user_id or "default_local_user",
                generation_status="completed",
            )

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
