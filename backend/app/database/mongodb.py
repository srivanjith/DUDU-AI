import asyncio
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.app.core.config import settings
from backend.app.core.security import redact_secrets

logger = logging.getLogger("dodo.database")

COLLECTIONS = [
    "users",
    "conversations",
    "messages",
    "projects",
    "tasks",
    "agent_runs",
    "tool_executions",
    "memories",
    "model_configs",
    "model_metrics",
    "workspace_files",
    "code_chunks",
    "permissions",
    "audit_logs",
    "settings",
]


class MongoDBManager:
    """
    Manages MongoDB connections, connection pooling, health checks,
    and automatic local persistence fallback when MongoDB standalone daemon is offline.
    """

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Any = None
        self.is_connected: bool = False
        self.is_mock: bool = False
        self._fallback_store: Dict[str, Dict[str, Any]] = {col: {} for col in COLLECTIONS}
        self._fallback_file = Path("D:/DODO/data/local_db_store.json")

    def connect(self) -> bool:
        """Connects to MongoDB using configured URI and pool settings."""
        try:
            logger.info(f"Connecting to MongoDB at {redact_secrets(settings.MONGODB_URI)}...")
            self.client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                connect=False,
            )
            # Verify connection with ping
            self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.is_connected = True
            self.is_mock = False
            logger.info(f"Successfully connected to MongoDB database '{settings.MONGODB_DB_NAME}'")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning(
                f"Could not connect to external MongoDB server ({str(e)}). "
                f"Enabling local robust in-memory/JSON storage fallback for collection operations."
            )
            self._init_mock_db()
            return False

    def _init_mock_db(self):
        """Initializes persistent mock collections for standalone operation."""
        try:
            import mongomock
            self.client = mongomock.MongoClient()
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.is_connected = True
            self.is_mock = True
            self._load_fallback_data()
            logger.info("Initialized local persistent mock MongoDB engine.")
        except Exception as ex:
            logger.error(f"Failed to initialize mock database: {ex}")
            self.is_connected = False

    def _load_fallback_data(self):
        """Loads persistent JSON data into mock collections if available."""
        if not self._fallback_file.exists():
            return
        try:
            with open(self._fallback_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for col_name, docs in data.items():
                    if col_name in self.db.list_collection_names() or col_name in COLLECTIONS:
                        col = self.db[col_name]
                        for doc in docs:
                            # Avoid duplicates
                            if "_id" in doc and not col.find_one({"_id": doc["_id"]}):
                                col.insert_one(doc)
        except Exception as e:
            logger.warning(f"Error reading fallback database file: {e}")

    def persist_fallback_data(self):
        """Persists mock data to disk so history survives restarts when standalone mongod is not present."""
        if not self.is_mock or not self.db:
            return
        try:
            self._fallback_file.parent.mkdir(parents=True, exist_ok=True)
            export_data = {}
            for col_name in COLLECTIONS:
                col = self.db[col_name]
                docs = list(col.find({}))
                # Convert ObjectIds to strings
                cleaned_docs = []
                for d in docs:
                    doc_copy = dict(d)
                    if "_id" in doc_copy:
                        doc_copy["_id"] = str(doc_copy["_id"])
                    cleaned_docs.append(doc_copy)
                export_data[col_name] = cleaned_docs

            with open(self._fallback_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not persist fallback data: {e}")

    def get_collection(self, name: str):
        """Retrieves a database collection safely."""
        if self.db is None:
            self.connect()
        return self.db[name]

    def check_health(self) -> Dict[str, Any]:
        """Returns detailed real database health status."""
        if not self.is_connected or self.client is None:
            return {
                "status": "disconnected",
                "database": settings.MONGODB_DB_NAME,
                "is_mock": False,
                "latency_ms": None,
                "error": "Not connected",
            }

        if self.is_mock:
            return {
                "status": "healthy_fallback",
                "database": settings.MONGODB_DB_NAME,
                "mode": "in-process mongomock (standalone persistence)",
                "collections_count": len(self.db.list_collection_names()),
                "latency_ms": 0.1,
            }

        import time
        start = time.perf_counter()
        try:
            self.client.admin.command("ping")
            latency = round((time.perf_counter() - start) * 1000, 2)
            server_info = self.client.server_info()
            return {
                "status": "connected",
                "database": settings.MONGODB_DB_NAME,
                "version": server_info.get("version", "unknown"),
                "collections_count": len(self.db.list_collection_names()),
                "latency_ms": latency,
                "is_mock": False,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": settings.MONGODB_DB_NAME,
                "error": str(e),
                "is_mock": False,
            }

    def close(self):
        """Gracefully closes MongoDB connections and saves mock state."""
        if self.is_mock:
            self.persist_fallback_data()
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed.")


db_manager = MongoDBManager()


def get_db():
    """Dependency helper to get the database instance."""
    if db_manager.db is None:
        db_manager.connect()
    return db_manager.db

