import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database.mongodb import db_manager
from backend.app.database.repositories.conversation_repository import ConversationRepository, MessageRepository
from backend.app.intelligence.ollama_client import ollama_client
from backend.app.model_router.model_registry import model_registry
from backend.app.model_router.model_router import model_router

client = TestClient(app)


# 1. Ollama Connectivity Test
@pytest.mark.asyncio
async def test_ollama_connectivity():
    health = await ollama_client.check_health()
    assert health["status"] in ["online", "offline"]
    assert "base_url" in health
    if health["status"] == "online":
        assert health["version"] is not None
        assert "latency_ms" in health
        print(f"\n[Test 1 PASSED] Ollama Online (v{health['version']}, latency: {health.get('latency_ms')} ms)")


# 2. Model Discovery Test
@pytest.mark.asyncio
async def test_model_discovery():
    models = await ollama_client.list_models()
    assert isinstance(models, list)
    print(f"\n[Test 2 PASSED] Discovered {len(models)} installed models: {[m.get('name') for m in models]}")


# 3. Model Selection & Role Assignment Test
def test_model_selection():
    # Assign model to role
    res = client.post("/api/models/roles", json={"role": "coding", "model_name": "qwen2.5-coder:7b"})
    assert res.status_code == 200
    assert res.json()["model_name"] == "qwen2.5-coder:7b"

    # Verify role mapping
    mapping = model_registry.get_role_mapping()
    assert mapping["coding"] == "qwen2.5-coder:7b"
    print("\n[Test 3 PASSED] Model role assignment verified.")


# 4. Model Routing & Capability Verification
@pytest.mark.asyncio
async def test_model_routing():
    res = await model_router.route("Write an async python function to query MongoDB")
    assert res.task_type == "coding"
    assert res.role == "coding"
    assert res.hardware_fit is not None
    print(f"\n[Test 4 PASSED] Model router correctly routed to '{res.selected_model}' ({res.reason})")


# 5. Streaming Response via SSE Test
def test_streaming_response_sse():
    # Create conversation
    conv_res = client.post("/api/conversations", json={"title": "SSE Stream Test"})
    assert conv_res.status_code == 200
    conv_id = conv_res.json()["id"]

    # Post to /api/chat
    chat_res = client.post(
        "/api/chat",
        json={"conversation_id": conv_id, "message": "Hello DODO test query", "model": "auto"},
    )
    assert chat_res.status_code == 200
    assert "text/event-stream" in chat_res.headers["content-type"]

    events = []
    for line in chat_res.iter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            events.append(data)

    assert len(events) >= 1
    event_types = [e.get("type") for e in events]
    assert "routing" in event_types
    print(f"\n[Test 5 PASSED] SSE Streaming verified. Received event types: {set(event_types)}")


# 6. Request Size Limit & Long History Test
def test_request_size_limit_and_pagination():
    # Oversized payload (>64KB)
    huge_message = "x" * 70000
    bad_res = client.post("/api/chat", json={"message": huge_message})
    assert bad_res.status_code == 422  # Pydantic validation error for max_length

    # Pagination test
    conv_res = client.post("/api/conversations", json={"title": "Pagination Test"})
    conv_id = conv_res.json()["id"]
    msg_repo = MessageRepository()
    for i in range(15):
        msg_repo.add_message(conv_id, role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")

    page1 = client.get(f"/api/conversations/{conv_id}?skip=0&limit=5")
    assert page1.status_code == 200
    assert len(page1.json()["messages"]) == 5

    page2 = client.get(f"/api/conversations/{conv_id}?skip=5&limit=5")
    assert page2.status_code == 200
    assert len(page2.json()["messages"]) == 5
    assert page1.json()["messages"][0]["content"] != page2.json()["messages"][0]["content"]
    print("\n[Test 6 PASSED] Request size limits and pagination verified.")


# 7. Conversation Saving & Persistence
def test_conversation_saving():
    conv_res = client.post("/api/conversations", json={"title": "Persistence Test", "user_id": "test_user"})
    assert conv_res.status_code == 200
    conv_id = conv_res.json()["id"]

    msg_repo = MessageRepository()
    msg = msg_repo.add_message(
        conversation_id=conv_id,
        role="assistant",
        content="Persistent response",
        model_used="qwen2.5:7b",
        user_id="test_user",
        generation_status="completed"
    )
    assert msg["id"] is not None
    assert msg["generation_status"] == "completed"

    retrieved = client.get(f"/api/conversations/{conv_id}")
    assert retrieved.status_code == 200
    assert retrieved.json()["conversation"]["title"] == "Persistence Test"
    assert len(retrieved.json()["messages"]) == 1
    print("\n[Test 7 PASSED] Conversation and messages saved in MongoDB.")


# 8. Conversation Retrieval After Restart
def test_conversation_retrieval_after_restart():
    # Save a test document
    conv_res = client.post("/api/conversations", json={"title": "Pre-Restart Chat"})
    conv_id = conv_res.json()["id"]
    msg_repo = MessageRepository()
    msg_repo.add_message(conv_id, role="user", content="Question before restart")

    # Simulate database manager shutdown and reconnection
    db_manager.close()
    db_manager.connect()

    # Retrieve again
    reopened = client.get(f"/api/conversations/{conv_id}")
    assert reopened.status_code == 200
    assert reopened.json()["conversation"]["title"] == "Pre-Restart Chat"
    assert len(reopened.json()["messages"]) >= 1
    print("\n[Test 8 PASSED] Conversation successfully survived database restart.")


# 9. Conversation Deletion Test
def test_conversation_deletion():
    conv_res = client.post("/api/conversations", json={"title": "To Delete"})
    conv_id = conv_res.json()["id"]
    msg_repo = MessageRepository()
    msg_repo.add_message(conv_id, role="user", content="Will be deleted")

    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200

    # Ensure conversation is gone
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 404

    # Ensure messages are gone
    remaining_messages = msg_repo.get_by_conversation(conv_id)
    assert len(remaining_messages) == 0
    print("\n[Test 9 PASSED] Conversation and cascaded message deletion verified.")


# 10. Model Unavailable Handling Test
def test_model_unavailable_handling():
    conv_res = client.post("/api/conversations", json={"title": "Missing Model Test"})
    conv_id = conv_res.json()["id"]

    # Request an explicitly missing model
    res = client.post(
        "/api/chat",
        json={"conversation_id": conv_id, "message": "Test missing", "model": "non_existent_model:xyz"}
    )
    assert res.status_code == 200
    lines = [line for line in res.iter_lines() if line.startswith("data: ")]
    events = [json.loads(line[6:]) for line in lines]
    error_events = [e for e in events if e.get("type") == "error"]
    assert len(error_events) >= 1
    assert "MODEL_NOT_FOUND" in error_events[0].get("error_code", "") or "not installed" in error_events[0].get("error", "")
    print(f"\n[Test 10 PASSED] Graceful unavailable model handling verified: {error_events[0].get('error_code')}")


# 11. Frontend-Backend Communication Endpoints
def test_frontend_backend_communication():
    # Test GET /api/models
    r1 = client.get("/api/models")
    assert r1.status_code == 200
    assert "installed_models" in r1.json()
    assert "role_mapping" in r1.json()

    # Test GET /api/models/status
    r2 = client.get("/api/models/status")
    assert r2.status_code == 200
    assert "ollama" in r2.json()
    assert "hardware" in r2.json()

    # Test GET /api/health
    r3 = client.get("/api/health")
    assert r3.status_code == 200
    assert r3.json()["status"] in ["healthy", "degraded"]
    print("\n[Test 11 PASSED] All frontend/backend communication endpoints verified.")


# 12. Input Error Handling & Validation
def test_error_handling():
    # Empty message
    r1 = client.post("/api/chat", json={"message": "   "})
    assert r1.status_code == 400

    # Non-existent conversation
    r2 = client.post("/api/chat", json={"conversation_id": "non_existent_conv_id", "message": "Hi"})
    assert r2.status_code == 404

    # Invalid role
    r3 = client.post("/api/models/roles", json={"role": "invalid_role", "model_name": "qwen2.5:7b"})
    assert r3.status_code == 400
    print("\n[Test 12 PASSED] Validation and error handling verified.")
