"""
DODO Projects & Workspaces API Router
Provides comprehensive project lifecycle management:
- GET /api/projects (list registered/recent projects with validation)
- POST /api/projects/open (validate path, register/activate project, scan, return files)
- POST /api/projects/create (validate, generate starter template files, register, activate)
- GET /api/projects/quick-paths (common accessible workspace locations on Windows)
- GET /api/projects/{project_id} (get project details)
- GET /api/projects/{project_id}/files (get project file tree)
- DELETE /api/projects/{project_id} (unregister project metadata while preserving files)
"""
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.database.repositories.workspace_repository import workspace_repo
from backend.app.intelligence.project_scanner import project_scanner
from backend.app.tools.filesystem_tools import list_workspace_files

logger = logging.getLogger("dodo.projects")
router = APIRouter(prefix="/api/projects", tags=["Projects & Workspaces"])

# Disallow invalid Windows path characters in project names
INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


# ==============================================================================
# Request & Response Models
# ==============================================================================

class OpenProjectRequest(BaseModel):
    path: str = Field(..., min_length=1, description="Absolute filesystem path to project folder")
    name: Optional[str] = Field(None, description="Optional custom project name")


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project directory name")
    destination_folder: str = Field(..., min_length=1, description="Parent folder where project will be created")
    template: str = Field(default="empty", description="empty | react-ts | nextjs | python-fastapi | node-express")
    description: Optional[str] = Field("", description="Optional project description")
    init_git: Optional[bool] = Field(True, description="Whether to initialize Git repository in project")


# ==============================================================================
# Template Generators
# ==============================================================================

def _generate_template_files(target_dir: Path, name: str, template: str, description: str):
    """Generates starter template files on disk for new projects."""
    name_clean = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Common .gitignore
    gitignore_common = """# Dependencies
node_modules/
.pnp
.pnp.js

# Testing & Coverage
coverage/
.pytest_cache/

# Production
build/
dist/
.next/
out/

# Environment variables & Secrets
.env
.env*.local
*.pem
*.key

# OS Files
.DS_Store
Thumbs.db

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.venv/
env/
venv/
"""

    if template == "react-ts":
        # Vite + React 18 + TypeScript Starter
        pkg_json = {
            "name": name_clean,
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "lucide-react": "^0.344.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.66",
                "@types/react-dom": "^18.2.22",
                "@vitejs/plugin-react": "^4.2.1",
                "typescript": "^5.2.2",
                "vite": "^5.1.6"
            }
        }
        import json
        (target_dir / "package.json").write_text(json.dumps(pkg_json, indent=2), encoding="utf-8")

        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"]
        }
        (target_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2), encoding="utf-8")

        vite_config = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: false
  }
});
"""
        (target_dir / "vite.config.ts").write_text(vite_config, encoding="utf-8")

        index_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        (target_dir / "index.html").write_text(index_html, encoding="utf-8")

        src_dir = target_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        main_tsx = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
        (src_dir / "main.tsx").write_text(main_tsx, encoding="utf-8")

        app_tsx = """import React, { useState } from 'react';

export default function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="card">
      <h1>🦅 __NAME__</h1>
      <p className="subtitle">__DESC__</p>
      
      <div className="button-group">
        <button onClick={() => setCount((c) => c + 1)}>
          Count is: <strong>{count}</strong>
        </button>
      </div>
      
      <p className="footer">
        Edit <code>src/App.tsx</code> and save to test fast refresh.
      </p>
    </div>
  );
}
""".replace("__NAME__", name).replace("__DESC__", description or "Built with React, TypeScript and DODO Autonomous IDE")
        (src_dir / "App.tsx").write_text(app_tsx, encoding="utf-8")

        index_css = """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: #090d16;
  color: #f8fafc;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.card {
  text-align: center;
  padding: 2.5rem;
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  max-width: 480px;
}

h1 {
  margin-top: 0;
  font-size: 2rem;
  color: #fbbf24;
}

.subtitle {
  color: #94a3b8;
  font-size: 0.95rem;
  margin-bottom: 2rem;
}

button {
  background: #f59e0b;
  color: #0f172a;
  border: none;
  padding: 0.75rem 1.75rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 700;
  transition: transform 0.1s ease, background 0.2s ease;
}

button:hover {
  background: #fbbf24;
  transform: translateY(-1px);
}

.footer {
  margin-top: 2rem;
  font-size: 0.8rem;
  color: #64748b;
}

code {
  background: #1e293b;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: monospace;
}
"""
        (src_dir / "index.css").write_text(index_css, encoding="utf-8")

    elif template == "nextjs":
        # Next.js 14 App Router Starter
        pkg_json = {
            "name": name_clean,
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "next": "^14.2.0",
                "lucide-react": "^0.344.0"
            },
            "devDependencies": {
                "typescript": "^5.2.2",
                "@types/node": "^20.11.0",
                "@types/react": "^18.2.66",
                "@types/react-dom": "^18.2.22"
            }
        }
        import json
        (target_dir / "package.json").write_text(json.dumps(pkg_json, indent=2), encoding="utf-8")

        next_cfg = "/** @type {import('next').NextConfig} */\nconst nextConfig = {};\nmodule.exports = nextConfig;\n"
        (target_dir / "next.config.js").write_text(next_cfg, encoding="utf-8")

        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}]
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        (target_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2), encoding="utf-8")

        app_dir = target_dir / "app"
        app_dir.mkdir(parents=True, exist_ok=True)

        layout_tsx = """import React from 'react';
import './globals.css';

export const metadata = {
  title: '__NAME__',
  description: '__DESC__',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
""".replace("__NAME__", name).replace("__DESC__", description or "Built with Next.js in DODO IDE")
        (app_dir / "layout.tsx").write_text(layout_tsx, encoding="utf-8")

        page_tsx = """export default function Home() {
  return (
    <main className="container">
      <h1>🦅 __NAME__</h1>
      <p>__DESC__</p>
    </main>
  );
}
""".replace("__NAME__", name).replace("__DESC__", description or "Next.js App Router project initialized in DODO IDE.")
        (app_dir / "page.tsx").write_text(page_tsx, encoding="utf-8")

        globals_css = """body {
  margin: 0;
  background: #0f172a;
  color: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.container {
  text-align: center;
  padding: 3rem;
  background: #1e293b;
  border-radius: 1rem;
}
h1 { color: #f59e0b; }
"""
        (app_dir / "globals.css").write_text(globals_css, encoding="utf-8")

    elif template == "python-fastapi":
        # Python + FastAPI Starter
        main_py = f'''"""
{name} — FastAPI Application
Generated by DODO Autonomous IDE
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="{name}",
    description="{description or 'REST API powered by FastAPI & DODO'}",
    version="0.1.0",
)

class Item(BaseModel):
    id: int
    title: str
    completed: bool = False

# In-memory sample data
items_db: List[Item] = [
    Item(id=1, title="Initialize project in DODO", completed=True),
    Item(id=2, title="Build awesome API endpoints", completed=False),
]

@app.get("/")
def read_root():
    return {{"project": "{name}", "status": "online", "docs": "/docs"}}

@app.get("/health")
def health_check():
    return {{"status": "healthy"}}

@app.get("/api/items", response_model=List[Item])
def list_items():
    return items_db

@app.post("/api/items", response_model=Item)
def create_item(item: Item):
    items_db.append(item)
    return item

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
'''
        (target_dir / "main.py").write_text(main_py, encoding="utf-8")

        reqs = """fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.6.0
pytest>=8.0.0
httpx>=0.27.0
"""
        (target_dir / "requirements.txt").write_text(reqs, encoding="utf-8")

        tests_dir = target_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")

        test_main = """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_items():
    response = client.get("/api/items")
    assert response.status_code == 200
    assert len(response.json()) >= 1
"""
        (tests_dir / "test_main.py").write_text(test_main, encoding="utf-8")

    elif template == "node-express":
        # Node.js + Express Starter
        pkg_json = {
            "name": name_clean,
            "version": "1.0.0",
            "description": description or f"{name} Express API",
            "main": "index.js",
            "type": "commonjs",
            "scripts": {
                "start": "node index.js",
                "dev": "nodemon index.js"
            },
            "dependencies": {
                "express": "^4.18.2",
                "cors": "^2.8.5"
            },
            "devDependencies": {
                "nodemon": "^3.1.0"
            }
        }
        import json
        (target_dir / "package.json").write_text(json.dumps(pkg_json, indent=2), encoding="utf-8")

        index_js = f"""const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

app.get('/api/health', (req, res) => {{
  res.json({{ status: 'healthy', project: '{name}' }});
}});

app.get('/api/data', (req, res) => {{
  res.json([
    {{ id: 1, name: 'Task 1', status: 'completed' }},
    {{ id: 2, name: 'Task 2', status: 'in-progress' }}
  ]);
}});

app.listen(PORT, () => {{
  console.log(`Server running on http://localhost:${{PORT}}`);
}});
"""
        (target_dir / "index.js").write_text(index_js, encoding="utf-8")

        pub_dir = target_dir / "public"
        pub_dir.mkdir(parents=True, exist_ok=True)
        pub_html = f"""<!DOCTYPE html>
<html>
<head>
  <title>{name}</title>
  <style>
    body {{ font-family: sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 4rem; }}
    h1 {{ color: #f59e0b; }}
  </style>
</head>
<body>
  <h1>{name}</h1>
  <p>Node.js & Express server is running!</p>
</body>
</html>
"""
        (pub_dir / "index.html").write_text(pub_html, encoding="utf-8")

    # Common README.md
    readme = f"""# {name}

{description or "Created with DODO Autonomous IDE."}

## Template Details
- **Architecture**: {template}
- **Created**: {now_str}
- **IDE**: DODO — Your AI. Your Machine. Your Rules.

## Getting Started

### Development
Review project configuration files and run relevant development commands in the DODO Terminal.
"""
    (target_dir / "README.md").write_text(readme, encoding="utf-8")
    (target_dir / ".gitignore").write_text(gitignore_common, encoding="utf-8")


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get("")
def list_projects():
    """
    Returns all registered/recent projects with their existence and scan status.
    """
    workspaces = workspace_repo.find_all(sort=[("updated_at", -1)])
    results = []

    for ws in workspaces:
        p = Path(ws["path"])
        exists = p.exists() and p.is_dir()
        
        scan_data = ws.get("scan_summary")
        if exists and not scan_data:
            try:
                scan = project_scanner.scan(str(p))
                scan_data = scan.model_dump()
                workspace_repo.update_scan_summary(ws["id"], scan_data)
            except Exception:
                pass

        results.append({
            "id": ws["id"],
            "name": ws.get("name") or p.name,
            "path": ws["path"],
            "description": ws.get("description", ""),
            "is_default": ws.get("is_default", False),
            "exists_on_disk": exists,
            "scan_summary": scan_data,
            "created_at": ws.get("created_at"),
            "updated_at": ws.get("updated_at"),
        })

    return results


@router.get("/quick-paths")
def get_quick_paths():
    """
    Returns common accessible workspace directory locations on Windows.
    """
    quick_paths = []
    
    # 1. Default workspace
    default_dir = Path(settings.AUTHORIZED_WORKSPACE_DIR).resolve()
    if default_dir.exists():
        quick_paths.append({
            "label": "DODO Workspace",
            "path": str(default_dir),
            "is_default": True
        })

    # 2. DODO root
    dodo_root = Path("D:/DODO").resolve()
    if dodo_root.exists() and str(dodo_root) != str(default_dir):
        quick_paths.append({
            "label": "DODO Project Root",
            "path": str(dodo_root),
            "is_default": False
        })

    # 3. User home projects / documents
    home = Path.home()
    dev_dir = home / "Projects"
    if dev_dir.exists():
        quick_paths.append({
            "label": "User Projects",
            "path": str(dev_dir),
            "is_default": False
        })

    return quick_paths


@router.post("/open")
def open_project(req: OpenProjectRequest):
    """
    Validates an existing folder on Windows, registers it in DODO,
    sets it as the active workspace, and returns project metadata with file tree.
    """
    target = Path(req.path).resolve()

    # 1. Validation
    if not target.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project folder does not exist on disk: '{req.path}'"
        )

    if not target.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"The specified path is a file, not a directory: '{req.path}'"
        )

    # 2. Security Check (Disallow raw drive roots or Windows system directories)
    target_str = str(target).lower().rstrip("\\/")
    if target_str in ["c:", "c:\\", "c:\\windows", "c:\\windows\\system32", "d:", "d:\\"]:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot open system root or system directory as project: '{target}'"
        )

    # Check read permissions
    try:
        next(target.iterdir(), None)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied accessing folder: '{target}'"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error accessing directory '{target}': {str(e)}"
        )

    # 3. Project Name
    proj_name = req.name.strip() if req.name and req.name.strip() else target.name
    if not proj_name:
        proj_name = "Project"

    # 4. Register or Update Workspace (set as active default)
    doc = workspace_repo.register_workspace(
        name=proj_name,
        path=str(target),
        description=f"Opened project at {target}",
        is_default=True
    )
    # Ensure default flag is set
    workspace_repo.collection.update_many({}, {"$set": {"is_default": False}})
    workspace_repo.update(doc["id"], {"is_default": True, "updated_at": datetime.now(timezone.utc)})

    # 5. Scan Project
    scan = project_scanner.scan(str(target))
    workspace_repo.update_scan_summary(doc["id"], scan.model_dump())
    doc["scan_summary"] = scan.model_dump()

    # 6. Get Initial Files
    file_res = list_workspace_files(subpath="", depth=3, workspace_root=str(target))
    files = file_res.get("items", [])

    return {
        "success": True,
        "message": f"Project '{proj_name}' opened successfully.",
        "project": doc,
        "scan": scan.model_dump(),
        "files": files,
        "workspace_path": str(target),
    }


@router.post("/create")
def create_project(req: CreateProjectRequest):
    """
    Validates project name & destination, creates project directory, generates
    production starter files, registers project, and sets it as active.
    """
    # 1. Validate Project Name
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty.")

    if INVALID_NAME_CHARS.search(name):
        raise HTTPException(
            status_code=400,
            detail='Project name contains invalid characters (cannot contain < > : " / \\ | ? *)'
        )

    if name.upper() in RESERVED_WINDOWS_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"'{name}' is a reserved Windows device name and cannot be used."
        )

    if name.endswith(".") or name.endswith(" "):
        raise HTTPException(
            status_code=400,
            detail="Project name cannot end with a period or space."
        )

    # 2. Validate Destination Directory
    dest = Path(req.destination_folder).resolve()
    if not dest.exists():
        try:
            dest.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Destination directory does not exist and could not be created: '{dest}': {str(e)}"
            )

    if not dest.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Destination path is not a directory: '{dest}'"
        )

    # 3. Target Path & Collision Prevention
    target_dir = dest / name
    if target_dir.exists():
        # Check if empty
        has_items = any(target_dir.iterdir())
        if has_items:
            raise HTTPException(
                status_code=409,
                detail=f"Folder '{name}' already exists in destination and is not empty. Choose another name or empty the directory."
            )
    else:
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create project directory '{target_dir}': {str(e)}"
            )

    # 4. Generate Template Files
    template = req.template.lower().strip()
    valid_templates = {"empty", "react-ts", "nextjs", "python-fastapi", "node-express"}
    if template not in valid_templates:
        template = "empty"

    try:
        _generate_template_files(target_dir, name, template, req.description or "")
    except Exception as e:
        logger.error(f"Error generating template files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate template starter files: {str(e)}"
        )

    # 5. Initialize Git if requested
    if req.init_git:
        try:
            subprocess.run(["git", "init"], cwd=str(target_dir), capture_output=True, timeout=5)
        except Exception:
            pass  # Git init is optional

    # 6. Register as Active Workspace
    doc = workspace_repo.register_workspace(
        name=name,
        path=str(target_dir),
        description=req.description or f"{template} starter project created by DODO",
        is_default=True
    )
    workspace_repo.collection.update_many({}, {"$set": {"is_default": False}})
    workspace_repo.update(doc["id"], {"is_default": True, "updated_at": datetime.now(timezone.utc)})

    # 7. Scan Project
    scan = project_scanner.scan(str(target_dir))
    workspace_repo.update_scan_summary(doc["id"], scan.model_dump())
    doc["scan_summary"] = scan.model_dump()

    # 8. List Created Files
    file_res = list_workspace_files(subpath="", depth=3, workspace_root=str(target_dir))
    files = file_res.get("items", [])

    return {
        "success": True,
        "message": f"Project '{name}' created successfully with {template} template.",
        "project": doc,
        "scan": scan.model_dump(),
        "files": files,
        "workspace_path": str(target_dir),
    }


@router.get("/{project_id}")
def get_project_details(project_id: str):
    """Retrieves full details of a registered project."""
    ws = workspace_repo.find_by_id(project_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    p = Path(ws["path"])
    ws["exists_on_disk"] = p.exists() and p.is_dir()
    return ws


@router.get("/{project_id}/files")
def get_project_files(project_id: str, depth: int = 3):
    """Retrieves the file tree for a registered project."""
    ws = workspace_repo.find_by_id(project_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    p = Path(ws["path"])
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail=f"Project directory '{ws['path']}' does not exist on disk.")

    return list_workspace_files(subpath="", depth=depth, workspace_root=str(p))
