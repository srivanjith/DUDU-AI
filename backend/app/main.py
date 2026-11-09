"""
DODO ASGI Application Entry Point for backend/app/main.py.
Re-exports the core FastAPI application from backend.main.
"""
import sys
from pathlib import Path

# Ensure project root (D:\DODO) is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Import the actual FastAPI instance
from backend.main import app

__all__ = ["app"]

