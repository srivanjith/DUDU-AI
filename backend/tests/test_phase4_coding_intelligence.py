"""
DODO Phase 4: Autonomous Coding & Project Intelligence Tests
Verifies:
1. Workspace registration & metadata retrieval.
2. Workspace validation & directory traversal prevention.
3. Project intelligence scanner (language, framework, entrypoints, dependencies).
4. Secure file listing with exclusions (node_modules, .git, secret files).
5. Secure file reading & binary file detection.
6. File searching (grep text across workspace files).
7. Path traversal prevention (cannot escape workspace root).
8. Secret-file exclusion (.env, keys, credentials blocked by default).
9. File write approval gate (WRITE permission enforcement).
10. Atomic file creation and modification.
11. Unified diff generation (preview_changes and diff generation).
12. Pre-modification checkpoint snapshot creation.
13. Checkpoint rollback & restoration.
14. Read-back verification (hashes, byte lengths, non-empty confirmation).
15. Multi-file changes planning & syntax validation.
16. Full autonomous coding acceptance workflow on a dedicated test workspace.
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.agents.orchestrator import agent_orchestrator
from backend.app.core.security import validate_workspace_path
from backend.app.database.repositories.project_repository import TaskRepository
from backend.app.database.repositories.workspace_repository import WorkspaceRepository
from backend.app.intelligence.checkpoint_manager import checkpoint_manager
from backend.app.intelligence.code_generator import code_generator
from backend.app.intelligence.project_scanner import project_scanner
from backend.app.tools.filesystem_tools import (
    delete_file,
    edit_file,
    file_metadata,
    list_workspace_files,
    preview_changes,
    read_file,
    rename_file,
    search_files,
    write_file,
)
from backend.app.tools.registry import PermissionLevel, tool_registry

client = TestClient(app)


@pytest.fixture
def test_workspace(tmp_path):
    """Creates an isolated temporary test workspace for tests."""
    ws = tmp_path / "test_dodo_workspace"
    ws.mkdir(parents=True, exist_ok=True)

    # Populate sample project structure
    (ws / "main.py").write_text("def hello():\n    return 'Hello DODO'\n", encoding="utf-8")
    (ws / "requirements.txt").write_text("fastapi==0.110.0\nuvicorn==0.28.0\npytest==8.0.0\n", encoding="utf-8")
    (ws / ".env").write_text("SECRET_KEY=super_secret_credentials_1234\n", encoding="utf-8")

    sub = ws / "src"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    tests_dir = ws / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_main.py").write_text("from main import hello\ndef test_hello():\n    assert hello() == 'Hello DODO'\n", encoding="utf-8")

    return str(ws)


def test_workspace_registration(test_workspace):
    """1. Test workspace registration and listing."""
    repo = WorkspaceRepository()
    ws = repo.register_workspace(name="Test Suite Workspace", path=test_workspace, is_default=False)
    assert ws["name"] == "Test Suite Workspace"
    assert ws["path"] == str(Path(test_workspace).resolve())

    # Verify API
    res = client.get("/api/workspaces")
    assert res.status_code == 200
    workspaces = res.json()
    assert any(w["path"] == str(Path(test_workspace).resolve()) for w in workspaces)
    print("\n[Test 1 PASSED] Workspace registration verified.")


def test_workspace_validation_and_path_traversal(test_workspace):
    """2. Test workspace validation & path traversal prevention."""
    # Valid relative path
    v1, p1, e1 = validate_workspace_path("main.py", workspace_root=test_workspace)
    assert v1 is True
    assert p1.exists()

    # Traversal attack
    v2, p2, e2 = validate_workspace_path("../../windows/system32/cmd.exe", workspace_root=test_workspace)
    assert v2 is False
    assert "escapes authorized workspace" in e2

    # Absolute path outside root
    v3, p3, e3 = validate_workspace_path("C:/Windows/System32", workspace_root=test_workspace)
    assert v3 is False
    assert "escapes authorized workspace" in e3
    print("\n[Test 2 PASSED] Workspace path traversal prevention verified.")


def test_project_intelligence_scanner(test_workspace):
    """3. Test Project Intelligence Scanner."""
    scan = project_scanner.scan(test_workspace)
    assert scan.primary_language == "Python"
    assert "FastAPI" in scan.frameworks
    assert "pip" in scan.package_managers
    assert any("main.py" in ep for ep in scan.entry_points)
    assert any("test_main.py" in tf for tf in scan.test_files)
    assert "fastapi" in [d.lower() for d in scan.dependencies]
    print(f"\n[Test 3 PASSED] Project scanner verified ({scan.summary}).")


def test_secure_file_listing_and_exclusions(test_workspace):
    """4. Test secure file listing with exclusions."""
    res = list_workspace_files("", depth=3, workspace_root=test_workspace)
    assert "items" in res
    item_paths = [it["path"] for it in res["items"]]
    assert "main.py" in item_paths
    assert "src/utils.py" in item_paths or "src\\utils.py" in [p.replace("/", "\\") for p in item_paths]
    # .env must be excluded from listing
    assert ".env" not in item_paths
    print("\n[Test 4 PASSED] Secure file listing & secret file exclusion verified.")


def test_file_reading_and_secret_block(test_workspace):
    """5. Test secure file reading and blocking secrets."""
    # 1. Normal read
    read_res = read_file("main.py", workspace_root=test_workspace)
    assert "Hello DODO" in read_res["content"]
    assert read_res["total_lines"] >= 2
    assert "file_hash" in read_res

    # 2. Secret read blocked by default
    secret_res = read_file(".env", workspace_root=test_workspace)
    assert "error" in secret_res
    assert "blocked by default" in secret_res["error"]
    print("\n[Test 5 PASSED] Secure file reading & credential protection verified.")


def test_file_searching(test_workspace):
    """6. Test file content search (grep)."""
    res = search_files(query="def hello", workspace_root=test_workspace)
    assert res["total_matches"] >= 1
    assert any("main.py" in m["path"] for m in res["matches"])
    print("\n[Test 6 PASSED] Workspace file searching verified.")


def test_file_metadata(test_workspace):
    """7. Test file metadata inspection."""
    meta = file_metadata("main.py", workspace_root=test_workspace)
    assert meta["is_dir"] is False
    assert meta["size_bytes"] > 0
    assert "line_count" in meta
    assert "file_hash" in meta
    print("\n[Test 7 PASSED] File metadata inspection verified.")


def test_preview_changes_diff(test_workspace):
    """8. Test unified diff preview."""
    diff_res = preview_changes(
        path="main.py",
        proposed_content="def hello():\n    return 'Hello DODO v2'\n",
        workspace_root=test_workspace
    )
    assert "diff" in diff_res
    assert "-    return 'Hello DODO'" in diff_res["diff"]
    assert "+    return 'Hello DODO v2'" in diff_res["diff"]
    print("\n[Test 8 PASSED] Unified diff preview verified.")


def test_file_write_and_modification(test_workspace):
    """9. Test atomic file write and edit."""
    # Write new file
    w_res = write_file("config.json", '{"version": 1}', overwrite=True, workspace_root=test_workspace)
    assert w_res["success"] is True
    assert (Path(test_workspace) / "config.json").exists()

    # Edit file
    e_res = edit_file("config.json", target='"version": 1', replacement='"version": 2', workspace_root=test_workspace)
    assert e_res["success"] is True
    content = (Path(test_workspace) / "config.json").read_text(encoding="utf-8")
    assert '"version": 2' in content
    print("\n[Test 9 PASSED] Atomic file write and edit verified.")


def test_file_rename_and_deletion(test_workspace):
    """10. Test safe rename and delete with confirmation."""
    write_file("config.json", '{"version": 1}', overwrite=True, workspace_root=test_workspace)
    # Rename
    r_res = rename_file("config.json", "settings.json", workspace_root=test_workspace)
    assert r_res["success"] is True
    assert (Path(test_workspace) / "settings.json").exists()
    assert not (Path(test_workspace) / "config.json").exists()

    # Delete without confirmation fails
    d_fail = delete_file("settings.json", confirmed=False, workspace_root=test_workspace)
    assert "error" in d_fail

    # Delete with confirmation succeeds
    d_res = delete_file("settings.json", confirmed=True, workspace_root=test_workspace)
    assert d_res["success"] is True
    assert not (Path(test_workspace) / "settings.json").exists()
    print("\n[Test 10 PASSED] File rename and safe deletion verified.")


def test_checkpoint_creation_and_rollback(test_workspace):
    """11. Test snapshot checkpoint creation and rollback."""
    ws_root = test_workspace
    orig_content = (Path(ws_root) / "main.py").read_text(encoding="utf-8")

    # 1. Create checkpoint
    cp = checkpoint_manager.create_checkpoint(
        workspace_root=ws_root,
        files_to_snapshot=["main.py"],
        title="Pre-corruption snapshot"
    )
    cp_id = cp["checkpoint_id"]

    # 2. Modify file
    write_file("main.py", "CORRUPTED CONTENT", overwrite=True, workspace_root=ws_root)
    assert "CORRUPTED" in (Path(ws_root) / "main.py").read_text(encoding="utf-8")

    # 3. Rollback
    rb = checkpoint_manager.rollback_checkpoint(cp_id, workspace_root=ws_root)
    assert rb["success"] is True
    assert "main.py" in rb["restored_files"]

    # 4. Verify original content restored
    restored = (Path(ws_root) / "main.py").read_text(encoding="utf-8")
    assert restored == orig_content
    print("\n[Test 11 PASSED] Checkpoint snapshot and rollback verified.")


def test_code_change_planning_and_syntax_validation(test_workspace):
    """12. Test code change planner and syntax validation."""
    plan = code_generator.plan_changes(
        prompt="Create a simple Python task management application with add, view, update and delete",
        workspace_path=test_workspace
    )
    assert plan.total_files == 3
    assert plan.all_syntax_valid is True

    file_names = [c.file_path for c in plan.changes]
    assert "task_manager.py" in file_names
    assert "main.py" in file_names
    assert "test_tasks.py" in file_names

    # Check diffs
    for c in plan.changes:
        assert c.syntax_valid is True
        assert len(c.diff) > 0
    print("\n[Test 12 PASSED] Code change planning & Python syntax validation verified.")


def test_apply_approved_change_and_read_back(test_workspace):
    """13. Test applying approved code change and read-back verification."""
    plan = code_generator.plan_changes(
        prompt="Create a simple Python task management application",
        workspace_path=test_workspace
    )
    change = plan.changes[0]  # task_manager.py
    change.is_approved = True

    res = code_generator.apply_approved_change(test_workspace, change)
    assert res["success"] is True
    assert res["verified"] is True
    assert res["bytes_written"] > 0

    # Read back directly
    file_on_disk = Path(test_workspace) / change.file_path
    assert file_on_disk.exists()
    content_on_disk = file_on_disk.read_text(encoding="utf-8")
    assert "class TaskManager:" in content_on_disk
    print("\n[Test 13 PASSED] Atomic approved change write & read-back verification verified.")


def test_workspace_api_endpoints(test_workspace):
    """14. Test Workspace API endpoints."""
    # 1. Register workspace via API
    reg_res = client.post("/api/workspaces", json={
        "name": "API Test Workspace",
        "path": test_workspace,
        "description": "Registered via API"
    })
    assert reg_res.status_code == 200
    ws_id = reg_res.json()["id"]

    # 2. Get workspace
    get_res = client.get(f"/api/workspaces/{ws_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "API Test Workspace"

    # 3. Scan workspace
    scan_res = client.get(f"/api/workspaces/{ws_id}/scan")
    assert scan_res.status_code == 200
    assert scan_res.json()["primary_language"] == "Python"

    # 4. Preview diff via API
    diff_res = client.post("/api/workspace/preview-diff", json={
        "path": "main.py",
        "proposed_content": "# Updated\n"
    })
    assert diff_res.status_code == 200
    assert "diff" in diff_res.json()
    print("\n[Test 14 PASSED] Workspace API endpoints verified.")


@pytest.mark.asyncio
async def test_full_autonomous_coding_acceptance_workflow(tmp_path):
    """
    15 & 16. Section 11 Acceptance Demonstration Test:
    "Create a simple Python task management application in this workspace with add, view, update and delete functionality."
    Expectation:
    1. Scan authorized workspace.
    2. Understand structure.
    3. Generate implementation plan.
    4. Prepare required files with diffs.
    5. Request approval.
    6. Apply approved changes to real filesystem.
    7. Read back and verify resulting structure.
    8. Provide truthful completion report.
    """
    dedicated_ws = tmp_path / "acceptance_task_app"
    dedicated_ws.mkdir(parents=True, exist_ok=True)
    ws_str = str(dedicated_ws)

    task_repo = TaskRepository()
    task = task_repo.create_task(
        prompt="Create a simple Python task management application in this workspace with add, view, update and delete functionality",
        workspace_path=ws_str,
        mode="developer"
    )
    task_id = task["id"]

    # Pre-approve the WRITE steps (steps 4, 5, 6)
    agent_orchestrator.approved_steps[task_id] = {4, 5, 6}

    events = []
    async for event in agent_orchestrator.execute_task_stream(task_id):
        events.append(event)

    event_types = {e["type"] for e in events}
    assert "plan_generated" in event_types
    assert "step_start" in event_types
    assert "observation" in event_types
    assert "task_completed" in event_types

    # VERIFY REAL FILES CREATED ON DISK
    assert (dedicated_ws / "task_manager.py").exists()
    assert (dedicated_ws / "main.py").exists()
    assert (dedicated_ws / "test_tasks.py").exists()

    # READ-BACK VERIFICATION
    tm_content = (dedicated_ws / "task_manager.py").read_text(encoding="utf-8")
    assert "class TaskManager:" in tm_content
    assert "def add_task" in tm_content
    assert "def delete_task" in tm_content

    main_content = (dedicated_ws / "main.py").read_text(encoding="utf-8")
    assert "DODO Task Manager CLI" in main_content

    test_content = (dedicated_ws / "test_tasks.py").read_text(encoding="utf-8")
    assert "def test_task_crud" in test_content

    # VERIFY TASK STATUS & REPORT
    final_task = task_repo.find_by_id(task_id)
    assert final_task["status"] == "completed"
    assert final_task["verified"] is True
    assert "DODO Autonomous Agent Completion Report" in final_task["result_summary"]
    print(f"\n[Test 15 & 16 PASSED] Full Autonomous Coding Acceptance Demonstration successfully verified ({len(events)} events).")
