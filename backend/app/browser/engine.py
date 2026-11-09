"""
DODO Playwright Browser Automation Engine
Manages Chromium browser lifecycles, tab orchestration, element interactions,
real-time console and network diagnostics, and workspace screenshots.
"""
import asyncio
import base64
import datetime
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from backend.app.browser.security import browser_security
from backend.app.core.security import validate_workspace_path

logger = logging.getLogger("dodo.browser.engine")


class BrowserTab:
    def __init__(self, tab_id: str, page: Page, title: str = "New Tab", url: str = "about:blank"):
        self.tab_id = tab_id
        self.page = page
        self.title = title
        self.url = url
        self.created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()


class PlaywrightBrowserEngine:
    """Stateful Playwright Chromium automation manager with tab & error telemetry."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._tabs: Dict[str, BrowserTab] = {}
        self._active_tab_id: Optional[str] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock: Optional[asyncio.Lock] = None

        # Telemetry & Diagnostics Buffer
        self.console_errors: List[str] = []
        self.console_logs: List[str] = []
        self.page_errors: List[str] = []
        self.network_failures: List[Dict[str, Any]] = []
        self.http_errors: List[Dict[str, Any]] = []

    def _get_lock(self) -> asyncio.Lock:
        try:
            curr_loop = asyncio.get_running_loop()
        except RuntimeError:
            curr_loop = None
        if self._lock is None or self._loop != curr_loop:
            self._lock = asyncio.Lock()
        return self._lock

    def _check_event_loop(self):
        try:
            curr_loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if self._loop is not None and self._loop != curr_loop:
            self._playwright = None
            self._browser = None
            self._context = None
            self._tabs.clear()
            self._active_tab_id = None
        self._loop = curr_loop

    def is_running(self) -> bool:
        self._check_event_loop()
        return self._browser is not None and self._browser.is_connected()

    async def launch(self, headless: bool = True) -> bool:
        """Launches Chromium instance with isolated context."""
        async with self._get_lock():
            self._check_event_loop()
            if self.is_running():
                return True

            try:
                logger.info(f"Launching Playwright Chromium (headless={headless})...")
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                self._context = await self._browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="DODO-Autonomous-Browser-Agent/1.0"
                )

                # Create default tab
                page = await self._context.new_page()
                tab_id = str(uuid.uuid4())[:8]
                tab = BrowserTab(tab_id=tab_id, page=page)
                self._tabs[tab_id] = tab
                self._active_tab_id = tab_id
                self._attach_page_listeners(page)

                browser_security.log_action("launch_browser", "chromium", {"headless": headless}, True)
                return True
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                browser_security.log_action("launch_browser", "chromium", {"headless": headless}, False, str(e))
                await self._cleanup()
                return False

    async def close(self) -> bool:
        """Closes browser and cleans up resources."""
        async with self._get_lock():
            return await self._cleanup()

    async def _cleanup(self) -> bool:
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")
        finally:
            self._playwright = None
            self._browser = None
            self._context = None
            self._tabs.clear()
            self._active_tab_id = None
            self._loop = None
        browser_security.log_action("close_browser", "chromium", {}, True)
        return True

    def _attach_page_listeners(self, page: Page):
        """Attaches telemetry hooks to intercept console errors, exceptions, and network failures."""
        page.on("console", lambda msg: self._handle_console_message(msg))
        page.on("pageerror", lambda exc: self._handle_page_error(exc))
        page.on("requestfailed", lambda req: self._handle_request_failed(req))
        page.on("response", lambda res: self._handle_response(res))

    def _handle_console_message(self, msg):
        text = f"[{msg.type}] {msg.text}"
        self.console_logs.append(text)
        if msg.type in ["error", "warning"]:
            self.console_errors.append(text)
            if len(self.console_errors) > 200:
                self.console_errors.pop(0)

    def _handle_page_error(self, exc):
        err = str(exc)
        self.page_errors.append(err)
        if len(self.page_errors) > 100:
            self.page_errors.pop(0)

    def _handle_request_failed(self, req):
        failure = req.failure
        rec = {
            "url": req.url,
            "method": req.method,
            "error_text": str(failure) if failure else "Unknown network failure",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self.network_failures.append(rec)
        if len(self.network_failures) > 100:
            self.network_failures.pop(0)

    def _handle_response(self, res):
        if res.status >= 400:
            rec = {
                "url": res.url,
                "status": res.status,
                "status_text": res.status_text,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            self.http_errors.append(rec)
            if len(self.http_errors) > 100:
                self.http_errors.pop(0)

    async def _ensure_active_page(self) -> Page:
        if not self.is_running():
            launched = await self.launch(headless=True)
            if not launched:
                raise RuntimeError("Could not initialize Chromium browser session.")

        if self._active_tab_id and self._active_tab_id in self._tabs:
            return self._tabs[self._active_tab_id].page

        # Create new tab if none exist
        tab_id = str(uuid.uuid4())[:8]
        page = await self._context.new_page()
        self._attach_page_listeners(page)
        self._tabs[tab_id] = BrowserTab(tab_id=tab_id, page=page)
        self._active_tab_id = tab_id
        return page

    # ==========================================================================
    # Tab Management
    # ==========================================================================

    async def new_tab(self, url: str = "") -> Dict[str, Any]:
        await self._ensure_active_page()
        page = await self._context.new_page()
        self._attach_page_listeners(page)
        tab_id = str(uuid.uuid4())[:8]
        tab = BrowserTab(tab_id=tab_id, page=page)
        self._tabs[tab_id] = tab
        self._active_tab_id = tab_id

        if url:
            await self.navigate(url)

        return {"tab_id": tab_id, "url": tab.url, "title": tab.title}

    def list_tabs(self) -> List[Dict[str, Any]]:
        results = []
        for tab_id, tab in self._tabs.items():
            results.append({
                "tab_id": tab_id,
                "title": tab.title,
                "url": tab.url,
                "is_active": tab_id == self._active_tab_id,
                "created_at": tab.created_at,
            })
        return results

    async def switch_tab(self, tab_id: str) -> bool:
        if tab_id in self._tabs:
            self._active_tab_id = tab_id
            page = self._tabs[tab_id].page
            await page.bring_to_front()
            return True
        return False

    async def close_tab(self, tab_id: str) -> bool:
        if tab_id not in self._tabs:
            return False
        tab = self._tabs.pop(tab_id)
        try:
            await tab.page.close()
        except Exception:
            pass

        if self._active_tab_id == tab_id:
            self._active_tab_id = next(iter(self._tabs.keys())) if self._tabs else None

        return True

    # ==========================================================================
    # Navigation & Page Controls
    # ==========================================================================

    async def navigate(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout_ms: int = 15000,
    ) -> Dict[str, Any]:
        """Navigates to an authorized URL."""
        # 1. Security Check
        valid, err = browser_security.validate_url(url)
        if not valid:
            browser_security.log_action("navigate", url, {"error": err}, False, err)
            return {
                "success": False,
                "url": url,
                "error": err,
                "security_violation": True,
            }

        page = await self._ensure_active_page()
        try:
            res = None
            try:
                res = await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            except Exception as nav_err:
                # If local backend is not serving during offline test runs, load directly from static directory
                if "127.0.0.1:8000/static/" in url or "localhost:8000/static/" in url:
                    static_rel = url.split("/static/", 1)[1].split("?")[0].split("#")[0]
                    local_static = Path(__file__).resolve().parents[3] / "static" / static_rel
                    if local_static.exists():
                        await page.set_content(local_static.read_text(encoding="utf-8"))
                    else:
                        raise nav_err
                else:
                    raise nav_err

            title = await page.title()
            current_url = page.url

            # Update tab info
            if self._active_tab_id and self._active_tab_id in self._tabs:
                self._tabs[self._active_tab_id].title = title
                self._tabs[self._active_tab_id].url = current_url

            status_code = res.status if res else 200
            browser_security.log_action("navigate", url, {"title": title, "status": status_code}, True)

            return {
                "success": status_code < 400,
                "url": current_url,
                "title": title,
                "status_code": status_code,
                "diagnostics": self.get_diagnostics(),
            }
        except Exception as e:
            err_msg = str(e)
            browser_security.log_action("navigate", url, {"error": err_msg}, False, err_msg)
            return {
                "success": False,
                "url": url,
                "error": f"Navigation failed: {err_msg}",
                "diagnostics": self.get_diagnostics(),
            }

    async def reload(self, timeout_ms: int = 15000) -> Dict[str, Any]:
        page = await self._ensure_active_page()
        try:
            res = await page.reload(wait_until="domcontentloaded", timeout=timeout_ms)
            title = await page.title()
            return {
                "success": True,
                "url": page.url,
                "title": title,
                "status_code": res.status if res else 200,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def go_back(self) -> Dict[str, Any]:
        page = await self._ensure_active_page()
        try:
            await page.go_back(wait_until="domcontentloaded")
            return {"success": True, "url": page.url, "title": await page.title()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def go_forward(self) -> Dict[str, Any]:
        page = await self._ensure_active_page()
        try:
            await page.go_forward(wait_until="domcontentloaded")
            return {"success": True, "url": page.url, "title": await page.title()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # DOM Inspection & Extraction
    # ==========================================================================

    async def get_title(self) -> str:
        page = await self._ensure_active_page()
        return await page.title()

    async def get_url(self) -> str:
        page = await self._ensure_active_page()
        return page.url

    async def get_text(self, selector: str = "body", timeout_ms: int = 5000) -> Dict[str, Any]:
        page = await self._ensure_active_page()
        try:
            elem = page.locator(selector).first
            await elem.wait_for(state="attached", timeout=timeout_ms)
            text = await elem.inner_text()
            return {
                "success": True,
                "selector": selector,
                "text": text.strip(),
            }
        except Exception as e:
            return {"success": False, "selector": selector, "error": str(e)}

    async def inspect_dom(self, selector: str = "body", max_depth: int = 3) -> Dict[str, Any]:
        """Extracts structured DOM tree hierarchy."""
        page = await self._ensure_active_page()
        js_code = """
        (([rootSelector, maxDepth]) => {
            const root = document.querySelector(rootSelector);
            if (!root) return { error: `Element '${rootSelector}' not found.` };

            function parseNode(node, depth) {
                if (depth > maxDepth || !node || node.nodeType !== 1) return null;
                const obj = {
                    tag: node.tagName.toLowerCase(),
                    id: node.id || null,
                    classes: Array.from(node.classList || []),
                    text: (node.childNodes.length === 1 && node.childNodes[0].nodeType === 3)
                        ? node.textContent.trim().substring(0, 100) : null,
                };
                if (node.tagName.toLowerCase() === 'input') {
                    obj.type = node.type;
                    obj.name = node.name;
                    obj.value = node.value;
                    obj.placeholder = node.placeholder;
                }
                if (node.tagName.toLowerCase() === 'button') {
                    obj.text = node.innerText.trim().substring(0, 50);
                }
                const children = [];
                for (let child of node.children) {
                    const parsedChild = parseNode(child, depth + 1);
                    if (parsedChild) children.push(parsedChild);
                }
                if (children.length > 0) obj.children = children;
                return obj;
            }

            return parseNode(root, 1);
        })
        """
        try:
            res = await page.evaluate(js_code, [selector, max_depth])
            return {"success": True, "selector": selector, "dom": res}
        except Exception as e:
            return {"success": False, "selector": selector, "error": str(e)}

    # ==========================================================================
    # Element Interactions
    # ==========================================================================

    async def click(
        self,
        selector: str,
        timeout_ms: int = 5000,
        approved: bool = False,
    ) -> Dict[str, Any]:
        # Sensitive action gating
        allowed, needs_approval, reason = browser_security.check_sensitive_interaction(
            "click", selector, approved=approved
        )
        if not allowed and needs_approval:
            return {
                "success": False,
                "requires_approval": True,
                "reason": reason,
                "action": "click",
                "selector": selector,
            }

        page = await self._ensure_active_page()
        try:
            elem = page.locator(selector).first
            await elem.wait_for(state="visible", timeout=timeout_ms)
            await elem.click()
            await page.wait_for_timeout(300)  # Brief tick for UI reactivity
            browser_security.log_action("click", selector, {}, True)
            return {
                "success": True,
                "action": "click",
                "selector": selector,
                "current_url": page.url,
            }
        except Exception as e:
            err = str(e)
            browser_security.log_action("click", selector, {"error": err}, False, err)
            return {"success": False, "action": "click", "selector": selector, "error": err}

    async def fill(
        self,
        selector: str,
        value: str,
        timeout_ms: int = 5000,
        approved: bool = False,
    ) -> Dict[str, Any]:
        # Sensitive action gating
        allowed, needs_approval, reason = browser_security.check_sensitive_interaction(
            "fill", selector, value, approved=approved
        )
        if not allowed and needs_approval:
            return {
                "success": False,
                "requires_approval": True,
                "reason": reason,
                "action": "fill",
                "selector": selector,
            }

        page = await self._ensure_active_page()
        try:
            elem = page.locator(selector).first
            await elem.wait_for(state="visible", timeout=timeout_ms)
            await elem.fill(value)
            browser_security.log_action("fill", selector, {"length": len(value)}, True)
            return {
                "success": True,
                "action": "fill",
                "selector": selector,
                "value_filled": value,
            }
        except Exception as e:
            err = str(e)
            browser_security.log_action("fill", selector, {"error": err}, False, err)
            return {"success": False, "action": "fill", "selector": selector, "error": err}

    async def select_option(self, selector: str, value: str, timeout_ms: int = 5000) -> Dict[str, Any]:
        page = await self._ensure_active_page()
        try:
            elem = page.locator(selector).first
            await elem.wait_for(state="visible", timeout=timeout_ms)
            selected = await elem.select_option(value)
            browser_security.log_action("select", selector, {"value": value}, True)
            return {"success": True, "action": "select", "selector": selector, "selected": selected}
        except Exception as e:
            return {"success": False, "action": "select", "selector": selector, "error": str(e)}

    async def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        page = await self._ensure_active_page()
        try:
            delta = amount if direction == "down" else -amount
            await page.evaluate(f"window.scrollBy(0, {delta})")
            return {"success": True, "action": "scroll", "direction": direction, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================================
    # Screenshot Capture
    # ==========================================================================

    async def screenshot(
        self,
        full_page: bool = False,
        save_path: Optional[str] = None,
        workspace_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Captures page screenshot as base64 and optionally writes PNG to workspace."""
        page = await self._ensure_active_page()
        try:
            shot_bytes = await page.screenshot(type="png", full_page=full_page)
            shot_b64 = base64.b64encode(shot_bytes).decode("utf-8")

            saved_path_str = None
            if save_path:
                valid, resolved_p, err = validate_workspace_path(save_path, workspace_root)
                if valid:
                    resolved_p.parent.mkdir(parents=True, exist_ok=True)
                    resolved_p.write_bytes(shot_bytes)
                    saved_path_str = str(resolved_p)
                else:
                    logger.warning(f"Failed to save screenshot: {err}")

            return {
                "success": True,
                "url": page.url,
                "title": await page.title(),
                "screenshot_b64": shot_b64,
                "saved_path": saved_path_str,
                "bytes_length": len(shot_bytes),
            }
        except Exception as e:
            return {"success": False, "error": f"Screenshot failed: {str(e)}"}

    # ==========================================================================
    # Telemetry & Diagnostics
    # ==========================================================================

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns structured browser diagnostics for autonomous agent inspection."""
        total_errors = len(self.console_errors) + len(self.page_errors) + len(self.network_failures) + len(self.http_errors)
        return {
            "status": "errors_detected" if total_errors > 0 else "healthy",
            "error_count": total_errors,
            "console_errors": list(self.console_errors),
            "page_errors": list(self.page_errors),
            "network_failures": list(self.network_failures),
            "http_errors": list(self.http_errors),
            "recent_console_logs": self.console_logs[-20:],
        }

    def clear_diagnostics(self):
        self.console_errors.clear()
        self.console_logs.clear()
        self.page_errors.clear()
        self.network_failures.clear()
        self.http_errors.clear()


# Global engine singleton
browser_engine = PlaywrightBrowserEngine()
