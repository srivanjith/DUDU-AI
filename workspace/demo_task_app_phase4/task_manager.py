"""
DODO Task Management Engine
Provides Add, View, Update, and Delete operations for tasks.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class TaskManager:
    def __init__(self, storage_path: str = "tasks.json"):
        self.storage_file = Path(storage_path)
        self.tasks: Dict[int, Task] = {}
        self._next_id: int = 1
        self.load()

    def add_task(self, title: str, description: str = "") -> Task:
        if not title.strip():
            raise ValueError("Task title cannot be empty.")
        task = Task(id=self._next_id, title=title.strip(), description=description.strip())
        self.tasks[self._next_id] = task
        self._next_id += 1
        self.save()
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.tasks.get(task_id)

    def list_tasks(self, include_completed: bool = True) -> List[Task]:
        if include_completed:
            return list(self.tasks.values())
        return [t for t in self.tasks.values() if not t.completed]

    def update_task(self, task_id: int, title: Optional[str] = None, description: Optional[str] = None, completed: Optional[bool] = None) -> Optional[Task]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip()
        if completed is not None:
            task.completed = completed
        self.save()
        return task

    def delete_task(self, task_id: int) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save()
            return True
        return False

    def save(self):
        data = {
            "next_id": self._next_id,
            "tasks": [asdict(t) for t in self.tasks.values()]
        }
        self.storage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self):
        if not self.storage_file.exists():
            return
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
            self._next_id = data.get("next_id", 1)
            for t_dict in data.get("tasks", []):
                task = Task(**t_dict)
                self.tasks[task.id] = task
        except Exception:
            pass
