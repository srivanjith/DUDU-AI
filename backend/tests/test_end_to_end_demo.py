import asyncio
import pytest
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.agents.state import AgentPhase
from backend.app.database.repositories.project_repository import TaskRepository
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_autonomous_developer_end_to_end_demonstration():
    """
    Executes Section 17 End-to-End Demonstration:
    'Create a complete task management application using React, FastAPI and MongoDB'
    Validates complete agent execution cycle:
    PLAN -> EXECUTE -> OBSERVE -> EVALUATE -> FIX -> VERIFY -> DELIVER
    """
    prompt = "Create a complete task management application using React, FastAPI and MongoDB."
    task_repo = TaskRepository()

    # 1. Register task in MongoDB
    task = task_repo.create_task(
        prompt=prompt,
        workspace_path=settings.AUTHORIZED_WORKSPACE_DIR,
        mode="developer",
    )
    task_id = task["id"]
    assert task_id is not None
    assert task["status"] == "queued"

    # 2. Run the full autonomous agent stream
    events = []
    async for event in agent_orchestrator.execute_task_stream(task_id):
        events.append(event)

    # 3. Verify event flow
    event_types = [e.get("type") for e in events]
    assert "phase_change" in event_types
    assert "plan_generated" in event_types
    assert "step_start" in event_types
    assert "step_complete" in event_types
    assert "task_completed" in event_types

    # 4. Check completed task in database
    completed_task = task_repo.find_by_id(task_id)
    assert completed_task["status"] == "completed"
    assert completed_task["verified"] is True
    assert completed_task["result_summary"] is not None
    assert "DODO Task Completion Report" in completed_task["result_summary"]

    # 5. Verify generated workspace files exist
    from pathlib import Path
    workspace = Path(settings.AUTHORIZED_WORKSPACE_DIR)
    assert (workspace / "backend_app.py").exists()
    assert (workspace / "index.html").exists()
    assert (workspace / "test_task_manager.py").exists()
    assert (workspace / "verification_preview.png").exists()

    print("\n--- End-to-End Autonomous Developer Demonstration Successfully Verified ---")
    print(completed_task["result_summary"])

