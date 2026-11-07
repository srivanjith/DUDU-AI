# DODO MongoDB Architecture & Schema Specification

**Database:** `dodo_db`  
**Driver:** `pymongo` / `motor` with persistent local standalone fallback

---

## 1. Primary Collections Overview

DODO manages 15 purpose-built collections:

| Collection | Schema / Role | Indexes |
|---|---|---|
| `users` | User credentials, roles, preferences | `email (unique)`, `username (unique)` |
| `conversations` | Multi-turn dialog sessions, active mode, metadata | `updated_at (desc)`, `project_id`, `user_id` |
| `messages` | Individual chat turns, role, content, tool calls | `(conversation_id, created_at)`, `role`, `content (text)` |
| `projects` | Registered project repositories and workspaces | `name`, `workspace_path (unique)` |
| `tasks` | High-level autonomous agent objectives & plans | `status`, `project_id`, `created_at (desc)` |
| `agent_runs` | Individual execution traces per task | `task_id`, `status` |
| `tool_executions` | Detailed log of all tool invocations, duration, IO | `task_id`, `tool_name`, `status` |
| `memories` | Persistent semantic & procedural facts | `project_id`, `category`, `content (text)` |
| `model_configs` | Roles, context length, quantization profiles | `model_name (unique)`, `role` |
| `model_metrics` | Latency, tokens/sec, prompt tokens | `(model_name, timestamp desc)` |
| `workspace_files` | File paths, SHA256 hashes, byte sizes | `(project_id, file_path unique)`, `file_hash` |
| `code_chunks` | Parsed syntax blocks and code embeddings | `(project_id, file_path)`, `content (text)` |
| `permissions` | Granted execution privileges per workspace | `operation` |
| `audit_logs` | Security events, prohibited command attempts | `timestamp (desc)`, `event_type` |
| `settings` | System preferences and runtime defaults | `key (unique)` |

---

## 2. Resilience and Storage Strategy

1. **Source Code Separation**: Full project source trees are never stored as monolithic blobs in MongoDB. Source files reside in the authorized filesystem (`workspace/`), while MongoDB indexes hashes, metadata, and chunk summaries.
2. **Offline Fallback Resilience**: When an external MongoDB server is not active during developer bootstrap, DODO automatically switches to an in-process document store (`mongomock` with disk persistence at `data/local_db_store.json`). All health endpoints report actual connectivity without throwing unhandled exceptions.
3. **Semantic Memory**: Employs MongoDB text indexing and vector embeddings. If MongoDB Atlas Vector Search is enabled, vector embeddings are queried; otherwise, high-performance in-memory semantic scoring is utilized.

