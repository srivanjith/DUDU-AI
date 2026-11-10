"""
DODO Workspace Management API
Provides endpoints for:
- POST /api/workspaces
- GET /api/workspaces
- GET /api/workspaces/{workspace_id}
- GET /api/workspaces/{workspace_id}/scan
- DELETE /api/workspaces/{workspace_id}
Also maintains backward-compatible endpoints under /workspace/...
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.core.security import validate_workspace_path
from backend.app.database.repositories.workspace_repository import CheckpointRepository, WorkspaceRepository
from backend.app.intelligence.checkpoint_manager import checkpoint_manager
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

router = APIRouter(tags=["Workspace"])
workspace_repo = WorkspaceRepository()
checkpoint_repo = CheckpointRepository()


class RegisterWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., description="Absolute local path to authorized project directory")
    description: Optional[str] = ""
    is_default: Optional[bool] = False


class SaveFileRequest(BaseModel):
    path: str
    content: str
    overwrite: Optional[bool] = True


class CreateFolderRequest(BaseModel):
    path: str
    workspace_path: Optional[str] = None


class EditFileRequest(BaseModel):
    path: str
    target: str
    replacement: str


class PreviewDiffRequest(BaseModel):
    path: str
    proposed_content: str


class RenameFileRequest(BaseModel):
    old_path: str
    new_path: str
    overwrite: Optional[bool] = False


class DeleteFileRequest(BaseModel):
    path: str
    confirmed: bool = True


# ==============================================================================
# WORKSPACE MANAGEMENT ENDPOINTS
# ==============================================================================

@router.post("/api/workspaces")
def register_workspace(req: RegisterWorkspaceRequest):
    root = Path(req.path).resolve()
    if not root.exists():
        try:
            root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot access or create directory '{req.path}': {str(e)}")

    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Path '{req.path}' is not a directory.")

    doc = workspace_repo.register_workspace(
        name=req.name,
        path=str(root),
        description=req.description or "",
        is_default=req.is_default or False
    )
    # Perform initial scan
    scan_res = project_scanner.scan(str(root))
    workspace_repo.update_scan_summary(doc["id"], scan_res.model_dump())
    doc["scan_summary"] = scan_res.model_dump()
    return doc


@router.get("/api/workspaces")
def list_workspaces():
    workspaces = workspace_repo.find_all(sort=[("created_at", -1)])
    if not workspaces:
        # Auto-register default workspace from settings
        default_dir = str(Path(settings.AUTHORIZED_WORKSPACE_DIR).resolve())
        default_doc = workspace_repo.register_workspace(
            name="Default Workspace",
            path=default_dir,
            description="Default DODO local development workspace",
            is_default=True
        )
        scan = project_scanner.scan(default_dir)
        workspace_repo.update_scan_summary(default_doc["id"], scan.model_dump())
        default_doc["scan_summary"] = scan.model_dump()
        return [default_doc]
    return workspaces


@router.get("/api/workspaces/{workspace_id}")
def get_workspace(workspace_id: str):
    ws = workspace_repo.find_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found.")
    return ws


@router.get("/api/workspaces/{workspace_id}/scan")
def scan_workspace(workspace_id: str):
    ws = workspace_repo.find_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found.")

    scan = project_scanner.scan(ws["path"])
    workspace_repo.update_scan_summary(workspace_id, scan.model_dump())
    return scan.model_dump()


@router.delete("/api/workspaces/{workspace_id}")
def delete_workspace_registration(workspace_id: str):
    ws = workspace_repo.find_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found.")

    workspace_repo.delete(workspace_id)
    return {
        "success": True,
        "message": f"Workspace registration '{ws.get('name')}' removed. Project directory on disk was preserved.",
        "path": ws["path"]
    }


# ==============================================================================
# SECURE FILE INTELLIGENCE & MONACO BACKEND ENDPOINTS
# ==============================================================================

@router.get("/workspace/status")
@router.get("/api/workspace/status")
def get_workspace_status():
    default_ws = workspace_repo.get_default_workspace()
    path = default_ws["path"] if default_ws else str(Path(settings.AUTHORIZED_WORKSPACE_DIR).resolve())
    scan = project_scanner.scan(path)
    return {
        "authorized_workspace": path,
        "scan": scan.model_dump(),
        "git": {
            "is_git_repo": scan.is_git_repo,
            "branch": scan.git_branch,
            "status": scan.git_status,
        }
    }


@router.get("/workspace/files")
@router.get("/api/workspace/files")
def get_files(subpath: str = "", depth: int = 3):
    return list_workspace_files(subpath, depth)


@router.get("/workspace/file")
@router.get("/api/workspace/file")
def get_file_content(path: str, start_line: int = 1, end_line: Optional[int] = None):
    res = read_file(path, start_line, end_line)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/workspace/file")
@router.post("/api/workspace/file")
def save_file(req: SaveFileRequest):
    res = write_file(req.path, req.content, req.overwrite if req.overwrite is not None else True)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/workspace/folder")
@router.post("/api/workspace/folder")
def create_folder(req: CreateFolderRequest):
    valid, target_path, err = validate_workspace_path(req.path, workspace_root=req.workspace_path)
    if not valid:
        raise HTTPException(status_code=400, detail=err)
    try:
        target_path.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": req.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/edit")
@router.post("/api/workspace/edit")
def apply_edit(req: EditFileRequest):
    res = edit_file(req.path, req.target, req.replacement)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/workspace/preview-diff")
@router.post("/api/workspace/preview-diff")
def preview_diff(req: PreviewDiffRequest):
    return preview_changes(req.path, req.proposed_content)


@router.get("/workspace/search")
@router.get("/api/workspace/search")
def search_in_workspace(query: str = Query(...), subpath: str = "", max_matches: int = 50):
    return search_files(query, subpath, max_matches)


@router.get("/workspace/metadata")
@router.get("/api/workspace/metadata")
def get_metadata(path: str = Query(...)):
    res = file_metadata(path)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/workspace/rename")
@router.post("/api/workspace/rename")
def rename_item(req: RenameFileRequest):
    res = rename_file(req.old_path, req.new_path, req.overwrite or False)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/workspace/delete")
@router.post("/api/workspace/delete")
def delete_item(req: DeleteFileRequest):
    res = delete_file(req.path, req.confirmed)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.get("/workspace/checkpoints")
@router.get("/api/workspace/checkpoints")
def list_checkpoints(workspace_path: Optional[str] = None):
    root = workspace_path or settings.AUTHORIZED_WORKSPACE_DIR
    return checkpoint_repo.get_by_workspace(str(Path(root).resolve()))


@router.post("/workspace/checkpoints/{checkpoint_id}/rollback")
@router.post("/api/workspace/checkpoints/{checkpoint_id}/rollback")
def rollback_to_checkpoint(checkpoint_id: str, workspace_path: Optional[str] = None):
    root = workspace_path or settings.AUTHORIZED_WORKSPACE_DIR
    res = checkpoint_manager.rollback_checkpoint(checkpoint_id, str(Path(root).resolve()))
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
