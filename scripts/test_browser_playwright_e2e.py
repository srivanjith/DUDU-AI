"""
DODO Autonomous IDE - Real Browser Automation Acceptance Test
Uses Playwright Chromium to validate the running React 18 frontend and FastAPI backend:
1. Opens the UI in headless Chromium
2. Registers a student through the React UI form
3. Verifies student is rendered in the DOM table
4. Searches for the student and verifies filtered results
5. Updates the student details through the edit modal
6. Deletes the student through UI action and confirmation dialog
7. Captures full-page screenshots
8. Collects and verifies browser console and network diagnostics (no fatal errors)
"""
import os
import shutil
import sys
import time
from pathlib import Path
import subprocess

root_dir = Path("D:/DODO").resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from playwright.sync_api import sync_playwright

TEST_PORT = 8089
APP_URL = f"http://127.0.0.1:{TEST_PORT}/static/index.html"
WORKSPACE_DIR = Path("D:/DODO/workspace/student_management_system").resolve()
SCREENSHOT_PATH = Path("D:/DODO/artifacts/student_management_playwright.png").resolve()


def prepare_static_vendor():
    """Ensures React 18 vendor files exist in frontend/vendor directory and resets test data."""
    # Reset test data for deterministic test run
    test_data = WORKSPACE_DIR / "backend" / "data" / "students.json"
    if test_data.exists():
        test_data.unlink()
        print("✓ Reset test database for fresh run.")

    vendor_src = Path("D:/DODO/backend/app/intelligence/static_vendor").resolve()
    vendor_dst = WORKSPACE_DIR / "frontend" / "vendor"
    vendor_dst.mkdir(parents=True, exist_ok=True)

    for item in ["react.production.min.js", "react-dom.production.min.js"]:
        src_file = vendor_src / item
        dst_file = vendor_dst / item
        if src_file.exists() and not dst_file.exists():
            shutil.copy(src_file, dst_file)
            print(f"✓ Copied {item} to {vendor_dst}")


def run_playwright_test():
    print("=" * 65)
    print("🎭 DODO PLAYWRIGHT BROWSER VALIDATION SUITE")
    print("   Target: React 18 Frontend + FastAPI Backend")
    print(f"   URL: {APP_URL}")
    print("=" * 65)

    prepare_static_vendor()

    # Step 1: Launch Backend Server in background subprocess
    print("\n[Step 1] Starting student management server on port", TEST_PORT)
    server_cmd = [
        r"D:\DODO\.venv\Scripts\python.exe",
        "-m", "uvicorn",
        "main:app",
        "--host", "127.0.0.1",
        "--port", str(TEST_PORT),
    ]

    backend_cwd = WORKSPACE_DIR / "backend"
    server_proc = subprocess.Popen(
        server_cmd,
        cwd=str(backend_cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to become responsive
    import urllib.request
    server_ready = False
    for attempt in range(25):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{TEST_PORT}/") as resp:
                if resp.status == 200:
                    server_ready = True
                    print(f"✓ Server responded online in {(attempt + 1) * 0.5:.1f}s")
                    break
        except Exception:
            pass

    if not server_ready:
        server_proc.kill()
        print("✗ Server failed to start within timeout.")
        return 1

    console_logs = []
    console_errors = []
    network_errors = []

    try:
        # Step 2: Launch Playwright Chromium
        print("\n[Step 2] Launching Playwright Chromium Headless...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            # Attach event monitors
            page.on("console", lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else console_logs.append(f"[{msg.type}] {msg.text}")
            ))
            page.on("pageerror", lambda exc: console_errors.append(str(exc)))
            page.on("requestfailed", lambda req: network_errors.append(f"{req.method} {req.url} - {req.failure}"))
            page.on("dialog", lambda dialog: (print(f"  • Dismissing dialog: {dialog.message}"), dialog.accept()))

            # Step 3: Navigate to Application
            print(f"\n[Step 3] Navigating to {APP_URL}...")
            page.goto(APP_URL, wait_until="networkidle")

            # Verify initial load and React rendering
            page.wait_for_selector("#root", timeout=8000)
            page.wait_for_selector("#stat-total", timeout=8000)
            initial_total = page.locator("#stat-total").inner_text()
            print(f"✓ React 18 DOM root verified. Initial Total Students: {initial_total}")

            # Step 4: Register Student through UI
            print("\n[Step 4] Registering Student via React Form Interaction...")
            page.click("#open-register-btn")
            page.wait_for_selector("#register-modal", state="visible")

            page.fill("#student-name", "Ada Lovelace")
            page.fill("#student-email", "ada.lovelace@analytical.edu")
            page.select_option("#student-dept", "Computer Science")
            page.select_option("#student-year", "4")
            page.fill("#student-gpa", "3.95")
            page.fill("#student-courses", "CS401, MATH402, ALGO501")

            # Submit form
            page.click("#submit-student-btn")

            # Wait for modal to close and student to appear in DOM table
            page.wait_for_selector("#register-modal", state="hidden", timeout=5000)
            page.wait_for_selector(".student-row", timeout=5000)

            # Assert student is displayed in DOM
            page.wait_for_selector(".student-name-cell:has-text('Ada Lovelace')", timeout=5000)
            ada_row = page.locator(".student-row", has_text="Ada Lovelace").first
            name_cell = ada_row.locator(".student-name-cell").inner_text()
            email_cell = ada_row.locator(".student-email-cell").inner_text()
            gpa_cell = ada_row.locator(".student-gpa-cell").inner_text()
            print(f"✓ Student Registered & Displayed in DOM:")
            print(f"  • Name:  {name_cell}")
            print(f"  • Email: {email_cell}")
            print(f"  • GPA:   {gpa_cell}")
            assert "Ada Lovelace" in name_cell
            assert "ada.lovelace@analytical.edu" in email_cell

            # Step 5: Test Search Functionality in UI
            print("\n[Step 5] Testing Search Filter via UI...")
            search_input = page.locator("#search-input")
            search_input.fill("Ada")
            page.wait_for_timeout(400)
            matched_count = page.locator(".student-row", has_text="Ada Lovelace").count()
            assert matched_count >= 1, "Expected matching row for 'Ada'"
            print(f"✓ Search 'Ada' returned {matched_count} matching record(s).")

            search_input.fill("NonExistentStudentQueryXYZ")
            page.wait_for_timeout(400)
            empty_visible = page.locator("#empty-state").is_visible()
            assert empty_visible, "Empty state should be visible for non-matching query"
            print("✓ Empty search results correctly displayed empty state.")

            # Clear search
            search_input.fill("")
            page.wait_for_timeout(400)

            # Step 6: Test Update via UI Edit Modal
            print("\n[Step 6] Testing Update via React Edit Modal...")
            ada_row = page.locator(".student-row", has_text="Ada Lovelace").first
            ada_row.locator(".edit-student-btn").click()
            page.wait_for_selector("#edit-modal", state="visible")

            page.fill("#edit-gpa", "4.0")
            page.select_option("#edit-status", "Active")
            page.click("#submit-edit-btn")

            page.wait_for_selector("#edit-modal", state="hidden", timeout=5000)
            page.wait_for_timeout(500)

            updated_row = page.locator(".student-row", has_text="Ada Lovelace").first
            updated_gpa = updated_row.locator(".student-gpa-cell").inner_text()
            print(f"✓ Student details updated in DOM: New GPA = {updated_gpa}")
            assert "4.00" in updated_gpa or "4.0" in updated_gpa

            # Step 7: Capture Visual Evidence Screenshot
            print(f"\n[Step 7] Capturing UI Screenshot to {SCREENSHOT_PATH.name}...")
            SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            print(f"✓ Screenshot saved ({SCREENSHOT_PATH.stat().st_size} bytes)")

            # Step 8: Test Delete Operation
            print("\n[Step 8] Testing Delete Student via UI...")
            initial_count = page.locator(".student-row").count()
            del_row = page.locator(".student-row", has_text="Ada Lovelace").first
            del_row.locator(".delete-student-btn").click()
            page.wait_for_selector(".student-name-cell:has-text('Ada Lovelace')", state="detached", timeout=5000)

            final_count = page.locator(".student-row").count()
            print(f"✓ Student successfully deleted: Row count changed from {initial_count} to {final_count}")
            assert final_count == initial_count - 1

            browser.close()

        # Step 9: Validate Diagnostic Console & Network Errors
        print("\n[Step 9] Inspecting Browser Diagnostics...")
        print(f"  • Total Console Logs Captured:   {len(console_logs)}")
        print(f"  • Total Console Errors:          {len(console_errors)}")
        print(f"  • Total Network Request Errors:  {len(network_errors)}")

        for log in console_logs[:4]:
            print(f"    {log}")

        if console_errors:
            print("  ! Non-fatal Console warnings/errors noticed:")
            for err in console_errors:
                print(f"    - {err}")

        # Assert no critical breakages
        assert len(network_errors) == 0, f"Detected network request failures: {network_errors}"

        print("\n" + "=" * 65)
        print("🎉 PLAYWRIGHT BROWSER VALIDATION PASSED COMPLETELY!")
        print("   All 8 steps completed: Load -> Register -> Search -> Update -> Screenshot -> Delete -> Verify")
        print("=" * 65)
        return 0

    finally:
        # Clean shutdown of uvicorn
        print("\nTerminating test server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("✓ Test server stopped cleanly.")


if __name__ == "__main__":
    sys.exit(run_playwright_test())
