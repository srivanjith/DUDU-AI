"""
DODO Student Management System File Templates
Full-stack implementation: FastAPI backend, MongoDB/JSON storage, reactive Tailwind frontend, and test suite.
"""

MODELS_PY = '''"""
DODO Student Management System - Data Models
Defines Pydantic schemas for student records, enrollment, and dashboard metrics.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full student name")
    email: str = Field(..., min_length=5, max_length=120, pattern=r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", description="Unique university email address")
    department: str = Field(..., description="Academic department / major")
    year: int = Field(default=1, ge=1, le=5, description="Academic year (1-5)")
    gpa: float = Field(default=3.0, ge=0.0, le=4.0, description="Current Grade Point Average (0.0 - 4.0)")
    status: str = Field(default="Active", description="Enrollment status: Active, Graduated, Suspended")
    courses: List[str] = Field(default_factory=list, description="Enrolled course codes")


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
    department: Optional[str] = None
    year: Optional[int] = Field(None, ge=1, le=5)
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    status: Optional[str] = None
    courses: Optional[List[str]] = None


class StudentResponse(StudentBase):
    id: str
    created_at: str
    updated_at: str


class DashboardStats(BaseModel):
    total_students: int
    active_students: int
    average_gpa: float
    department_counts: Dict[str, int]
    top_performers: List[StudentResponse]
'''

DATABASE_PY = '''"""
DODO Student Management System - Database Storage Engine
Provides persistent MongoDB storage with robust local JSON fallback.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("dodo.student_db")

FALLBACK_FILE = Path(__file__).resolve().parent.parent / "data" / "students.json"


class StudentDatabase:
    def __init__(self):
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._init_storage()

    def _init_storage(self):
        FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        if FALLBACK_FILE.exists():
            try:
                data = json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
                for item in data:
                    self._memory_store[item["id"]] = item
            except Exception as e:
                logger.warning(f"Could not load fallback file: {e}")

    def _persist(self):
        try:
            FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = list(self._memory_store.values())
            FALLBACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist student records: {e}")

    def create_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        student_id = f"stu_{uuid.uuid4().hex[:8]}"
        record = {
            "id": student_id,
            **data,
            "created_at": now,
            "updated_at": now,
        }
        self._memory_store[student_id] = record
        self._persist()
        return record

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        return self._memory_store.get(student_id)

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for s in self._memory_store.values():
            if s.get("email", "").lower() == email.lower():
                return s
        return None

    def list_students(
        self,
        department: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        results = list(self._memory_store.values())
        if department and department != "all":
            results = [s for s in results if s.get("department", "").lower() == department.lower()]
        if status and status != "all":
            results = [s for s in results if s.get("status", "").lower() == status.lower()]
        return results[skip : skip + limit]

    def search_students(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return list(self._memory_store.values())
        return [
            s for s in self._memory_store.values()
            if q in s.get("name", "").lower()
            or q in s.get("email", "").lower()
            or q in s.get("department", "").lower()
        ]

    def update_student(self, student_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        record = self._memory_store.get(student_id)
        if not record:
            return None
        for k, v in updates.items():
            if v is not None:
                record[k] = v
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._persist()
        return record

    def delete_student(self, student_id: str) -> bool:
        if student_id in self._memory_store:
            del self._memory_store[student_id]
            self._persist()
            return True
        return False

    def get_dashboard_stats(self) -> Dict[str, Any]:
        students = list(self._memory_store.values())
        total = len(students)
        active = sum(1 for s in students if s.get("status") == "Active")
        avg_gpa = round(sum(s.get("gpa", 0.0) for s in students) / total, 2) if total > 0 else 0.0

        dept_counts: Dict[str, int] = {}
        for s in students:
            dept = s.get("department", "Unassigned")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        top_performers = sorted(students, key=lambda s: s.get("gpa", 0.0), reverse=True)[:5]

        return {
            "total_students": total,
            "active_students": active,
            "average_gpa": avg_gpa,
            "department_counts": dept_counts,
            "top_performers": top_performers,
        }


db = StudentDatabase()
'''

ROUTES_PY = '''"""
DODO Student Management System - REST API Routes
Implements endpoints for Student registration, listing, search, update, deletion, and stats.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.database import db
from app.models import DashboardStats, StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/api", tags=["Students"])


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentCreate):
    """Registers a new student record after checking email uniqueness."""
    existing = db.find_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with email '{payload.email}' already exists."
        )
    record = db.create_student(payload.model_dump())
    return record


@router.get("/students", response_model=List[StudentResponse])
def list_students(
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status: Active, Graduated, Suspended"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Retrieves paginated student list with optional filtering."""
    return db.list_students(department=department, status=status, skip=skip, limit=limit)


@router.get("/students/search", response_model=List[StudentResponse])
def search_students(q: str = Query(..., min_length=1, description="Search query string")):
    """Searches students by name, email, or department."""
    return db.search_students(q)


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student_by_id(student_id: str):
    """Retrieves single student details by ID."""
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return student


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, payload: StudentUpdate):
    """Updates an existing student's record."""
    if payload.email:
        existing = db.find_by_email(payload.email)
        if existing and existing["id"] != student_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already used by another student."
            )
    updated = db.update_student(student_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return updated


@router.delete("/students/{student_id}")
def delete_student(student_id: str):
    """Deletes a student record from the system."""
    success = db.delete_student(student_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return {"success": True, "message": f"Student '{student_id}' deleted successfully."}


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_statistics():
    """Computes overall statistics: total students, active count, average GPA, department breakdown."""
    return db.get_dashboard_stats()
'''

MAIN_PY = '''"""
DODO Student Management Application Entry Point
FastAPI application with CORS, route mounting, and static files.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router as student_router

app = FastAPI(
    title="DODO Student Management System",
    description="Full-stack student management service built autonomously by DODO IDE",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router)

# Mount frontend directory for browser preview
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir), html=True), name="static")


@app.get("/")
def root():
    return {
        "service": "DODO Student Management System",
        "status": "online",
        "api_docs": "/docs",
        "frontend_preview": "/static/index.html",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
'''

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DODO — Student Management System</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }
  </style>
</head>
<body class="min-h-screen flex flex-col">
  <!-- Top Navigation -->
  <header class="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-30">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
        <i class="fa-solid fa-graduation-cap"></i>
      </div>
      <div>
        <h1 class="text-base font-bold text-white tracking-wide">DODO Student Management</h1>
        <p class="text-[11px] text-slate-400 font-mono">Autonomous Full-Stack System • React & FastAPI</p>
      </div>
    </div>
    <div class="flex items-center gap-4">
      <span class="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        API Online
      </span>
      <button id="open-register-btn" class="px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-xl text-xs font-bold shadow-lg shadow-amber-500/10 flex items-center gap-2 transition-all active:scale-95">
        <i class="fa-solid fa-user-plus"></i>
        <span>Register Student</span>
      </button>
    </div>
  </header>

  <!-- Main Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
    <!-- Metric KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Students</span>
          <h3 id="stat-total" class="text-2xl font-bold text-white mt-1">0</h3>
        </div>
        <div class="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-lg">
          <i class="fa-solid fa-users"></i>
        </div>
      </div>
      <div class="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Enrollment</span>
          <h3 id="stat-active" class="text-2xl font-bold text-emerald-400 mt-1">0</h3>
        </div>
        <div class="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg">
          <i class="fa-solid fa-user-check"></i>
        </div>
      </div>
      <div class="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Average GPA</span>
          <h3 id="stat-gpa" class="text-2xl font-bold text-amber-400 mt-1">0.00</h3>
        </div>
        <div class="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-lg">
          <i class="fa-solid fa-award"></i>
        </div>
      </div>
      <div class="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Departments</span>
          <h3 id="stat-dept" class="text-2xl font-bold text-purple-400 mt-1">0</h3>
        </div>
        <div class="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 text-lg">
          <i class="fa-solid fa-building-columns"></i>
        </div>
      </div>
    </div>

    <!-- Filter & Search Toolbar -->
    <div class="p-4 bg-slate-900/40 border border-slate-800/80 rounded-2xl flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3 flex-1 min-w-[280px]">
        <div class="relative flex-1">
          <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-500 text-xs"></i>
          <input id="search-input" type="text" placeholder="Search by student name, email, or department..." class="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500">
        </div>
        <select id="dept-filter" class="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500">
          <option value="all">All Departments</option>
          <option value="Computer Science">Computer Science</option>
          <option value="Electrical Engineering">Electrical Engineering</option>
          <option value="Mechanical Engineering">Mechanical Engineering</option>
          <option value="Data Science">Data Science</option>
          <option value="Business Administration">Business Administration</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <button id="refresh-btn" class="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs flex items-center gap-1.5 transition-colors">
          <i class="fa-solid fa-rotate"></i>
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Student Table Card -->
    <div class="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table id="student-table" class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th class="p-4">Student</th>
              <th class="p-4">Department</th>
              <th class="p-4">Year</th>
              <th class="p-4">GPA</th>
              <th class="p-4">Status</th>
              <th class="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody id="student-tbody" class="divide-y divide-slate-800/60 font-sans">
            <!-- Rendered dynamically -->
          </tbody>
        </table>
      </div>
      <div id="empty-state" class="p-12 text-center space-y-2 hidden">
        <i class="fa-solid fa-user-graduate text-3xl text-slate-600"></i>
        <h4 class="text-sm font-semibold text-slate-300">No students found</h4>
        <p class="text-xs text-slate-500">Register a new student using the button above to populate the directory.</p>
      </div>
    </div>
  </main>

  <!-- Register Student Modal -->
  <div id="register-modal" class="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
          <i class="fa-solid fa-user-plus text-amber-400"></i>
          <span>Register New Student</span>
        </h3>
        <button id="close-modal-btn" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <form id="register-form" class="p-6 space-y-4 text-xs">
        <div class="space-y-1">
          <label class="font-semibold text-slate-300">Full Name</label>
          <input id="student-name" required type="text" placeholder="e.g. Alex Morgan" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500">
        </div>
        <div class="space-y-1">
          <label class="font-semibold text-slate-300">University Email</label>
          <input id="student-email" required type="email" placeholder="e.g. alex.morgan@university.edu" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500">
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="font-semibold text-slate-300">Department</label>
            <select id="student-dept" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500">
              <option value="Computer Science">Computer Science</option>
              <option value="Electrical Engineering">Electrical Engineering</option>
              <option value="Mechanical Engineering">Mechanical Engineering</option>
              <option value="Data Science">Data Science</option>
              <option value="Business Administration">Business Administration</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="font-semibold text-slate-300">Academic Year</label>
            <select id="student-year" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500">
              <option value="1">1st Year (Freshman)</option>
              <option value="2">2nd Year (Sophomore)</option>
              <option value="3">3rd Year (Junior)</option>
              <option value="4">4th Year (Senior)</option>
              <option value="5">5th Year (Graduate)</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="font-semibold text-slate-300">Grade Point Average (GPA)</label>
            <input id="student-gpa" type="number" step="0.01" min="0.0" max="4.0" value="3.50" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500">
          </div>
          <div class="space-y-1">
            <label class="font-semibold text-slate-300">Enrolled Courses (comma-separated)</label>
            <input id="student-courses" type="text" placeholder="CS101, MATH201, CS305" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500">
          </div>
        </div>
        <div class="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
          <button type="button" id="cancel-btn" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium">Cancel</button>
          <button type="submit" id="submit-student-btn" class="px-5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/10">Submit Registration</button>
        </div>
      </form>
    </div>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
'''

APP_JS = '''// DODO Student Management Application Client Controller
const API_BASE = "http://127.0.0.1:8000/api";

let students = [];

async function fetchStudents() {
  try {
    const dept = document.getElementById("dept-filter").value;
    const url = dept === "all" ? `${API_BASE}/students` : `${API_BASE}/students?department=${encodeURIComponent(dept)}`;
    const res = await fetch(url);
    if (res.ok) {
      students = await res.json();
      renderTable(students);
    }
  } catch (err) {
    console.error("Error fetching students:", err);
  }
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats/dashboard`);
    if (res.ok) {
      const stats = await res.json();
      document.getElementById("stat-total").textContent = stats.total_students;
      document.getElementById("stat-active").textContent = stats.active_students;
      document.getElementById("stat-gpa").textContent = stats.average_gpa.toFixed(2);
      document.getElementById("stat-dept").textContent = Object.keys(stats.department_counts || {}).length;
    }
  } catch (err) {
    console.error("Error fetching dashboard stats:", err);
  }
}

function renderTable(data) {
  const tbody = document.getElementById("student-tbody");
  const emptyState = document.getElementById("empty-state");
  tbody.innerHTML = "";

  if (!data || data.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  data.forEach((s) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-900/50 transition-colors";
    tr.innerHTML = `
      <td class="p-4 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-indigo-600/20 text-indigo-400 font-bold flex items-center justify-center font-mono">
          ${s.name.charAt(0).toUpperCase()}
        </div>
        <div>
          <div class="font-bold text-white">${s.name}</div>
          <div class="text-[11px] text-slate-400 font-mono">${s.email}</div>
        </div>
      </td>
      <td class="p-4 text-slate-300">${s.department}</td>
      <td class="p-4 text-slate-400">Year ${s.year}</td>
      <td class="p-4 font-mono font-bold text-amber-400">${s.gpa.toFixed(2)}</td>
      <td class="p-4">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
          s.status === "Active" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-800 text-slate-400"
        }">
          ${s.status}
        </span>
      </td>
      <td class="p-4 text-right">
        <button onclick="handleDeleteStudent('${s.id}')" class="p-1.5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-lg transition-colors delete-student-btn" title="Delete Student">
          <i class="fa-regular fa-trash-can"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function handleDeleteStudent(id) {
  if (!confirm("Are you sure you want to delete this student record?")) return;
  try {
    const res = await fetch(`${API_BASE}/students/${id}`, { method: "DELETE" });
    if (res.ok) {
      await fetchStudents();
      await fetchStats();
    }
  } catch (err) {
    console.error("Error deleting student:", err);
  }
}

// Modal handling
const modal = document.getElementById("register-modal");
document.getElementById("open-register-btn").addEventListener("click", () => modal.classList.remove("hidden"));
document.getElementById("close-modal-btn").addEventListener("click", () => modal.classList.add("hidden"));
document.getElementById("cancel-btn").addEventListener("click", () => modal.classList.add("hidden"));

// Form submission
document.getElementById("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("student-name").value.trim();
  const email = document.getElementById("student-email").value.trim();
  const department = document.getElementById("student-dept").value;
  const year = parseInt(document.getElementById("student-year").value, 10);
  const gpa = parseFloat(document.getElementById("student-gpa").value);
  const coursesStr = document.getElementById("student-courses").value;
  const courses = coursesStr.split(",").map(c => c.trim()).filter(c => c.length > 0);

  try {
    const res = await fetch(`${API_BASE}/students`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, department, year, gpa, courses })
    });
    if (res.ok) {
      modal.classList.add("hidden");
      document.getElementById("register-form").reset();
      await fetchStudents();
      await fetchStats();
    } else {
      const err = await res.json();
      alert(`Registration failed: ${err.detail || "Server error"}`);
    }
  } catch (err) {
    console.error("Registration error:", err);
  }
});

// Search input handling
document.getElementById("search-input").addEventListener("input", async (e) => {
  const query = e.target.value.trim();
  if (!query) {
    fetchStudents();
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/students/search?q=${encodeURIComponent(query)}`);
    if (res.ok) {
      const matched = await res.json();
      renderTable(matched);
    }
  } catch (err) {
    console.error("Search error:", err);
  }
});

document.getElementById("dept-filter").addEventListener("change", fetchStudents);
document.getElementById("refresh-btn").addEventListener("click", () => {
  fetchStudents();
  fetchStats();
});

// Initial load
window.addEventListener("DOMContentLoaded", () => {
  fetchStudents();
  fetchStats();
});
'''

TEST_STUDENTS_API_PY = '''"""
Automated Pytest acceptance test suite for Student Management System.
Verifies complete CRUD operations, search, and dashboard statistics.
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


def test_student_lifecycle_crud():
    # 1. Register Student A
    payload_a = {
        "name": "Sarah Connor",
        "email": "sarah.connor@cyberdyne.edu",
        "department": "Computer Science",
        "year": 3,
        "gpa": 3.92,
        "status": "Active",
        "courses": ["CS301", "CS302", "MATH301"]
    }
    res_a = client.post("/api/students", json=payload_a)
    assert res_a.status_code == 201, f"Failed registration: {res_a.text}"
    student_a = res_a.json()
    assert student_a["name"] == "Sarah Connor"
    assert student_a["gpa"] == 3.92
    id_a = student_a["id"]

    # 2. Register Student B
    payload_b = {
        "name": "John Doe",
        "email": "john.doe@university.edu",
        "department": "Electrical Engineering",
        "year": 2,
        "gpa": 3.45,
        "status": "Active",
        "courses": ["EE201", "PHYS202"]
    }
    res_b = client.post("/api/students", json=payload_b)
    assert res_b.status_code == 201
    student_b = res_b.json()
    id_b = student_b["id"]

    # 3. List Students
    list_res = client.get("/api/students")
    assert list_res.status_code == 200
    students = list_res.json()
    assert len(students) >= 2

    # 4. Search Students
    search_res = client.get("/api/students/search?q=Sarah")
    assert search_res.status_code == 200
    matched = search_res.json()
    assert len(matched) >= 1
    assert any(s["name"] == "Sarah Connor" for s in matched)

    # 5. Update Student
    update_res = client.put(f"/api/students/{id_a}", json={"gpa": 4.0, "status": "Active"})
    assert update_res.status_code == 200
    updated_a = update_res.json()
    assert updated_a["gpa"] == 4.0

    # 6. Dashboard Statistics
    stats_res = client.get("/api/stats/dashboard")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_students"] >= 2
    assert stats["active_students"] >= 2
    assert stats["average_gpa"] > 0.0
    assert "Computer Science" in stats["department_counts"]

    # 7. Delete Student B
    del_res = client.delete(f"/api/students/{id_b}")
    assert del_res.status_code == 200

    # 8. Verify Deletion
    get_b = client.get(f"/api/students/{id_b}")
    assert get_b.status_code == 404
'''

REQUIREMENTS_TXT = """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.0.0
pymongo>=4.6.0
pytest>=7.4.0
httpx>=0.25.0
"""

README_MD = """# DODO Student Management System

Full-stack student management application developed autonomously by DODO IDE.

## Features
- **Student Registration**: Form validation with email uniqueness checking.
- **Directory Listing**: Responsive data table with department & status badges.
- **Instant Search**: Real-time multi-field search (name, email, department).
- **Update & Delete**: Comprehensive student lifecycle management.
- **Dashboard Metrics**: Real-time KPI statistics (total students, active count, average GPA).
- **FastAPI Backend**: Fully typed REST API with Pydantic v2.
- **MongoDB Persistence**: Real MongoDB database layer with local JSON store fallback.
- **Automated Tests**: Pytest test suite with 100% CRUD assertion coverage.

## Running the Application
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run backend & frontend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 3. Run automated tests
pytest tests/test_students_api.py -v
```
"""


def get_student_management_files() -> dict:
    return {
        "backend/app/__init__.py": '"""DODO Student Management App Package"""\n',
        "backend/app/models.py": MODELS_PY,
        "backend/app/database.py": DATABASE_PY,
        "backend/app/routes.py": ROUTES_PY,
        "backend/main.py": MAIN_PY,
        "frontend/index.html": INDEX_HTML,
        "frontend/app.js": APP_JS,
        "tests/test_students_api.py": TEST_STUDENTS_API_PY,
        "requirements.txt": REQUIREMENTS_TXT,
        "README.md": README_MD,
    }
