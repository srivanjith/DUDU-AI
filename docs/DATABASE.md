# 🗄️ DODO Database Architecture & Migration Guide

## Overview

DODO provides a dual-mode persistence architecture:
1. **Production Mode**: External standalone MongoDB instance (local `mongod` or MongoDB Atlas cloud cluster).
2. **Standalone Fallback Mode**: In-process `mongomock` instance backed by JSON file persistence at `D:\DODO\data\local_db_store.json`.

If an external MongoDB daemon is not running, DODO automatically activates the persistent fallback store, ensuring conversations, tasks, code checkpoints, and memories survive application restarts.

DODO **never falsely reports a real MongoDB connection**. When using fallback persistence, `/api/health` and `/api/diagnostics` explicitly report:
```json
{
  "status": "healthy_fallback",
  "database": "dodo_db",
  "mode": "in-process mongomock (standalone persistence)",
  "collections_count": 15,
  "latency_ms": 0.1
}
```

---

## The 15 Collections

| Collection | Description | Primary Indexes |
|---|---|---|
| `users` | User credentials and settings | `username` (unique) |
| `conversations` | Conversation metadata and active sessions | `user_id`, `updated_at` |
| `messages` | Chat messages and SSE generation status | `conversation_id`, `created_at` |
| `projects` | Registered workspaces and tech stack info | `name`, `path` |
| `tasks` | Autonomous multi-step agent tasks | `status`, `created_at` |
| `agent_runs` | Individual step executions and observations | `task_id`, `step_id` |
| `tool_executions` | Tool invocation telemetry and durations | `tool_name`, `timestamp` |
| `memories` | Long-term persistent memories (Phase 7) | `category`, `project_id`, `status` |
| `model_configs` | Model registry settings and parameters | `role`, `model_name` |
| `model_metrics` | Inference latency and token throughput | `model_name`, `timestamp` |
| `workspace_files` | Workspace file tree and hash cache | `workspace_path`, `file_path` |
| `code_chunks` | Parsed AST and syntax blocks | `file_path`, `chunk_id` |
| `permissions` | Tool permission registry entries | `tool_name`, `permission_level` |
| `audit_logs` | Security events and approval audit trails | `event_type`, `timestamp` |
| `settings` | DODO system configuration settings | `key` (unique) |

---

## Safe Database Migration to MongoDB

DODO includes a safe database migration engine (`backend/app/database/migration.py` and `scripts/migrate_to_mongodb.py`).

### Key Safety Guarantees:
1. **Non-destructive**: Uses `$setOnInsert` so existing MongoDB documents are never overwritten or deleted.
2. **Dry-Run by Default**: Audits and previews all records before writing.
3. **Connection Verification**: Strictly tests target database connectivity and ping before attempting migration.

### Running Migration CLI:

#### Step 1: Preview with Dry Run
```powershell
$env:PYTHONPATH = "D:\DODO"
python scripts/migrate_to_mongodb.py
```
Output audits all records present in `local_db_store.json`:
```text
[Source JSON File]: D:\DODO\data\local_db_store.json
[Total Records in Fallback]: 450
  - conversations: 33 records
  - messages: 155 records
  - tasks: 36 records
  - tool_executions: 142 records
  - model_configs: 5 records
  - model_metrics: 15 records
  - audit_logs: 64 records
```

#### Step 2: Apply Migration to Local or Atlas MongoDB
```powershell
# For local MongoDB:
python scripts/migrate_to_mongodb.py --uri "mongodb://localhost:27017" --apply

# For MongoDB Atlas (requires approved connection string in .env):
python scripts/migrate_to_mongodb.py --uri "mongodb+srv://user:password@cluster.mongodb.net" --apply
```
