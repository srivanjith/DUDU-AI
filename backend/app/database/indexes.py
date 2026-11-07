import logging
from pymongo import ASCENDING, DESCENDING, TEXT
from backend.app.database.mongodb import get_db

logger = logging.getLogger("dodo.database.indexes")


def create_database_indexes():
    """
    Creates necessary performance indexes for all DODO MongoDB collections:
    - Unique indexes where applicable
    - Query optimization indexes
    - Text search indexes for messages, code chunks, and memories
    """
    db = get_db()
    if db is None:
        return

    try:
        # 1. users
        db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
        db.users.create_index([("username", ASCENDING)], unique=True, sparse=True)

        # 2. conversations
        db.conversations.create_index([("updated_at", DESCENDING)])
        db.conversations.create_index([("project_id", ASCENDING)])
        db.conversations.create_index([("user_id", ASCENDING)])

        # 3. messages
        db.messages.create_index([("conversation_id", ASCENDING), ("created_at", ASCENDING)])
        db.messages.create_index([("role", ASCENDING)])
        db.messages.create_index([("content", TEXT)])

        # 4. projects
        db.projects.create_index([("name", ASCENDING)])
        db.projects.create_index([("workspace_path", ASCENDING)], unique=True, sparse=True)

        # 5. tasks
        db.tasks.create_index([("status", ASCENDING)])
        db.tasks.create_index([("project_id", ASCENDING)])
        db.tasks.create_index([("created_at", DESCENDING)])

        # 6. agent_runs
        db.agent_runs.create_index([("task_id", ASCENDING)])
        db.agent_runs.create_index([("status", ASCENDING)])

        # 7. tool_executions
        db.tool_executions.create_index([("task_id", ASCENDING)])
        db.tool_executions.create_index([("tool_name", ASCENDING)])
        db.tool_executions.create_index([("status", ASCENDING)])

        # 8. memories
        db.memories.create_index([("project_id", ASCENDING)])
        db.memories.create_index([("category", ASCENDING)])
        db.memories.create_index([("content", TEXT)])

        # 9. model_configs
        db.model_configs.create_index([("model_name", ASCENDING)], unique=True)
        db.model_configs.create_index([("role", ASCENDING)])

        # 10. model_metrics
        db.model_metrics.create_index([("model_name", ASCENDING), ("timestamp", DESCENDING)])

        # 11. workspace_files
        db.workspace_files.create_index([("project_id", ASCENDING), ("file_path", ASCENDING)], unique=True)
        db.workspace_files.create_index([("file_hash", ASCENDING)])

        # 12. code_chunks
        db.code_chunks.create_index([("project_id", ASCENDING), ("file_path", ASCENDING)])
        db.code_chunks.create_index([("content", TEXT)])

        # 13. permissions
        db.permissions.create_index([("operation", ASCENDING)])

        # 14. audit_logs
        db.audit_logs.create_index([("timestamp", DESCENDING)])
        db.audit_logs.create_index([("event_type", ASCENDING)])

        # 15. settings
        db.settings.create_index([("key", ASCENDING)], unique=True)

        logger.info("Successfully ensured all database indexes.")
    except Exception as e:
        logger.warning(f"Error creating database indexes (indexes might be mocked or existing): {e}")

