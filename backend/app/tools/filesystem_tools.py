"""
DODO Secure Filesystem Intelligence Tools
Provides path-jailed, permission-aware filesystem operations:
- read_file (READ permission)
- list_workspace_files (READ permission)
- search_files (READ permission)
- file_metadata (READ permission)
- preview_changes (READ permission)
- write_file / create_file (WRITE permission - requires approval)
- edit_file / modify_file (WRITE permission - requires approval)
- rename_file (WRITE permission - requires approval)
- delete_file (DELETE permission - requires approval & confirmation)
Enforces file size limits (5 MB max), binary protection, and secret exclusions.
"""
from datetime import datetime, timezone
import difflib
import hashlib
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.security import validate_workspace_path
from backend.app.tools.registry import PermissionLevel, RiskLevel, ToolDefinition, ToolParameter, tool_registry

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def get_file_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def is_binary_string(bytes_data: bytes) -> bool:
    """Detects whether byte content is binary."""
    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes_data.translate(None, text_chars))


def is_secret_filename(filename: str) -> bool:
    patterns = [r"^\.env(\..+)?$", r".*id_rsa.*", r".*\.pem$", r".*\.key$", r".*credentials.*"]
    return any(re.match(p, filename, re.IGNORECASE) for p in patterns)


# ==============================================================================
# 1. READ FILE
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="read_file",
    description="Reads content from an authorized workspace file.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="path", type="string", description="Relative path within authorized workspace"),
        ToolParameter(name="start_line", type="integer", description="Line to start reading from (1-indexed)", required=False, default=1),
        ToolParameter(name="end_line", type="integer", description="Line to end reading at", required=False, default=None),
        ToolParameter(name="allow_secret", type="boolean", description="Whether to allow reading sensitive files", required=False, default=False),
    ]
))
def read_file(path: str, start_line: int = 1, end_line: Optional[int] = None, allow_secret: bool = False, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path, workspace_root=workspace_root)
    if not valid:
        return {"error": err}
    if not target_path.exists():
        return {"error": f"File '{path}' does not exist."}
    if target_path.is_dir():
        return {"error": f"Path '{path}' is a directory, not a file."}

    # Secret file check
    if not allow_secret and is_secret_filename(target_path.name):
        return {"error": f"Security restriction: Access to sensitive file '{target_path.name}' is blocked by default."}

    # File size check
    stat = target_path.stat()
    if stat.st_size > MAX_FILE_SIZE_BYTES:
        return {"error": f"File size ({round(stat.st_size / (1024*1024), 2)} MB) exceeds maximum allowed limit (5 MB)."}

    # Binary check
    with open(target_path, "rb") as f:
        chunk = f.read(1024)
        if is_binary_string(chunk):
            return {"error": f"Cannot read binary file '{path}'. Only text source files are supported."}

    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        end_idx = total_lines if end_line is None else min(total_lines, end_line)
        selected = lines[start_idx:end_idx]

        return {
            "path": str(target_path),
            "content": "".join(selected),
            "total_lines": total_lines,
            "start_line": start_line,
            "end_line": end_idx,
            "file_hash": get_file_hash("".join(lines)),
            "size_bytes": stat.st_size,
        }
    except Exception as e:
        return {"error": f"Failed to read file '{path}': {str(e)}"}


# ==============================================================================
# 2. WRITE FILE (CREATE OR REPLACE)
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="write_file",
    description="Creates a new file or replaces entire content in authorized workspace.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
    requires_approval=True,
    parameters=[
        ToolParameter(name="path", type="string", description="Relative path in workspace"),
        ToolParameter(name="content", type="string", description="Full content to write"),
        ToolParameter(name="overwrite", type="boolean", description="Whether to overwrite if already exists", required=False, default=True),
    ]
))
def write_file(path: str, content: str, overwrite: bool = True, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path, workspace_root=workspace_root)
    if not valid:
        return {"error": err}

    if target_path.exists() and not overwrite:
        return {"error": f"File '{path}' already exists and overwrite is set to False."}

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        old_content = target_path.read_text(encoding="utf-8", errors="replace") if target_path.exists() else ""

        # Atomic write: write to temp file then rename
        temp_file = target_path.with_name(f".{target_path.name}.tmp")
        temp_file.write_text(content, encoding="utf-8")
        if target_path.exists():
            target_path.unlink()
        temp_file.rename(target_path)

        # Generate diff if existed
        diff_str = ""
        if old_content:
            diff_lines = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                n=3,
            ))
            diff_str = "".join(diff_lines)

        return {
            "success": True,
            "path": str(target_path),
            "bytes_written": len(content.encode("utf-8")),
            "file_hash": get_file_hash(content),
            "diff": diff_str,
        }
    except Exception as e:
        return {"error": f"Failed to write file '{path}': {str(e)}"}


# ==============================================================================
# 3. EDIT FILE (TARGETED MODIFICATION)
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="edit_file",
    description="Applies a targeted search-and-replace edit to an existing workspace file.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
    requires_approval=True,
    parameters=[
        ToolParameter(name="path", type="string", description="Path of the file to edit"),
        ToolParameter(name="target", type="string", description="Exact string block to find"),
        ToolParameter(name="replacement", type="string", description="Exact string to replace target with"),
    ]
))
def edit_file(path: str, target: str, replacement: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path, workspace_root=workspace_root)
    if not valid:
        return {"error": err}
    if not target_path.exists():
        return {"error": f"File '{path}' does not exist to edit."}

    try:
        old_content = target_path.read_text(encoding="utf-8", errors="replace")
        if target not in old_content:
            return {
                "error": f"Target string not found in '{path}'. Please ensure exact match including whitespace."
            }

        new_content = old_content.replace(target, replacement, 1)

        # Atomic write
        temp_file = target_path.with_name(f".{target_path.name}.tmp")
        temp_file.write_text(new_content, encoding="utf-8")
        if target_path.exists():
            target_path.unlink()
        temp_file.rename(target_path)

        diff_lines = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        ))

        return {
            "success": True,
            "path": str(target_path),
            "diff": "".join(diff_lines),
            "new_hash": get_file_hash(new_content),
        }
    except Exception as e:
        return {"error": f"Failed to edit file '{path}': {str(e)}"}


# ==============================================================================
# 4. LIST WORKSPACE FILES
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="list_workspace_files",
    description="Lists files and directories inside the authorized workspace.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="subpath", type="string", description="Subfolder path inside workspace", required=False, default=""),
        ToolParameter(name="depth", type="integer", description="Max directory depth to scan", required=False, default=3),
    ]
))
def list_workspace_files(subpath: str = "", depth: int = 3, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, root_path, err = validate_workspace_path(subpath, workspace_root=workspace_root)
    if not valid:
        return {"error": err}
    if not root_path.exists():
        root_path.mkdir(parents=True, exist_ok=True)

    items = []
    ignored = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist", "build", ".dodo_checkpoints"}

    def scan(current: Path, current_depth: int):
        if current_depth > depth:
            return
        try:
            for entry in current.iterdir():
                if entry.name in ignored:
                    continue
                if is_secret_filename(entry.name):
                    continue

                rel_path = str(entry.relative_to(root_path)).replace("\\", "/")
                is_dir = entry.is_dir()
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "is_dir": is_dir,
                    "size": entry.stat().st_size if not is_dir else None,
                })
                if is_dir:
                    scan(entry, current_depth + 1)
        except PermissionError:
            pass

    scan(root_path, 1)
    return {
        "workspace_root": str(root_path),
        "total_items": len(items),
        "items": items,
    }


# ==============================================================================
# 5. SEARCH FILES (GREP CONTENT)
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="search_files",
    description="Searches for exact text or regex across text files in the authorized workspace.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="query", type="string", description="Text or pattern to search for"),
        ToolParameter(name="subpath", type="string", description="Subfolder to limit search to", required=False, default=""),
        ToolParameter(name="max_matches", type="integer", description="Max match results to return", required=False, default=50),
    ]
))
def search_files(query: str, subpath: str = "", max_matches: int = 50, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, root_path, err = validate_workspace_path(subpath, workspace_root=workspace_root)
    if not valid:
        return {"error": err}

    matches = []
    ignored = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist", "build", ".dodo_checkpoints"}

    for current_dir, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        for f in filenames:
            if is_secret_filename(f):
                continue
            file_p = Path(current_dir) / f
            if file_p.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".html", ".css", ".md", ".txt", ".sql", ".yaml", ".yml"}:
                continue

            try:
                content = file_p.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                for line_num, line_str in enumerate(lines, 1):
                    if query.lower() in line_str.lower():
                        rel = str(file_p.relative_to(root_path)).replace("\\", "/")
                        matches.append({
                            "path": rel,
                            "line": line_num,
                            "match": line_str.strip()[:150],
                        })
                        if len(matches) >= max_matches:
                            return {"query": query, "total_matches": len(matches), "matches": matches}
            except Exception:
                pass

    return {"query": query, "total_matches": len(matches), "matches": matches}


# ==============================================================================
# 6. FILE METADATA
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="file_metadata",
    description="Inspects detailed filesystem metadata for an authorized file.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="path", type="string", description="Relative path within authorized workspace"),
    ]
))
def file_metadata(path: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path, workspace_root=workspace_root)
    if not valid:
        return {"error": err}
    if not target_path.exists():
        return {"error": f"Path '{path}' does not exist."}

    stat = target_path.stat()
    is_dir = target_path.is_dir()

    meta = {
        "path": path,
        "absolute_path": str(target_path),
        "is_dir": is_dir,
        "size_bytes": stat.st_size if not is_dir else None,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "created_at": datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
    }

    if not is_dir and stat.st_size <= MAX_FILE_SIZE_BYTES:
        try:
            content = target_path.read_text(encoding="utf-8", errors="replace")
            meta["line_count"] = len(content.splitlines())
            meta["file_hash"] = get_file_hash(content)
        except Exception:
            pass

    return meta


# ==============================================================================
# 7. PREVIEW CHANGES (DIFF PREVIEW)
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="preview_changes",
    description="Generates a preview diff for proposed changes without writing to disk.",
    permission_level=PermissionLevel.READ,
    risk_level=RiskLevel.LOW,
    parameters=[
        ToolParameter(name="path", type="string", description="Relative path within workspace"),
        ToolParameter(name="proposed_content", type="string", description="Proposed new content"),
    ]
))
def preview_changes(path: str, proposed_content: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path, workspace_root=workspace_root)
    if not valid:
        return {"error": err}

    old_content = target_path.read_text(encoding="utf-8", errors="replace") if target_path.exists() else ""
    diff_lines = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        proposed_content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        n=3,
    ))

    return {
        "path": path,
        "exists_previously": target_path.exists(),
        "diff": "".join(diff_lines),
        "old_hash": get_file_hash(old_content) if old_content else None,
        "proposed_hash": get_file_hash(proposed_content),
        "line_delta": len(proposed_content.splitlines()) - len(old_content.splitlines()),
    }


# ==============================================================================
# 8. RENAME FILE
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="rename_file",
    description="Renames or moves a file within the authorized workspace.",
    permission_level=PermissionLevel.WRITE,
    risk_level=RiskLevel.MEDIUM,
    requires_approval=True,
    parameters=[
        ToolParameter(name="old_path", type="string", description="Current relative path"),
        ToolParameter(name="new_path", type="string", description="Target relative path"),
        ToolParameter(name="overwrite", type="boolean", description="Whether to overwrite existing target", required=False, default=False),
    ]
))
def rename_file(old_path: str, new_path: str, overwrite: bool = False, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    v1, p1, e1 = validate_workspace_path(old_path, workspace_root=workspace_root)
    if not v1:
        return {"error": e1}
    v2, p2, e2 = validate_workspace_path(new_path, workspace_root=workspace_root)
    if not v2:
        return {"error": e2}

    if not p1.exists():
        return {"error": f"Source file '{old_path}' does not exist."}
    if p2.exists() and not overwrite:
        return {"error": f"Target path '{new_path}' already exists."}

    try:
        p2.parent.mkdir(parents=True, exist_ok=True)
        if p2.exists() and overwrite:
            p2.unlink()
        p1.rename(p2)
        return {"success": True, "old_path": old_path, "new_path": new_path}
    except Exception as e:
        return {"error": f"Failed to rename '{old_path}' to '{new_path}': {str(e)}"}


# ==============================================================================
# 9. DELETE FILE
# ==============================================================================
@tool_registry.register(ToolDefinition(
    name="delete_file",
    description="Deletes a file within the authorized workspace with mandatory confirmation.",
    permission_level=PermissionLevel.DELETE,
    risk_level=RiskLevel.CRITICAL,
    requires_approval=True,
    parameters=[
        ToolParameter(name="path", type="string", description="Relative path within workspace to delete"),
        ToolParameter(name="confirmed", type="boolean", description="Mandatory confirmation flag", required=True),
    ]
))
def delete_file(path: str, confirmed: bool = False, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    if not confirmed:
        return {"error": "Delete operation aborted: 'confirmed=True' must be provided."}

    valid, target_path, err = validate_workspace_path(path, workspace_root=workspace_root)
    if not valid:
        return {"error": err}
    if not target_path.exists():
        return {"error": f"File '{path}' does not exist to delete."}
    if target_path.is_dir():
        return {"error": f"Path '{path}' is a directory. Directory deletion is forbidden for safety."}

    try:
        # Create safety backup in .dodo_checkpoints before deleting
        root = target_path.parent
        backup_dir = root / ".dodo_checkpoints" / "deleted_files"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"{target_path.name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        backup_file.write_text(target_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

        target_path.unlink()
        return {
            "success": True,
            "deleted_path": path,
            "backup_restorable_at": str(backup_file),
            "message": f"File '{path}' deleted successfully (safety backup created)."
        }
    except Exception as e:
        return {"error": f"Failed to delete '{path}': {str(e)}"}
