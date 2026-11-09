# 🔌 DODO REST & WebSocket API Reference

Base URL: `http://localhost:8000`  
Interactive Swagger Documentation: `http://localhost:8000/docs`

---

## 1. System Health & Unified Diagnostics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Fast status check of core subsystems |
| `GET` | `/api/diagnostics` | Complete multi-subsystem diagnostic map (frontend, backend, database, ollama, local_agent, browser, memory, tasks) |

---

## 2. AI Chat & Streaming

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Streaming SSE endpoint for conversational AI with automatic memory capture and context injection |

---

## 3. Autonomous Agent Tasks

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/agent/tasks` | List all autonomous tasks |
| `POST` | `/api/agent/tasks` | Create and plan an autonomous task (`mode: developer`) |
| `GET` | `/api/agent/tasks/{task_id}` | Get task details, steps, and progress |
| `GET` | `/api/agent/tasks/{task_id}/execute` | SSE stream for real-time task execution |
| `POST` | `/api/agent/tasks/{task_id}/approve/{step_id}` | Approve sensitive gated step execution |
| `POST` | `/api/agent/tasks/{task_id}/cancel` | Cancel active task execution |

---

## 4. Persistent Memory (Phase 7)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/memory` | List memories with category, project, and keyword filters |
| `POST` | `/api/memory` | Create a validated, sanitized memory item |
| `GET` | `/api/memory/categories` | Counts of memories grouped by category |
| `GET` | `/api/memory/projects` | List of distinct project IDs with stored memories |
| `GET` | `/api/memory/{memory_id}` | Retrieve single memory item details |
| `PUT` | `/api/memory/{memory_id}` | Update memory content, importance, or tags |
| `DELETE` | `/api/memory/{memory_id}` | Delete a single memory item |
| `POST` | `/api/memory/search` | Multi-factor semantic retrieval with relevance scoring |
| `POST` | `/api/memory/summarize` | Condense and store conversation context |
| `DELETE` | `/api/memory/project/{project_id}` | Wipe all memories associated with a project |
| `DELETE` | `/api/memory/clear?confirm=true` | Destructive wipe of all memories across DODO |

---

## 5. Browser Automation (Phase 6)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/browser/status` | Check if Playwright Chromium instance is active |
| `POST` | `/api/browser/launch` | Launch isolated Chromium browser session |
| `POST` | `/api/browser/close` | Gracefully close browser and clean up resources |
| `POST` | `/api/browser/navigate` | Navigate to an authorized URL |
| `POST` | `/api/browser/interact` | Execute click, fill, select, or scroll actions |
| `GET` | `/api/browser/screenshot` | Capture base64 screenshot or save to workspace |
| `GET` | `/api/browser/diagnostics` | Retrieve intercepted console and network errors |
| `GET` | `/api/browser/dom` | Inspect structured DOM hierarchy |
| `GET` | `/api/browser/tabs` | List open tabs and active tab state |

---

## 6. Terminal & Local Agent (Phase 5)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/terminal/execute` | Execute approved command inside registered workspace |
| `GET` | `/api/terminal/status` | Check Local Agent connectivity on port 8001 |
| `GET` | `/api/terminal/history` | Auditable execution history log |
| `GET` | `/api/terminal/pending-approvals` | List commands awaiting explicit user confirmation |
| `POST` | `/api/terminal/approve/{exec_id}` | Approve or reject a pending command |
| `POST` | `/api/terminal/cancel/{exec_id}` | Terminate running process |

---

## 7. Model Router & Hardware

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/models` | List configured model roles |
| `GET` | `/api/models/status` | Hardware status, Ollama latency, and model recommendations |
| `POST` | `/api/models/roles` | Map model roles (`general`, `coding`, `reasoning`) |
