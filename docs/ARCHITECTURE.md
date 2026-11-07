# DODO Architecture Blueprint

**Tagline:** Your AI. Your Machine. Your Rules.  
**Product Category:** Autonomous AI Agent & AI Software Development Environment

---

## 1. System Overview

DODO is an independent, local-first autonomous development platform and conversational AI assistant built without any reliance on proprietary APIs (Anthropic, Claude, Antigravity, or other hosted vendor locks).

The platform consists of three core applications operating in synergy:
1. **DODO Web Application (`frontend/`)**: Modern responsive IDE & assistant UI built with Next.js, React, Tailwind CSS, Monaco Editor, and Server-Sent Events / WebSockets.
2. **DODO Backend (`backend/`)**: High-performance Python FastAPI service managing authentication, conversation persistence, intelligent model routing, stateful agent planning, bounded execution, and MongoDB operations.
3. **DODO Local Agent (`local_agent/`)**: Isolated local execution runtime that connects securely to the backend, enforcing strict workspace path boundaries, sandboxed command execution, and Playwright-driven browser automation.

```
                    ┌──────────────────────────────┐
                    │      DODO Web Frontend       │
                    │   Next.js / React / Monaco   │
                    └──────────────┬───────────────┘
                                   │ HTTP / SSE / WS
                                   ▼
                    ┌──────────────────────────────┐
                    │         DODO Backend         │
                    │       FastAPI Runtime        │
                    ├──────────────┬───────────────┤
                    │ Model Router │ Agent Engine  │
                    │ Tool Registry│ Memory Store  │
                    └──────┬───────┴───────┬───────┘
                           │               │
            Token-Auth RPC │               │ PyMongo / Motor
                           ▼               ▼
        ┌───────────────────────┐   ┌───────────────────────────┐
        │    DODO Local Agent   │   │     MongoDB Database      │
        │ Playwright / Terminal │   │         (dodo_db)         │
        └───────────────────────┘   └───────────────────────────┘
```

---

## 2. Operating Modes

### Mode A: AI Assistant
- Conversational chat with streaming tokens.
- Context retention across multi-turn sessions stored in MongoDB `conversations` and `messages`.
- Intelligent task classification to route requests between lightweight models (`llama3.2:1b`), general models (`qwen2.5:7b`), and reasoning models (`deepseek-r1:8b`).

### Mode B: Autonomous Developer
- Stateful execution lifecycle:
  $$\text{PLAN} \longrightarrow \text{EXECUTE} \longrightarrow \text{OBSERVE} \longrightarrow \text{EVALUATE} \longrightarrow \text{FIX} \longrightarrow \text{VERIFY} \longrightarrow \text{DELIVER}$$
- Deconstructs complex user requests into discrete, tool-executable steps.
- Bounded execution with retry limits and automated verification (running pytest and Playwright).

### Mode C: Computer & Browser Agent
- Controlled terminal execution with command safety sanitization.
- Workspace filesystem jail ensuring operations never escape authorized directories.
- Playwright headless browser automation for live web app inspection, console diagnostics, and visual screenshot rendering.

---

## 3. Model Routing Architecture

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
                           │
                           ▼
                   Token Stream / Fallback
```

DODO dynamically selects the optimal model based on task intent and hardware constraints. If the configured model is not yet pulled locally, DODO gracefully selects an installed model or delivers native intelligence instructions.

