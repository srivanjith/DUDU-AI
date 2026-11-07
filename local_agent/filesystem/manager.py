from pathlib import Path
from typing import Any, Dict, List, Optional
import difflib
import hashlib
from local_agent.security import jail_path


class LocalFilesystemManager:
    """Safely manages filesystem operations inside authorized workspace directory."""

    def read(self, path: str, start_line: int = 1, end_line: Optional[int] = None) -> Dict[str, Any]:
        valid, target, err = jail_path(path)
        if not valid:
            return {"error": err, "success": False}
        if not target.exists():
            return {"error": f"File '{path}' does not exist.", "success": False}

        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            start_idx = max(0, start_line - 1)
            end_idx = len(lines) if end_line is None else min(len(lines), end_line)
            content = "".join(lines[start_idx:end_idx])
            return {"success": True, "path": str(target), "content": content, "total_lines": len(lines)}
        except Exception as e:
            return {"error": str(e), "success": False}

    def write(self, path: str, content: str) -> Dict[str, Any]:
        valid, target, err = jail_path(path)
        if not valid:
            return {"error": err, "success": False}

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(target), "bytes": len(content.encode("utf-8"))}
        except Exception as e:
            return {"error": str(e), "success": False}

    def list_files(self, subpath: str = "") -> Dict[str, Any]:
        valid, target, err = jail_path(subpath)
        if not valid:
            return {"error": err, "success": False}

        results = []
        for p in target.rglob("*"):
            if any(part in {".git", "node_modules", ".venv", "__pycache__"} for part in p.parts):
                continue
            results.append({
                "path": str(p.relative_to(target)).replace("\\", "/"),
                "is_dir": p.is_dir(),
                "size": p.stat().st_size if p.is_file() else None,
            })
        return {"success": True, "files": results}


fs_manager = LocalFilesystemManager()

