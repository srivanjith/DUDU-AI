"""
DODO Safe Database Migration Utility
Migrates persistent JSON fallback store to real local MongoDB or MongoDB Atlas
with dry-run verification, non-destructive upserts, and count auditing.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from backend.app.core.config import settings
from backend.app.core.security import redact_secrets
from backend.app.database.mongodb import COLLECTIONS

logger = logging.getLogger("dodo.database.migration")


class DatabaseMigrationManager:
    """Manages explicit, verified data migration from JSON fallback to real MongoDB."""

    def __init__(self, fallback_file: Optional[Path] = None):
        self.fallback_file = fallback_file or Path("D:/DODO/data/local_db_store.json")

    def test_target_connection(self, mongo_uri: Optional[str] = None, db_name: Optional[str] = None) -> Tuple[bool, str, Optional[MongoClient]]:
        """Verifies reachability of target MongoDB instance."""
        target_uri = mongo_uri or settings.MONGODB_URI
        target_db_name = db_name or settings.MONGODB_DB_NAME

        try:
            client = MongoClient(
                target_uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )
            client.admin.command("ping")
            return True, f"Successfully connected to MongoDB ({redact_secrets(target_uri)})", client
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            return False, f"Cannot connect to target MongoDB: {str(e)}", None

    def inspect_source_data(self) -> Dict[str, Any]:
        """Audits the records present in the local fallback store."""
        if not self.fallback_file.exists():
            return {"exists": False, "total_records": 0, "collections": {}}

        try:
            with open(self.fallback_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            counts = {col: len(docs) for col, docs in data.items() if isinstance(docs, list)}
            return {
                "exists": True,
                "file_path": str(self.fallback_file),
                "file_size_bytes": self.fallback_file.stat().st_size,
                "total_records": sum(counts.values()),
                "collections": counts,
            }
        except Exception as e:
            return {"exists": True, "error": str(e), "total_records": 0, "collections": {}}

    def migrate(
        self,
        mongo_uri: Optional[str] = None,
        db_name: Optional[str] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes safe migration from JSON store to MongoDB.
        If dry_run=True, simulates and audits without writing.
        Never overwrites existing documents in MongoDB ($setOnInsert).
        """
        target_uri = mongo_uri or settings.MONGODB_URI
        target_db_name = db_name or settings.MONGODB_DB_NAME

        # 1. Test target reachability
        connected, msg, client = self.test_target_connection(target_uri, target_db_name)
        if not connected or client is None:
            return {
                "success": False,
                "error": msg,
                "dry_run": dry_run,
                "migrated_count": 0,
            }

        # 2. Inspect source fallback
        source_audit = self.inspect_source_data()
        if not source_audit.get("exists") or source_audit.get("total_records", 0) == 0:
            return {
                "success": True,
                "message": "Source JSON fallback store is empty or does not exist. Nothing to migrate.",
                "dry_run": dry_run,
                "migrated_count": 0,
                "source_audit": source_audit,
            }

        target_db = client[target_db_name]

        with open(self.fallback_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)

        migration_results: Dict[str, Any] = {}
        total_migrated = 0
        total_skipped = 0

        for col_name in COLLECTIONS:
            docs = source_data.get(col_name, [])
            if not isinstance(docs, list) or len(docs) == 0:
                continue

            target_col = target_db[col_name]
            initial_count = target_col.count_documents({})
            inserted_count = 0
            skipped_count = 0

            for doc in docs:
                doc_copy = dict(doc)
                raw_id = doc_copy.get("_id")
                query: Dict[str, Any] = {}

                if raw_id:
                    if ObjectId.is_valid(raw_id):
                        doc_copy["_id"] = ObjectId(raw_id)
                        query = {"$or": [{"_id": ObjectId(raw_id)}, {"_id": str(raw_id)}]}
                    else:
                        query = {"_id": raw_id}
                else:
                    query = doc_copy

                existing = target_col.find_one(query)
                if existing:
                    skipped_count += 1
                else:
                    if not dry_run:
                        target_col.insert_one(doc_copy)
                    inserted_count += 1

            post_count = target_col.count_documents({}) if not dry_run else initial_count + inserted_count
            migration_results[col_name] = {
                "source_count": len(docs),
                "target_initial_count": initial_count,
                "inserted": inserted_count,
                "skipped_existing": skipped_count,
                "target_final_count": post_count,
            }
            total_migrated += inserted_count
            total_skipped += skipped_count

        return {
            "success": True,
            "dry_run": dry_run,
            "target_database": target_db_name,
            "target_uri": redact_secrets(target_uri),
            "total_inserted": total_migrated,
            "total_skipped_existing": total_skipped,
            "collections_processed": len(migration_results),
            "details": migration_results,
        }


migration_manager = DatabaseMigrationManager()
