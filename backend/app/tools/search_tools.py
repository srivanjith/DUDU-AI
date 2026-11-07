import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.security import validate_workspace_path
from backend.app.tools.registry import tool_registry, ToolDefinition, ToolParameter


@tool_registry.register(ToolDefinition(
    name="search_code",
    description="Searches code files within workspace for a specific text string or regex pattern.",
    permission_level="automatic",
    parameters=[
        ToolParameter(name="query", type="string", description="Search string or regex"),
        ToolParameter(name="subpath", type="string", description="Subfolder in workspace to search", required=False, default=""),
        ToolParameter(name="extension", type="string", description="File extension filter (e.g. .py, .tsx, .js)", required=False, default=None),
        ToolParameter(name="max_matches", type="integer", description="Maximum number of matches to return", required=False, default=50),
    ]
))
def search_code(query: str, subpath: str = "", extension: Optional[str] = None, max_matches: int = 50) -> Dict[str, Any]:
    valid, root_dir, err = validate_workspace_path(subpath)
    if not valid:
        return {"error": err}
    if not root_dir.exists():
        return {"matches": [], "total": 0}

    matches = []
    ignored = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist", "build"}

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    for current_dir, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored]
        for f in files:
            if extension and not f.endswith(extension):
                continue

            file_path = Path(current_dir) / f
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                    for line_num, line in enumerate(file, 1):
                        if pattern.search(line):
                            rel_path = str(file_path.relative_to(root_dir)).replace("\\", "/")
                            matches.append({
                                "file": rel_path,
                                "line_number": line_num,
                                "content": line.strip()[:200],
                            })
                            if len(matches) >= max_matches:
                                return {"matches": matches, "total": len(matches), "truncated": True}
            except Exception:
                continue

    return {"matches": matches, "total": len(matches), "truncated": False}

