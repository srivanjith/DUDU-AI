"""
DODO ASGI Application Entry Point (app.main:app).
Re-exports the core FastAPI application from backend.main for standard Uvicorn invocation.
Allows running:
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    or
    python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"""
import sys
from pathlib import Path

# Ensure project root (D:\DODO) is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Import the actual FastAPI instance
from backend.main import app

__all__ = ["app"]

