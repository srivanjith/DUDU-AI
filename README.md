# 🦅 DODO

> **Your AI. Your Machine. Your Rules.**  
> Autonomous AI Agent and AI Software Development Environment.

---

## What is DODO?

DODO is an independent, local-first autonomous development platform and conversational AI environment built around open-weight models. It combines conversational intelligence with stateful autonomous software engineering — creating files, modifying codebases, executing terminal commands, starting servers, running unit tests, and verifying live web applications via Playwright browser automation.

DODO is completely independent from proprietary AI APIs (No Claude, No Anthropic, No Antigravity API dependencies).

---

## Three Operating Modes

- **Mode A: AI Assistant** — Conversational intelligence, code explanations, document analysis, and hardware-aware open-weight model routing.
- **Mode B: Autonomous Developer** — Stateful execution cycle: `PLAN → EXECUTE → OBSERVE → EVALUATE → FIX → VERIFY → DELIVER`. Deconstructs user objectives into concrete multi-file development, server startup, and test suites.
- **Mode C: Computer & Browser Agent** — Controlled terminal execution, workspace filesystem boundary enforcement, and Playwright browser verification with visual screenshot capture and console error analysis.

---

## Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Monaco Editor, Server-Sent Events & WebSockets.
- **Backend**: Python 3.14, FastAPI, Pydantic, PyMongo with high-performance standalone persistence fallback.
- **Database**: MongoDB (`dodo_db`) with 15 specialized collections and performance indexing.
- **Browser Automation**: Playwright (Headless Chromium, screenshot engine, console diagnostics).
- **Inference**: Ollama client with dynamic open-weight model router (Qwen 2.5, DeepSeek R1, Llama 3.2).

---

## Getting Started

### 1. Launch the Backend
```powershell
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. Launch the Local Agent
```powershell
$env:PYTHONPATH = "D:\DODO"
& ".\.venv\Scripts\python.exe" -m uvicorn local_agent.main:app --host 127.0.0.1 --port 8001
```

### 3. Launch the Web Frontend
```powershell
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the DODO developer workspace.

---

## Documentation
- [Architecture Blueprint](docs/ARCHITECTURE.md)
- [Database Schema & Collections](docs/DATABASE.md)
- [REST & WebSocket API Reference](docs/API.md)
- [Security & Boundary Isolation](docs/SECURITY.md)
- [Performance & Hardware Sizing](docs/PERFORMANCE.md)
- [Development Guide](docs/DEVELOPMENT.md)

