from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pymongo import DESCENDING
from backend.app.database.repositories.base_repository import BaseRepository
from backend.app.core.config import settings


class ProjectRepository(BaseRepository):
    def __init__(self):
        super().__init__("projects")

    def create_project(self, name: str, workspace_path: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        path = str(Path(workspace_path or settings.AUTHORIZED_WORKSPACE_DIR).resolve())
        now = datetime.utcnow()
        doc = {
            "name": name,
            "workspace_path": path,
            "description": description,
            "created_at": now,
            "updated_at": now,
            "file_count": 0,
        }
        # Check if project at workspace already exists
        existing = self.collection.find_one({"workspace_path": path})
        if existing:
            return self._convert_id(existing)
        return self.create(doc)

    def get_by_workspace(self, workspace_path: str) -> Optional[Dict[str, Any]]:
        path = str(Path(workspace_path).resolve())
        doc = self.collection.find_one({"workspace_path": path})
        return self._convert_id(doc)


class TaskRepository(BaseRepository):
    def __init__(self):
        super().__init__("tasks")

    def create_task(self, prompt: str, project_id: Optional[str] = None, workspace_path: Optional[str] = None, mode: str = "developer") -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "prompt": prompt,
            "project_id": project_id,
            "workspace_path": workspace_path or settings.AUTHORIZED_WORKSPACE_DIR,
            "mode": mode,
            "status": "queued",  # queued, planning, executing, evaluating, fixing, verified, completed, failed, cancelled
            "plan": None,
            "current_step_index": 0,
            "result_summary": None,
            "verified": False,
            "created_at": now,
            "updated_at": now,
        }
        return self.create(doc)

    def update_task_plan(self, task_id: str, plan_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.update(task_id, {
            "plan": plan_dict,
            "status": "executing",
            "updated_at": datetime.utcnow()
        })

    def update_step_status(self, task_id: str, step_id: int, status: str, result: Optional[str] = None, error: Optional[str] = None) -> Optional[Dict[str, Any]]:
        task = self.find_by_id(task_id)
        if not task or not task.get("plan"):
            return None

        plan = task["plan"]
        steps = plan.get("steps", [])
        for step in steps:
            if step.get("step_id") == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result
                if error is not None:
                    step["error"] = error
                break

        return self.update(task_id, {
            "plan": plan,
            "current_step_index": step_id,
            "updated_at": datetime.utcnow(),
        })

    def complete_task(self, task_id: str, status: str = "completed", summary: str = "", verified: bool = True) -> Optional[Dict[str, Any]]:
        return self.update(task_id, {
            "status": status,
            "result_summary": summary,
            "verified": verified,
            "updated_at": datetime.utcnow(),
        })

