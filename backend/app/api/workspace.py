from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.tools.filesystem_tools import list_workspace_files, read_file, write_file, edit_file

router = APIRouter(prefix="/workspace", tags=["Workspace"])


class SaveFileRequest(BaseModel):
    path: str
    content: str
    overwrite: Optional[bool] = True


class EditFileRequest(BaseModel):
    path: str
    target: str
    replacement: str


@router.get("/status")
def get_workspace_status():
    return {
        "authorized_workspace": settings.AUTHORIZED_WORKSPACE_DIR,
    }


@router.get("/files")
def get_files(subpath: str = "", depth: int = 3):
    return list_workspace_files(subpath, depth)


@router.get("/file")
def get_file_content(path: str, start_line: int = 1, end_line: Optional[int] = None):
    res = read_file(path, start_line, end_line)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/file")
def save_file(req: SaveFileRequest):
    res = write_file(req.path, req.content, req.overwrite if req.overwrite is not None else True)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/edit")
def apply_edit(req: EditFileRequest):
    res = edit_file(req.path, req.target, req.replacement)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

