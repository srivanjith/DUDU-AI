import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.security import validate_workspace_path
from backend.app.tools.registry import tool_registry, ToolDefinition, ToolParameter

logger = logging.getLogger("dodo.tools.browser")


@tool_registry.register(ToolDefinition(
    name="open_and_inspect_page",
    description="Opens a web application URL in Playwright headless browser and inspects title, status, and console logs.",
    permission_level="automatic",
    parameters=[
        ToolParameter(name="url", type="string", description="URL to open (e.g. http://localhost:3000)"),
        ToolParameter(name="wait_ms", type="integer", description="Milliseconds to wait for page to render", required=False, default=2000),
    ]
))
async def open_and_inspect_page(url: str, wait_ms: int = 2000) -> Dict[str, Any]:
    from playwright.async_api import async_playwright

    console_logs = []
    page_errors = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(wait_ms)

            title = await page.title()
            content = await page.content()
            status_code = response.status if response else None

            # Capture a screenshot as base64 preview
            screenshot_bytes = await page.screenshot(type="jpeg", quality=60)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            await browser.close()

            return {
                "url": url,
                "status_code": status_code,
                "title": title,
                "html_length": len(content),
                "console_logs": console_logs,
                "page_errors": page_errors,
                "has_errors": len(page_errors) > 0,
                "screenshot_b64": screenshot_b64,
                "success": status_code in [200, 304] if status_code else True,
            }
    except Exception as e:
        return {
            "url": url,
            "error": f"Failed to inspect page: {str(e)}",
            "has_errors": True,
            "success": False,
        }


@tool_registry.register(ToolDefinition(
    name="take_screenshot",
    description="Takes a screenshot of a web application and saves it to an authorized workspace path.",
    permission_level="controlled",
    parameters=[
        ToolParameter(name="url", type="string", description="URL of the web application"),
        ToolParameter(name="save_path", type="string", description="Relative path in workspace to save screenshot PNG"),
    ]
))
async def take_screenshot(url: str, save_path: str = "screenshot.png") -> Dict[str, Any]:
    from playwright.async_api import async_playwright

    valid, out_path, err = validate_workspace_path(save_path)
    if not valid:
        return {"error": err}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=15000)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(out_path), full_page=True)
            await browser.close()

            return {
                "success": True,
                "saved_path": str(out_path),
                "url": url,
            }
    except Exception as e:
        return {"error": f"Failed to take screenshot: {str(e)}"}

