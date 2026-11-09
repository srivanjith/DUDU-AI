"""
DODO Task App CLI Entry Point
"""
import sys
from task_manager import TaskManager


def main():
    manager = TaskManager()
    print("=== DODO Task Manager CLI ===")
    print("1. Add Task")
    print("2. List Tasks")
    print("3. Update Task")
    print("4. Delete Task")
    print("5. Exit")

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "add" and len(sys.argv) > 2:
            t = manager.add_task(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
            print(f"Added Task #{t.id}: {t.title}")
        elif cmd == "list":
            tasks = manager.list_tasks()
            for t in tasks:
                status = "[x]" if t.completed else "[ ]"
                print(f"{status} #{t.id}: {t.title} - {t.description}")
        elif cmd == "delete" and len(sys.argv) > 2:
            ok = manager.delete_task(int(sys.argv[2]))
            print("Deleted" if ok else "Not found")
        return

    print(f"Currently managing {len(manager.tasks)} tasks.")


if __name__ == "__main__":
    main()
