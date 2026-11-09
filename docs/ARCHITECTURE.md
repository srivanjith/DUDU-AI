# 🏛️ DODO Architecture Blueprint

**Tagline:** Your AI. Your Machine. Your Rules.  
**Product Category:** Autonomous AI Agent & Local AI Software Development Environment  
**Git Repository:** [https://github.com/srivanjith/DUDU-AI.git](https://github.com/srivanjith/DUDU-AI.git)

---

## 1. System Overview

DODO is an independent, local-first autonomous development platform and conversational AI assistant built without any reliance on proprietary APIs (Anthropic, Claude, Antigravity, or other hosted vendor locks).

The platform consists of four primary subsystems operating in synergy:
1. **DODO Web Application (`frontend/`)**: Modern responsive IDE & assistant UI built with Next.js, React, Tailwind CSS, Monaco Editor, Server-Sent Events, and WebSockets.
2. **DODO Backend (`backend/`)**: High-performance Python FastAPI service managing authentication, conversation persistence, hardware-aware model routing, stateful agent planning, unified diagnostics, and database operations.
3. **DODO Local Agent (`local_agent/`)**: Isolated local execution runtime that connects securely on port 8001, enforcing strict workspace path boundaries, sandboxed command execution, and Playwright-driven browser automation.
4. **Persistent Memory Engine (`backend/app/memory/`)**: Multi-category long-term memory engine with deduplication, conflict resolution, secret filtering, and multi-factor semantic retrieval.

```
                    ┌──────────────────────────────┐
                    │      DODO Web Frontend       │
                    │   Next.js / React / Monaco   │
                    │  Chat • Dev • Terminal • Web │
                    └──────────────┬───────────────┘
                                   │ HTTP / SSE / WS (Port 8000)
                                   ▼
                    ┌──────────────────────────────┐
                    │         DODO Backend         │
                    │       FastAPI Runtime        │
                    ├──────────────┬───────────────┤
                    │ Model Router │ Agent Engine  │
                    │ Tool Registry│ Memory Engine │
                    │ Diagnostics  │ Migration CLI │
                    └──────┬───────┴───────┬───────┘
                           │               │
            Token-Auth RPC │               │ PyMongo / mongomock
                           ▼               ▼
        ┌───────────────────────┐   ┌───────────────────────────┐
        │    DODO Local Agent   │   │     MongoDB Database      │
        │ Playwright / Terminal │   │    (dodo_db / Fallback)   │
        └───────────────────────┘   └───────────────────────────┘
```

---

## 2. Operating Modes & Capabilities

### Mode A: AI Assistant
- Conversational chat with streaming tokens via Server-Sent Events (SSE).
- Context retention across multi-turn sessions stored in MongoDB `conversations` and `messages`.
- Autonomous memory capture from conversational interactions (detects tech stacks, fixes, preferences).

### Mode B: Autonomous Dev
- Stateful execution lifecycle:
  $$\text{PLAN} \longrightarrow \text{EXECUTE} \longrightarrow \text{OBSERVE} \longrightarrow \text{EVALUATE} \longrightarrow \text{FIX} \longrightarrow \text{VERIFY} \longrightarrow \text{DELIVER}$$
- Deconstructs complex user requests into discrete, tool-executable steps.
- Bounded execution with retry limits and automated verification (running pytest and Playwright).

### Mode C: Terminal & Processes
- Controlled terminal execution with command safety sanitization.
- Workspace filesystem jail ensuring operations never escape authorized directories.
- Streaming stdout/stderr output directly to xterm.js UI.

### Browser Verification
- Playwright headless Chromium automation for live web app inspection, console diagnostics, and visual screenshot rendering.
- Sensitive action approval gating (delete button clicks, purchases).

### Memory Center
- Persistent memory across 5 categories (`project`, `task_experience`, `preference`, `knowledge`, `conversation`).
- Multi-factor retrieval engine (token overlap, importance weighting, recency decay, project isolation).

---

## 3. Hardware-Aware Model Routing

```
                       User Prompt
                           │
                           ▼
                  Task Classification
            (General, Coding, Reasoning, Lightweight)
                           │
                           ▼
                 Complexity Estimation
                 (Low, Medium, High)
                           │
                           ▼
               Hardware & Availability Check
          (Ollama tags, RAM: 16GB, VRAM: 4GB RTX 3050)
                           │
                           ▼
                     Model Selected
                 (qwen2.5-coder:1.5b)
```
- Fits 100% inside 4GB VRAM on RTX 3050 Laptop GPU.
- Delivers 116+ tokens/sec throughput with sub-5s TTFT.
