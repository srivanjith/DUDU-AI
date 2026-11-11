"""
Comprehensive Project Lifecycle Verification Script
Tests:
1. List Projects & Quick Paths
2. Open Project with valid & invalid paths
3. Create New Project for all templates (React+TS, FastAPI, Next.js, Node.js, Empty)
4. Verify files on disk & file reading
5. Test collision prevention & Windows name validation
6. Test security path restrictions
"""
import sys
from pathlib import Path

# Add D:\DODO to sys.path
root_dir = Path("D:/DODO").resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import shutil
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database.mongodb import db_manager

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("🚀 DODO PROJECT LIFECYCLE ACCEPTANCE TESTS")
    print("=" * 60)

    # 1. Test Quick Paths
    print("\n--- 1. Testing GET /api/projects/quick-paths ---")
    res = client.get("/api/projects/quick-paths")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    quick_paths = res.json()
    print(f"✓ Quick paths retrieved: {len(quick_paths)} entries")
    for qp in quick_paths:
        print(f"   • {qp['label']}: {qp['path']}")

    # 2. Test List Projects
    print("\n--- 2. Testing GET /api/projects ---")
    res = client.get("/api/projects")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    projects = res.json()
    print(f"✓ Registered projects retrieved: {len(projects)} projects")

    # 3. Test New Project Creation (React + TypeScript)
    test_workspace_dir = Path("D:/DODO/workspace/_test_projects").resolve()
    if test_workspace_dir.exists():
        shutil.rmtree(test_workspace_dir, ignore_errors=True)
    test_workspace_dir.mkdir(parents=True, exist_ok=True)

    print("\n--- 3. Testing POST /api/projects/create (React + TypeScript) ---")
    react_payload = {
        "name": "test-react-app",
        "destination_folder": str(test_workspace_dir),
        "template": "react-ts",
        "description": "Automated acceptance test React application",
        "init_git": True
    }
    res = client.post("/api/projects/create", json=react_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    created_path = Path(data["workspace_path"])
    print(f"✓ Project created at: {created_path}")
    assert (created_path / "package.json").exists(), "package.json missing"
    assert (created_path / "vite.config.ts").exists(), "vite.config.ts missing"
    assert (created_path / "src" / "App.tsx").exists(), "src/App.tsx missing"
    assert (created_path / "README.md").exists(), "README.md missing"
    print("✓ All React+TS starter files verified on disk.")

    # 4. Test New Project Creation (Python + FastAPI)
    print("\n--- 4. Testing POST /api/projects/create (Python + FastAPI) ---")
    fastapi_payload = {
        "name": "test-fastapi-service",
        "destination_folder": str(test_workspace_dir),
        "template": "python-fastapi",
        "description": "Automated acceptance test FastAPI service",
        "init_git": False
    }
    res = client.post("/api/projects/create", json=fastapi_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    fastapi_path = Path(data["workspace_path"])
    assert (fastapi_path / "main.py").exists(), "main.py missing"
    assert (fastapi_path / "requirements.txt").exists(), "requirements.txt missing"
    assert (fastapi_path / "tests" / "test_main.py").exists(), "tests/test_main.py missing"
    print(f"✓ FastAPI project created and verified at: {fastapi_path}")

    # 5. Test Open Project (Valid)
    print("\n--- 5. Testing POST /api/projects/open (Open existing project) ---")
    open_payload = {
        "path": str(created_path)
    }
    res = client.post("/api/projects/open", json=open_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    open_data = res.json()
    assert open_data["success"] is True
    assert open_data["project"]["name"] == "test-react-app"
    print(f"✓ Successfully opened project: {open_data['project']['name']}")
    print(f"   • Files count: {len(open_data['files'])}")
    print(f"   • Detected primary language: {open_data['scan']['primary_language']}")

    # 6. Test File Reading from Opened Project
    print("\n--- 6. Testing GET /workspace/file with workspace_path ---")
    res = client.get(f"/workspace/file?path=package.json&workspace_path={created_path}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    file_content = res.json()["content"]
    assert "react" in file_content, "react dependency missing from package.json"
    print("✓ Successfully read package.json through workspace file endpoint.")

    # 7. Test Error Handling — Non-existent Path
    print("\n--- 7. Testing Error Handling: Non-existent folder path ---")
    res = client.post("/api/projects/open", json={"path": "D:/NonExistentPath_XYZ123"})
    assert res.status_code == 404, f"Expected 404, got {res.status_code}: {res.text}"
    print(f"✓ Properly rejected non-existent path with 404: {res.json()['detail']}")

    # 8. Test Error Handling — System Directory Blocked
    print("\n--- 8. Testing Error Handling: System directory blocked ---")
    res = client.post("/api/projects/open", json={"path": "C:\\Windows"})
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print(f"✓ Properly blocked system directory with 403: {res.json()['detail']}")

    # 9. Test Error Handling — Collision / Overwrite Prevention
    print("\n--- 9. Testing Error Handling: Folder collision prevention ---")
    res = client.post("/api/projects/create", json=react_payload)
    assert res.status_code == 409, f"Expected 409, got {res.status_code}: {res.text}"
    print(f"✓ Properly prevented non-empty folder overwrite with 409: {res.json()['detail']}")

    # 10. Test Error Handling — Invalid Windows Project Name
    print("\n--- 10. Testing Error Handling: Invalid Windows filename chars ---")
    res = client.post("/api/projects/create", json={
        "name": "invalid<name>?*",
        "destination_folder": str(test_workspace_dir),
        "template": "empty"
    })
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
    print(f"✓ Properly rejected invalid characters with 400: {res.json()['detail']}")

    # 11. Test Error Handling — Reserved Windows Device Name
    print("\n--- 11. Testing Error Handling: Reserved Windows device name ---")
    res = client.post("/api/projects/create", json={
        "name": "CON",
        "destination_folder": str(test_workspace_dir),
        "template": "empty"
    })
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
    print(f"✓ Properly rejected reserved device name with 400: {res.json()['detail']}")

    # Cleanup test projects directory
    shutil.rmtree(test_workspace_dir, ignore_errors=True)
    print("\n✓ Cleaned up temporary test projects.")

    print("\n" + "=" * 60)
    print("🎉 ALL PROJECT LIFECYCLE ACCEPTANCE TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
