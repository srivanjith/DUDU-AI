"""
DODO Browser Automation Tools
Registers fine-grained browser interaction tools with the central tool registry.
Provides real browser control via the Playwright engine with security gating.
"""
import logging
from typing import Any, Dict, List, Optional
from backend.app.browser.engine import browser_engine
from backend.app.tools.registry import PermissionLevel, RiskLevel, ToolDefinition, ToolParameter, tool_registry

logger = logging.getLogger("dodo.tools.browser")


# ==============================================================================
# 1. Navigation Tools
# ==============================================================================

@tool_registry.register(ToolDefinition(
    name="browser_navigate",
    description="Navigates the Chromium browser to an authorized URL.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="url", type="string", description="URL to navigate to (e.g. http://localhost:3000)"),
        ToolParameter(name="wait_until", type="string", description="Load state: domcontentloaded, load, networkidle", required=False, default="domcontentloaded"),
        ToolParameter(name="timeout_ms", type="integer", description="Navigation timeout in milliseconds", required=False, default=15000),
    ]
))
async def browser_navigate(url: str, wait_until: str = "domcontentloaded", timeout_ms: int = 15000) -> Dict[str, Any]:
    return await browser_engine.navigate(url=url, wait_until=wait_until, timeout_ms=timeout_ms)


@tool_registry.register(ToolDefinition(
    name="browser_get_url",
    description="Returns current browser page URL.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[]
))
async def browser_get_url() -> Dict[str, Any]:
    url = await browser_engine.get_url()
    return {"success": True, "url": url}


@tool_registry.register(ToolDefinition(
    name="browser_get_title",
    description="Returns current browser page title.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[]
))
async def browser_get_title() -> Dict[str, Any]:
    title = await browser_engine.get_title()
    return {"success": True, "title": title}


# ==============================================================================
# 2. Element Interaction Tools
# ==============================================================================

@tool_registry.register(ToolDefinition(
    name="browser_click",
    description="Clicks an element on the current page matching a CSS selector.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
    parameters=[
        ToolParameter(name="selector", type="string", description="CSS selector of element to click"),
        ToolParameter(name="timeout_ms", type="integer", description="Wait timeout in milliseconds", required=False, default=5000),
        ToolParameter(name="approved", type="boolean", description="Whether user explicitly approved sensitive click", required=False, default=False),
    ]
))
async def browser_click(selector: str, timeout_ms: int = 5000, approved: bool = False) -> Dict[str, Any]:
    return await browser_engine.click(selector=selector, timeout_ms=timeout_ms, approved=approved)


@tool_registry.register(ToolDefinition(
    name="browser_fill",
    description="Fills an input, textarea, or form field with text.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="selector", type="string", description="CSS selector of input element"),
        ToolParameter(name="value", type="string", description="Text string to type into input"),
        ToolParameter(name="timeout_ms", type="integer", description="Wait timeout in milliseconds", required=False, default=5000),
        ToolParameter(name="approved", type="boolean", description="Whether user explicitly approved sensitive fill", required=False, default=False),
    ]
))
async def browser_fill(selector: str, value: str, timeout_ms: int = 5000, approved: bool = False) -> Dict[str, Any]:
    return await browser_engine.fill(selector=selector, value=value, timeout_ms=timeout_ms, approved=approved)


@tool_registry.register(ToolDefinition(
    name="browser_select",
    description="Selects an option in a <select> dropdown element.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="selector", type="string", description="CSS selector of <select> dropdown"),
        ToolParameter(name="value", type="string", description="Value to select"),
        ToolParameter(name="timeout_ms", type="integer", description="Wait timeout in milliseconds", required=False, default=5000),
    ]
))
async def browser_select(selector: str, value: str, timeout_ms: int = 5000) -> Dict[str, Any]:
    return await browser_engine.select_option(selector=selector, value=value, timeout_ms=timeout_ms)


@tool_registry.register(ToolDefinition(
    name="browser_scroll",
    description="Scrolls the page up or down.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="direction", type="string", description="Scroll direction: 'up' or 'down'", required=False, default="down"),
        ToolParameter(name="amount", type="integer", description="Pixel distance to scroll", required=False, default=500),
    ]
))
async def browser_scroll(direction: str = "down", amount: int = 500) -> Dict[str, Any]:
    return await browser_engine.scroll(direction=direction, amount=amount)


# ==============================================================================
# 3. DOM & Text Extraction Tools
# ==============================================================================

@tool_registry.register(ToolDefinition(
    name="browser_get_text",
    description="Extracts visible inner text from an element.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="selector", type="string", description="CSS selector of element (default: 'body')", required=False, default="body"),
        ToolParameter(name="timeout_ms", type="integer", description="Wait timeout in milliseconds", required=False, default=5000),
    ]
))
async def browser_get_text(selector: str = "body", timeout_ms: int = 5000) -> Dict[str, Any]:
    return await browser_engine.get_text(selector=selector, timeout_ms=timeout_ms)


@tool_registry.register(ToolDefinition(
    name="browser_inspect_dom",
    description="Inspects structured DOM tree hierarchy for elements, IDs, classes, and form inputs.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="selector", type="string", description="CSS selector to inspect from (default: 'body')", required=False, default="body"),
        ToolParameter(name="max_depth", type="integer", description="Maximum descendant depth to inspect", required=False, default=3),
    ]
))
async def browser_inspect_dom(selector: str = "body", max_depth: int = 3) -> Dict[str, Any]:
    return await browser_engine.inspect_dom(selector=selector, max_depth=max_depth)


# ==============================================================================
# 4. Screenshot Tools
# ==============================================================================

@tool_registry.register(ToolDefinition(
    name="browser_screenshot",
    description="Takes a screenshot of the current browser page, returns base64 and optionally saves PNG in workspace.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="save_path", type="string", description="Workspace-relative path to save screenshot PNG", required=False, default=None),
        ToolParameter(name="full_page", type="boolean", description="Whether to capture full scrollable page", required=False, default=False),
        ToolParameter(name="workspace_root", type="string", description="Workspace directory root", required=False, default=None),
    ]
))
async def browser_screenshot(
    save_path: Optional[str] = None,
    full_page: bool = False,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    return await browser_engine.screenshot(full_page=full_page, save_path=save_path, workspace_root=workspace_root)


# ==============================================================================
# 5. Tab Management Tools
# ==============================================================================

@tool_registry.register(ToolDefinition(
    name="browser_list_tabs",
    description="Lists all open browser tabs with IDs, titles, and URLs.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[]
))
async def browser_list_tabs() -> Dict[str, Any]:
    tabs = browser_engine.list_tabs()
    return {"success": True, "tabs": tabs, "count": len(tabs)}


@tool_registry.register(ToolDefinition(
    name="browser_switch_tab",
    description="Switches active tab to the specified tab ID.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="tab_id", type="string", description="Tab ID to switch to"),
    ]
))
async def browser_switch_tab(tab_id: str) -> Dict[str, Any]:
    switched = await browser_engine.switch_tab(tab_id)
    return {"success": switched, "tab_id": tab_id}


@tool_registry.register(ToolDefinition(
    name="browser_close_tab",
    description="Closes the specified browser tab.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="tab_id", type="string", description="Tab ID to close"),
    ]
))
async def browser_close_tab(tab_id: str) -> Dict[str, Any]:
    closed = await browser_engine.close_tab(tab_id)
    return {"success": closed, "tab_id": tab_id}


# ==============================================================================
# 6. Legacy Compatibility Wrappers
# ==============================================================================

async def open_and_inspect_page(url: str, wait_ms: int = 2000) -> Dict[str, Any]:
    """Legacy helper: opens URL, waits, returns diagnostics and screenshot."""
    nav_res = await browser_engine.navigate(url)
    if not nav_res["success"]:
        return nav_res

    import asyncio
    await asyncio.sleep(wait_ms / 1000.0)

    title = await browser_engine.get_title()
    shot_res = await browser_engine.screenshot()
    diag = browser_engine.get_diagnostics()

    return {
        "url": url,
        "status_code": nav_res.get("status_code", 200),
        "title": title,
        "console_logs": diag.get("recent_console_logs", []),
        "page_errors": diag.get("page_errors", []),
        "has_errors": diag.get("error_count", 0) > 0,
        "screenshot_b64": shot_res.get("screenshot_b64"),
        "success": True,
    }


async def take_screenshot(url: str, save_path: str = "screenshot.png") -> Dict[str, Any]:
    """Legacy helper: opens URL and saves screenshot."""
    await browser_engine.navigate(url)
    return await browser_engine.screenshot(save_path=save_path)
