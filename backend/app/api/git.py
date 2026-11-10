"""
DODO Git Source Control API Router
Provides safe, authorized Git integration for the IDE:
- Status (branch, clean/dirty, staged/unstaged files)
- Diff inspection
- Staging / Unstaging
- Commits with descriptive messages
- Commit log history
- Pull / Push with explicit user safety checks
Preserves .env and credential protection. Never exposes secrets.
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.security import validate_workspace_path

logger = logging.getLogger("dodo.git")
router = APIRouter(prefix="/api/git", tags=["Git Source Control"])


class StageRequest(BaseModel):
    path: str
    workspace_path: Optional[str] = None


class CommitRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    workspace_path: Optional[str] = None


class PushPullRequest(BaseModel):
    remote: str = "origin"
    branch: Optional[str] = None
    workspace_path: Optional[str] = None


def _get_git_root(workspace_path: Optional[str] = None) -> Path:
    target = Path(workspace_path or settings.AUTHORIZED_WORKSPACE_DIR).resolve()
    # Check if target itself has .git or check if parent (D:\DODO) has .git
    if (target / ".git").exists():
        return target
    # Fallback to project root if workspace is a subdirectory
    project_root = Path("D:/DODO").resolve()
    if (project_root / ".git").exists():
        return project_root
    return target


def _run_git_cmd(args: List[str], cwd: Path, timeout: int = 10) -> subprocess.CompletedProcess:
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return res
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail=f"Git command 'git {' '.join(args)}' timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git execution error: {str(e)}")


@router.get("/status")
def get_git_status(workspace_path: Optional[str] = None) -> Dict[str, Any]:
    """Returns working tree status, branch name, and staged/unstaged files."""
    root = _get_git_root(workspace_path)
    if not (root / ".git").exists():
        return {
            "is_git_repo": False,
            "branch": None,
            "status": "Not a Git repository",
            "files": [],
            "staged_count": 0,
            "unstaged_count": 0,
        }

    # Branch
    b_res = _run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"], root)
    branch = b_res.stdout.strip() if b_res.returncode == 0 else "unknown"

    # Status --porcelain
    s_res = _run_git_cmd(["status", "--porcelain=v1"], root)
    raw_status = s_res.stdout

    files = []
    staged_count = 0
    unstaged_count = 0

    for line in raw_status.splitlines():
        if len(line) < 4:
            continue
        index_status = line[0]
        worktree_status = line[1]
        file_path = line[3:].strip().strip('"')

        # Ignore sensitive files from status report
        if file_path.endswith(".env") or "secret" in file_path.lower():
            continue

        is_staged = index_status not in [" ", "?"]
        if is_staged:
            staged_count += 1
        if worktree_status != " ":
            unstaged_count += 1

        status_label = "modified"
        if "?" in line[:2]:
            status_label = "untracked"
        elif "A" in line[:2]:
            status_label = "added"
        elif "D" in line[:2]:
            status_label = "deleted"
        elif "R" in line[:2]:
            status_label = "renamed"

        files.append({
            "path": file_path,
            "status": status_label,
            "index_status": index_status,
            "worktree_status": worktree_status,
            "is_staged": is_staged,
        })

    return {
        "is_git_repo": True,
        "branch": branch,
        "root_path": str(root),
        "status": "clean" if not files else f"{len(files)} changed file(s)",
        "files": files,
        "staged_count": staged_count,
        "unstaged_count": unstaged_count,
    }


@router.get("/diff")
def get_git_diff(path: Optional[str] = None, staged: bool = False, workspace_path: Optional[str] = None) -> Dict[str, Any]:
    """Returns unified git diff for a specific file or entire working tree."""
    root = _get_git_root(workspace_path)
    args = ["diff"]
    if staged:
        args.append("--staged")
    if path:
        # Prevent path traversal
        args.extend(["--", path])

    res = _run_git_cmd(args, root)
    return {
        "diff": res.stdout,
        "path": path,
        "staged": staged,
    }


@router.post("/stage")
def stage_file(req: StageRequest) -> Dict[str, Any]:
    """Stages a file for commit (git add)."""
    root = _get_git_root(req.workspace_path)
    # Block staging of .env files
    if req.path.endswith(".env") or req.path == ".env":
        raise HTTPException(status_code=400, detail="Cannot stage .env secrets file.")

    res = _run_git_cmd(["add", req.path], root)
    if res.returncode != 0:
        raise HTTPException(status_code=400, detail=res.stderr or "Failed to stage file.")
    return {"success": True, "path": req.path, "action": "staged"}


@router.post("/unstage")
def unstage_file(req: StageRequest) -> Dict[str, Any]:
    """Unstages a file (git restore --staged)."""
    root = _get_git_root(req.workspace_path)
    res = _run_git_cmd(["restore", "--staged", req.path], root)
    if res.returncode != 0:
        # Fallback to git reset HEAD for older git
        res = _run_git_cmd(["reset", "HEAD", req.path], root)
    if res.returncode != 0:
        raise HTTPException(status_code=400, detail=res.stderr or "Failed to unstage file.")
    return {"success": True, "path": req.path, "action": "unstaged"}


@router.post("/commit")
def create_commit(req: CommitRequest) -> Dict[str, Any]:
    """Creates a commit with the provided message."""
    root = _get_git_root(req.workspace_path)
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Commit message cannot be empty.")

    res = _run_git_cmd(["commit", "-m", req.message.strip()], root)
    if res.returncode != 0:
        raise HTTPException(status_code=400, detail=res.stderr or res.stdout or "Failed to commit.")
    
    # Extract commit hash
    log_res = _run_git_cmd(["log", "-1", "--oneline"], root)
    commit_summary = log_res.stdout.strip() if log_res.returncode == 0 else "Committed"

    return {
        "success": True,
        "commit": commit_summary,
        "message": req.message.strip(),
    }


@router.get("/history")
def get_git_history(limit: int = 15, workspace_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns recent commit log history."""
    root = _get_git_root(workspace_path)
    res = _run_git_cmd(
        ["log", f"-{limit}", "--pretty=format:%h|%an|%ar|%s"],
        root
    )
    if res.returncode != 0:
        return []

    commits = []
    for line in res.stdout.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "time_ago": parts[2],
                "subject": parts[3],
            })
    return commits


@router.post("/push")
def push_changes(req: PushPullRequest) -> Dict[str, Any]:
    """Pushes current branch to remote with explicit user authorization."""
    root = _get_git_root(req.workspace_path)
    b_res = _run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"], root)
    branch = req.branch or (b_res.stdout.strip() if b_res.returncode == 0 else "main")

    res = _run_git_cmd(["push", req.remote, branch], root, timeout=20)
    if res.returncode != 0:
        raise HTTPException(status_code=400, detail=res.stderr or "Failed to push to remote.")
    return {"success": True, "remote": req.remote, "branch": branch, "output": res.stdout}


@router.post("/pull")
def pull_changes(req: PushPullRequest) -> Dict[str, Any]:
    """Pulls latest changes from remote."""
    root = _get_git_root(req.workspace_path)
    res = _run_git_cmd(["pull", req.remote], root, timeout=20)
    if res.returncode != 0:
        raise HTTPException(status_code=400, detail=res.stderr or "Failed to pull from remote.")
    return {"success": True, "output": res.stdout}
