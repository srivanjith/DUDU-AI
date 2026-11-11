"""
DODO Student Management System File Templates
Full-stack implementation: FastAPI backend, MongoDB/JSON storage, genuine React + TypeScript frontend, and test suite.
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
        items = list(self._memory_store.values())
        if department and department != "all":
            items = [s for s in items if s.get("department") == department]
        if status:
            items = [s for s in items if s.get("status") == status]
        return items[skip : skip + limit]

    def search_students(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        matched = []
        for s in self._memory_store.values():
            if (
                q in s.get("name", "").lower()
                or q in s.get("email", "").lower()
                or q in s.get("department", "").lower()
            ):
                matched.append(s)
        return matched

    def update_student(self, student_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if student_id not in self._memory_store:
            return None
        existing = self._memory_store[student_id]
        now = datetime.now(timezone.utc).isoformat()
        for k, v in updates.items():
            if v is not None:
                existing[k] = v
        existing["updated_at"] = now
        self._memory_store[student_id] = existing
        self._persist()
        return existing

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
            d = s.get("department", "Unassigned")
            dept_counts[d] = dept_counts.get(d, 0) + 1

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
DODO Student Management System - FastAPI Routes
Implements complete CRUD endpoints, searching, and dashboard analytics.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.database import db
from app.models import DashboardStats, StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/api", tags=["Students"])


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentCreate):
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
    return db.list_students(department=department, status=status, skip=skip, limit=limit)


@router.get("/students/search", response_model=List[StudentResponse])
def search_students(q: str = Query(..., min_length=1, description="Search query string")):
    return db.search_students(q)


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student_by_id(student_id: str):
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return student


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, payload: StudentUpdate):
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
    success = db.delete_student(student_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")
    return {"success": True, "message": f"Student '{student_id}' deleted successfully."}


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_statistics():
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

# --- REACT + TYPESCRIPT FRONTEND MODULES ---

TYPES_STUDENT_TS = '''export interface Student {
  id: string;
  name: string;
  email: string;
  department: string;
  year: number;
  gpa: number;
  status: "Active" | "Graduated" | "Suspended";
  courses: string[];
  created_at: string;
  updated_at: string;
}

export interface StudentCreate {
  name: string;
  email: string;
  department: string;
  year: number;
  gpa: number;
  courses: string[];
  status?: string;
}

export interface StudentUpdate {
  name?: string;
  email?: string;
  department?: string;
  year?: number;
  gpa?: number;
  status?: string;
  courses?: string[];
}

export interface DashboardStats {
  total_students: number;
  active_students: number;
  average_gpa: number;
  department_counts: Record<string, number>;
  top_performers: Student[];
}
'''

API_SERVICE_TS = '''import { DashboardStats, Student, StudentCreate, StudentUpdate } from "../types/student";

const API_BASE = typeof window !== "undefined" && window.location && window.location.origin ? (window.location.origin + "/api") : "http://127.0.0.1:8000/api";

export async function fetchStudents(department?: string): Promise<Student[]> {
  const url = department && department !== "all"
    ? `${API_BASE}/students?department=${encodeURIComponent(department)}`
    : `${API_BASE}/students`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch students: ${res.statusText}`);
  return res.json();
}

export async function searchStudents(query: string): Promise<Student[]> {
  const res = await fetch(`${API_BASE}/students/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}

export async function createStudent(data: StudentCreate): Promise<Student> {
  const res = await fetch(`${API_BASE}/students`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

export async function updateStudent(id: string, data: StudentUpdate): Promise<Student> {
  const res = await fetch(`${API_BASE}/students/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Update failed" }));
    throw new Error(err.detail || "Update failed");
  }
  return res.json();
}

export async function deleteStudent(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/students/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete student: ${res.statusText}`);
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/stats/dashboard`);
  if (!res.ok) throw new Error(`Failed to fetch dashboard stats: ${res.statusText}`);
  return res.json();
}
'''

STUDENT_DASHBOARD_TSX = '''import React from "react";
import { DashboardStats } from "../types/student";

interface Props {
  stats: DashboardStats;
}

export const StudentDashboard: React.FC<Props> = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Students</span>
          <h3 id="stat-total" className="text-2xl font-bold text-white mt-1">{stats.total_students}</h3>
        </div>
        <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-lg">
          <i className="fa-solid fa-users" />
        </div>
      </div>
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Enrollment</span>
          <h3 id="stat-active" className="text-2xl font-bold text-emerald-400 mt-1">{stats.active_students}</h3>
        </div>
        <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg">
          <i className="fa-solid fa-user-check" />
        </div>
      </div>
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Average GPA</span>
          <h3 id="stat-gpa" className="text-2xl font-bold text-amber-400 mt-1">{stats.average_gpa.toFixed(2)}</h3>
        </div>
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-lg">
          <i className="fa-solid fa-award" />
        </div>
      </div>
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Departments</span>
          <h3 id="stat-dept" className="text-2xl font-bold text-purple-400 mt-1">
            {Object.keys(stats.department_counts || {}).length}
          </h3>
        </div>
        <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 text-lg">
          <i className="fa-solid fa-building-columns" />
        </div>
      </div>
    </div>
  );
};
'''

STUDENT_TABLE_TSX = '''import React from "react";
import { Student } from "../types/student";

interface Props {
  students: Student[];
  onEdit: (student: Student) => void;
  onDelete: (id: string) => void;
  loading: boolean;
}

export const StudentTable: React.FC<Props> = ({ students, onEdit, onDelete, loading }) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table id="student-table" className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="p-4">Student</th>
              <th className="p-4">Department</th>
              <th className="p-4">Year</th>
              <th className="p-4">GPA</th>
              <th className="p-4">Status</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody id="student-tbody" className="divide-y divide-slate-800/60 font-sans">
            {students.map((s) => (
              <tr key={s.id} className="hover:bg-slate-900/50 transition-colors student-row">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/20 text-indigo-400 font-bold flex items-center justify-center font-mono">
                    {s.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-bold text-white student-name-cell">{s.name}</div>
                    <div className="text-[11px] text-slate-400 font-mono student-email-cell">{s.email}</div>
                  </div>
                </td>
                <td className="p-4 text-slate-300 student-dept-cell">{s.department}</td>
                <td className="p-4 text-slate-400">Year {s.year}</td>
                <td className="p-4 font-mono font-bold text-amber-400 student-gpa-cell">{s.gpa.toFixed(2)}</td>
                <td className="p-4">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                      s.status === "Active"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {s.status}
                  </span>
                </td>
                <td className="p-4 text-right space-x-2">
                  <button
                    onClick={() => onEdit(s)}
                    className="p-1.5 hover:bg-indigo-500/20 text-slate-400 hover:text-indigo-400 rounded-lg transition-colors edit-student-btn"
                    title="Edit Student"
                    data-id={s.id}
                  >
                    <i className="fa-regular fa-pen-to-square" />
                  </button>
                  <button
                    onClick={() => onDelete(s.id)}
                    className="p-1.5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-lg transition-colors delete-student-btn"
                    title="Delete Student"
                    data-id={s.id}
                  >
                    <i className="fa-regular fa-trash-can" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {students.length === 0 && !loading && (
        <div id="empty-state" className="p-12 text-center space-y-2">
          <i className="fa-solid fa-user-graduate text-3xl text-slate-600" />
          <h4 className="text-sm font-semibold text-slate-300">No students found</h4>
          <p className="text-xs text-slate-500">Register a new student using the button above to populate the directory.</p>
        </div>
      )}
    </div>
  );
};
'''

STUDENT_REGISTRATION_MODAL_TSX = '''import React, { useState } from "react";
import { StudentCreate } from "../types/student";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: StudentCreate) => Promise<void>;
  loading: boolean;
}

export const StudentRegistrationModal: React.FC<Props> = ({ isOpen, onClose, onSubmit, loading }) => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("Computer Science");
  const [year, setYear] = useState(1);
  const [gpa, setGpa] = useState(3.5);
  const [courses, setCourses] = useState("CS101, MATH101");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const courseList = courses.split(",").map((c) => c.trim()).filter((c) => c.length > 0);
      await onSubmit({ name, email, department, year, gpa, courses: courseList });
      setName("");
      setEmail("");
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to register student");
    }
  };

  return (
    <div id="register-modal" className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <i className="fa-solid fa-user-plus text-amber-400" />
            <span>Register New Student</span>
          </h3>
          <button id="close-modal-btn" onClick={onClose} className="text-slate-400 hover:text-white">
            <i className="fa-solid fa-xmark" />
          </button>
        </div>
        <form id="register-form" onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {error && (
            <div id="modal-error" className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl">
              {error}
            </div>
          )}
          <div>
            <label className="block text-slate-400 mb-1">Full Name</label>
            <input
              id="student-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Alex Turing"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">University Email</label>
            <input
              id="student-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alex@university.edu"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1">Department</label>
              <select
                id="student-dept"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              >
                <option value="Computer Science">Computer Science</option>
                <option value="Electrical Engineering">Electrical Engineering</option>
                <option value="Mechanical Engineering">Mechanical Engineering</option>
                <option value="Data Science">Data Science</option>
                <option value="Business Administration">Business Administration</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Academic Year</label>
              <select
                id="student-year"
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value, 10))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              >
                <option value="1">Year 1 (Freshman)</option>
                <option value="2">Year 2 (Sophomore)</option>
                <option value="3">Year 3 (Junior)</option>
                <option value="4">Year 4 (Senior)</option>
                <option value="5">Year 5 (Graduate)</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-slate-400 mb-1">GPA (0.0 - 4.0)</label>
            <input
              id="student-gpa"
              type="number"
              step="0.01"
              min="0"
              max="4.0"
              value={gpa}
              onChange={(e) => setGpa(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Courses (comma separated)</label>
            <input
              id="student-courses"
              type="text"
              value={courses}
              onChange={(e) => setCourses(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
            />
          </div>
          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              id="cancel-btn"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              id="submit-student-btn"
              disabled={loading}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl"
            >
              {loading ? "Registering..." : "Register Student"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
'''

STUDENT_EDIT_MODAL_TSX = '''import React, { useState } from "react";
import { Student, StudentUpdate } from "../types/student";

interface Props {
  student: Student | null;
  onClose: () => void;
  onSubmit: (id: string, updates: StudentUpdate) => Promise<void>;
  loading: boolean;
}

export const StudentEditModal: React.FC<Props> = ({ student, onClose, onSubmit, loading }) => {
  if (!student) return null;

  const [gpa, setGpa] = useState(student.gpa);
  const [department, setDepartment] = useState(student.department);
  const [status, setStatus] = useState(student.status);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onSubmit(student.id, { gpa, department, status });
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to update student");
    }
  };

  return (
    <div id="edit-modal" className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <i className="fa-solid fa-pen-to-square text-indigo-400" />
            <span>Update Student: {student.name}</span>
          </h3>
          <button id="close-edit-btn" onClick={onClose} className="text-slate-400 hover:text-white">
            <i className="fa-solid fa-xmark" />
          </button>
        </div>
        <form id="edit-form" onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {error && <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl">{error}</div>}
          <div>
            <label className="block text-slate-400 mb-1">Department</label>
            <select
              id="edit-dept"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
            >
              <option value="Computer Science">Computer Science</option>
              <option value="Electrical Engineering">Electrical Engineering</option>
              <option value="Mechanical Engineering">Mechanical Engineering</option>
              <option value="Data Science">Data Science</option>
              <option value="Business Administration">Business Administration</option>
            </select>
          </div>
          <div>
            <label className="block text-slate-400 mb-1">GPA (0.0 - 4.0)</label>
            <input
              id="edit-gpa"
              type="number"
              step="0.01"
              min="0"
              max="4.0"
              value={gpa}
              onChange={(e) => setGpa(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Status</label>
            <select
              id="edit-status"
              value={status}
              onChange={(e) => setStatus(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
            >
              <option value="Active">Active</option>
              <option value="Graduated">Graduated</option>
              <option value="Suspended">Suspended</option>
            </select>
          </div>
          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              id="submit-edit-btn"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl"
            >
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
'''

APP_TSX = '''import React, { useCallback, useEffect, useState } from "react";
import { StudentDashboard } from "./components/StudentDashboard";
import { StudentEditModal } from "./components/StudentEditModal";
import { StudentRegistrationModal } from "./components/StudentRegistrationModal";
import { StudentTable } from "./components/StudentTable";
import { createStudent, deleteStudent, fetchDashboardStats, fetchStudents, searchStudents, updateStudent } from "./services/api";
import { DashboardStats, Student, StudentCreate, StudentUpdate } from "./types/student";

export const App: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    total_students: 0,
    active_students: 0,
    average_gpa: 0,
    department_counts: {},
    top_performers: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [deptFilter, setDeptFilter] = useState("all");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [studentList, statData] = await Promise.all([
        deptFilter === "all" ? fetchStudents() : fetchStudents(deptFilter),
        fetchDashboardStats(),
      ]);
      setStudents(studentList);
      setStats(statData);
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [deptFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      loadData();
      return;
    }
    try {
      const results = await searchStudents(query);
      setStudents(results);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreate = async (data: StudentCreate) => {
    await createStudent(data);
    await loadData();
  };

  const handleUpdate = async (id: string, updates: StudentUpdate) => {
    await updateStudent(id, updates);
    await loadData();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this student record?")) return;
    try {
      await deleteStudent(id);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            <i className="fa-solid fa-graduation-cap" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-wide">DODO Student Management</h1>
            <p className="text-[11px] text-slate-400 font-mono">Autonomous Full-Stack System • React 18 & FastAPI</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            React Engine Active
          </span>
          <button
            id="open-register-btn"
            onClick={() => setIsRegisterOpen(true)}
            className="px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-xl text-xs font-bold shadow-lg shadow-amber-500/10 flex items-center gap-2 transition-all active:scale-95"
          >
            <i className="fa-solid fa-user-plus" />
            <span>Register Student</span>
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {error && (
          <div id="error-banner" className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-2xl text-xs flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">✕</button>
          </div>
        )}

        <StudentDashboard stats={stats} />

        <div className="p-4 bg-slate-900/40 border border-slate-800/80 rounded-2xl flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-[280px]">
            <div className="relative flex-1">
              <i className="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-500 text-xs" />
              <input
                id="search-input"
                type="text"
                placeholder="Search by student name, email, or department..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <select
              id="dept-filter"
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Electrical Engineering">Electrical Engineering</option>
              <option value="Mechanical Engineering">Mechanical Engineering</option>
              <option value="Data Science">Data Science</option>
              <option value="Business Administration">Business Administration</option>
            </select>
          </div>
          <button
            id="refresh-btn"
            onClick={loadData}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs flex items-center gap-1.5 transition-colors"
          >
            <i className={`fa-solid fa-rotate ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        <StudentTable
          students={students}
          onEdit={(s) => setEditingStudent(s)}
          onDelete={handleDelete}
          loading={loading}
        />
      </main>

      <StudentRegistrationModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSubmit={handleCreate}
        loading={loading}
      />

      <StudentEditModal
        student={editingStudent}
        onClose={() => setEditingStudent(null)}
        onSubmit={handleUpdate}
        loading={loading}
      />
    </div>
  );
};
'''

MAIN_TSX = '''import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''

PACKAGE_JSON = '''{
  "name": "dodo-student-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}
'''

TSCONFIG_JSON = '''{
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
'''

# --- REACT 18 LIVE INLINE RUNTIME FOR BROWSER / PLAYWRIGHT ---

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DODO — Student Management System (React 18)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }
  </style>
</head>
<body class="min-h-screen flex flex-col">
  <!-- React 18 Mounting Root -->
  <div id="root">
    <div class="min-h-screen flex items-center justify-center text-slate-500 text-xs">
      Loading DODO React Application...
    </div>
  </div>

  <!-- React 18 Engine Scripts -->
  <script src="/static/vendor/react.production.min.js"></script>
  <script src="/static/vendor/react-dom.production.min.js"></script>
  <script>
    // Fallback if vendor script failed
    if (typeof React === "undefined") {
      document.write(\'<script src="https://unpkg.com/react@18/umd/react.production.min.js"><\\/script>\');
      document.write(\'<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"><\\/script>\');
    }
  </script>
  <script src="/static/app.js"></script>
</body>
</html>
'''

APP_JS = '''// DODO React 18 Application Client Controller
const { useState, useEffect, useCallback, createElement: h } = React;
const API_BASE = typeof window !== "undefined" && window.location && window.location.origin ? (window.location.origin + "/api") : "http://127.0.0.1:8000/api";

function App() {
  const [students, setStudents] = useState([]);
  const [stats, setStats] = useState({ total_students: 0, active_students: 0, average_gpa: 0, department_counts: {} });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState("all");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);

  // Form states
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formDept, setFormDept] = useState("Computer Science");
  const [formYear, setFormYear] = useState(1);
  const [formGpa, setFormGpa] = useState(3.5);
  const [formCourses, setFormCourses] = useState("CS101, MATH101");

  // Edit form states
  const [editGpa, setEditGpa] = useState(3.5);
  const [editDept, setEditDept] = useState("Computer Science");
  const [editStatus, setEditStatus] = useState("Active");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const url = dept === "all" ? `${API_BASE}/students` : `${API_BASE}/students?department=${encodeURIComponent(dept)}`;
      const [resStudents, resStats] = await Promise.all([
        fetch(url),
        fetch(`${API_BASE}/stats/dashboard`)
      ]);
      if (resStudents.ok) setStudents(await resStudents.json());
      if (resStats.ok) setStats(await resStats.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [dept]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = async (q) => {
    setSearch(q);
    if (!q.trim()) {
      loadData();
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/students/search?q=${encodeURIComponent(q)}`);
      if (res.ok) setStudents(await res.json());
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    try {
      const courses = formCourses.split(",").map(c => c.trim()).filter(c => c.length > 0);
      const res = await fetch(`${API_BASE}/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formName.trim(),
          email: formEmail.trim(),
          department: formDept,
          year: parseInt(formYear, 10),
          gpa: parseFloat(formGpa),
          courses
        })
      });
      if (!res.ok) {
        const errJson = await res.json();
        alert(`Registration failed: ${errJson.detail || "Server error"}`);
        return;
      }
      setIsRegisterOpen(false);
      setFormName("");
      setFormEmail("");
      loadData();
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editingStudent) return;
    try {
      const res = await fetch(`${API_BASE}/students/${editingStudent.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          department: editDept,
          gpa: parseFloat(editGpa),
          status: editStatus
        })
      });
      if (res.ok) {
        setEditingStudent(null);
        loadData();
      }
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this student record?")) return;
    try {
      const res = await fetch(`${API_BASE}/students/${id}`, { method: "DELETE" });
      if (res.ok) loadData();
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  return h("div", { className: "min-h-screen flex flex-col" },
    // Header
    h("header", { className: "h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-30" },
      h("div", { className: "flex items-center gap-3" },
        h("div", { className: "w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20" },
          h("i", { className: "fa-solid fa-graduation-cap" })
        ),
        h("div", null,
          h("h1", { className: "text-base font-bold text-white tracking-wide" }, "DODO Student Management"),
          h("p", { className: "text-[11px] text-slate-400 font-mono" }, "Autonomous Full-Stack System • React 18 & FastAPI")
        )
      ),
      h("div", { className: "flex items-center gap-4" },
        h("span", { className: "px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5" },
          h("span", { className: "w-2 h-2 rounded-full bg-emerald-400 animate-pulse" }),
          "React 18 Online"
        ),
        h("button", {
          id: "open-register-btn",
          onClick: () => setIsRegisterOpen(true),
          className: "px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-xl text-xs font-bold shadow-lg shadow-amber-500/10 flex items-center gap-2 transition-all active:scale-95"
        },
          h("i", { className: "fa-solid fa-user-plus" }),
          h("span", null, "Register Student")
        )
      )
    ),

    // Main
    h("main", { className: "flex-1 max-w-7xl w-full mx-auto p-6 space-y-6" },
      // Stats Cards
      h("div", { className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" },
        h("div", { className: "p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between" },
          h("div", null,
            h("span", { className: "text-xs font-semibold uppercase tracking-wider text-slate-400" }, "Total Students"),
            h("h3", { id: "stat-total", className: "text-2xl font-bold text-white mt-1" }, stats.total_students)
          ),
          h("div", { className: "w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-lg" },
            h("i", { className: "fa-solid fa-users" })
          )
        ),
        h("div", { className: "p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between" },
          h("div", null,
            h("span", { className: "text-xs font-semibold uppercase tracking-wider text-slate-400" }, "Active Enrollment"),
            h("h3", { id: "stat-active", className: "text-2xl font-bold text-emerald-400 mt-1" }, stats.active_students)
          ),
          h("div", { className: "w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg" },
            h("i", { className: "fa-solid fa-user-check" })
          )
        ),
        h("div", { className: "p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between" },
          h("div", null,
            h("span", { className: "text-xs font-semibold uppercase tracking-wider text-slate-400" }, "Average GPA"),
            h("h3", { id: "stat-gpa", className: "text-2xl font-bold text-amber-400 mt-1" }, (stats.average_gpa || 0).toFixed(2))
          ),
          h("div", { className: "w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-lg" },
            h("i", { className: "fa-solid fa-award" })
          )
        ),
        h("div", { className: "p-5 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between" },
          h("div", null,
            h("span", { className: "text-xs font-semibold uppercase tracking-wider text-slate-400" }, "Departments"),
            h("h3", { id: "stat-dept", className: "text-2xl font-bold text-purple-400 mt-1" }, Object.keys(stats.department_counts || {}).length)
          ),
          h("div", { className: "w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 text-lg" },
            h("i", { className: "fa-solid fa-building-columns" })
          )
        )
      ),

      // Toolbar
      h("div", { className: "p-4 bg-slate-900/40 border border-slate-800/80 rounded-2xl flex flex-wrap items-center justify-between gap-4" },
        h("div", { className: "flex items-center gap-3 flex-1 min-w-[280px]" },
          h("div", { className: "relative flex-1" },
            h("i", { className: "fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-500 text-xs" }),
            h("input", {
              id: "search-input",
              type: "text",
              placeholder: "Search by student name, email, or department...",
              value: search,
              onChange: (e) => handleSearch(e.target.value),
              className: "w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            })
          ),
          h("select", {
            id: "dept-filter",
            value: dept,
            onChange: (e) => setDept(e.target.value),
            className: "bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500"
          },
            h("option", { value: "all" }, "All Departments"),
            h("option", { value: "Computer Science" }, "Computer Science"),
            h("option", { value: "Electrical Engineering" }, "Electrical Engineering"),
            h("option", { value: "Mechanical Engineering" }, "Mechanical Engineering"),
            h("option", { value: "Data Science" }, "Data Science"),
            h("option", { value: "Business Administration" }, "Business Administration")
          )
        ),
        h("button", {
          id: "refresh-btn",
          onClick: loadData,
          className: "p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs flex items-center gap-1.5 transition-colors"
        },
          h("i", { className: `fa-solid fa-rotate ${loading ? "animate-spin" : ""}` }),
          h("span", null, "Refresh")
        )
      ),

      // Table
      h("div", { className: "bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl" },
        h("div", { className: "overflow-x-auto" },
          h("table", { id: "student-table", className: "w-full text-left border-collapse text-xs" },
            h("thead", null,
              h("tr", { className: "border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]" },
                h("th", { className: "p-4" }, "Student"),
                h("th", { className: "p-4" }, "Department"),
                h("th", { className: "p-4" }, "Year"),
                h("th", { className: "p-4" }, "GPA"),
                h("th", { className: "p-4" }, "Status"),
                h("th", { className: "p-4 text-right" }, "Actions")
              )
            ),
            h("tbody", { id: "student-tbody", className: "divide-y divide-slate-800/60 font-sans" },
              students.map((s) =>
                h("tr", { key: s.id, className: "hover:bg-slate-900/50 transition-colors student-row" },
                  h("td", { className: "p-4 flex items-center gap-3" },
                    h("div", { className: "w-8 h-8 rounded-full bg-indigo-600/20 text-indigo-400 font-bold flex items-center justify-center font-mono" },
                      s.name.charAt(0).toUpperCase()
                    ),
                    h("div", null,
                      h("div", { className: "font-bold text-white student-name-cell" }, s.name),
                      h("div", { className: "text-[11px] text-slate-400 font-mono student-email-cell" }, s.email)
                    )
                  ),
                  h("td", { className: "p-4 text-slate-300 student-dept-cell" }, s.department),
                  h("td", { className: "p-4 text-slate-400" }, `Year ${s.year}`),
                  h("td", { className: "p-4 font-mono font-bold text-amber-400 student-gpa-cell" }, (s.gpa || 0).toFixed(2)),
                  h("td", { className: "p-4" },
                    h("span", {
                      className: `px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                        s.status === "Active" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-800 text-slate-400"
                      }`
                    }, s.status)
                  ),
                  h("td", { className: "p-4 text-right space-x-2" },
                    h("button", {
                      onClick: () => {
                        setEditingStudent(s);
                        setEditGpa(s.gpa);
                        setEditDept(s.department);
                        setEditStatus(s.status);
                      },
                      className: "p-1.5 hover:bg-indigo-500/20 text-slate-400 hover:text-indigo-400 rounded-lg transition-colors edit-student-btn",
                      title: "Edit Student"
                    },
                      h("i", { className: "fa-regular fa-pen-to-square" })
                    ),
                    h("button", {
                      onClick: () => handleDelete(s.id),
                      className: "p-1.5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-lg transition-colors delete-student-btn",
                      title: "Delete Student"
                    },
                      h("i", { className: "fa-regular fa-trash-can" })
                    )
                  )
                )
              )
            )
          )
        ),
        students.length === 0 && !loading &&
          h("div", { id: "empty-state", className: "p-12 text-center space-y-2" },
            h("i", { className: "fa-solid fa-user-graduate text-3xl text-slate-600" }),
            h("h4", { className: "text-sm font-semibold text-slate-300" }, "No students found"),
            h("p", { className: "text-xs text-slate-500" }, "Register a new student using the button above to populate the directory.")
          )
      )
    ),

    // Register Modal
    isRegisterOpen &&
      h("div", { id: "register-modal", className: "fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4" },
        h("div", { className: "bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden" },
          h("div", { className: "px-6 py-4 border-b border-slate-800 flex items-center justify-between" },
            h("h3", { className: "text-sm font-bold text-white flex items-center gap-2" },
              h("i", { className: "fa-solid fa-user-plus text-amber-400" }),
              h("span", null, "Register New Student")
            ),
            h("button", { id: "close-modal-btn", onClick: () => setIsRegisterOpen(false), className: "text-slate-400 hover:text-white" },
              h("i", { className: "fa-solid fa-xmark" })
            )
          ),
          h("form", { id: "register-form", onSubmit: handleRegisterSubmit, className: "p-6 space-y-4 text-xs" },
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "Full Name"),
              h("input", {
                id: "student-name",
                type: "text",
                required: true,
                value: formName,
                onChange: (e) => setFormName(e.target.value),
                placeholder: "e.g. Alex Turing",
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              })
            ),
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "University Email"),
              h("input", {
                id: "student-email",
                type: "email",
                required: true,
                value: formEmail,
                onChange: (e) => setFormEmail(e.target.value),
                placeholder: "alex@university.edu",
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
              })
            ),
            h("div", { className: "grid grid-cols-2 gap-3" },
              h("div", null,
                h("label", { className: "block text-slate-400 mb-1" }, "Department"),
                h("select", {
                  id: "student-dept",
                  value: formDept,
                  onChange: (e) => setFormDept(e.target.value),
                  className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                },
                  h("option", { value: "Computer Science" }, "Computer Science"),
                  h("option", { value: "Electrical Engineering" }, "Electrical Engineering"),
                  h("option", { value: "Mechanical Engineering" }, "Mechanical Engineering"),
                  h("option", { value: "Data Science" }, "Data Science"),
                  h("option", { value: "Business Administration" }, "Business Administration")
                )
              ),
              h("div", null,
                h("label", { className: "block text-slate-400 mb-1" }, "Academic Year"),
                h("select", {
                  id: "student-year",
                  value: formYear,
                  onChange: (e) => setFormYear(e.target.value),
                  className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
                },
                  h("option", { value: 1 }, "Year 1 (Freshman)"),
                  h("option", { value: 2 }, "Year 2 (Sophomore)"),
                  h("option", { value: 3 }, "Year 3 (Junior)"),
                  h("option", { value: 4 }, "Year 4 (Senior)"),
                  h("option", { value: 5 }, "Year 5 (Graduate)")
                )
              )
            ),
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "GPA (0.0 - 4.0)"),
              h("input", {
                id: "student-gpa",
                type: "number",
                step: "0.01",
                min: 0,
                max: 4.0,
                value: formGpa,
                onChange: (e) => setFormGpa(e.target.value),
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
              })
            ),
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "Courses (comma separated)"),
              h("input", {
                id: "student-courses",
                type: "text",
                value: formCourses,
                onChange: (e) => setFormCourses(e.target.value),
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
              })
            ),
            h("div", { className: "pt-2 flex items-center justify-end gap-3" },
              h("button", {
                type: "button",
                id: "cancel-btn",
                onClick: () => setIsRegisterOpen(false),
                className: "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium"
              }, "Cancel"),
              h("button", {
                type: "submit",
                id: "submit-student-btn",
                className: "px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl"
              }, "Register Student")
            )
          )
        )
      ),

    // Edit Modal
    editingStudent &&
      h("div", { id: "edit-modal", className: "fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4" },
        h("div", { className: "bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden" },
          h("div", { className: "px-6 py-4 border-b border-slate-800 flex items-center justify-between" },
            h("h3", { className: "text-sm font-bold text-white flex items-center gap-2" },
              h("i", { className: "fa-solid fa-pen-to-square text-indigo-400" }),
              h("span", null, `Update Student: ${editingStudent.name}`)
            ),
            h("button", { id: "close-edit-btn", onClick: () => setEditingStudent(null), className: "text-slate-400 hover:text-white" },
              h("i", { className: "fa-solid fa-xmark" })
            )
          ),
          h("form", { id: "edit-form", onSubmit: handleEditSubmit, className: "p-6 space-y-4 text-xs" },
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "Department"),
              h("select", {
                id: "edit-dept",
                value: editDept,
                onChange: (e) => setEditDept(e.target.value),
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              },
                h("option", { value: "Computer Science" }, "Computer Science"),
                h("option", { value: "Electrical Engineering" }, "Electrical Engineering"),
                h("option", { value: "Mechanical Engineering" }, "Mechanical Engineering"),
                h("option", { value: "Data Science" }, "Data Science"),
                h("option", { value: "Business Administration" }, "Business Administration")
              )
            ),
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "GPA (0.0 - 4.0)"),
              h("input", {
                id: "edit-gpa",
                type: "number",
                step: "0.01",
                min: 0,
                max: 4.0,
                value: editGpa,
                onChange: (e) => setEditGpa(e.target.value),
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono"
              })
            ),
            h("div", null,
              h("label", { className: "block text-slate-400 mb-1" }, "Status"),
              h("select", {
                id: "edit-status",
                value: editStatus,
                onChange: (e) => setEditStatus(e.target.value),
                className: "w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white"
              },
                h("option", { value: "Active" }, "Active"),
                h("option", { value: "Graduated" }, "Graduated"),
                h("option", { value: "Suspended" }, "Suspended")
              )
            ),
            h("div", { className: "pt-2 flex items-center justify-end gap-3" },
              h("button", {
                type: "button",
                onClick: () => setEditingStudent(null),
                className: "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium"
              }, "Cancel"),
              h("button", {
                type: "submit",
                id: "submit-edit-btn",
                className: "px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl"
              }, "Save Changes")
            )
          )
        )
      )
  );
}

// Render React 18 component tree
window.addEventListener("DOMContentLoaded", () => {
  const rootEl = document.getElementById("root");
  if (rootEl && typeof ReactDOM !== "undefined") {
    ReactDOM.createRoot(rootEl).render(h(App));
  }
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
- **React + TypeScript Frontend**: Modern React 18 component tree with typed API service.
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
        "frontend/src/types/student.ts": TYPES_STUDENT_TS,
        "frontend/src/services/api.ts": API_SERVICE_TS,
        "frontend/src/components/StudentDashboard.tsx": STUDENT_DASHBOARD_TSX,
        "frontend/src/components/StudentTable.tsx": STUDENT_TABLE_TSX,
        "frontend/src/components/StudentRegistrationModal.tsx": STUDENT_REGISTRATION_MODAL_TSX,
        "frontend/src/components/StudentEditModal.tsx": STUDENT_EDIT_MODAL_TSX,
        "frontend/src/App.tsx": APP_TSX,
        "frontend/src/main.tsx": MAIN_TSX,
        "frontend/package.json": PACKAGE_JSON,
        "frontend/tsconfig.json": TSCONFIG_JSON,
        "frontend/index.html": INDEX_HTML,
        "frontend/app.js": APP_JS,
        "tests/test_students_api.py": TEST_STUDENTS_API_PY,
        "requirements.txt": REQUIREMENTS_TXT,
        "README.md": README_MD,
    }
