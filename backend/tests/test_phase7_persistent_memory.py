"""
DODO Phase 7: Persistent Memory & Long-Term Project Context Tests
Validates memory creation, secret filtering, deduplication, conflict detection,
multi-factor semantic retrieval, project isolation, REST APIs, persistence across backend
restarts, and the full 10-step autonomous acceptance demonstration.
"""
import json
import os
import shutil
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.app.database.mongodb import db_manager
from backend.app.memory.models import MemoryCategory
from backend.app.memory.security import memory_security
from backend.app.memory.repository import memory_repo, PersistentMemoryRepository
from backend.app.memory.retrieval import retrieval_engine
from backend.app.memory.manager import memory_manager


@pytest.fixture(autouse=True)
def clean_memory_fixture():
    """Wipes test memories before and after each test for predictable isolation."""
    yield
    memory_repo.clear_all_memories()


# ==============================================================================
# 1. Memory Creation, Validation & Categories
# ==============================================================================

def test_memory_creation_and_categories():
    # 1. Create project memory
    mem1, status1 = memory_repo.create_memory(
        content="Backend is built with FastAPI and runs on port 8000.",
        category=MemoryCategory.PROJECT.value,
        project_id="dodo_core",
        importance=4,
        tags=["fastapi", "backend", "api"],
    )
    assert status1 == "created"
    assert mem1["id"] is not None
    assert mem1["category"] == "project"
    assert mem1["importance"] == 4
    assert "fastapi" in mem1["tags"]

    # 2. Create user preference memory
    mem2, status2 = memory_repo.create_memory(
        content="User prefers strict Python typing and descriptive docstrings.",
        category=MemoryCategory.PREFERENCE.value,
        importance=5,
        tags=["python", "style"],
    )
    assert status2 == "created"
    assert mem2["category"] == "preference"

    # 3. Verify category breakdown counts
    counts = memory_repo.count_by_category()
    assert counts["project"] >= 1
    assert counts["preference"] >= 1


# ==============================================================================
# 2. Secret Filtering & Privacy Enforcement
# ==============================================================================

def test_secret_filtering_and_privacy():
    # 1. API key should be redacted
    leak_prompt = "Project API key is api_key='sk-live-1234567890abcdef123456'."
    sanitized = memory_security.sanitize_content(leak_prompt)
    assert "sk-live" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized

    # 2. JWT bearer token should be redacted
    jwt_leak = "Auth token is bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisTokenString"
    sanitized_jwt = memory_security.sanitize_content(jwt_leak)
    assert "doNotLeakThisTokenString" not in sanitized_jwt
    assert "[REDACTED_SECRET]" in sanitized_jwt

    # 3. Hidden chain-of-thought should be stripped
    thought_text = "<think>Let me analyze the internal hidden thoughts</think>The actual answer is here."
    clean_text = memory_security.sanitize_content(thought_text)
    assert "<think>" not in clean_text
    assert "hidden thoughts" not in clean_text
    assert clean_text == "The actual answer is here."

    # 4. Pure chain-of-thought rejected from storage
    pure_thought = "<think>Only internal reflection without useful facts</think>"
    valid, reason = memory_security.validate_for_storage(pure_thought)
    assert valid is False
    assert "chain-of-thought" in reason


# ==============================================================================
# 3. Deduplication & Conflict Detection
# ==============================================================================

def test_deduplication_and_refresh():
    content = "The database uses mongomock for local standalone persistence."

    # First insert
    mem1, status1 = memory_repo.create_memory(
        content=content,
        category="project",
        project_id="dodo_demo",
        importance=3,
    )
    assert status1 == "created"

    # Second insert with higher importance
    mem2, status2 = memory_repo.create_memory(
        content=content,
        category="project",
        project_id="dodo_demo",
        importance=5,
    )
    assert status2 == "duplicate_refreshed"
    assert mem2["id"] == mem1["id"]
    assert mem2["importance"] == 5

    # Count must remain 1
    mems = memory_repo.list_memories(project_id="dodo_demo")
    assert len(mems) == 1


def test_conflict_detection_and_superseding():
    # Initial tech stack memory
    mem1, _ = memory_repo.create_memory(
        content="Project framework is React with Vite",
        category="project",
        project_id="test_app",
    )
    assert mem1["status"] == "active"

    # Conflicting / updated tech stack memory
    mem2, _ = memory_repo.create_memory(
        content="Project framework is Next.js 14 with App Router",
        category="project",
        project_id="test_app",
    )
    assert mem2["status"] == "active"
    assert mem2["supersedes_id"] == mem1["id"]

    # Verify older memory was marked superseded
    old_mem = memory_repo.find_by_id(mem1["id"])
    assert old_mem["status"] == "superseded"


# ==============================================================================
# 4. Semantic Multi-Factor Retrieval & Project Isolation
# ==============================================================================

def test_semantic_retrieval_and_project_isolation():
    # Insert memories across two isolated projects
    memory_repo.create_memory(
        content="Project Alpha uses PostgreSQL and Redis for caching.",
        category="project",
        project_id="project_alpha",
        importance=4,
    )
    memory_repo.create_memory(
        content="Project Beta uses MongoDB and Celery for background workers.",
        category="project",
        project_id="project_beta",
        importance=4,
    )

    # 1. Search with Project Alpha isolation
    res_alpha = retrieval_engine.search(
        query="What database is used for caching?",
        project_id="project_alpha",
        limit=5,
    )
    assert len(res_alpha) >= 1
    assert "PostgreSQL" in res_alpha[0]["content"]
    assert "Redis" in res_alpha[0]["content"]

    # 2. Search with Project Beta isolation
    res_beta = retrieval_engine.search(
        query="What background worker is used?",
        project_id="project_beta",
        limit=5,
    )
    assert len(res_beta) >= 1
    assert "Celery" in res_beta[0]["content"]
    assert "MongoDB" in res_beta[0]["content"]


# ==============================================================================
# 5. Autonomous Interaction Capture & Context Injection
# ==============================================================================

def test_autonomous_interaction_capture():
    # 1. Tech stack declaration
    msg1 = "My current project uses React, FastAPI and MongoDB."
    mem1 = memory_manager.capture_from_interaction(msg1, conversation_id="conv_101", project_id="dodo_core")
    assert mem1 is not None
    assert mem1["category"] == "project"
    assert "React, FastAPI and MongoDB" in mem1["content"]

    # 2. Verified error fix declaration
    msg2 = "I fixed the authentication error by correcting the JWT configuration."
    mem2 = memory_manager.capture_from_interaction(msg2, conversation_id="conv_101", project_id="dodo_core")
    assert mem2 is not None
    assert mem2["category"] == "task_experience"
    assert "JWT configuration" in mem2["content"]

    # 3. User preference declaration
    msg3 = "I prefer TypeScript over JavaScript for all frontend components."
    mem3 = memory_manager.capture_from_interaction(msg3, conversation_id="conv_101")
    assert mem3 is not None
    assert mem3["category"] == "preference"
    assert "TypeScript" in mem3["content"]


def test_context_injection_and_token_budget():
    memory_repo.create_memory(
        content="Critical project rule: Always use async/await for I/O operations.",
        category="preference",
        importance=5,
    )

    prompt = "How should I structure the file reader function?"
    injected_block, categories = memory_manager.build_memory_prompt_injection(
        query=prompt,
        max_tokens=200,
    )
    assert "[RELEVANT LONG-TERM MEMORY]" in injected_block
    assert "Always use async/await" in injected_block
    assert "preference" in categories


# ==============================================================================
# 6. REST API Endpoints
# ==============================================================================

@pytest.mark.asyncio
async def test_rest_api_memory_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Memory
        create_res = await ac.post("/api/memory", json={
            "content": "API endpoint for payments is /api/v1/payments",
            "category": "project",
            "project_id": "shop_app",
            "importance": 4,
            "tags": ["payments", "routes"],
        })
        assert create_res.status_code == 201
        created_data = create_res.json()["memory"]
        mem_id = created_data["id"]

        # 2. Get Memory by ID
        get_res = await ac.get(f"/api/memory/{mem_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == mem_id

        # 3. List Memories
        list_res = await ac.get("/api/memory?category=project&project_id=shop_app")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 4. Search Memories
        search_res = await ac.post("/api/memory/search", json={
            "query": "payments endpoint",
            "project_id": "shop_app",
        })
        assert search_res.status_code == 200
        assert search_res.json()["count"] >= 1

        # 5. Update Memory
        update_res = await ac.put(f"/api/memory/{mem_id}", json={
            "content": "API endpoint for payments is /api/v2/payments (v2 upgraded)",
            "importance": 5,
        })
        assert update_res.status_code == 200
        assert "v2 upgraded" in update_res.json()["memory"]["content"]
        assert update_res.json()["memory"]["importance"] == 5

        # 6. Categories & Projects count
        cat_res = await ac.get("/api/memory/categories")
        assert cat_res.status_code == 200
        assert "categories" in cat_res.json()

        proj_res = await ac.get("/api/memory/projects")
        assert proj_res.status_code == 200
        assert "shop_app" in proj_res.json()["projects"]

        # 7. Delete Memory
        del_res = await ac.delete(f"/api/memory/{mem_id}")
        assert del_res.status_code == 200

        # Verify not found
        get_after_del = await ac.get(f"/api/memory/{mem_id}")
        assert get_after_del.status_code == 404


# ==============================================================================
# 7. Persistence Across Backend Restarts
# ==============================================================================

def test_persistence_across_backend_restart():
    # 1. Store persistent memory
    unique_content = "Architecture decision: Microservices communication uses gRPC on port 50051."
    mem, _ = memory_repo.create_memory(
        content=unique_content,
        category="project",
        project_id="grpc_core",
        importance=5,
    )
    mem_id = mem["id"]

    # 2. Simulate Backend Shutdown & Disk Flush
    db_manager.persist_fallback_data()

    # 3. Simulate Backend Startup by loading a fresh repository instance
    new_repo = PersistentMemoryRepository()
    retrieved = new_repo.find_by_id(mem_id)

    assert retrieved is not None
    assert retrieved["id"] == mem_id
    assert retrieved["content"] == unique_content
    assert retrieved["project_id"] == "grpc_core"


# ==============================================================================
# 8. Full 10-Step Acceptance Demonstration Workflow
# ==============================================================================

def test_phase7_acceptance_demonstration_workflow():
    """
    Executes the exact 10-step acceptance demonstration required by Phase 7:
    1. Start DODO.
    2. Provide a project detail in a conversation.
    3. Confirm that the memory is stored.
    4. Stop and restart the backend (simulate disk flush & fresh reload).
    5. Start a new conversation.
    6. Ask DODO about the earlier project detail.
    7. Verify that DODO retrieves the correct memory.
    8. Edit the stored memory.
    9. Ask again and verify the updated information.
    10. Delete the memory and verify that it is no longer retrieved.
    """
    project_name = "acceptance_demo_project"

    # Step 1 & 2: User provides project detail in a conversation
    user_msg_1 = "My current project uses React, FastAPI and MongoDB."
    captured_1 = memory_manager.capture_from_interaction(
        user_message=user_msg_1,
        conversation_id="conv_phase7_demo",
        project_id=project_name,
    )

    # Step 3: Confirm memory is stored in database
    assert captured_1 is not None
    mem_id = captured_1["id"]
    stored_doc = memory_repo.find_by_id(mem_id)
    assert stored_doc is not None
    assert "React, FastAPI and MongoDB" in stored_doc["content"]
    assert stored_doc["category"] == "project"

    # Step 4: Stop and restart the backend (simulated via database disk persistence)
    db_manager.persist_fallback_data()
    restarted_repo = PersistentMemoryRepository()
    persisted_doc = restarted_repo.find_by_id(mem_id)
    assert persisted_doc is not None
    assert persisted_doc["id"] == mem_id

    # Step 5 & 6: Start a new conversation and ask DODO about the earlier project detail
    user_query = "What technology stack am I using in my project?"
    retrieved_results = retrieval_engine.search(
        query=user_query,
        project_id=project_name,
        limit=3,
    )

    # Step 7: Verify DODO retrieves the correct memory
    assert len(retrieved_results) >= 1
    top_result = retrieved_results[0]
    assert "React, FastAPI and MongoDB" in top_result["content"]
    assert top_result["category"] == "project"

    # Step 8: Edit the stored memory
    updated_content = "Project Tech Stack: My current project uses Next.js 14, FastAPI and PostgreSQL."
    restarted_repo.update(mem_id, {"content": updated_content, "importance": 5})

    # Step 9: Ask again and verify the updated information
    updated_results = retrieval_engine.search(
        query=user_query,
        project_id=project_name,
        limit=3,
    )
    assert len(updated_results) >= 1
    assert "Next.js 14, FastAPI and PostgreSQL" in updated_results[0]["content"]

    # Step 10: Delete the memory and verify that it is no longer retrieved
    delete_success = restarted_repo.delete(mem_id)
    assert delete_success is True

    final_results = retrieval_engine.search(
        query=user_query,
        project_id=project_name,
        limit=3,
    )
    matching_ids = [m["id"] for m in final_results]
    assert mem_id not in matching_ids

