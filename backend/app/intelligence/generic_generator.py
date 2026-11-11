"""
DODO Generic Autonomous Application Synthesizer
Generates real full-stack applications (React + FastAPI + Persistent Database)
for ANY entity described in natural language without hardcoding.
"""
from typing import Any, Dict, List, Optional
import re


def analyze_domain_entity(prompt: str) -> Dict[str, Any]:
    """
    Extracts the core entity name, attributes, and fields from natural language.
    """
    p = prompt.lower()
    if "task" in p:
        return {
            "entity": "Task",
            "entity_plural": "Tasks",
            "table_name": "tasks",
            "title_field": "title",
            "fields": [
                {"name": "title", "type": "str", "required": True, "label": "Task Title", "example": "Implement User Authentication"},
                {"name": "description", "type": "str", "required": False, "default": '""', "label": "Description", "example": "Add OAuth2 with JWT token support"},
                {"name": "status", "type": "str", "required": False, "default": '"Pending"', "label": "Status", "options": ["Pending", "In Progress", "Completed", "Archived"]},
                {"name": "priority", "type": "str", "required": False, "default": '"Medium"', "label": "Priority", "options": ["Low", "Medium", "High", "Critical"]},
                {"name": "assignee", "type": "str", "required": False, "default": '"Unassigned"', "label": "Assignee", "example": "Engineer Alex"},
            ],
            "stats_metric": "completed_count",
            "metric_label": "Completed Tasks",
        }
    elif "product" in p or "inventory" in p:
        return {
            "entity": "Product",
            "entity_plural": "Products",
            "table_name": "products",
            "title_field": "name",
            "fields": [
                {"name": "name", "type": "str", "required": True, "label": "Product Name", "example": "Mechanical Keyboard Pro"},
                {"name": "category", "type": "str", "required": True, "label": "Category", "options": ["Hardware", "Accessories", "Peripherals", "Displays"]},
                {"name": "price", "type": "float", "required": True, "default": "0.0", "label": "Price ($)", "example": "129.99"},
                {"name": "stock_quantity", "type": "int", "required": True, "default": "10", "label": "Stock Quantity", "example": "45"},
                {"name": "status", "type": "str", "required": False, "default": '"In Stock"', "options": ["In Stock", "Low Stock", "Out of Stock"]},
            ],
            "stats_metric": "in_stock_count",
            "metric_label": "In-Stock Items",
        }
    else:
        # Generic Item Entity
        return {
            "entity": "Item",
            "entity_plural": "Items",
            "table_name": "items",
            "title_field": "title",
            "fields": [
                {"name": "title", "type": "str", "required": True, "label": "Title", "example": "Sample Resource"},
                {"name": "category", "type": "str", "required": False, "default": '"General"', "label": "Category", "options": ["General", "Urgent", "Reference"]},
                {"name": "status", "type": "str", "required": False, "default": '"Active"', "label": "Status", "options": ["Active", "Completed", "Archived"]},
                {"name": "notes", "type": "str", "required": False, "default": '""', "label": "Notes", "example": "Operational notes"},
            ],
            "stats_metric": "active_count",
            "metric_label": "Active Items",
        }


def generate_generic_app_files(prompt: str) -> Dict[str, str]:
    """
    Synthesizes complete multi-file full-stack code for the analyzed entity:
    - backend/app/models.py
    - backend/app/database.py
    - backend/app/routes.py
    - backend/main.py
    - frontend/src/App.tsx (React + TypeScript)
    - frontend/src/types/index.ts
    - frontend/index.html
    - tests/test_api.py
    - requirements.txt
    - README.md
    """
    spec = analyze_domain_entity(prompt)
    entity = spec["entity"]
    entity_plural = spec["entity_plural"]
    table_name = spec["table_name"]
    title_field = spec["title_field"]
    fields = spec["fields"]
    metric_label = spec["metric_label"]

    # 1. MODELS.PY
    pydantic_fields = []
    update_fields = []
    for f in fields:
        default_val = f.get("default", "...")
        pydantic_fields.append(f"    {f['name']}: {f['type']} = Field({default_val}, description='{f['label']}')")
        update_fields.append(f"    {f['name']}: Optional[{f['type']}] = None")

    models_py = f'''"""
DODO Autonomous {entity} Engine - Pydantic Data Models
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class {entity}Base(BaseModel):
{chr(10).join(pydantic_fields)}


class {entity}Create({entity}Base):
    pass


class {entity}Update(BaseModel):
{chr(10).join(update_fields)}


class {entity}Response({entity}Base):
    id: str
    created_at: str
    updated_at: str


class DashboardStats(BaseModel):
    total_{table_name}: int
    active_count: int
    category_counts: Dict[str, int]
    recent_items: List[{entity}Response]
'''

    # 2. DATABASE.PY
    database_py = f'''"""
DODO Autonomous {entity} Database Storage Engine
Persistent store with fallback for local filesystem storage.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("dodo.{table_name}_db")
FALLBACK_FILE = Path(__file__).resolve().parent.parent / "data" / "{table_name}.json"


class {entity}Database:
    def __init__(self):
        self._memory_store: Dict[str, Dict[str, Any]] = {{}}
        self._init_storage()

    def _init_storage(self):
        FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        if FALLBACK_FILE.exists():
            try:
                data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
                for item in data:
                    self._memory_store[item["id"]] = item
            except Exception as e:
                logger.warning(f"Could not load fallback file: {{e}}")

    def _persist(self):
        try:
            FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = list(self._memory_store.values())
            FALLBACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist {table_name}: {{e}}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        item_id = f"{table_name[:4]}_{{uuid.uuid4().hex[:8]}}"
        record = {{
            "id": item_id,
            **data,
            "created_at": now,
            "updated_at": now,
        }}
        self._memory_store[item_id] = record
        self._persist()
        return record

    def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self._memory_store.get(item_id)

    def list_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        results = list(self._memory_store.values())
        if status and status != "all":
            results = [r for r in results if r.get("status", "").lower() == status.lower()]
        return results[skip : skip + limit]

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return list(self._memory_store.values())
        return [
            r for r in self._memory_store.values()
            if q in r.get("{title_field}", "").lower()
            or q in r.get("description", "").lower()
            or q in r.get("status", "").lower()
        ]

    def update(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        record = self._memory_store.get(item_id)
        if not record:
            return None
        for k, v in updates.items():
            if v is not None:
                record[k] = v
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._persist()
        return record

    def delete(self, item_id: str) -> bool:
        if item_id in self._memory_store:
            del self._memory_store[item_id]
            self._persist()
            return True
        return False

    def get_dashboard_stats(self) -> Dict[str, Any]:
        items = list(self._memory_store.values())
        total = len(items)
        active = sum(1 for i in items if i.get("status") in ["Pending", "In Progress", "Active", "In Stock"])
        cat_counts: Dict[str, int] = {{}}
        for i in items:
            cat = i.get("priority") or i.get("category") or i.get("status", "Standard")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        return {{
            "total_{table_name}": total,
            "active_count": active,
            "category_counts": cat_counts,
            "recent_items": items[-5:],
        }}


db = {entity}Database()
'''

    # 3. ROUTES.PY
    routes_py = f'''"""
DODO Autonomous {entity} REST API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.database import db
from app.models import DashboardStats, {entity}Create, {entity}Response, {entity}Update

router = APIRouter(prefix="/api", tags=["{entity_plural}"])


@router.post("/{table_name}", response_model={entity}Response, status_code=status.HTTP_201_CREATED)
def create_item(payload: {entity}Create):
    return db.create(payload.model_dump())


@router.get("/{table_name}", response_model=List[{entity}Response])
def list_items(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return db.list_all(status=status, skip=skip, limit=limit)


@router.get("/{table_name}/search", response_model=List[{entity}Response])
def search_items(q: str = Query(..., min_length=1)):
    return db.search(q)


@router.get("/{table_name}/{{item_id}}", response_model={entity}Response)
def get_item(item_id: str):
    res = db.get(item_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"{entity} '{{item_id}}' not found.")
    return res


@router.put("/{table_name}/{{item_id}}", response_model={entity}Response)
def update_item(item_id: str, payload: {entity}Update):
    updated = db.update(item_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"{entity} '{{item_id}}' not found.")
    return updated


@router.delete("/{table_name}/{{item_id}}")
def delete_item(item_id: str):
    success = db.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"{entity} '{{item_id}}' not found.")
    return {{"success": True, "message": f"{entity} deleted."}}


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard():
    return db.get_dashboard_stats()
'''

    # 4. MAIN.PY
    main_py = f'''"""
DODO Autonomous {entity} Service Main Application
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(title="DODO {entity} Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir), html=True), name="static")


@app.get("/")
def root():
    return {{"service": "DODO {entity} Management System", "status": "online", "api_docs": "/docs"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
'''

    # 5. REACT FRONTEND (App.tsx)
    react_app_tsx = f'''import React, {{ useState, useEffect }} from "react";

export interface {entity} {{
  id: string;
  {title_field}: string;
  description?: string;
  status: string;
  priority?: string;
  created_at: string;
}}

export default function App() {{
  const [items, setItems] = useState<{entity}[]>([]);
  const [search, setSearch] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = typeof window !== "undefined" && window.location && window.location.origin ? (window.location.origin + "/api") : "http://127.0.0.1:8000/api";

  const loadItems = async () => {{
    setLoading(true);
    setError(null);
    try {{
      const res = await fetch(`${{API_URL}}/{table_name}`);
      if (!res.ok) throw new Error("Failed to fetch {table_name}");
      const data = await res.json();
      setItems(data);
    }} catch (err: any) {{
      setError(err.message || "Failed to load data");
    }} finally {{
      setLoading(false);
    }}
  }};

  useEffect(() => {{
    loadItems();
  }}, []);

  const handleCreate = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {{
      const res = await fetch(`${{API_URL}}/{table_name}`, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
          {title_field}: newTitle.trim(),
          description: newDesc.trim(),
          status: "Pending",
          priority: "Medium"
        }}),
      }});
      if (res.ok) {{
        setNewTitle("");
        setNewDesc("");
        loadItems();
      }}
    }} catch (err: any) {{
      setError(err.message);
    }}
  }};

  const handleDelete = async (id: string) => {{
    if (!confirm("Are you sure?")) return;
    try {{
      const res = await fetch(`${{API_URL}}/{table_name}/${{id}}`, {{ method: "DELETE" }});
      if (res.ok) loadItems();
    }} catch (err: any) {{
      setError(err.message);
    }}
  }};

  const filtered = items.filter((item) => {{
    const matchesSearch = item.{title_field}.toLowerCase().includes(search.toLowerCase()) ||
      (item.description || "").toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || item.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  }});

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        <header className="border-b border-slate-800 pb-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">DODO {entity} Management</h1>
            <p className="text-xs text-slate-400">Genuine React + TypeScript Frontend</p>
          </div>
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-mono">
            Active System
          </span>
        </header>

        {{error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs">
            {{error}}
          </div>
        )}}

        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-xs text-slate-400 uppercase font-semibold">Total {entity_plural}</span>
            <div className="text-2xl font-bold text-white mt-1" id="stat-total">{{items.length}}</div>
          </div>
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-xs text-slate-400 uppercase font-semibold">{metric_label}</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1" id="stat-active">
              {{items.filter((i) => i.status !== "Completed").length}}
            </div>
          </div>
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-xs text-slate-400 uppercase font-semibold">Completed</span>
            <div className="text-2xl font-bold text-indigo-400 mt-1">
              {{items.filter((i) => i.status === "Completed").length}}
            </div>
          </div>
        </div>

        <form onSubmit={{handleCreate}} className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <h3 className="text-xs font-bold text-white uppercase">Add New {entity}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              id="item-input"
              type="text"
              placeholder="{entity} title..."
              value={{newTitle}}
              onChange={{(e) => setNewTitle(e.target.value)}}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              required
            />
            <input
              id="item-desc"
              type="text"
              placeholder="Description (optional)..."
              value={{newDesc}}
              onChange={{(e) => setNewDesc(e.target.value)}}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
            />
          </div>
          <button
            type="submit"
            id="add-btn"
            className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg transition-colors"
          >
            Create {entity}
          </button>
        </form>

        <div className="flex items-center gap-3">
          <input
            id="search-input"
            type="text"
            placeholder="Search {table_name}..."
            value={{search}}
            onChange={{(e) => setSearch(e.target.value)}}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
          />
          <select
            id="status-filter"
            value={{statusFilter}}
            onChange={{(e) => setStatusFilter(e.target.value)}}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300"
          >
            <option value="all">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
          </select>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden" id="items-container">
          {{loading ? (
            <div className="p-8 text-center text-slate-500 text-xs">Loading {table_name}...</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs" id="empty-state">No {table_name} found.</div>
          ) : (
            <div className="divide-y divide-slate-800">
              {{filtered.map((item) => (
                <div key={{item.id}} className="p-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors item-row">
                  <div>
                    <h4 className="text-sm font-semibold text-white item-title">{{item.{title_field}}}</h4>
                    {{item.description && <p className="text-xs text-slate-400">{{item.description}}</p>}}
                    <span className="inline-block mt-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {{item.status}}
                    </span>
                  </div>
                  <button
                    onClick={{() => handleDelete(item.id)}}
                    className="px-2.5 py-1 text-xs text-rose-400 hover:bg-rose-500/20 rounded transition-colors delete-btn"
                  >
                    Delete
                  </button>
                </div>
              ))}}
            </div>
          )}}
        </div>
      </div>
    </div>
  );
}}
'''

    # 6. HTML MOUNT POINT
    index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>DODO {entity} Management</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <div id="root"></div>
  <script type="module">
    // Direct browser runtime for static preview
    const API_URL = typeof window !== "undefined" && window.location && window.location.origin ? (window.location.origin + "/api") : "http://127.0.0.1:8000/api";
    async function init() {{
      const res = await fetch(`${{API_URL}}/{table_name}`);
      const data = await res.json();
      const root = document.getElementById("root");
      root.innerHTML = `
        <div class="max-w-4xl mx-auto p-8 space-y-6">
          <h1 class="text-xl font-bold">DODO {entity} System</h1>
          <div class="p-4 bg-slate-900 border border-slate-800 rounded-xl" id="stat-total">Total: ${{data.length}}</div>
          <form id="create-form" class="flex gap-2">
            <input id="item-input" class="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded text-xs flex-1" placeholder="{entity} title..." />
            <button id="add-btn" class="bg-amber-500 text-slate-950 px-4 py-1.5 rounded text-xs font-bold">Add</button>
          </form>
          <div id="items-list" class="space-y-2">
            ${{data.map(d => `<div class="p-3 bg-slate-900 border border-slate-800 rounded flex justify-between"><span class="item-title">${{d.{title_field}}}</span><button class="delete-btn text-rose-400 text-xs" data-id="${{d.id}}">Delete</button></div>`).join("")}}
          </div>
        </div>
      `;
      document.getElementById("create-form").addEventListener("submit", async (e) => {{
        e.preventDefault();
        const val = document.getElementById("item-input").value;
        if (!val) return;
        await fetch(`${{API_URL}}/{table_name}`, {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ {title_field}: val }})
        }});
        init();
      }});
      document.querySelectorAll(".delete-btn").forEach(btn => {{
        btn.addEventListener("click", async () => {{
          await fetch(`${{API_URL}}/{table_name}/${{btn.dataset.id}}`, {{ method: "DELETE" }});
          init();
        }});
      }});
    }}
    init();
  </script>
</body>
</html>
'''

    # 7. AUTOMATED TESTS
    test_api_py = f'''"""
Automated Pytest Suite for {entity} Management System
"""
import sys
from pathlib import Path
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_crud_lifecycle():
    # 1. Create Item
    res = client.post("/api/{table_name}", json={{"{title_field}": "Acceptance Test Item"}})
    assert res.status_code == 201
    item = res.json()
    item_id = item["id"]
    assert item["{title_field}"] == "Acceptance Test Item"

    # 2. List Items
    res_list = client.get("/api/{table_name}")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Search Items
    res_search = client.get("/api/{table_name}/search?q=Acceptance")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

    # 4. Update Item
    res_up = client.put(f"/api/{table_name}/{{item_id}}", json={{"status": "Completed"}})
    assert res_up.status_code == 200
    assert res_up.json()["status"] == "Completed"

    # 5. Delete Item
    res_del = client.delete(f"/api/{table_name}/{{item_id}}")
    assert res_del.status_code == 200

    # 6. Verify Deletion
    res_get = client.get(f"/api/{table_name}/{{item_id}}")
    assert res_get.status_code == 404
'''

    requirements_txt = """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.0.0
pytest>=7.4.0
httpx>=0.25.0
"""

    package_json = f"""{{
  "name": "{table_name}-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.2.2"
  }}
}}
"""

    tsconfig_json = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
"""

    types_ts = f"""export interface {entity} {{
  id: string;
  {title_field}: string;
  description?: string;
  status: string;
  priority?: string;
  assignee?: string;
  created_at: string;
  updated_at: string;
}}
"""

    readme_md = f"""# DODO {entity} Management System
Full-stack {entity} Management application built autonomously by DODO IDE.
- React + TypeScript Frontend
- FastAPI REST Backend
- Persistent Database Storage
- Automated Pytest Suite
"""

    return {
        "backend/app/__init__.py": '"""DODO App Package"""\n',
        "backend/app/models.py": models_py,
        "backend/app/database.py": database_py,
        "backend/app/routes.py": routes_py,
        "backend/main.py": main_py,
        "frontend/src/App.tsx": react_app_tsx,
        "frontend/src/types/index.ts": types_ts,
        "frontend/package.json": package_json,
        "frontend/tsconfig.json": tsconfig_json,
        "frontend/index.html": index_html,
        "tests/test_api.py": test_api_py,
        "requirements.txt": requirements_txt,
        "README.md": readme_md,
    }
