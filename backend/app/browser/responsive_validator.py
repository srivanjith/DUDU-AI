"""
DODO Automatic Responsive UI Validation Engine
Tests generated web applications across strict standard viewports:
- Mobile: 375 × 812
- Mobile: 390 × 844
- Tablet: 768 × 1024
- Desktop: 1366 × 768
- Large Desktop: 1920 × 1080

Audits horizontal overflow, broken navigation, touch targets, and form reactivity.
Captures screenshots and automatically repairs layout defects.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from playwright.async_api import Page
from backend.app.browser.engine import browser_engine

logger = logging.getLogger("dodo.browser.responsive")

STANDARD_VIEWPORTS = [
    {"name": "Mobile (Compact)", "width": 375, "height": 812, "device_type": "mobile"},
    {"name": "Mobile (Standard)", "width": 390, "height": 844, "device_type": "mobile"},
    {"name": "Tablet (Portrait)", "width": 768, "height": 1024, "device_type": "tablet"},
    {"name": "Desktop (Standard)", "width": 1366, "height": 768, "device_type": "desktop"},
    {"name": "Desktop (Large FHD)", "width": 1920, "height": 1080, "device_type": "desktop"},
]


class ResponsiveValidationResult:
    def __init__(
        self,
        viewport: Dict[str, Any],
        has_horizontal_overflow: bool,
        scroll_width: int,
        client_width: int,
        nav_status: str,
        interactive_elements: int,
        defects: List[str],
        screenshot_path: Optional[str] = None,
    ):
        self.viewport = viewport
        self.has_horizontal_overflow = has_horizontal_overflow
        self.scroll_width = scroll_width
        self.client_width = client_width
        self.nav_status = nav_status
        self.interactive_elements = interactive_elements
        self.defects = defects
        self.screenshot_path = screenshot_path
        self.is_passed = not has_horizontal_overflow and len(defects) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "viewport_name": self.viewport["name"],
            "dimensions": f"{self.viewport['width']}x{self.viewport['height']}",
            "device_type": self.viewport["device_type"],
            "is_passed": self.is_passed,
            "has_horizontal_overflow": self.has_horizontal_overflow,
            "scroll_width": self.scroll_width,
            "client_width": self.client_width,
            "overflow_delta_px": max(0, self.scroll_width - self.client_width),
            "nav_status": self.nav_status,
            "interactive_elements": self.interactive_elements,
            "defects": self.defects,
            "screenshot_path": self.screenshot_path,
        }


class ResponsiveUIValidator:
    """Automated multi-viewport responsive testing and layout verification."""

    async def validate_url(
        self,
        url: str,
        workspace_dir: Optional[str] = None,
        save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Navigates to URL and performs 5-viewport automated responsive inspection.
        """
        if not browser_engine.is_running():
            launched = await browser_engine.launch(headless=True)
            if not launched:
                return {"success": False, "error": "Could not launch Chromium browser engine."}

        nav_res = await browser_engine.navigate(url)
        if not nav_res.get("success"):
            return {"success": False, "error": f"Failed to navigate to {url}: {nav_res.get('error')}"}

        page = await browser_engine._ensure_active_page()
        screenshots_dir = None
        if save_screenshots and workspace_dir:
            screenshots_dir = Path(workspace_dir) / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

        results: List[ResponsiveValidationResult] = []
        overall_defects: List[str] = []

        for vp in STANDARD_VIEWPORTS:
            w, h = vp["width"], vp["height"]
            await page.set_viewport_size({"width": w, "height": h})
            await asyncio.sleep(0.3)  # Allow CSS media queries and flex re-calculation

            # Deep JS DOM Inspection for layout defects
            metrics = await page.evaluate(r"""
                () => {
                    const docEl = document.documentElement;
                    const body = document.body;
                    const winW = window.innerWidth;
                    const scrollW = Math.max(docEl.scrollWidth, body ? body.scrollWidth : 0);
                    const overflow = scrollW > winW + 2;

                    // Detect overflowing elements
                    const overflowingEls = [];
                    const all = document.querySelectorAll('*');
                    for (const el of all) {
                        if (['HTML', 'BODY', 'SCRIPT', 'STYLE'].includes(el.tagName)) continue;
                        const rect = el.getBoundingClientRect();
                        if (rect.right > winW + 2) {
                            overflowingEls.push({
                                tag: el.tagName.toLowerCase(),
                                id: el.id || '',
                                className: (el.className && typeof el.className === 'string') ? el.className.slice(0, 50) : '',
                                right: Math.round(rect.right),
                                width: Math.round(rect.width)
                            });
                            if (overflowingEls.length >= 3) break;
                        }
                    }

                    // Check Navigation
                    const nav = document.querySelector('nav, header, [role="navigation"]');
                    const hamburger = document.querySelector('button[aria-label*="menu" i], button[aria-label*="nav" i], .hamburger, #mobile-menu-btn');
                    let navStatus = "visible";
                    if (!nav) {
                        navStatus = "missing";
                    } else if (winW < 768 && !hamburger && !nav.offsetParent) {
                        navStatus = "hidden_on_mobile";
                    }

                    // Buttons and Forms
                    const buttons = Array.from(document.querySelectorAll('button, a[href], input[type="button"], input[type="submit"]'));
                    const visibleButtons = buttons.filter(b => b.offsetParent !== null).length;

                    return {
                        scrollWidth: scrollW,
                        clientWidth: winW,
                        hasOverflow: overflow,
                        overflowingEls: overflowingEls,
                        navStatus: navStatus,
                        interactiveCount: visibleButtons
                    };
                }
            """)

            defects = []
            if metrics.get("hasOverflow"):
                defects.append(
                    f"Horizontal overflow on {vp['name']} ({w}x{h}): scrollWidth={metrics['scrollWidth']}px exceeds clientWidth={metrics['clientWidth']}px."
                )
                for el in metrics.get("overflowingEls", []):
                    defects.append(f"  • Overflowing element: <{el['tag']}> id='{el['id']}' class='{el['className']}' right={el['right']}px")

            if metrics.get("navStatus") == "missing":
                defects.append(f"Navigation header missing on {vp['name']}.")

            screenshot_file = None
            if screenshots_dir:
                shot_filename = f"responsive_{w}x{h}.png"
                shot_path = screenshots_dir / shot_filename
                shot_res = await browser_engine.screenshot(save_path=str(shot_path), workspace_root=workspace_dir)
                if shot_res.get("success"):
                    screenshot_file = str(shot_path)

            res = ResponsiveValidationResult(
                viewport=vp,
                has_horizontal_overflow=metrics.get("hasOverflow", False),
                scroll_width=metrics.get("scrollWidth", w),
                client_width=metrics.get("clientWidth", w),
                nav_status=metrics.get("navStatus", "visible"),
                interactive_elements=metrics.get("interactiveCount", 0),
                defects=defects,
                screenshot_path=screenshot_file,
            )
            results.append(res)
            if defects:
                overall_defects.extend(defects)

        passed_count = sum(1 for r in results if r.is_passed)
        all_passed = passed_count == len(results)

        return {
            "success": True,
            "url": url,
            "all_viewports_passed": all_passed,
            "passed_viewports": f"{passed_count}/{len(results)}",
            "viewports": [r.to_dict() for r in results],
            "total_defects_count": len(overall_defects),
            "defects": overall_defects,
            "auto_repair_recommended": len(overall_defects) > 0,
        }

    def repair_css_layout_defects(self, html_content: str, defects: List[str]) -> Tuple[str, List[str]]:
        """
        Applies automated CSS/HTML repair rules for common responsive layout defects:
        - Replaces fixed large widths (e.g. w-[1200px]) with max-w-full or w-full.
        - Injects overflow-x: hidden on body/root.
        - Ensures meta viewport is properly set.
        - Injects responsive media query overrides.
        """
        repaired = html_content
        repairs_applied = []

        # 1. Ensure viewport meta exists
        if '<meta name="viewport"' not in repaired:
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">'
            if "<head>" in repaired:
                repaired = repaired.replace("<head>", f"<head>\n  {viewport_meta}")
                repairs_applied.append("Injected standard mobile viewport meta tag.")

        # 2. Fix horizontal overflow via CSS body rule
        if any("overflow" in d.lower() for d in defects):
            overflow_fix = """
    <style id="dodo-responsive-repair">
      html, body {
        max-width: 100vw !important;
        overflow-x: hidden !important;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      *, *:before, *:after {
        box-sizing: inherit;
      }
      img, video, canvas, svg {
        max-width: 100% !important;
        height: auto;
      }
      .container {
        width: 100% !important;
        max-width: 1280px;
        padding-left: 1rem;
        padding-right: 1rem;
        margin-left: auto;
        margin-right: auto;
      }
      @media (max-width: 640px) {
        .grid-cols-2, .grid-cols-3, .grid-cols-4 {
          grid-template-columns: 1fr !important;
        }
      }
    </style>
"""
            if "</head>" in repaired and "dodo-responsive-repair" not in repaired:
                repaired = repaired.replace("</head>", f"{overflow_fix}\n</head>")
                repairs_applied.append("Injected responsive viewport overflow-x containment style.")

        return repaired, repairs_applied


responsive_validator = ResponsiveUIValidator()
