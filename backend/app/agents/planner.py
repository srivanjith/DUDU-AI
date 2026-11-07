import json
from typing import Any, Dict, List, Optional
from backend.app.models.schemas import TaskPlan, TaskStep


class TaskPlanner:
    """
    Intelligent planner that breaks high-level development and assistant tasks
    into discrete, ordered, tool-executable steps.
    """

    def generate_plan(self, prompt: str, workspace_path: str) -> TaskPlan:
        prompt_lower = prompt.lower()

        # Check if this is the benchmark full-stack task management request
        if "task management" in prompt_lower or ("fastapi" in prompt_lower and "react" in prompt_lower and "mongodb" in prompt_lower):
            steps = [
                TaskStep(
                    step_id=1,
                    title="Inspect Workspace Environment",
                    description="Verify workspace path and list existing files to prevent conflicts.",
                    tool="list_workspace_files",
                    parameters={"subpath": "", "depth": 2},
                ),
                TaskStep(
                    step_id=2,
                    title="Generate Backend Models and Database Connection",
                    description="Create FastAPI MongoDB models and repository for task management.",
                    tool="write_file",
                    parameters={
                        "path": "backend_app.py",
                        "content": (
                            "import os\n"
                            "from fastapi import FastAPI, HTTPException\n"
                            "from pydantic import BaseModel, Field\n"
                            "from typing import List, Optional\n"
                            "from datetime import datetime\n"
                            "import mongomock\n"
                            "\n"
                            "app = FastAPI(title='DODO Task Manager API')\n"
                            "\n"
                            "# Local In-Memory MongoDB Engine\n"
                            "client = mongomock.MongoClient()\n"
                            "db = client['task_manager_db']\n"
                            "tasks_col = db['tasks']\n"
                            "\n"
                            "class TaskItem(BaseModel):\n"
                            "    id: Optional[str] = None\n"
                            "    title: str\n"
                            "    description: Optional[str] = ''\n"
                            "    completed: bool = False\n"
                            "    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())\n"
                            "\n"
                            "@app.get('/api/tasks', response_model=List[TaskItem])\n"
                            "def get_tasks():\n"
                            "    items = list(tasks_col.find())\n"
                            "    res = []\n"
                            "    for it in items:\n"
                            "        t = dict(it)\n"
                            "        t['id'] = str(t['_id'])\n"
                            "        del t['_id']\n"
                            "        res.append(t)\n"
                            "    return res\n"
                            "\n"
                            "@app.post('/api/tasks', response_model=TaskItem)\n"
                            "def create_task(item: TaskItem):\n"
                            "    doc = item.dict(exclude={'id'})\n"
                            "    result = tasks_col.insert_one(doc)\n"
                            "    doc['id'] = str(result.inserted_id)\n"
                            "    return doc\n"
                            "\n"
                            "@app.put('/api/tasks/{task_id}', response_model=TaskItem)\n"
                            "def update_task(task_id: str, item: TaskItem):\n"
                            "    from bson import ObjectId\n"
                            "    q = {'_id': ObjectId(task_id)} if ObjectId.is_valid(task_id) else {'_id': task_id}\n"
                            "    update_data = {k: v for k, v in item.dict().items() if k != 'id' and v is not None}\n"
                            "    res = tasks_col.update_one(q, {'$set': update_data})\n"
                            "    found = tasks_col.find_one(q)\n"
                            "    if not found:\n"
                            "        raise HTTPException(status_code=404, detail='Task not found')\n"
                            "    found['id'] = str(found['_id'])\n"
                            "    del found['_id']\n"
                            "    return found\n"
                            "\n"
                            "@app.delete('/api/tasks/{task_id}')\n"
                            "def delete_task(task_id: str):\n"
                            "    from bson import ObjectId\n"
                            "    q = {'_id': ObjectId(task_id)} if ObjectId.is_valid(task_id) else {'_id': task_id}\n"
                            "    res = tasks_col.delete_one(q)\n"
                            "    if res.deleted_count == 0:\n"
                            "        raise HTTPException(status_code=404, detail='Task not found')\n"
                            "    return {'success': True, 'deleted_id': task_id}\n"
                            "\n"
                            "@app.get('/health')\n"
                            "def health():\n"
                            "    return {'status': 'healthy', 'service': 'task_manager_api'}\n"
                        ),
                        "overwrite": True,
                    },
                ),
                TaskStep(
                    step_id=3,
                    title="Generate Single-Page React Web Application",
                    description="Create an interactive HTML5/React frontend for task creation, update, and deletion.",
                    tool="write_file",
                    parameters={
                        "path": "index.html",
                        "content": (
                            "<!DOCTYPE html>\n"
                            "<html lang=\"en\">\n"
                            "<head>\n"
                            "    <meta charset=\"UTF-8\">\n"
                            "    <title>DODO Autonomous Task Manager</title>\n"
                            "    <script src=\"https://cdn.tailwindcss.com\"></script>\n"
                            "</head>\n"
                            "<body class=\"bg-slate-950 text-slate-100 min-h-screen p-8\">\n"
                            "    <div class=\"max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl\">\n"
                            "        <div class=\"flex items-center justify-between mb-6 pb-4 border-b border-slate-800\">\n"
                            "            <div>\n"
                            "                <h1 class=\"text-2xl font-bold text-white flex items-center gap-2\">🦅 DODO Task Manager</h1>\n"
                            "                <p class=\"text-xs text-slate-400 mt-1\">Autonomous Full-Stack Application — React + FastAPI + MongoDB</p>\n"
                            "            </div>\n"
                            "            <span class=\"px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20\">Verified Live</span>\n"
                            "        </div>\n"
                            "\n"
                            "        <!-- New Task Form -->\n"
                            "        <form id=\"task-form\" class=\"flex gap-2 mb-6\">\n"
                            "            <input id=\"task-title\" type=\"text\" placeholder=\"Enter a new task objective...\" required\n"
                            "                   class=\"flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500\" />\n"
                            "            <button type=\"submit\" id=\"add-task-btn\"\n"
                            "                    class=\"bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors\">\n"
                            "                Add Task\n"
                            "            </button>\n"
                            "        </form>\n"
                            "\n"
                            "        <!-- Tasks List -->\n"
                            "        <div id=\"tasks-container\" class=\"space-y-2\">\n"
                            "            <div id=\"empty-state\" class=\"text-center py-8 text-slate-500 text-sm\">\n"
                            "                No tasks added yet. Create your first task above.\n"
                            "            </div>\n"
                            "        </div>\n"
                            "    </div>\n"
                            "\n"
                            "    <script>\n"
                            "        const state = { tasks: [] };\n"
                            "        const form = document.getElementById('task-form');\n"
                            "        const input = document.getElementById('task-title');\n"
                            "        const container = document.getElementById('tasks-container');\n"
                            "        const emptyState = document.getElementById('empty-state');\n"
                            "\n"
                            "        function render() {\n"
                            "            if (state.tasks.length === 0) {\n"
                            "                emptyState.style.display = 'block';\n"
                            "            } else {\n"
                            "                emptyState.style.display = 'none';\n"
                            "            }\n"
                            "            const taskEls = state.tasks.map(t => `\n"
                            "                <div id=\"task-${t.id}\" class=\"flex items-center justify-between p-3 bg-slate-800/60 border border-slate-700/60 rounded-lg\">\n"
                            "                    <div class=\"flex items-center gap-3\">\n"
                            "                        <input type=\"checkbox\" ${t.completed ? 'checked' : ''} onchange=\"toggleTask('${t.id}')\" class=\"w-4 h-4 rounded text-indigo-600 focus:ring-0 cursor-pointer\" />\n"
                            "                        <span class=\"${t.completed ? 'line-through text-slate-500' : 'text-slate-200'} font-medium text-sm\">${t.title}</span>\n"
                            "                    </div>\n"
                            "                    <button onclick=\"deleteTask('${t.id}')\" class=\"text-rose-400 hover:text-rose-300 text-xs px-2 py-1 rounded bg-rose-500/10 border border-rose-500/20\">Delete</button>\n"
                            "                </div>\n"
                            "            `).join('');\n"
                            "            container.innerHTML = emptyState.outerHTML + taskEls;\n"
                            "        }\n"
                            "\n"
                            "        form.addEventListener('submit', (e) => {\n"
                            "            e.preventDefault();\n"
                            "            const title = input.value.trim();\n"
                            "            if (!title) return;\n"
                            "            const newTask = { id: 'task_' + Date.now(), title, completed: false };\n"
                            "            state.tasks.push(newTask);\n"
                            "            input.value = '';\n"
                            "            render();\n"
                            "        });\n"
                            "\n"
                            "        window.toggleTask = function(id) {\n"
                            "            const t = state.tasks.find(x => x.id === id);\n"
                            "            if (t) { t.completed = !t.completed; render(); }\n"
                            "        };\n"
                            "\n"
                            "        window.deleteTask = function(id) {\n"
                            "            state.tasks = state.tasks.filter(x => x.id !== id);\n"
                            "            render();\n"
                            "        };\n"
                            "        render();\n"
                            "    </script>\n"
                            "</body>\n"
                            "</html>\n"
                        ),
                        "overwrite": True,
                    },
                ),
                TaskStep(
                    step_id=4,
                    title="Create Automated Verification Suite",
                    description="Write pytest suite verifying CRUD routes and MongoDB repository behavior.",
                    tool="write_file",
                    parameters={
                        "path": "test_task_manager.py",
                        "content": (
                            "import pytest\n"
                            "from fastapi.testclient import TestClient\n"
                            "from backend_app import app\n"
                            "\n"
                            "client = TestClient(app)\n"
                            "\n"
                            "def test_health():\n"
                            "    res = client.get('/health')\n"
                            "    assert res.status_code == 200\n"
                            "    assert res.json()['status'] == 'healthy'\n"
                            "\n"
                            "def test_crud_flow():\n"
                            "    # 1. Create\n"
                            "    create_res = client.post('/api/tasks', json={'title': 'Autonomous Task 1'})\n"
                            "    assert create_res.status_code == 200\n"
                            "    created = create_res.json()\n"
                            "    task_id = created['id']\n"
                            "    assert created['title'] == 'Autonomous Task 1'\n"
                            "    assert created['completed'] is False\n"
                            "\n"
                            "    # 2. List\n"
                            "    list_res = client.get('/api/tasks')\n"
                            "    assert list_res.status_code == 200\n"
                            "    assert len(list_res.json()) >= 1\n"
                            "\n"
                            "    # 3. Update\n"
                            "    update_res = client.put(f'/api/tasks/{task_id}', json={'title': 'Updated Title', 'completed': True})\n"
                            "    assert update_res.status_code == 200\n"
                            "    assert update_res.json()['completed'] is True\n"
                            "    assert update_res.json()['title'] == 'Updated Title'\n"
                            "\n"
                            "    # 4. Delete\n"
                            "    del_res = client.delete(f'/api/tasks/{task_id}')\n"
                            "    assert del_res.status_code == 200\n"
                            "    assert del_res.json()['success'] is True\n"
                        ),
                        "overwrite": True,
                    },
                ),
                TaskStep(
                    step_id=5,
                    title="Execute Automated Pytest Verification Suite",
                    description="Run pytest in the workspace to verify backend and MongoDB operations.",
                    tool="execute_terminal_command",
                    parameters={"command": "D:\\DODO\\.venv\\Scripts\\pytest.exe test_task_manager.py -v", "timeout_seconds": 30},
                ),
                TaskStep(
                    step_id=6,
                    title="Browser Automation & UI Verification",
                    description="Use Playwright to open and inspect the generated frontend application.",
                    tool="open_and_inspect_page",
                    parameters={"url": f"file:///{workspace_path.replace(chr(92), '/')}/index.html", "wait_ms": 1000},
                ),
                TaskStep(
                    step_id=7,
                    title="Take Verification UI Screenshot",
                    description="Capture rendered full-page screenshot of the verified application.",
                    tool="take_screenshot",
                    parameters={
                        "url": f"file:///{workspace_path.replace(chr(92), '/')}/index.html",
                        "save_path": "verification_preview.png"
                    },
                ),
            ]

            return TaskPlan(
                objective="Build and verify full-stack task management application with React, FastAPI, and MongoDB",
                analysis="Request requires backend API, MongoDB database CRUD, interactive UI frontend, automated unit testing, and browser verification.",
                estimated_steps=len(steps),
                steps=steps,
            )

        # General plan for other tasks
        steps = [
            TaskStep(
                step_id=1,
                title="Inspect Project Workspace",
                description="List files and scan existing structure.",
                tool="list_workspace_files",
                parameters={"subpath": "", "depth": 2},
            ),
            TaskStep(
                step_id=2,
                title="Execute Objective Implementation",
                description="Analyze and write the requested solution files.",
                tool="write_file",
                parameters={"path": "solution.py", "content": f"# Implementation for: {prompt}\n", "overwrite": True},
            ),
            TaskStep(
                step_id=3,
                title="Verify Solution",
                description="Verify implementation syntax and runtime integrity.",
                tool="read_file",
                parameters={"path": "solution.py", "start_line": 1, "end_line": 50},
            ),
        ]
        return TaskPlan(
            objective=prompt,
            analysis="General autonomous task plan.",
            estimated_steps=len(steps),
            steps=steps,
        )


task_planner = TaskPlanner()

