"""
DODO Checkpoint and Diff Manager
Provides atomic snapshot creation, rollback safety, unified diff generation,
and Git change inspection to guarantee non-destructive file operations.
"""
from datetime import datetime, timezone
import difflib
import json
import logging
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from backend.app.database.repositories.workspace_repository import CheckpointRepository

logger = logging.getLogger("dodo.intelligence.checkpoint_manager")


class CheckpointManager:
    """
    Manages safe state checkpoints, rollback capabilities, and diff generation.
    Always creates a checkpoint before modifying user project files.
    """

    def __init__(self):
        self.repo = CheckpointRepository()

    def generate_diff(self, old_content: str, new_content: str, file_path: str = "file") -> str:
        """Generates unified diff between original and proposed content."""
        old_lines = old_content.splitlines(keepends=True) if old_content else []
        new_lines = new_content.splitlines(keepends=True) if new_content else []

        diff_lines = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=3,
        ))
        return "".join(diff_lines)

    def create_checkpoint(
        self,
        workspace_root: str,
        files_to_snapshot: List[str],
        title: str = "Pre-modification snapshot",
        task_id: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Creates a snapshot of specified files before modifications occur.
        Stores content in MongoDB and backup checkpoint directory on disk.
        """
        root = Path(workspace_root).resolve()
        snapshot: Dict[str, str] = {}

        checkpoint_id = f"cp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        disk_backup_dir = root / ".dodo_checkpoints" / checkpoint_id

        for rel_path in files_to_snapshot:
            file_path = root / rel_path
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    snapshot[rel_path] = content

                    # Also write to local checkpoint directory
                    backup_file = disk_backup_dir / rel_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    backup_file.write_text(content, encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Could not snapshot {rel_path}: {e}")

        doc = self.repo.create_checkpoint(
            workspace_id=str(root),
            task_id=task_id,
            title=title,
            files_snapshot=snapshot,
            description=description,
        )
        doc["checkpoint_id"] = checkpoint_id
        doc["disk_backup_dir"] = str(disk_backup_dir)
        return doc

    def rollback_checkpoint(self, checkpoint_id: str, workspace_root: str) -> Dict[str, Any]:
        """
        Restores files from a previously created checkpoint.
        """
        cp = self.repo.find_by_id(checkpoint_id)
        root = Path(workspace_root).resolve()

        if not cp or not cp.get("files_snapshot"):
            # Try disk backup directory
            disk_dir = root / ".dodo_checkpoints" / checkpoint_id
            if disk_dir.exists():
                restored = []
                for p in disk_dir.rglob("*"):
                    if p.is_file():
                        rel = str(p.relative_to(disk_dir))
                        target = root / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(p.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
                        restored.append(rel)
                return {"success": True, "restored_files": restored, "checkpoint_id": checkpoint_id}

            return {"success": False, "error": f"Checkpoint '{checkpoint_id}' not found or empty."}

        snapshot = cp["files_snapshot"]
        restored_files = []
        for rel_path, content in snapshot.items():
            target_path = root / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            restored_files.append(rel_path)

        return {
            "success": True,
            "restored_files": restored_files,
            "checkpoint_id": checkpoint_id,
            "message": f"Successfully restored {len(restored_files)} file(s) from checkpoint."
        }

    def get_git_diff(self, workspace_root: str) -> Optional[str]:
        """Inspects real git diff if workspace is a git repository."""
        root = Path(workspace_root).resolve()
        if not (root / ".git").exists():
            return None
        try:
            res = subprocess.run(["git", "diff"], cwd=str(root), capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                return res.stdout
        except Exception:
            pass
        return None


checkpoint_manager = CheckpointManager()

