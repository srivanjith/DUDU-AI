"""
DODO Phase 5: Secure Terminal Automation & Local Runtime Tests
Tests Local Agent authentication, workspace isolation, command permissions,
real terminal execution, exit codes, streaming, dev server management,
secret redaction, audit logging, and the full Phase 5 autonomous test execution workflow.
"""
import asyncio
import os
import shutil
import sys
import tempfile
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.main import app
from local_agent.config import local_settings
from local_agent.main import app as local_agent_app
from local_agent.security import (
    CommandCategory,
    PermissionRisk,
    classify_command,
    jail_path,
    redact_secrets,
    verify_token_string,
)
from local_agent.terminal.executor import terminal_executor
from local_agent.terminal.manager import process_manager

client = TestClient(app)
agent_client = TestClient(local_agent_app)


@pytest.fixture
def temp_workspace():
    """Creates a temporary workspace directory for safe isolated tests."""
    temp_dir = tempfile.mkdtemp(prefix="dodo_test_ws_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# 1. Local Agent Authentication Tests
# ==============================================================================

def test_local_agent_health():
    res = agent_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["agent"] == "DODO Local Agent"
    assert "active_processes_count" in data


def test_local_agent_auth_enforcement():
    # 1. Missing Token -> 401 Unauthorized
    res = agent_client.post("/api/exec", json={"command": "dir"})
    assert res.status_code == 401
    assert "Unauthorized" in res.json()["detail"]

    # 2. Invalid Token -> 401 Unauthorized
    res = agent_client.post(
        "/api/exec",
        headers={"X-DODO-Token": "invalid_token_12345"},
        json={"command": "dir"}
    )
    assert res.status_code == 401

    # 3. Valid Token -> Accepted
    res = agent_client.post(
        "/api/exec",
        headers={"X-DODO-Token": local_settings.SECRET_TOKEN},
        json={"command": "python --version"}
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_token_string_verification():
    assert verify_token_string(local_settings.SECRET_TOKEN) is True
    assert verify_token_string("wrong_token") is False
    assert verify_token_string(None) is False
    assert verify_token_string("") is False


# ==============================================================================
# 2. Workspace Isolation & Directory Traversal Prevention
# ==============================================================================

def test_path_jail_isolation(temp_workspace):
    # Valid relative subpath inside workspace
    valid, p, err = jail_path("src/components", temp_workspace)
    assert valid is True
    assert str(p).startswith(str(Path(temp_workspace).resolve()))
    assert err == ""

    # Directory traversal escape using '..'
    valid, p, err = jail_path("../../escaped_dir", temp_workspace)
    assert valid is False
    assert "escapes authorized workspace" in err

    # Absolute path escaping authorized workspace
    foreign_path = "C:\\Windows\\System32" if sys.platform == "win32" else "/etc"
    valid, p, err = jail_path(foreign_path, temp_workspace)
    assert valid is False
    assert "escapes authorized workspace" in err


# ==============================================================================
# 3. Command Classification & Permission Enforcement
# ==============================================================================

def test_command_classification():
    # Read Commands
    cat, risk, _ = classify_command("git status")
    assert cat == CommandCategory.READ
    assert risk == PermissionRisk.AUTOMATIC

    cat, risk, _ = classify_command("python --version")
    assert cat == CommandCategory.READ
    assert risk == PermissionRisk.AUTOMATIC

    # Test Commands
    cat, risk, _ = classify_command("python -m pytest test_tasks.py -v")
    assert cat == CommandCategory.TEST
    assert risk == PermissionRisk.AUTOMATIC

    # Dev Server Commands
    cat, risk, _ = classify_command("npm run dev")
    assert cat == CommandCategory.DEV_SERVER
    assert risk == PermissionRisk.AUTOMATIC

    # Dependency Installation -> MUST REQUIRE APPROVAL
    cat, risk, reason = classify_command("pip install pytest")
    assert cat == CommandCategory.DEPENDENCY_INSTALL
    assert risk == PermissionRisk.REQUIRES_APPROVAL
    assert "explicit user approval" in reason

    cat, risk, _ = classify_command("npm install lodash")
    assert cat == CommandCategory.DEPENDENCY_INSTALL
    assert risk == PermissionRisk.REQUIRES_APPROVAL

    # Dangerous Prohibited Commands -> PROHIBITED
    cat, risk, _ = classify_command("format C:")
    assert cat == CommandCategory.PROHIBITED
    assert risk == PermissionRisk.PROHIBITED

    cat, risk, _ = classify_command("shutdown /s /t 0")
    assert cat == CommandCategory.PROHIBITED
    assert risk == PermissionRisk.PROHIBITED

    cat, risk, _ = classify_command("rmdir /s C:\\")
    assert cat == CommandCategory.PROHIBITED
    assert risk == PermissionRisk.PROHIBITED


# ==============================================================================
# 4. Real Command Execution in Isolated Workspace
# ==============================================================================

@pytest.mark.asyncio
async def test_real_command_execution(temp_workspace):
    # Safe python command printing output
    cmd = 'python -c "print(\'DODO_PHASE_5_REAL_TERMINAL_OUTPUT\')"'
    res = await terminal_executor.execute(
        command=cmd,
        cwd="",
        workspace_root=temp_workspace,
        timeout=15,
        approved=True,
    )

    assert res["success"] is True
    assert res["exit_code"] == 0
    assert "DODO_PHASE_5_REAL_TERMINAL_OUTPUT" in res["stdout"]
    assert res["duration_ms"] > 0


@pytest.mark.asyncio
async def test_failing_command_exit_code(temp_workspace):
    # Non-zero exit code capture
    cmd = 'python -c "import sys; sys.exit(42)"'
    res = await terminal_executor.execute(
        command=cmd,
        cwd="",
        workspace_root=temp_workspace,
        timeout=15,
        approved=True,
    )

    assert res["success"] is False
    assert res["exit_code"] == 42


@pytest.mark.asyncio
async def test_prohibited_command_blocked(temp_workspace):
    res = await terminal_executor.execute(
        command="format D:",
        cwd="",
        workspace_root=temp_workspace,
        timeout=5,
        approved=True,
    )
    assert res["success"] is False
    assert res["exit_code"] == -1
    assert "Security Policy Violation" in res["error"]


@pytest.mark.asyncio
async def test_dependency_install_requires_approval(temp_workspace):
    # Unapproved pip install must be paused
    res = await terminal_executor.execute(
        command="pip install some-package",
        cwd="",
        workspace_root=temp_workspace,
        timeout=15,
        approved=False,
    )
    assert res["requires_approval"] is True
    assert res["success"] is False
    assert "Approval Required" in res["error"]


# ==============================================================================
# 5. Output Streaming, Redaction & Limits
# ==============================================================================

def test_secret_redaction():
    raw = "Connected using token=dodo_local_agent_shared_secure_token_v1 with api_key='sk-1234567890abcdef'"
    redacted = redact_secrets(raw)
    assert "dodo_local_agent_shared_secure_token_v1" not in redacted
    assert "sk-1234567890abcdef" not in redacted
    assert "***REDACTED***" in redacted or "***DODO_SECRET_TOKEN_REDACTED***" in redacted


@pytest.mark.asyncio
async def test_streaming_callback(temp_workspace):
    chunks = []

    def on_output(stream, text):
        chunks.append((stream, text))

    cmd = 'python -c "print(\'LINE_1\'); print(\'LINE_2\')"'
    res = await terminal_executor.execute(
        command=cmd,
        cwd="",
        workspace_root=temp_workspace,
        timeout=15,
        approved=True,
        on_output=on_output,
    )

    assert res["success"] is True
    assert len(chunks) >= 2
    output_joined = "".join(text for _, text in chunks)
    assert "LINE_1" in output_joined
    assert "LINE_2" in output_joined


# ==============================================================================
# 6. Process Manager & Dev Server Duplicate Prevention
# ==============================================================================

@pytest.mark.asyncio
async def test_dev_server_duplicate_prevention(temp_workspace):
    # Spawn background dev server command
    cmd = 'python -c "import time; time.sleep(10)"'
    res1 = await terminal_executor.execute(
        command=cmd,
        cwd="",
        workspace_root=temp_workspace,
        timeout=15,
        approved=True,
        is_dev_server=True,
    )

    # Attempt to start the exact same dev server concurrently
    res2 = await terminal_executor.execute(
        command=cmd,
        cwd="",
        workspace_root=temp_workspace,
        timeout=15,
        approved=True,
        is_dev_server=True,
    )

    # Second invocation must detect duplicate
    assert res2.get("already_running") is True
    assert res2.get("pid") == res1.get("pid")

    # Clean up process
    pid = res1.get("pid")
    if pid:
        await process_manager.kill_process(pid)


# ==============================================================================
# 7. Audit Logging
# ==============================================================================

@pytest.mark.asyncio
async def test_audit_history_logging(temp_workspace):
    cmd = 'python -c "print(\'AUDIT_TEST\')"'
    res = await terminal_executor.execute(
        command=cmd,
        cwd="",
        workspace_root=temp_workspace,
        timeout=10,
        approved=True,
    )
    assert res["success"] is True

    history = terminal_executor.get_audit_history(limit=10)
    assert len(history) > 0
    latest = history[-1]
    assert latest["command"] == cmd
    assert latest["success"] is True
    assert latest["exit_code"] == 0
    assert "timestamp" in latest


# ==============================================================================
# 8. Backend API Endpoints Tests
# ==============================================================================

def test_backend_terminal_agent_status():
    res = client.get("/api/terminal/agent/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data


def test_backend_terminal_execution_approval_flow(temp_workspace):
    # 1. Submit dependency install command requiring approval
    res = client.post("/api/terminal/execute", json={
        "command": "pip install pytest",
        "workspace_root": temp_workspace,
        "approved": False,
    })
    assert res.status_code == 200
    data = res.json()
    assert data.get("requires_approval") is True
    exec_id = data.get("execution_id")
    assert exec_id is not None

    # 2. Check pending approvals endpoint
    pend_res = client.get("/api/terminal/pending-approvals")
    assert pend_res.status_code == 200
    pending_list = pend_res.json()
    assert any(p["execution_id"] == exec_id for p in pending_list)

    # 3. Approve and execute
    appr_res = client.post(f"/api/terminal/approve/{exec_id}")
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert "exit_code" in appr_data


def test_backend_terminal_history_endpoint():
    res = client.get("/api/terminal/history?limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_backend_terminal_processes_endpoint():
    res = client.get("/api/terminal/processes")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ==============================================================================
# 9. Acceptance Demonstration: Full 9-Step Autonomous Test Workflow
# ==============================================================================

@pytest.mark.asyncio
async def test_phase5_autonomous_acceptance_workflow():
    """
    Simulates the acceptance user request:
    'Run the Python task manager tests in my registered workspace.
     If dependencies are missing, explain what is required and request approval before installation.
     Execute the tests, inspect failures, propose fixes, and verify the final result.'
    """
    from backend.app.agents.orchestrator import agent_orchestrator
    from backend.app.agents.task_decomposer import task_decomposer
    from backend.app.database.repositories.workspace_repository import workspace_repo

    # 1. Use the Phase 4 Task App Workspace
    workspace_path = "D:\\DODO\\workspace\\demo_task_app_phase4"
    os.makedirs(workspace_path, exist_ok=True)

    ws_record = workspace_repo.register_workspace(
        name="demo_task_app_phase4",
        path=workspace_path,
        description="Phase 5 Terminal Testing Acceptance Workspace",
    )

    prompt = (
        "Run the Python task manager tests in my registered workspace. "
        "If dependencies are missing, explain what is required and request approval before installation. "
        "Execute the tests, inspect failures, propose fixes, and verify the final result."
    )

    # 2. Task Decomposition
    steps = task_decomposer.decompose(prompt)
    assert len(steps) == 9
    assert steps[0].title.startswith("PLAN")
    assert steps[1].title.startswith("INSPECT")
    assert steps[2].title.startswith("REQUEST APPROVAL")
    assert steps[2].approval_required is True
    assert steps[2].permission_level == "DEPENDENCY_INSTALL"
    assert steps[3].title.startswith("EXECUTE")
    assert steps[4].title.startswith("OBSERVE")
    assert steps[5].title.startswith("EVALUATE")
    assert steps[6].title.startswith("FIX")
    assert steps[7].title.startswith("VERIFY")
    assert steps[8].title.startswith("DELIVER")

    # 3. Create Orchestrator Task in Database
    from backend.app.database.repositories.project_repository import TaskRepository
    task_repo = TaskRepository()
    task = task_repo.create_task(
        prompt=prompt,
        workspace_path=workspace_path,
    )
    task_id = task["id"]

    # 4. Pre-approve Step 3 (Dependency Install Approval Gate)
    agent_orchestrator.approved_steps[task_id] = {3}

    # 5. Run Orchestrator Execution Stream
    events = []
    async for event in agent_orchestrator.execute_task_stream(task_id):
        events.append(event)

    # 6. Verify Task State & Event Telemetry
    event_types = {e["type"] for e in events}
    assert "plan_generated" in event_types
    assert "task_completed" in event_types

    # 7. Check that real test execution evidence was recorded
    final_task = task_repo.find_by_id(task_id)
    assert final_task["status"] == "completed"
    assert final_task["verified"] is True
    assert final_task["result_summary"] is not None
    assert "DODO Autonomous Agent Completion Report" in final_task["result_summary"]
