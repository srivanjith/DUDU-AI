import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database.mongodb import db_manager
from backend.app.database.repositories.conversation_repository import ConversationRepository, MessageRepository
from backend.app.database.repositories.project_repository import TaskRepository, ProjectRepository
from backend.app.model_router.model_router import model_router
from backend.app.tools.registry import tool_registry

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "DODO"
    assert "Your AI. Your Machine. Your Rules." in data["tagline"]


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "inference_engine" in data
    assert "local_agent" in data


def test_conversation_crud():
    # 1. Create conversation
    create_res = client.post("/conversations", json={"title": "Test Chat", "mode": "assistant"})
    assert create_res.status_code == 200
    conv = create_res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Test Chat"

    # 2. Add message
    msg_repo = MessageRepository()
    msg = msg_repo.add_message(conv_id, role="user", content="Hello DODO")
    assert msg["content"] == "Hello DODO"

    # 3. Get conversation
    get_res = client.get(f"/conversations/{conv_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert len(data["messages"]) >= 1

    # 4. Delete conversation
    del_res = client.delete(f"/conversations/{conv_id}")
    assert del_res.status_code == 200


def test_model_router_classification():
    # Conversational
    r1 = model_router.classify_task("Tell me a story about space exploration")
    assert r1 == "general"

    # Coding
    r2 = model_router.classify_task("Fix this bug in python fastapi route")
    assert r2 == "coding"

    # Reasoning / Autonomous Plan
    r3 = model_router.classify_task("Build a complete full-stack e-commerce application using React and FastAPI")
    assert r3 in ["reasoning", "coding"]


def test_tool_registry():
    defs = tool_registry.list_definitions()
    tool_names = [d["name"] for d in defs]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "edit_file" in tool_names
    assert "list_workspace_files" in tool_names
    assert "execute_terminal_command" in tool_names


@pytest.mark.asyncio
async def test_filesystem_tools():
    # Write file
    write_res = await tool_registry.execute(
        "write_file",
        {"path": "test_sample.txt", "content": "Hello DODO Workspace\nLine 2"},
    )
    assert write_res["success"] is True

    # Read file
    read_res = await tool_registry.execute(
        "read_file",
        {"path": "test_sample.txt", "start_line": 1, "end_line": 2},
    )
    assert read_res["success"] is True
    assert "Hello DODO Workspace" in read_res["result"]["content"]

    # Edit file
    edit_res = await tool_registry.execute(
        "edit_file",
        {"path": "test_sample.txt", "target": "Line 2", "replacement": "Updated Line 2"},
    )
    assert edit_res["success"] is True

