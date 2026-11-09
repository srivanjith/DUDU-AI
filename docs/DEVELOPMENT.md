# 💻 DODO Local Development Guide

## 1. Prerequisites
- **Python**: 3.11+ (verified on 3.14.6 x64 Windows 11)
- **Node.js**: 18+ and npm
- **Ollama**: v0.40.15 with `qwen2.5-coder:1.5b`
- **Playwright Chromium**: installed via `python -m playwright install chromium`

---

## 2. Windows Startup Sequence

### Step 1: Start Ollama Daemon
```powershell
& "C:\Users\Asus\AppData\Local\Programs\Ollama\ollama.exe" serve
```

### Step 2: Start DODO Local Agent (Port 8001)
```powershell
cd D:\DODO
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001
```

### Step 3: Start DODO FastAPI Backend (Port 8000)
```powershell
cd D:\DODO
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Step 4: Start DODO Next.js Frontend (Port 3000)
```powershell
cd D:\DODO\frontend
npm run start
# For live development with hot reload:
# npm run dev
```

---

## 3. Automated Test Suites

### Run Phase 8 Performance & Reliability Suite:
```powershell
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m pytest backend/tests/test_phase8_performance_and_reliability.py -v
```

### Run Phase 7 Persistent Memory Suite:
```powershell
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m pytest backend/tests/test_phase7_persistent_memory.py -v
```

### Run Phase 6 Browser Automation Suite:
```powershell
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m pytest backend/tests/test_phase6_browser_automation.py -v
```

---

## 4. Diagnostics & Maintenance Utilities

### Query Unified Multi-Subsystem Diagnostics:
```powershell
Invoke-RestMethod http://localhost:8000/api/diagnostics | ConvertTo-Json -Depth 5
```

### Run Ollama Inference Benchmark:
```powershell
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" scripts/benchmark_ollama.py
```

### Safe Database Migration:
```powershell
# Preview (dry run):
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" scripts/migrate_to_mongodb.py

# Live non-destructive apply:
& ".\.venv\Scripts\python.exe" scripts/migrate_to_mongodb.py --apply
```
