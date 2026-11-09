"""
DODO Workspace Repository
Persists registered workspaces, project metadata, and checkpoint snapshots in MongoDB / local store.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.database.repositories.base_repository import BaseRepository
from backend.app.core.config import settings


class WorkspaceRepository(BaseRepository):
    def __init__(self):
        super().__init__("workspaces")

    def register_workspace(
        self,
        name: str,
        path: str,
        description: str = "",
        is_default: bool = False
    ) -> Dict[str, Any]:
        resolved_path = str(Path(path).resolve())
        now = datetime.now(timezone.utc)

        # If already exists, return existing
        existing = self.collection.find_one({"path": resolved_path})
        if existing:
            return self._convert_id(existing)

        # If is_default, clear default on other workspaces
        if is_default:
            self.collection.update_many({}, {"$set": {"is_default": False}})

        doc = {
            "name": name,
            "path": resolved_path,
            "description": description,
            "is_default": is_default,
            "scan_summary": None,
            "checkpoints_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        return self.create(doc)

    def get_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        resolved = str(Path(path).resolve())
        doc = self.collection.find_one({"path": resolved})
        return self._convert_id(doc)

    def get_default_workspace(self) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"is_default": True})
        if not doc:
            doc = self.collection.find_one()
        return self._convert_id(doc)

    def update_scan_summary(self, workspace_id: str, scan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.update(workspace_id, {
            "scan_summary": scan_data,
            "updated_at": datetime.now(timezone.utc)
        })


class CheckpointRepository(BaseRepository):
    def __init__(self):
        super().__init__("checkpoints")

    def create_checkpoint(
        self,
        workspace_id: str,
        task_id: Optional[str],
        title: str,
        files_snapshot: Dict[str, str],  # rel_path -> content
        description: str = "",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            "workspace_id": workspace_id,
            "task_id": task_id,
            "title": title,
            "description": description,
            "files_snapshot": files_snapshot,
            "file_count": len(files_snapshot),
            "created_at": now,
        }
        return self.create(doc)

    def get_by_workspace(self, workspace_id: str) -> List[Dict[str, Any]]:
        return self.find_all(query={"workspace_id": workspace_id}, sort=[("created_at", -1)])


workspace_repo = WorkspaceRepository()
checkpoint_repo = CheckpointRepository()


