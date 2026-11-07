# DODO Local Development Guide

## 1. Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Ollama (Optional for local inference; native fallback active if offline)
- MongoDB Community Server (Optional; standalone persistence fallback active if offline)

### Setup Virtual Environment & Backend
```powershell
# Virtual Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Dependencies
pip install -r requirements.txt

# Run Backend
$env:PYTHONPATH = "D:\DODO"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Setup & Run Local Agent
```powershell
python -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001
```

### Setup & Run Frontend
```powershell
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 2. Running Automated Tests
```powershell
$env:PYTHONPATH = "D:\DODO"
pytest backend/tests/test_backend.py -v
```

