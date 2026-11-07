# DODO REST and Real-Time API Reference

**Base URL:** `http://localhost:8000`  
**Interactive Swagger Docs:** `http://localhost:8000/docs`

---

## 1. Core Endpoints

### System Health
- **`GET /health`**
  - Returns operational status of MongoDB, Ollama inference engine, Local Agent, and host OS platform metrics.

### Mode A: Conversations
- **`GET /conversations`**: List recent conversations.
- **`POST /conversations`**: Create a new conversation session.
- **`GET /conversations/{id}`**: Retrieve conversation metadata and messages.
- **`DELETE /conversations/{id}`**: Delete conversation and associated messages.
- **`POST /conversations/{id}/messages`**: Send message and stream AI response tokens via Server-Sent Events (`text/event-stream`).

### Mode B: Autonomous Agent Tasks
- **`GET /tasks`**: List recent autonomous tasks.
- **`POST /tasks`**: Launch a new autonomous objective.
- **`GET /tasks/{id}`**: Get task plan, step statuses, and verification report.
- **`POST /tasks/{id}/cancel`**: Cancel in-progress autonomous run.
- **`GET /tasks/{id}/stream`**: Subscribe to live SSE stream of step-by-step agent lifecycle events.

### Mode C: Terminal, Workspace & Browser
- **`GET /workspace/files`**: List files within authorized workspace.
- **`GET /workspace/file?path={path}`**: Read file content with line range slicing.
- **`POST /workspace/file`**: Write/save file content.
- **`POST /workspace/edit`**: Apply search-and-replace edit with unified diff generation.
- **`POST /terminal/execute`**: Execute command with security sanitization.
- **`POST /browser/inspect`**: Headless Playwright session inspection and screenshot generation.
- **`POST /browser/screenshot`**: Capture full-page screenshot of target URL.

### Models & Memory
- **`GET /models`**: List installed Ollama models and active role mappings.
- **`POST /models/roles`**: Configure model assignment for a role (`general`, `coding`, `reasoning`, `lightweight`, `embedding`).
- **`GET /memory`**: Retrieve semantic memories matching a search query.
- **`POST /memory`**: Create persistent memory fact.
- **`DELETE /memory/{id}`**: Remove memory entry.

---

## 2. WebSocket Telemetry Bus
- **`ws://localhost:8000/ws`**: Real-time bi-directional agent communication bus for terminal streaming and UI status updates.

