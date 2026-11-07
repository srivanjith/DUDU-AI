import base64
from typing import Any, Dict
from local_agent.security import jail_path


class LocalBrowserRunner:
    """Automates browser sessions and takes screenshots via Playwright."""

    async def inspect(self, url: str) -> Dict[str, Any]:
        from playwright.async_api import async_playwright
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                res = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                title = await page.title()
                shot = await page.screenshot(type="jpeg", quality=60)
                await browser.close()
                return {
                    "success": True,
                    "title": title,
                    "status_code": res.status if res else None,
                    "screenshot_b64": base64.b64encode(shot).decode("utf-8"),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


browser_runner = LocalBrowserRunner()

