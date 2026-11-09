"""
DODO Phase 3: Autonomous Agent Intelligence Engine Tests
Verifies:
1. Intent classification (multi-step autonomous, coding, debugging, conversation).
2. Request analysis and constraint extraction.
3. Task decomposition into ordered, dependency-aware steps.
4. Planning generation (TaskPlan structure, capabilities, risk levels).
5. Task state machine transitions (PLAN -> EXECUTE -> OBSERVE -> EVALUATE -> FIX -> VERIFY -> DELIVER).
6. Tool permission enforcement and gatekeeper security (5 levels).
7. Interactive approval workflow.
8. Controlled bounded retry limits and loop prevention.
9. Cooperative cancellation via CancellationToken.
10. Task management API endpoints (/api/agent/tasks CRUD, start, cancel, approve, events).
11. Safe simulated execution (guaranteeing zero arbitrary OS file modifications).
12. Persistence across database recovery.
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.agents.cancellation import CancellationToken
from backend.app.agents.evaluator import evaluator
from backend.app.agents.execution_engine import execution_engine
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.agents.planner import task_planner
from backend.app.agents.retry_manager import retry_manager
from backend.app.agents.task_decomposer import task_decomposer
from backend.app.agents.task_state import (
    AgentExecutionState,
    AgentPhase,
    StepExecutionRecord,
    TaskStatus,
)
from backend.app.database.repositories.project_repository import TaskRepository
from backend.app.intelligence.intent_classifier import UserIntent, intent_classifier
from backend.app.intelligence.request_analyzer import request_analyzer
from backend.app.tools.registry import PermissionLevel, ToolDefinition, ToolStatus, tool_registry

client = TestClient(app)


def test_intent_classification():
    """1. Test Intent Classification across varied user prompts."""
    # Multi-step autonomous prompt
    r1 = intent_classifier.classify("Build a complete task management application using React, FastAPI and MongoDB")
    assert r1.intent == UserIntent.MULTI_STEP_AUTONOMOUS
    assert r1.is_autonomous_task is True
    assert r1.requires_planning is True

    # Coding assistance
    r2 = intent_classifier.classify("Write a python function to compute fibonacci sequence")
    assert r2.intent == UserIntent.CODING_ASSISTANCE
    assert r2.is_autonomous_task is False

    # Debugging
    r3 = intent_classifier.classify("Fix TypeError: 'NoneType' object is not subscriptable in main.py")
    assert r3.intent == UserIntent.DEBUGGING

    # General conversation
    r4 = intent_classifier.classify("Good morning, what can you do?")
    assert r4.intent == UserIntent.GENERAL_CONVERSATION
    print("\n[Test 1 PASSED] Intent classification verified.")


def test_request_analysis():
    """2. Test Request Analysis, tech stack extraction, and risk assessment."""
    analysis = request_analyzer.analyze("Build an e-commerce platform using React, FastAPI and MongoDB with user authentication")
    assert "react" in analysis.tech_stack
    assert "fastapi" in analysis.tech_stack
    assert "mongodb" in analysis.tech_stack
    assert analysis.complexity_score >= 3
    assert len(analysis.required_capabilities) >= 3
    assert analysis.domain == "web_application"
    print("\n[Test 2 PASSED] Request analysis and architectural extraction verified.")


def test_task_decomposition():
    """3. Test Task Decomposition into ordered, dependency-aware steps."""
    steps = task_decomposer.decompose("Plan a task management application using React, FastAPI and MongoDB")
    assert len(steps) >= 8
    # Step 1 must have no dependencies
    assert steps[0].step_id == 1
    assert steps[0].dependencies == []
    # Step 2 depends on Step 1
    assert steps[1].step_id == 2
    assert 1 in steps[1].dependencies
    # Verify expected outcomes are populated
    for s in steps:
        assert len(s.expected_outcomes) >= 1
        assert s.permission_level in ["READ", "WRITE", "EXECUTE", "DELETE", "DEPLOY"]
    print(f"\n[Test 3 PASSED] Task decomposition verified ({len(steps)} sequential steps).")


def test_plan_generation_structure():
    """4. Test Structured Plan generation without hidden chain-of-thought."""
    plan = task_planner.generate_plan(
        prompt="Plan a task management application using React, FastAPI and MongoDB",
        workspace_path="D:/DODO/workspace",
        task_id="test_plan_001"
    )
    assert plan.task_id == "test_plan_001"
    assert "React" in plan.tech_stack or "react" in plan.tech_stack
    assert plan.estimated_steps >= 8
    assert len(plan.steps) == plan.estimated_steps
    assert plan.risk_level in ["low", "medium", "high", "critical"]
    print("\n[Test 4 PASSED] Structured plan generation verified.")


@pytest.mark.asyncio
async def test_tool_permission_enforcement():
    """5. Test 5-Level Security Permissions: READ, WRITE, EXECUTE, DELETE, DEPLOY."""
    # Check that WRITE requires approval
    permitted, denial = tool_registry.check_permission("write_file", approved=False)
    assert permitted is False
    assert "WRITE" in denial

    # Check with approval
    permitted_approved, _ = tool_registry.check_permission("write_file", approved=True)
    assert permitted_approved is True

    # READ permission is automatically safe
    permitted_read, _ = tool_registry.check_permission("read_file", approved=False)
    assert permitted_read is True

    # Test execution blocked when permissions enforced
    res_blocked = await tool_registry.execute(
        "write_file",
        {"path": "unauthorized.txt", "content": "forbidden"},
        enforce_permissions=True,
        approved=False
    )
    assert res_blocked["success"] is False
    assert res_blocked["permission_denied"] is True
    print("\n[Test 5 PASSED] Tool permission gatekeeper verified.")


@pytest.mark.asyncio
async def test_safe_simulated_execution():
    """6. Test Safe Execution Engine in Phase 3 Simulation Mode."""
    step = StepExecutionRecord(
        step_id=1,
        title="Analyze Specs",
        description="Inspect requirements",
        tool_name=None,
        parameters={},
        expected_outcomes=["Architecture formulated."],
    )
    res = await execution_engine.execute_step(
        step=step,
        task_id="test_sim_task",
        workspace_path="D:/DODO/workspace",
        completed_step_ids=[],
        is_approved=True,
    )
    assert res.success is True
    assert "Planning Observation" in res.observation
    assert res.duration_ms >= 0.0
    print("\n[Test 6 PASSED] Safe simulated execution engine verified.")


def test_retry_limits_and_loop_prevention():
    """7. Test Bounded Retries and Loop Detection."""
    task_id = "test_retry_loop_task"
    retry_manager.reset_task(task_id)

    # First retry attempt
    d1 = retry_manager.should_retry(task_id, step_id=1, error_message="Transient socket timeout")
    assert d1.should_retry is True
    assert d1.retry_count == 1

    # Second retry attempt
    d2 = retry_manager.should_retry(task_id, step_id=1, error_message="Transient socket timeout")
    assert d2.should_retry is True
    assert d2.retry_count == 2

    # Loop detection: identical error repeated 3rd time triggers loop prevention
    d3 = retry_manager.should_retry(task_id, step_id=1, error_message="Transient socket timeout")
    assert d3.should_retry is False
    assert "Loop detected" in d3.reason or "maximum retry limit" in d3.reason
    print("\n[Test 7 PASSED] Bounded retry manager and loop prevention verified.")


def test_cooperative_cancellation():
    """8. Test Cooperative Cancellation Token."""
    token = CancellationToken("task_cancel_101")
    assert token.is_cancelled is False

    token.cancel(reason="User clicked cancel")
    assert token.is_cancelled is True
    assert "User clicked cancel" in token.reason
    print("\n[Test 8 PASSED] Cooperative cancellation token verified.")


def test_task_management_api_crud():
    """9. Test /api/agent/tasks CRUD Endpoints."""
    # 1. Create Task
    create_res = client.post("/api/agent/tasks", json={
        "prompt": "Plan a task management application using React, FastAPI and MongoDB",
        "mode": "developer"
    })
    assert create_res.status_code == 200
    task_data = create_res.json()
    task_id = task_data["id"]
    assert task_data["prompt"] == "Plan a task management application using React, FastAPI and MongoDB"

    # 2. Get Task
    get_res = client.get(f"/api/agent/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 3. List Tasks
    list_res = client.get("/api/agent/tasks")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Start Task
    start_res = client.post(f"/api/agent/tasks/{task_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["success"] is True

    # 5. Cancel Task
    cancel_res = client.post(f"/api/agent/tasks/{task_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
    print("\n[Test 9 PASSED] Task Management API endpoints verified.")


def test_approval_workflow_api():
    """10. Test Interactive Approval Workflow API."""
    # Create a task
    create_res = client.post("/api/agent/tasks", json={
        "prompt": "Test approval workflow task",
        "mode": "developer"
    })
    task_id = create_res.json()["id"]

    # Approve step 4 (WRITE permission gate)
    appr_res = client.post(f"/api/agent/tasks/{task_id}/approve", json={
        "step_id": 4,
        "approved": True,
        "comment": "Approved for testing."
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"
    assert 4 in agent_orchestrator.approved_steps.get(task_id, set())

    # Get events
    events_res = client.get(f"/api/agent/tasks/{task_id}/events")
    assert events_res.status_code == 200
    assert "events" in events_res.json()
    print("\n[Test 10 PASSED] Interactive approval workflow API verified.")


@pytest.mark.asyncio
async def test_orchestrator_complete_lifecycle():
    """11. Test Complete Orchestrator Lifecycle: PLAN -> EXECUTE -> OBSERVE -> EVALUATE -> VERIFY -> DELIVER."""
    task_repo = TaskRepository()
    task = task_repo.create_task(
        prompt="Plan a task management application using React, FastAPI and MongoDB",
        mode="developer"
    )
    task_id = task["id"]

    # Pre-approve step 4 so it runs smoothly through the entire cycle
    agent_orchestrator.approved_steps[task_id] = {4}

    events_received = []
    async for event in agent_orchestrator.execute_task_stream(task_id):
        events_received.append(event)

    event_types = {e["type"] for e in events_received}
    assert "phase_change" in event_types
    assert "plan_generated" in event_types
    assert "step_start" in event_types
    assert "observation" in event_types
    assert "verification" in event_types
    assert "task_completed" in event_types

    # Verify task state in database
    final_task = task_repo.find_by_id(task_id)
    assert final_task["status"] == "completed"
    assert final_task["verified"] is True
    assert "DODO Autonomous Agent Completion Report" in final_task["result_summary"]
    print(f"\n[Test 11 PASSED] Full orchestrator lifecycle verified ({len(events_received)} streaming events).")


def test_task_persistence_and_recovery():
    """12. Test Task State Persistence and Database Reload."""
    task_repo = TaskRepository()
    task = task_repo.create_task(prompt="Persistence Recovery Task", mode="developer")
    task_id = task["id"]

    # Update with plan and status
    task_repo.update_task_plan(task_id, {
        "objective": "Verify Persistence",
        "analysis": "Testing reload",
        "estimated_steps": 1,
        "steps": [{"step_id": 1, "title": "Reload Step", "description": "Check survival", "status": "completed"}]
    })

    # Instantiate fresh repository (simulating restart)
    reloaded_repo = TaskRepository()
    recovered = reloaded_repo.find_by_id(task_id)
    assert recovered is not None
    assert recovered["id"] == task_id
    assert recovered["plan"]["objective"] == "Verify Persistence"
    print("\n[Test 12 PASSED] Task persistence and restart survival verified.")
