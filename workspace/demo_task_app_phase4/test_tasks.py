"""
Automated test suite for DODO Task Manager.
"""
import os
import pytest
from task_manager import TaskManager


def test_task_crud(tmp_path):
    storage = str(tmp_path / "test_tasks.json")
    mgr = TaskManager(storage_path=storage)

    # 1. Add Task
    t1 = mgr.add_task("Buy groceries", "Milk, eggs, coffee")
    assert t1.id == 1
    assert t1.title == "Buy groceries"
    assert t1.completed is False

    # 2. View Tasks
    tasks = mgr.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Buy groceries"

    # 3. Update Task
    updated = mgr.update_task(1, completed=True)
    assert updated is not None
    assert updated.completed is True

    # 4. Delete Task
    assert mgr.delete_task(1) is True
    assert len(mgr.list_tasks()) == 0
