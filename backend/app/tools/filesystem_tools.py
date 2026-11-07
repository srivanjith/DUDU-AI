import difflib
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.security import validate_workspace_path
from backend.app.tools.registry import tool_registry, ToolDefinition, ToolParameter


def get_file_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


@tool_registry.register(ToolDefinition(
    name="read_file",
    description="Reads content from an authorized workspace file.",
    permission_level="automatic",
    parameters=[
        ToolParameter(name="path", type="string", description="Relative or absolute path within workspace"),
        ToolParameter(name="start_line", type="integer", description="Line to start reading from (1-indexed)", required=False, default=1),
        ToolParameter(name="end_line", type="integer", description="Line to end reading at", required=False, default=None),
    ]
))
def read_file(path: str, start_line: int = 1, end_line: Optional[int] = None) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path)
    if not valid:
        return {"error": err}
    if not target_path.exists():
        return {"error": f"File '{path}' does not exist."}
    if target_path.is_dir():
        return {"error": f"Path '{path}' is a directory, not a file."}

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
        }
    except Exception as e:
        return {"error": f"Failed to read file '{path}': {str(e)}"}


@tool_registry.register(ToolDefinition(
    name="write_file",
    description="Creates a new file or replaces entire content in authorized workspace.",
    permission_level="controlled",
    parameters=[
        ToolParameter(name="path", type="string", description="Relative or absolute path in workspace"),
        ToolParameter(name="content", type="string", description="Full content to write"),
        ToolParameter(name="overwrite", type="boolean", description="Whether to overwrite if already exists", required=False, default=True),
    ]
))
def write_file(path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path)
    if not valid:
        return {"error": err}

    if target_path.exists() and not overwrite:
        return {"error": f"File '{path}' already exists and overwrite is set to False."}

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        old_content = target_path.read_text(encoding="utf-8", errors="replace") if target_path.exists() else ""
        target_path.write_text(content, encoding="utf-8")

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


@tool_registry.register(ToolDefinition(
    name="edit_file",
    description="Applies a targeted search-and-replace edit to an existing workspace file.",
    permission_level="controlled",
    parameters=[
        ToolParameter(name="path", type="string", description="Path of the file to edit"),
        ToolParameter(name="target", type="string", description="Exact string block to find"),
        ToolParameter(name="replacement", type="string", description="Exact string to replace target with"),
    ]
))
def edit_file(path: str, target: str, replacement: str) -> Dict[str, Any]:
    valid, target_path, err = validate_workspace_path(path)
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
        target_path.write_text(new_content, encoding="utf-8")

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


@tool_registry.register(ToolDefinition(
    name="list_workspace_files",
    description="Lists files and directories inside the authorized workspace.",
    permission_level="automatic",
    parameters=[
        ToolParameter(name="subpath", type="string", description="Subfolder path inside workspace", required=False, default=""),
        ToolParameter(name="depth", type="integer", description="Max directory depth to scan", required=False, default=3),
    ]
))
def list_workspace_files(subpath: str = "", depth: int = 3) -> Dict[str, Any]:
    valid, root_path, err = validate_workspace_path(subpath)
    if not valid:
        return {"error": err}
    if not root_path.exists():
        root_path.mkdir(parents=True, exist_ok=True)

    items = []
    ignored = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist", "build"}

    def scan(current: Path, current_depth: int):
        if current_depth > depth:
            return
        try:
            for entry in current.iterdir():
                if entry.name in ignored:
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
        except Exception:
            pass

    scan(root_path, 1)
    return {"workspace": str(root_path), "total_items": len(items), "items": items}

