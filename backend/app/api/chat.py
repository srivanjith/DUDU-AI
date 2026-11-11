import json
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from backend.app.database.repositories.conversation_repository import ConversationRepository, MessageRepository
from backend.app.database.repositories.model_repository import ModelRepository
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.intelligence.openrouter_client import openrouter_client, NEMOTRON_MODEL_ID
from backend.app.model_router.model_router import model_router

logger = logging.getLogger("dodo.api.chat")

router = APIRouter(tags=["AI Chat"])

conv_repo = ConversationRepository()
msg_repo = MessageRepository()
model_repo = ModelRepository()

MAX_PROMPT_LENGTH = 65536  # 64 KB safety limit


class ChatCompletionRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID. If omitted, a new conversation is started.")
    message: str = Field(..., max_length=MAX_PROMPT_LENGTH, description="User prompt text (max 64KB)")
    model: Optional[str] = Field("auto", description="Requested model or 'auto' for hardware-aware router")
    temperature: Optional[float] = Field(0.3, ge=0.0, le=2.0)
    system_prompt: Optional[str] = Field(None, description="Optional custom system prompt")
    user_id: Optional[str] = Field("default_local_user", description="Local session identifier")


@router.post("/chat")
@router.post("/api/chat")
async def chat_completion(req: ChatCompletionRequest):
    """
    Executes streaming AI inference with local model routing and MongoDB conversation persistence.
    Returns a Server-Sent Events (SSE) stream.
    Does NOT fabricate AI responses. If Ollama is offline or model is missing, returns clear errors.
    """
    # 1. Input sanitization and size check
    prompt = req.message.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    # 2. Resolve or create conversation
    conv_id = req.conversation_id
    if conv_id:
        conv = conv_repo.find_by_id(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail=f"Conversation '{conv_id}' not found.")
    else:
        # Generate initial title from prompt
        title = prompt[:40] + ("..." if len(prompt) > 40 else "")
        new_conv = conv_repo.create_conversation(title=title, mode="assistant", user_id=req.user_id or "default_local_user")
        conv_id = new_conv["id"]

    # 3. Save User message to MongoDB
    user_msg = msg_repo.add_message(
        conversation_id=conv_id,
        role="user",
        content=prompt,
        user_id=req.user_id or "default_local_user",
        generation_status="completed",
    )

    # 4. Route to optimal model based on hardware & intent
    route_result = await model_router.route(prompt, req.model)
    selected_model = route_result.selected_model

    # 5. Autonomous Memory Capture & Long-Term Context Retrieval
    captured_mem = None
    memory_block = ""
    memory_categories: List[str] = []
    try:
        from backend.app.memory.manager import memory_manager
        captured_mem = memory_manager.capture_from_interaction(prompt, conv_id)
        memory_block, memory_categories = memory_manager.build_memory_prompt_injection(prompt, max_tokens=400)
    except Exception as mem_err:
        logger.warning(f"Error managing memory in chat: {mem_err}")

    # 6. Build context history from MongoDB
    history_docs = msg_repo.get_by_conversation(conv_id, limit=12)
    messages_payload: List[Dict[str, str]] = []

    # Construct bounded system prompt with injected long-term memory
    default_sys = "You are DODO, an autonomous local-first AI engineering assistant. Your AI. Your Machine. Your Rules."
    if req.system_prompt:
        sys_content = f"{req.system_prompt}\n\n{memory_block}" if memory_block else req.system_prompt
    elif memory_block:
        sys_content = f"{default_sys}\n\n{memory_block}"
    else:
        sys_content = default_sys

    messages_payload.append({"role": "system", "content": sys_content})

    for doc in history_docs:
        role = doc.get("role", "user")
        content = doc.get("content", "")
        if role in ["user", "assistant"] and content:
            messages_payload.append({"role": role, "content": content})

    # Ensure the latest user message is at the end
    if not messages_payload or messages_payload[-1]["content"] != prompt:
        messages_payload.append({"role": "user", "content": prompt})

    # 7. Stream tokens via SSE
    async def sse_event_stream():
        accumulated_chunks: List[str] = []
        token_count = 0
        has_error = False
        error_details = None
        start_time = time.perf_counter()

        # Emit routing metadata event
        yield f"data: {json.dumps({'type': 'routing', 'conversation_id': conv_id, 'model': selected_model, 'role': route_result.role, 'reason': route_result.reason, 'is_installed': route_result.is_installed, 'hardware_fit': route_result.hardware_fit, 'provider': getattr(route_result, 'provider', 'Ollama')})}\n\n"

        # Emit memory telemetry events
        if memory_categories:
            yield f"data: {json.dumps({'type': 'memory_influence', 'categories': memory_categories, 'count': len(memory_categories)})}\n\n"
        if captured_mem:
            yield f"data: {json.dumps({'type': 'memory_captured', 'category': captured_mem.get('category'), 'memory_id': captured_mem.get('id')})}\n\n"

        options = {"temperature": req.temperature or 0.3}

        # Route to OpenRouter cloud or Ollama local
        if getattr(route_result, "provider", "") == "OpenRouter" or selected_model == NEMOTRON_MODEL_ID:
            stream_gen = openrouter_client.chat_stream(selected_model, messages_payload, options=options)
        else:
            stream_gen = ollama_client.chat_stream(selected_model, messages_payload, options=options)

        async for chunk in stream_gen:
            if "error" in chunk:
                has_error = True
                error_details = chunk["error"]
                yield f"data: {json.dumps({'type': 'error', 'error': error_details, 'error_code': chunk.get('error_code'), 'model': selected_model, 'can_fallback_to_qwen': chunk.get('can_fallback_to_qwen', False)})}\n\n"
                break

            token = chunk.get("content", "")
            done = chunk.get("done", False)

            if token:
                token_count += 1
                accumulated_chunks.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token, 'done': False, 'model': selected_model})}\n\n"

            if done:
                total_duration = chunk.get("total_duration")
                yield f"data: {json.dumps({'type': 'done', 'done': True, 'model': selected_model, 'eval_count': chunk.get('eval_count', token_count)})}\n\n"
                break

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        full_content = "".join(accumulated_chunks)

        # 7. Persist Assistant response to MongoDB
        if has_error:
            msg_repo.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=f"⚠️ {error_details}",
                model_used=selected_model,
                user_id=req.user_id or "default_local_user",
                generation_status="error",
                error_message=error_details,
            )
        else:
            msg_repo.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=full_content,
                model_used=selected_model,
                user_id=req.user_id or "default_local_user",
                generation_status="completed",
            )
            # Record telemetry metric
            tps = round(token_count / (duration_ms / 1000), 2) if duration_ms > 0 else 0.0
            model_repo.record_metric(
                model_name=selected_model,
                task_type=route_result.task_type,
                latency_ms=duration_ms,
                tokens_per_sec=tps,
                prompt_tokens=len(prompt.split()),
                completion_tokens=token_count,
            )

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")


@router.websocket("/ws/chat/{conversation_id}")
@router.websocket("/api/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: str):
    """
    Real-time bidirectional WebSocket endpoint for streaming chat with cancellation support.
    """
    await websocket.accept()
    conv = conv_repo.find_by_id(conversation_id)
    if not conv:
        await websocket.send_json({"type": "error", "message": f"Conversation '{conversation_id}' not found."})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        while True:
            data = await websocket.receive_json()
            user_prompt = data.get("message", "").strip()
            requested_model = data.get("model", "auto")

            if not user_prompt:
                continue

            # Save user message
            msg_repo.add_message(conversation_id, role="user", content=user_prompt)

            # Route model
            route_res = await model_router.route(user_prompt, requested_model)
            model_to_use = route_res.selected_model

            await websocket.send_json({
                "type": "routing",
                "model": model_to_use,
                "role": route_res.role,
                "reason": route_res.reason,
                "is_installed": route_res.is_installed,
            })

            # Retrieve context
            history = msg_repo.get_by_conversation(conversation_id, limit=10)
            formatted = [{"role": h["role"], "content": h["content"]} for h in history]

            accumulated = []
            cancelled = False

            if getattr(route_res, "provider", "") == "OpenRouter" or model_to_use == NEMOTRON_MODEL_ID:
                stream_gen = openrouter_client.chat_stream(model_to_use, formatted)
            else:
                stream_gen = ollama_client.chat_stream(model_to_use, formatted)

            async for chunk in stream_gen:
                if "error" in chunk:
                    await websocket.send_json({"type": "error", "error": chunk["error"], "can_fallback_to_qwen": chunk.get("can_fallback_to_qwen", False)})
                    msg_repo.add_message(conversation_id, role="assistant", content=f"⚠️ {chunk['error']}", model_used=model_to_use, generation_status="error")
                    break

                token = chunk.get("content", "")
                done = chunk.get("done", False)

                if token:
                    accumulated.append(token)
                    await websocket.send_json({"type": "token", "token": token})

                if done:
                    await websocket.send_json({"type": "done", "model": model_to_use})
                    full_reply = "".join(accumulated)
                    msg_repo.add_message(conversation_id, role="assistant", content=full_reply, model_used=model_to_use, generation_status="completed")
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

