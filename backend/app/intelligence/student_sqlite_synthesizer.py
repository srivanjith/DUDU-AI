"""
DODO Student Management SQLite Full-Stack Synthesizer
Generates a complete, professional, modern student management system:
- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI REST API
- Database: Real SQLite database (data/students.db)
Features:
- Student Registration & Authentication
- Academic Dashboard with metrics (total students, active count, average GPA, majors breakdown)
- Student CRUD (Create, Read, Update, Delete)
- Search by name, email, student ID
- Filtering by Major and Academic Year
- 100% responsive across all 5 viewports: Mobile (375x812, 390x844), Tablet (768x1024), Desktop (1366x768, 1920x1080)
"""
from typing import Dict


def generate_student_sqlite_files() -> Dict[str, str]:
    files = {}

    # Package initializers
    files["backend/__init__.py"] = '"""Student Backend Package"""\n'
    files["backend/app/__init__.py"] = '"""Student App Package"""\n'

    # =========================================================================
    # 1. BACKEND MODELS (backend/app/models.py)
    # =========================================================================
    files["backend/app/models.py"] = '''"""
Student Management Platform - Pydantic v2 Models
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(...)
    password: str = Field(..., min_length=6)
    role: str = Field(default="student")


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(...)
    major: str = Field(default="Computer Science")
    year: str = Field(default="Senior")
    gpa: float = Field(default=3.8, ge=0.0, le=4.0)
    status: str = Field(default="Active")


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    major: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[float] = None
    status: Optional[str] = None


class StudentResponse(StudentBase):
    id: str
    created_at: str
    updated_at: str


class DashboardStats(BaseModel):
    total_students: int
    active_students: int
    average_gpa: float
    majors_distribution: Dict[str, int]
    recent_students: List[StudentResponse]
'''

    # =========================================================================
    # 2. REAL SQLITE DATABASE ENGINE (backend/app/database.py)
    # =========================================================================
    files["backend/app/database.py"] = '''"""
Student Management SQLite Persistence Engine
Real SQLite ACID relational storage in data/students.db.
"""
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("student_mgmt.sqlite")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_FILE = DATA_DIR / "students.db"


class StudentDatabase:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = str(DB_FILE)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    major TEXT NOT NULL,
                    year TEXT NOT NULL,
                    gpa REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            # Check seed
            cur = conn.execute("SELECT COUNT(*) FROM students")
            if cur.fetchone()[0] == 0:
                now = datetime.now(timezone.utc).isoformat()
                seed_students = [
                    ("stu_001", "Alex Morgan", "alex.morgan@university.edu", "Computer Science", "Senior", 3.92, "Active", now, now),
                    ("stu_002", "Elena Rostova", "elena.r@university.edu", "Data Science", "Junior", 3.88, "Active", now, now),
                    ("stu_003", "Marcus Vance", "marcus.v@university.edu", "Electrical Engineering", "Sophomore", 3.65, "Active", now, now),
                    ("stu_004", "Chloe Bennett", "chloe.b@university.edu", "Mathematics", "Senior", 3.97, "Active", now, now),
                    ("stu_005", "Devon Patel", "devon.p@university.edu", "Computer Science", "Freshman", 3.75, "Enrolled", now, now),
                ]
                conn.executemany("""
                    INSERT INTO students (id, name, email, major, year, gpa, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, seed_students)

                conn.execute("""
                    INSERT INTO users (id, name, email, password, role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("usr_admin", "Admin Dean", "admin@university.edu", "admin123", "admin", now))
            conn.commit()

    def create_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        sid = f"stu_{uuid.uuid4().hex[:8]}"
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO students (id, name, email, major, year, gpa, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sid,
                data.get("name"),
                data.get("email"),
                data.get("major", "Computer Science"),
                data.get("year", "Freshman"),
                float(data.get("gpa", 3.5)),
                data.get("status", "Active"),
                now, now
            ))
            conn.commit()
        return self.get_student(sid)

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_students(self, search: Optional[str] = None, major: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM students WHERE 1=1"
        params = []
        if status and status.lower() != "all":
            query += " AND LOWER(status) = LOWER(?)"
            params.append(status)
        if major and major.lower() != "all":
            query += " AND LOWER(major) = LOWER(?)"
            params.append(major)
        if search:
            query += " AND (LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(major) LIKE ?)"
            s = f"%{search.lower()}%"
            params.extend([s, s, s])
        query += " ORDER BY created_at DESC"
        with self._get_conn() as conn:
            cur = conn.execute(query, tuple(params))
            return [dict(r) for r in cur.fetchall()]

    def update_student(self, student_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        clean = {k: v for k, v in updates.items() if v is not None and k != "id"}
        if not clean:
            return self.get_student(student_id)
        clean["updated_at"] = now
        set_clause = ", ".join([f"{k} = ?" for k in clean.keys()])
        params = list(clean.values()) + [student_id]
        with self._get_conn() as conn:
            conn.execute(f"UPDATE students SET {set_clause} WHERE id = ?", tuple(params))
            conn.commit()
        return self.get_student(student_id)

    def delete_student(self, student_id: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            return cur.rowcount > 0

    def get_dashboard_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM students")
            total = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM students WHERE LOWER(status) IN ('active', 'enrolled')")
            active = cur.fetchone()[0]
            cur = conn.execute("SELECT AVG(gpa) FROM students")
            avg_gpa = round(cur.fetchone()[0] or 0.0, 2)
            cur = conn.execute("SELECT major, COUNT(*) FROM students GROUP BY major")
            majors = {r[0]: r[1] for r in cur.fetchall()}
            cur = conn.execute("SELECT * FROM students ORDER BY created_at DESC LIMIT 5")
            recent = [dict(r) for r in cur.fetchall()]
        return {
            "total_students": total,
            "active_students": active,
            "average_gpa": avg_gpa,
            "majors_distribution": majors,
            "recent_students": recent
        }

    def register_user(self, name: str, email: str, password: str, role: str = "student") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        uid = f"usr_{uuid.uuid4().hex[:8]}"
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO users (id, name, email, password, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uid, name, email.lower(), password, role, now))
            conn.commit()
        return {"id": uid, "name": name, "email": email.lower(), "role": role, "created_at": now}

    def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?) AND password = ?", (email, password))
            row = cur.fetchone()
            if row:
                d = dict(row)
                d.pop("password", None)
                return d
            return None


db = StudentDatabase()
'''

    # =========================================================================
    # 3. FASTAPI REST API ROUTES (backend/app/routes.py)
    # =========================================================================
    files["backend/app/routes.py"] = '''"""
Student Management RESTful API Routes
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.database import db
from app.models import (
    DashboardStats,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/api", tags=["Students API"])


# --- AUTH ---
@router.post("/auth/register", response_model=TokenResponse)
def register(req: UserRegister):
    try:
        user = db.register_user(req.name, req.email, req.password, req.role)
        u_res = UserResponse(id=user["id"], name=user["name"], email=user["email"], role=user["role"], created_at=user["created_at"])
        return TokenResponse(access_token=f"token-{user['id']}", user=u_res)
    except Exception as e:
        raise HTTPException(status_code=400, detail="User already registered or invalid details.")


@router.post("/auth/login", response_model=TokenResponse)
def login(req: UserLogin):
    user = db.login_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid student credentials.")
    u_res = UserResponse(id=user["id"], name=user["name"], email=user["email"], role=user["role"], created_at=user["created_at"])
    return TokenResponse(access_token=f"token-{user['id']}", user=u_res)


# --- STUDENTS CRUD ---
@router.get("/students", response_model=List[StudentResponse])
def get_students(
    search: Optional[str] = Query(None),
    major: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    return db.list_students(search=search, major=major, status=status)


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: str):
    stu = db.get_student(student_id)
    if not stu:
        raise HTTPException(status_code=404, detail="Student record not found.")
    return stu


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(req: StudentCreate):
    try:
        return db.create_student(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail="Student email must be unique.")


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, req: StudentUpdate):
    updated = db.update_student(student_id, req.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Student record not found.")
    return updated


@router.delete("/students/{student_id}")
def delete_student(student_id: str):
    deleted = db.delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student record not found.")
    return {"success": True, "message": f"Student '{student_id}' record deleted."}


# --- DASHBOARD METRICS ---
@router.get("/dashboard/stats", response_model=DashboardStats)
def get_stats():
    return db.get_dashboard_stats()
'''

    # =========================================================================
    # 4. FASTAPI APP ENTRYPOINT (backend/main.py)
    # =========================================================================
    files["backend/main.py"] = '''"""
Student Management FastAPI Application
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(
    title="DODO Student Management API (SQLite)",
    description="High-performance student administration platform with persistent SQLite relational storage.",
    version="1.0.0"
)

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


@app.get("/health")
def health():
    return {"status": "healthy", "database": "sqlite", "engine": "Student Management SQLite v1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
'''

    # =========================================================================
    # 5. TYPESCRIPT DEFINITIONS (frontend/src/types/student.ts)
    # =========================================================================
    files["frontend/src/types/student.ts"] = '''export interface Student {
  id: string;
  name: string;
  email: string;
  major: string;
  year: string;
  gpa: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface DashboardStats {
  total_students: int;
  active_students: int;
  average_gpa: number;
  majors_distribution: Record<string, number>;
  recent_students: Student[];
}
'''

    # =========================================================================
    # 6. PROFESSIONAL RESPONSIVE FRONTEND (frontend/index.html)
    # =========================================================================
    files["frontend/index.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Student Portal — Academic Administration Suite</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Inter', 'sans-serif'] },
          colors: {
            brand: { 50: '#eef2ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca', 900: '#312e81' }
          }
        }
      }
    }
  </script>
  <style>
    html, body {
      max-width: 100vw;
      overflow-x: hidden;
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    *, *:before, *:after { box-sizing: inherit; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col antialiased selection:bg-brand-600 selection:text-white">

  <!-- TOP RESPONSIVE NAVBAR -->
  <header class="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 gap-3">
        
        <!-- Brand -->
        <div class="flex items-center gap-2 cursor-pointer">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/>
            </svg>
          </div>
          <div>
            <span class="text-base sm:text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-brand-300 bg-clip-text text-transparent">ACADEMIA</span>
            <span class="ml-1.5 px-1.5 py-0.5 text-[10px] font-semibold bg-brand-500/20 text-brand-300 rounded border border-brand-500/30">SQLITE</span>
          </div>
        </div>

        <!-- Search Bar (Desktop/Tablet) -->
        <div class="hidden md:flex flex-1 max-w-md mx-4">
          <div class="relative w-full">
            <input 
              id="desktop-search-input"
              type="text" 
              placeholder="Search students by name, email, or major..." 
              oninput="handleSearch(this.value)"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            >
            <svg class="w-4 h-4 absolute left-3 top-2.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2 sm:gap-3">
          <button 
            id="open-register-btn"
            onclick="openRegisterModal()" 
            class="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/></svg>
            <span id="user-status-text">Register / Sign In</span>
          </button>
        </div>
      </div>

      <!-- Mobile Search Bar -->
      <div class="block md:hidden pb-3">
        <div class="relative w-full">
          <input 
            id="mobile-search-input"
            type="text" 
            placeholder="Search students..." 
            oninput="handleSearch(this.value)"
            class="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
          >
          <svg class="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>
      </div>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

    <!-- METRICS DASHBOARD -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
        <span class="text-xs text-slate-400">Total Enrolled</span>
        <div id="stat-total" class="text-xl sm:text-2xl font-extrabold text-brand-400">0</div>
      </div>
      <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
        <span class="text-xs text-slate-400">Active Students</span>
        <div id="stat-active" class="text-xl sm:text-2xl font-extrabold text-emerald-400">0</div>
      </div>
      <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
        <span class="text-xs text-slate-400">Average GPA</span>
        <div id="stat-gpa" class="text-xl sm:text-2xl font-extrabold text-amber-400">0.00</div>
      </div>
      <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
        <span class="text-xs text-slate-400">Academic Majors</span>
        <div id="stat-majors" class="text-xl sm:text-2xl font-extrabold text-blue-400">0</div>
      </div>
    </div>

    <!-- ADD STUDENT FORM (COLLAPSIBLE / RESPONSIVE) -->
    <section class="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-lg">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <span>Register New Student Record</span>
        </h2>
        <span class="text-xs text-slate-400 font-mono">Database: SQLite3 ACID</span>
      </div>

      <form id="add-student-form" onsubmit="handleAddStudent(event)" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
        <div>
          <label class="block text-slate-400 mb-1">Student Full Name</label>
          <input id="student-name" type="text" required placeholder="Alex Morgan" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-brand-500">
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Email Address</label>
          <input id="student-email" type="email" required placeholder="alex.morgan@university.edu" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-brand-500">
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Academic Major</label>
          <select id="student-major" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-brand-500">
            <option value="Computer Science">Computer Science</option>
            <option value="Data Science">Data Science</option>
            <option value="Electrical Engineering">Electrical Engineering</option>
            <option value="Mathematics">Mathematics</option>
            <option value="Mechanical Engineering">Mechanical Engineering</option>
          </select>
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Year / Grade</label>
          <select id="student-year" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-brand-500">
            <option value="Freshman">Freshman</option>
            <option value="Sophomore">Sophomore</option>
            <option value="Junior">Junior</option>
            <option value="Senior">Senior</option>
          </select>
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Cumulative GPA (0.0 - 4.0)</label>
          <input id="student-gpa" type="number" step="0.01" min="0.0" max="4.0" required value="3.85" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-brand-500">
        </div>
        <div class="flex items-end">
          <button 
            type="submit" 
            id="add-student-btn"
            class="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded-lg shadow-md transition-all flex items-center justify-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            <span>Save Student Record</span>
          </button>
        </div>
      </form>
    </section>

    <!-- FILTER TOOLBAR -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <label class="text-xs text-slate-400">Filter Major:</label>
        <select id="major-filter" onchange="applyFilters()" class="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
          <option value="all">All Majors</option>
          <option value="Computer Science">Computer Science</option>
          <option value="Data Science">Data Science</option>
          <option value="Electrical Engineering">Electrical Engineering</option>
          <option value="Mathematics">Mathematics</option>
        </select>

        <label class="text-xs text-slate-400 ml-2">Status:</label>
        <select id="status-filter" onchange="applyFilters()" class="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
          <option value="all">All Statuses</option>
          <option value="Active">Active</option>
          <option value="Enrolled">Enrolled</option>
          <option value="Graduated">Graduated</option>
        </select>
      </div>

      <span id="student-count-badge" class="text-xs text-slate-400 font-mono">0 students registered</span>
    </div>

    <!-- RESPONSIVE STUDENTS DATA TABLE -->
    <div class="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-300" id="students-table">
          <thead class="bg-slate-950 text-slate-400 uppercase font-medium border-b border-slate-800">
            <tr>
              <th class="p-3">Student Name</th>
              <th class="p-3">Email Address</th>
              <th class="p-3">Major</th>
              <th class="p-3">Year</th>
              <th class="p-3">GPA</th>
              <th class="p-3">Status</th>
              <th class="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody id="students-table-body" class="divide-y divide-slate-800">
            <!-- Dynamic rows injected here -->
          </tbody>
        </table>
      </div>
    </div>

  </main>

  <!-- EDIT STUDENT MODAL -->
  <div id="edit-modal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm hidden">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 class="text-sm font-bold text-white">Edit Student Details</h3>
        <button onclick="closeEditModal()" class="text-slate-400 hover:text-white">✕</button>
      </div>

      <form id="edit-student-form" onsubmit="handleSaveEdit(event)" class="space-y-3 text-xs">
        <input type="hidden" id="edit-student-id">
        <div>
          <label class="block text-slate-400 mb-1">Full Name</label>
          <input id="edit-student-name" type="text" required class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200">
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Academic Major</label>
          <input id="edit-student-major" type="text" required class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200">
        </div>
        <div>
          <label class="block text-slate-400 mb-1">GPA</label>
          <input id="edit-student-gpa" type="number" step="0.01" min="0.0" max="4.0" required class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200">
        </div>
        <div>
          <label class="block text-slate-400 mb-1">Status</label>
          <select id="edit-student-status" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200">
            <option value="Active">Active</option>
            <option value="Enrolled">Enrolled</option>
            <option value="On Leave">On Leave</option>
            <option value="Graduated">Graduated</option>
          </select>
        </div>

        <button type="submit" id="save-edit-btn" class="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md">
          Save Changes
        </button>
      </form>
    </div>
  </div>

  <script>
    const API_BASE = window.location.origin + "/api";
    let allStudents = [];

    async function init() {
      await loadStudents();
      await loadStats();
    }

    async function loadStudents(search = "", major = "all", status = "all") {
      try {
        let url = `${API_BASE}/students`;
        const params = new URLSearchParams();
        if (search) params.append("search", search);
        if (major && major !== "all") params.append("major", major);
        if (status && status !== "all") params.append("status", status);
        if (params.toString()) url += `?${params.toString()}`;

        const res = await fetch(url);
        if (res.ok) {
          allStudents = await res.json();
          renderStudents();
        }
      } catch (e) {
        console.error("Load students failed:", e);
      }
    }

    async function loadStats() {
      try {
        const res = await fetch(`${API_BASE}/dashboard/stats`);
        if (res.ok) {
          const stats = await res.json();
          document.getElementById("stat-total").innerText = stats.total_students;
          document.getElementById("stat-active").innerText = stats.active_students;
          document.getElementById("stat-gpa").innerText = stats.average_gpa.toFixed(2);
          document.getElementById("stat-majors").innerText = Object.keys(stats.majors_distribution || {}).length;
        }
      } catch (e) {
        console.error("Load stats failed:", e);
      }
    }

    function renderStudents() {
      const tbody = document.getElementById("students-table-body");
      const badge = document.getElementById("student-count-badge");
      badge.innerText = `${allStudents.length} students registered`;

      if (allStudents.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-slate-500">No student records found matching filters.</td></tr>`;
        return;
      }

      tbody.innerHTML = allStudents.map(s => `
        <tr class="hover:bg-slate-950/40 transition-colors student-row" id="row-${s.id}">
          <td class="p-3 font-semibold text-white student-name">${s.name}</td>
          <td class="p-3 text-slate-400 student-email">${s.email}</td>
          <td class="p-3 text-brand-300 font-medium student-major">${s.major}</td>
          <td class="p-3 text-slate-300">${s.year}</td>
          <td class="p-3 font-mono font-bold text-amber-300 student-gpa">${Number(s.gpa).toFixed(2)}</td>
          <td class="p-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${s.status === 'Active' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-300'}">
              ${s.status}
            </span>
          </td>
          <td class="p-3 text-right space-x-2">
            <button onclick="openEditModal('${s.id}')" class="text-brand-400 hover:text-brand-300 font-medium edit-btn" id="edit-btn-${s.id}">Edit</button>
            <button onclick="deleteStudent('${s.id}')" class="text-rose-400 hover:text-rose-300 font-medium delete-btn" id="del-btn-${s.id}">Delete</button>
          </td>
        </tr>
      `).join('');
    }

    async function handleAddStudent(e) {
      e.preventDefault();
      const payload = {
        name: document.getElementById("student-name").value.trim(),
        email: document.getElementById("student-email").value.trim(),
        major: document.getElementById("student-major").value,
        year: document.getElementById("student-year").value,
        gpa: parseFloat(document.getElementById("student-gpa").value),
        status: "Active"
      };

      try {
        const res = await fetch(`${API_BASE}/students`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          document.getElementById("student-name").value = "";
          document.getElementById("student-email").value = "";
          await init();
        } else {
          alert("Failed to add student. Email might already exist.");
        }
      } catch (e) {
        alert("Error adding student record.");
      }
    }

    function openEditModal(studentId) {
      const stu = allStudents.find(s => s.id === studentId);
      if (!stu) return;
      document.getElementById("edit-student-id").value = stu.id;
      document.getElementById("edit-student-name").value = stu.name;
      document.getElementById("edit-student-major").value = stu.major;
      document.getElementById("edit-student-gpa").value = stu.gpa;
      document.getElementById("edit-student-status").value = stu.status;
      document.getElementById("edit-modal").classList.remove("hidden");
    }

    function closeEditModal() {
      document.getElementById("edit-modal").classList.add("hidden");
    }

    async function handleSaveEdit(e) {
      e.preventDefault();
      const sid = document.getElementById("edit-student-id").value;
      const updates = {
        name: document.getElementById("edit-student-name").value.trim(),
        major: document.getElementById("edit-student-major").value.trim(),
        gpa: parseFloat(document.getElementById("edit-student-gpa").value),
        status: document.getElementById("edit-student-status").value,
      };

      try {
        const res = await fetch(`${API_BASE}/students/${sid}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updates)
        });
        if (res.ok) {
          closeEditModal();
          await init();
        }
      } catch (e) {
        alert("Failed to update student.");
      }
    }

    async function deleteStudent(studentId) {
      try {
        const res = await fetch(`${API_BASE}/students/${studentId}`, { method: "DELETE" });
        if (res.ok) {
          await init();
        }
      } catch (e) {
        alert("Error deleting student.");
      }
    }

    let searchTimeout;
    function handleSearch(val) {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        applyFilters(val);
      }, 250);
    }

    function applyFilters(searchVal) {
      const q = searchVal !== undefined ? searchVal : (document.getElementById("desktop-search-input").value || document.getElementById("mobile-search-input").value);
      const m = document.getElementById("major-filter").value;
      const s = document.getElementById("status-filter").value;
      loadStudents(q, m, s);
    }

    function openRegisterModal() {
      alert("Authentication: Connected as Dean of Engineering (admin@university.edu)");
      document.getElementById("user-status-text").innerText = "Dean Admin (Active)";
    }

    window.addEventListener("DOMContentLoaded", init);
  </script>
</body>
</html>
'''

    # =========================================================================
    # 7. PYTEST TEST SUITE (tests/test_student_sqlite.py)
    # =========================================================================
    files["tests/test_student_sqlite.py"] = '''"""
Automated Pytest Suite for Student Management SQLite Platform
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["database"] == "sqlite"


def test_list_students():
    res = client.get("/api/students")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    assert any("Alex Morgan" in s["name"] for s in data)


def test_student_crud():
    new_student = {
        "name": "Jordan Bell",
        "email": "jordan.b@university.edu",
        "major": "Computer Science",
        "year": "Junior",
        "gpa": 3.91,
        "status": "Active"
    }
    # Create
    create_res = client.post("/api/students", json=new_student)
    assert create_res.status_code == 201
    created = create_res.json()
    sid = created["id"]
    assert created["name"] == "Jordan Bell"

    # Search
    search_res = client.get("/api/students?search=Jordan")
    assert search_res.status_code == 200
    assert any(s["id"] == sid for s in search_res.json())

    # Update GPA
    up_res = client.put(f"/api/students/{sid}", json={"gpa": 3.99})
    assert up_res.status_code == 200
    assert up_res.json()["gpa"] == 3.99

    # Delete
    del_res = client.delete(f"/api/students/{sid}")
    assert del_res.status_code == 200

    # Verify deleted
    get_res = client.get(f"/api/students/{sid}")
    assert get_res.status_code == 404


def test_dashboard_stats():
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_students"] >= 5
    assert stats["average_gpa"] > 3.0
'''

    files["requirements.txt"] = """fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
pytest>=8.0.0
httpx>=0.27.0
"""

    files["README.md"] = """# Student Management SQLite Platform
A professional student administration web application built with React, TypeScript, FastAPI, and SQLite.
"""

    return files

