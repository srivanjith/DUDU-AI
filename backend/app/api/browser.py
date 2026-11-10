"""
DODO Browser Automation API Endpoints
Provides REST routes for Playwright browser lifecycles, navigation, element interaction,
multi-tab management, live screenshots, and real-time diagnostic telemetry.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.browser.engine import browser_engine
from backend.app.browser.security import browser_security

logger = logging.getLogger("dodo.api.browser")

router = APIRouter(prefix="/api/browser", tags=["Browser Automation & Playwright"])


class LaunchRequest(BaseModel):
    headless: Optional[bool] = Field(True, description="Whether to run Chromium headlessly")


class NavigateRequest(BaseModel):
    url: str = Field(..., description="Target web URL to navigate to")
    wait_until: Optional[str] = Field("domcontentloaded", description="Page load condition")
    timeout_ms: Optional[int] = Field(15000, description="Navigation timeout in milliseconds")


class InteractRequest(BaseModel):
    action: str = Field(..., description="Interaction: click, fill, select, scroll")
    selector: Optional[str] = Field("body", description="CSS selector for target element")
    value: Optional[str] = Field("", description="Input string or option value")
    timeout_ms: Optional[int] = Field(5000, description="Timeout in milliseconds")
    approved: Optional[bool] = Field(False, description="Approval flag for sensitive actions")


class TabSwitchRequest(BaseModel):
    tab_id: str


class ScreenshotReq(BaseModel):
    save_path: Optional[str] = Field(None, description="Workspace path to save image file")
    full_page: Optional[bool] = Field(False, description="Full scrollable page capture")


# ==============================================================================
# Browser Lifecycle & Status
# ==============================================================================

@router.get("/status")
async def get_browser_status():
    """Returns operational status of the Playwright Chromium browser."""
    running = browser_engine.is_running()
    url = await browser_engine.get_url() if running else None
    title = await browser_engine.get_title() if running else None
    tabs = browser_engine.list_tabs() if running else []
    diag = browser_engine.get_diagnostics() if running else {
        "status": "idle",
        "error_count": 0,
        "console_errors": [],
        "page_errors": [],
        "network_failures": [],
        "http_errors": [],
        "recent_console_logs": [],
    }

    return {
        "status": "online" if running else "stopped",
        "running": running,
        "current_url": url,
        "page_title": title,
        "tabs_count": len(tabs),
        "diagnostics": diag,
    }


@router.post("/launch")
async def launch_browser(req: LaunchRequest):
    """Launches Playwright Chromium browser."""
    success = await browser_engine.launch(headless=req.headless if req.headless is not None else True)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to initialize Playwright Chromium instance.")
    return {"success": True, "status": "online"}


@router.post("/close")
@router.post("/stop")
async def close_browser():
    """Closes all browser sessions and frees resources."""
    await browser_engine.close()
    return {"success": True, "status": "stopped"}


# ==============================================================================
# Navigation & Actions
# ==============================================================================

@router.post("/navigate")
async def navigate_page(req: NavigateRequest):
    """Navigates browser to authorized URL."""
    res = await browser_engine.navigate(
        url=req.url,
        wait_until=req.wait_until or "domcontentloaded",
        timeout_ms=req.timeout_ms or 15000,
    )
    if res.get("security_violation"):
        raise HTTPException(status_code=403, detail=res.get("error"))
    return res


@router.post("/interact")
async def interact_element(req: InteractRequest):
    """Performs element click, fill, select, or scroll."""
    act = req.action.lower()
    if act == "click":
        return await browser_engine.click(
            selector=req.selector or "body",
            timeout_ms=req.timeout_ms or 5000,
            approved=req.approved or False,
        )
    elif act == "fill":
        return await browser_engine.fill(
            selector=req.selector or "input",
            value=req.value or "",
            timeout_ms=req.timeout_ms or 5000,
            approved=req.approved or False,
        )
    elif act == "select":
        return await browser_engine.select_option(
            selector=req.selector or "select",
            value=req.value or "",
            timeout_ms=req.timeout_ms or 5000,
        )
    elif act == "scroll":
        return await browser_engine.scroll(
            direction="down" if "down" in req.value.lower() else "up",
            amount=500,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported browser action: '{req.action}'.")


# ==============================================================================
# Visual Screenshot & DOM Diagnostics
# ==============================================================================

@router.get("/screenshot")
@router.post("/screenshot")
async def get_screenshot(full_page: bool = Query(False), save_path: Optional[str] = Query(None)):
    """Captures screenshot of current page."""
    return await browser_engine.screenshot(full_page=full_page, save_path=save_path)


@router.get("/diagnostics")
def get_browser_diagnostics():
    """Returns captured console errors, page exceptions, and network errors."""
    return browser_engine.get_diagnostics()


@router.post("/diagnostics/clear")
def clear_browser_diagnostics():
    """Clears diagnostic log buffer."""
    browser_engine.clear_diagnostics()
    return {"success": True, "message": "Diagnostics cleared."}


@router.get("/dom")
async def inspect_page_dom(selector: str = "body", max_depth: int = 3):
    """Returns structured DOM hierarchy for the current page."""
    return await browser_engine.inspect_dom(selector=selector, max_depth=max_depth)


# ==============================================================================
# Multi-tab Management
# ==============================================================================

@router.get("/tabs")
def list_browser_tabs():
    """Lists open tabs with IDs, titles, and URLs."""
    tabs = browser_engine.list_tabs()
    return {"tabs": tabs, "count": len(tabs)}


@router.post("/tabs/switch")
async def switch_browser_tab(req: TabSwitchRequest):
    """Switches active tab."""
    success = await browser_engine.switch_tab(req.tab_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tab '{req.tab_id}' not found.")
    return {"success": True, "active_tab_id": req.tab_id}


@router.post("/tabs/close")
async def close_browser_tab(req: TabSwitchRequest):
    """Closes specified tab."""
    success = await browser_engine.close_tab(req.tab_id)
    return {"success": success, "closed_tab_id": req.tab_id}


# ==============================================================================
# Legacy Route Endpoints for Backward Compatibility
# ==============================================================================

class InspectPageRequest(BaseModel):
    url: str
    wait_ms: Optional[int] = 2000


@router.post("/inspect")
async def legacy_inspect_url(req: InspectPageRequest):
    from backend.app.tools.browser_tools import open_and_inspect_page
    return await open_and_inspect_page(req.url, req.wait_ms or 2000)
