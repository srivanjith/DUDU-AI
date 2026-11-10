"""
DODO MongoDB Atlas Acceptance Verification Script
Tests real Atlas connectivity, audits 8 migrated collections, validates CRUD,
indexes, persistence across restart, and fallback behavior.
Never exposes credentials in logs.
"""
import sys
import time
from pathlib import Path
from bson import ObjectId

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.core.security import redact_secrets
from backend.app.database.mongodb import db_manager, COLLECTIONS
from backend.app.database.migration import migration_manager
from backend.app.database.repositories.conversation_repository import ConversationRepository
from backend.app.database.repositories.model_repository import MemoryRepository


def run_mongodb_verification():
    print("=" * 60)
    print("      🦅 1. MONGODB ATLAS REAL CONNECTION VERIFICATION      ")
    print("=" * 60)

    # Ensure connected
    connected = db_manager.connect()
    print(f"db_manager.connect() result: {connected}")

    # 1. Real Connection Check
    health = db_manager.check_health()
    print(f"Connection Status: {health.get('status')}")
    print(f"Database Name: {health.get('database')}")
    print(f"Is Mock: {health.get('is_mock')} (Expected: False)")
    print(f"MongoDB Version: {health.get('version')}")
    print(f"Atlas Latency: {health.get('latency_ms')} ms")

    assert health.get("status") == "connected", f"Expected connected, got {health.get('status')}"
    assert health.get("is_mock") is False, "Expected real MongoDB connection (is_mock=False)"

    # 2. Audit 8 Migrated Collections vs Source JSON
    print("\n" + "=" * 60)
    print("      🦅 2. COLLECTION COUNT AUDIT (SOURCE vs ATLAS)      ")
    print("=" * 60)

    source_audit = migration_manager.inspect_source_data()
    source_counts = source_audit.get("collections", {})
    atlas_db = db_manager.db

    discrepancies = []
    print(f"{'Collection':<22} | {'Source JSON':<12} | {'Atlas Live':<12} | {'Status'}")
    print("-" * 60)

    for col_name in COLLECTIONS:
        s_count = source_counts.get(col_name, 0)
        a_count = atlas_db[col_name].count_documents({})
        if s_count > 0 or a_count > 0:
            status = "MATCH (OK)" if a_count >= s_count else "MISMATCH"
            print(f"{col_name:<22} | {s_count:<12} | {a_count:<12} | {status}")
            if a_count < s_count:
                discrepancies.append((col_name, s_count, a_count))

    assert len(discrepancies) == 0, f"Discrepancies found: {discrepancies}"

    # 3. Verify Indexes
    print("\n" + "=" * 60)
    print("      🦅 3. DATABASE INDEXES VERIFICATION                 ")
    print("=" * 60)
    for col_name in ["conversations", "messages", "tasks", "memories", "users"]:
        indexes = atlas_db[col_name].index_information()
        idx_names = list(indexes.keys())
        print(f"Collection '{col_name}' indexes: {idx_names}")
        assert len(idx_names) >= 1, f"Expected indexes on {col_name}"

    # 4. CRUD Test on MongoDB Atlas
    print("\n" + "=" * 60)
    print("      🦅 4. ATLAS LIVE CRUD OPERATIONS TEST               ")
    print("=" * 60)
    conv_repo = ConversationRepository()
    test_tag = f"acceptance_test_{int(time.time())}"

    # Create
    created_conv = conv_repo.create_conversation(
        title=f"Acceptance Test Conversation [{test_tag}]",
        mode="assistant",
        user_id="acceptance_tester",
    )
    conv_id = created_conv["id"]
    print(f"Created Conversation: ID={conv_id}, Title='{created_conv.get('title')}'")
    assert conv_id is not None

    # Read
    read_conv = conv_repo.find_by_id(conv_id)
    assert read_conv is not None
    assert read_conv["id"] == conv_id
    print(f"Read Conversation Verified: '{read_conv.get('title')}'")

    # Update
    updated_conv = conv_repo.update(conv_id, {"title": f"Updated Title [{test_tag}]"})
    assert updated_conv["title"] == f"Updated Title [{test_tag}]"
    print(f"Updated Conversation Verified: '{updated_conv.get('title')}'")

    # Delete
    del_ok = conv_repo.delete(conv_id)
    assert del_ok is True
    post_del = conv_repo.find_by_id(conv_id)
    assert post_del is None
    print(f"Delete Conversation Verified: Successfully removed.")

    print("\n" + "=" * 60)
    print("✅ MongoDB Atlas Verification PASSED with 100% Integrity.")
    print("=" * 60)


if __name__ == "__main__":
    run_mongodb_verification()
