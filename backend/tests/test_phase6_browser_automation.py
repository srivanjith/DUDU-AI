"""
DODO Phase 6: Browser Automation & Autonomous Web Interaction Tests
Tests Playwright Chromium launch/shutdown, multi-tab management, navigation,
DOM inspection, element interaction (click, fill, select, scroll), screenshot capture,
real-time console/network error diagnostics, domain security, sensitive action gating,
and the full 9-stage autonomous web testing acceptance workflow.
"""
import asyncio
import os
import shutil
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.browser.engine import browser_engine
from backend.app.browser.security import browser_security
from backend.app.tools.browser_tools import (
    browser_click,
    browser_close_tab,
    browser_fill,
    browser_get_text,
    browser_get_title,
    browser_get_url,
    browser_inspect_dom,
    browser_list_tabs,
    browser_navigate,
    browser_screenshot,
    browser_scroll,
    browser_select,
    browser_switch_tab,
)

client = TestClient(app)

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Test Playground</title>
</head>
<body>
  <h1 id="header">DODO Browser Test Header</h1>
  <p class="description">Interactive automation test page</p>
  
  <input type="text" id="name-input" name="username" placeholder="Enter name" />
  <button id="submit-btn" onclick="document.getElementById('result').textContent = 'Submitted: ' + document.getElementById('name-input').value">Submit</button>

  <button id="delete-btn" class="delete-btn">Delete Account</button>

  <select id="role-select">
    <option value="developer">Developer</option>
    <option value="manager">Manager</option>
  </select>

  <div id="result">Initial</div>

  <button id="error-btn" onclick="console.error('Simulated Console Error 404');">Trigger Error</button>
</body>
</html>
"""


@pytest.fixture(scope="module", autouse=True)
def cleanup_browser():
    """Ensures browser is closed after module tests."""
    yield
    asyncio.run(browser_engine.close())


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp(prefix="dodo_browser_test_ws_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# 1. Security & URL Restriction Tests
# ==============================================================================

def test_browser_security_domain_and_protocol():
    # 1. file:// protocol MUST be blocked
    valid, err = browser_security.validate_url("file:///C:/Windows/System32/calc.exe")
    assert valid is False
    assert "Security Policy Violation" in err

    # 2. javascript: protocol MUST be blocked
    valid, err = browser_security.validate_url("javascript:alert(1)")
    assert valid is False

    # 3. Localhost development URLs permitted
    valid, err = browser_security.validate_url("http://localhost:3000")
    assert valid is True

    valid, err = browser_security.validate_url("http://127.0.0.1:8000/static/index.html")
    assert valid is True

    # 4. Data URLs permitted for HTML testing
    valid, err = browser_security.validate_url("data:text/html,<h1>Test</h1>")
    assert valid is True


def test_sensitive_action_detection():
    # Action matching delete pattern requires approval
    allowed, needs_approval, reason = browser_security.check_sensitive_interaction(
        action="click", selector="#delete-btn", approved=False
    )
    assert allowed is False
    assert needs_approval is True
    assert "Approval Required" in reason

    # When approved=True, action is allowed
    allowed, needs_approval, _ = browser_security.check_sensitive_interaction(
        action="click", selector="#delete-btn", approved=True
    )
    assert allowed is True
    assert needs_approval is False


# ==============================================================================
# 2. Browser Engine Lifecycle & Navigation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_browser_launch_and_navigation():
    # 1. Launch Chromium
    launched = await browser_engine.launch(headless=True)
    assert launched is True
    assert browser_engine.is_running() is True

    # 2. Navigate to data URL
    data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"
    res = await browser_engine.navigate(data_url)
    assert res["success"] is True
    assert res["title"] == "Test Playground"

    # 3. Verify Title and URL
    assert await browser_engine.get_title() == "Test Playground"
    curr_url = await browser_engine.get_url()
    assert "data:text/html" in curr_url


@pytest.mark.asyncio
async def test_multi_tab_management():
    # 1. Open second tab
    t2 = await browser_engine.new_tab("data:text/html,<title>Tab 2</title>")
    assert "tab_id" in t2

    # 2. List tabs
    tabs = browser_engine.list_tabs()
    assert len(tabs) >= 2

    # 3. Switch tab
    switched = await browser_engine.switch_tab(t2["tab_id"])
    assert switched is True
    assert await browser_engine.get_title() == "Tab 2"

    # 4. Close tab
    closed = await browser_engine.close_tab(t2["tab_id"])
    assert closed is True


# ==============================================================================
# 3. DOM Inspection & Element Interaction Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_dom_inspection_and_text_extraction():
    data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"
    await browser_engine.navigate(data_url)

    # 1. Inspect DOM
    dom_res = await browser_engine.inspect_dom(selector="body", max_depth=3)
    assert dom_res["success"] is True
    tree = dom_res["dom"]
    assert tree["tag"] == "body"
    assert len(tree["children"]) > 0

    # 2. Get Text
    text_res = await browser_engine.get_text("#header")
    assert text_res["success"] is True
    assert text_res["text"] == "DODO Browser Test Header"


@pytest.mark.asyncio
async def test_element_interactions():
    data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"
    await browser_engine.navigate(data_url)

    # 1. Fill Input Field
    fill_res = await browser_engine.fill("#name-input", "PlaywrightUser")
    assert fill_res["success"] is True

    # 2. Click Button
    click_res = await browser_engine.click("#submit-btn")
    assert click_res["success"] is True

    # 3. Verify resulting DOM update
    res_text = await browser_engine.get_text("#result")
    assert res_text["text"] == "Submitted: PlaywrightUser"

    # 4. Select Dropdown Option
    sel_res = await browser_engine.select_option("#role-select", "manager")
    assert sel_res["success"] is True

    # 5. Scroll page
    scroll_res = await browser_engine.scroll("down", 200)
    assert scroll_res["success"] is True


# ==============================================================================
# 4. Screenshot Capture & Workspace Storage Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_screenshot_capture(temp_workspace):
    data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"
    await browser_engine.navigate(data_url)

    # In-memory base64 screenshot
    shot_res = await browser_engine.screenshot()
    assert shot_res["success"] is True
    assert len(shot_res["screenshot_b64"]) > 100
    assert shot_res["bytes_length"] > 0

    # Save to workspace path
    save_file = "test_shot.png"
    shot_save = await browser_engine.screenshot(save_path=save_file, workspace_root=temp_workspace)
    assert shot_save["success"] is True
    assert shot_save["saved_path"] is not None
    assert Path(shot_save["saved_path"]).exists()
    assert Path(shot_save["saved_path"]).stat().st_size > 0


# ==============================================================================
# 5. Real-Time Console and Network Error Monitoring Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_console_error_monitoring():
    browser_engine.clear_diagnostics()
    data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"
    await browser_engine.navigate(data_url)

    # Click button that logs console error
    await browser_engine.click("#error-btn")

    # Verify diagnostic buffer captured error
    diag = browser_engine.get_diagnostics()
    assert diag["error_count"] >= 1
    assert any("Simulated Console Error 404" in e for e in diag["console_errors"])


# ==============================================================================
# 6. Tool Registry Browser Tools Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_browser_tool_registry():
    data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"

    # browser_navigate
    res = await browser_navigate(url=data_url)
    assert res["success"] is True

    # browser_get_title
    res = await browser_get_title()
    assert res["title"] == "Test Playground"

    # browser_get_url
    res = await browser_get_url()
    assert "data:text/html" in res["url"]

    # browser_fill & browser_click
    await browser_fill(selector="#name-input", value="ToolUser")
    await browser_click(selector="#submit-btn")
    res = await browser_get_text(selector="#result")
    assert res["text"] == "Submitted: ToolUser"

    # browser_screenshot
    res = await browser_screenshot()
    assert res["success"] is True
    assert "screenshot_b64" in res


# ==============================================================================
# 7. Backend Browser API Endpoints Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_api_browser_status_and_lifecycle():
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Status endpoint
        res = await ac.get("/api/browser/status")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data

        # 2. Navigate via REST
        data_url = f"data:text/html,{SAMPLE_HTML.replace(' ', '%20').replace('\n', '')}"
        res = await ac.post("/api/browser/navigate", json={"url": data_url})
        assert res.status_code == 200
        assert res.json()["success"] is True

        # 3. Screenshot endpoint
        res = await ac.get("/api/browser/screenshot")
        assert res.status_code == 200
        assert "screenshot_b64" in res.json()

        # 4. Diagnostics endpoint
        res = await ac.get("/api/browser/diagnostics")
        assert res.status_code == 200
        assert "error_count" in res.json()

        # 5. DOM endpoint
        res = await ac.get("/api/browser/dom?selector=body")
        assert res.status_code == 200
        assert res.json()["success"] is True

        # 6. Tabs endpoint
        res = await ac.get("/api/browser/tabs")
        assert res.status_code == 200
        assert "tabs" in res.json()


# ==============================================================================
# 8. Acceptance Test: Full 9-Step Autonomous Web Testing Workflow
# ==============================================================================

@pytest.mark.asyncio
async def test_phase6_autonomous_web_acceptance_workflow():
    """
    Simulates the acceptance user request:
    'Open my local task management application in the browser.
     Inspect the interface, test adding a task, updating a task, viewing tasks and deleting a task.
     Detect browser errors and report the results.'
    """
    from backend.app.agents.orchestrator import agent_orchestrator
    from backend.app.agents.task_decomposer import task_decomposer
    from backend.app.database.repositories.project_repository import TaskRepository
    from backend.app.database.repositories.workspace_repository import workspace_repo

    workspace_path = "D:\\DODO\\workspace\\demo_task_app_phase4"
    os.makedirs(workspace_path, exist_ok=True)

    workspace_repo.register_workspace(
        name="demo_task_app_phase4",
        path=workspace_path,
        description="Phase 6 Browser Verification Acceptance Workspace",
    )

    prompt = (
        "Open my local task management application in the browser. "
        "Inspect the interface, test adding a task, updating a task, viewing tasks and deleting a task. "
        "Detect browser errors and report the results."
    )

    # 1. Task Decomposition
    steps = task_decomposer.decompose(prompt)
    assert len(steps) == 9
    assert steps[0].title.startswith("PLAN")
    assert steps[1].title.startswith("NAVIGATE")
    assert steps[2].title.startswith("INSPECT")
    assert steps[3].title.startswith("INTERACT")
    assert steps[4].title.startswith("INTERACT")
    assert steps[5].title.startswith("INTERACT & APPROVAL")
    assert steps[5].approval_required is True
    assert steps[6].title.startswith("OBSERVE & DIAGNOSE")
    assert steps[7].title.startswith("EVALUATE & VERIFY")
    assert steps[8].title.startswith("DELIVER")

    # 2. Create Task in Database
    task_repo = TaskRepository()
    task = task_repo.create_task(
        prompt=prompt,
        workspace_path=workspace_path,
    )
    task_id = task["id"]

    # 3. Pre-approve Step 6 (Sensitive Deletion Action)
    agent_orchestrator.approved_steps[task_id] = {6}

    # 4. Execute Orchestrator Task Stream
    events = []
    async for event in agent_orchestrator.execute_task_stream(task_id):
        events.append(event)

    # 5. Verify Telemetry & Execution State
    event_types = {e["type"] for e in events}
    assert "plan_generated" in event_types
    assert "task_completed" in event_types

    final_task = task_repo.find_by_id(task_id)
    assert final_task["status"] == "completed"
    assert final_task["verified"] is True
    assert final_task["result_summary"] is not None
    assert "DODO Autonomous Agent Completion Report" in final_task["result_summary"]

