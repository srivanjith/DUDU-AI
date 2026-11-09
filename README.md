# 🦅 DODO

> **Your AI. Your Machine. Your Rules.**  
> Autonomous AI Agent and AI Software Development Environment.  
> Git: [https://github.com/srivanjith/DUDU-AI.git](https://github.com/srivanjith/DUDU-AI.git)

---

## What is DODO?

DODO is an independent, local-first autonomous software development platform built around local open-weight models. It combines conversational intelligence with stateful autonomous software engineering — creating workspace files, modifying codebases, executing terminal commands via a secure Local Agent, starting servers, running unit tests, and verifying live web applications via Playwright browser automation with persistent long-term memory across restarts.

DODO is completely independent from proprietary cloud AI APIs (zero dependencies on Claude, OpenAI, or Antigravity APIs).

---

## Operating Modes

- **Mode A: AI Assistant** — Conversational intelligence, code explanations, document analysis, and hardware-aware open-weight model routing.
- **Mode B: Autonomous Dev** — Stateful execution cycle: `PLAN → EXECUTE → OBSERVE → EVALUATE → FIX → VERIFY → DELIVER`. Deconstructs user objectives into concrete multi-file development, server startup, and test suites.
- **Mode C: Terminal & Processes** — Controlled terminal execution, workspace filesystem boundary enforcement, process lifecycle monitoring, and streaming terminal output via xterm.js.
- **Browser Verification** — Playwright Chromium automation: DOM hierarchy inspection, element interaction (click, fill, select, scroll), full-page screenshots, and real-time JavaScript console and network error detection.
- **Memory Center** — Long-term persistent memory across 5 categories (`project`, `task_experience`, `preference`, `knowledge`, `conversation`). Bounded token budgets and automatic secret filtering.

---

## Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Monaco Editor, Server-Sent Events (SSE) & WebSockets.
- **Backend**: Python 3.14, FastAPI, Pydantic, PyMongo with high-performance JSON fallback adapter (`data/local_db_store.json`).
- **Database**: MongoDB (`dodo_db`) with safe migration CLI (`scripts/migrate_to_mongodb.py`). Accurately reports `healthy_fallback` when running without an external MongoDB server.
- **Browser Automation**: Playwright async API (Headless Chromium, screenshot engine, console/network telemetry).
- **Inference Engine**: Ollama daemon (v0.40.15) with `qwen2.5-coder:1.5b` running on NVIDIA GeForce RTX 3050 Laptop GPU (116+ tokens/sec).

---

## Getting Started on Windows

### 1. Launch Ollama Service Daemon
```powershell
& "C:\Users\Asus\AppData\Local\Programs\Ollama\ollama.exe" serve
```

### 2. Launch the Local Agent (Port 8001)
```powershell
cd D:\DODO
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001
```

### 3. Launch the FastAPI Backend (Port 8000)
```powershell
cd D:\DODO
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4. Launch the Web Frontend (Port 3000)
```powershell
cd D:\DODO\frontend
npm run start
# Or for development with live reload:
# npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the DODO developer workspace.

---

## Verification & Diagnostics

Query the unified multi-subsystem diagnostics endpoint:
```powershell
Invoke-RestMethod http://localhost:8000/api/diagnostics | ConvertTo-Json -Depth 4
```

To run the safe database migration preview:
```powershell
$env:PYTHONPATH = "D:\DODO"; python scripts/migrate_to_mongodb.py
```

To run the local model performance benchmark:
```powershell
$env:PYTHONPATH = "D:\DODO"; python scripts/benchmark_ollama.py
```

---

## Documentation
- [Architecture Blueprint](docs/ARCHITECTURE.md)
- [Database Schema & Migration](docs/DATABASE.md)
- [REST & WebSocket API Reference](docs/API.md)
- [Security & Sandbox Boundaries](docs/SECURITY.md)
- [Performance Benchmarks & Sizing](docs/PERFORMANCE.md)
- [Development Guide](docs/DEVELOPMENT.md)
