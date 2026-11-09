"""
DODO CLI Database Migration Script
Usage:
    python scripts/migrate_to_mongodb.py [--uri MONGODB_URI] [--db DB_NAME] [--apply]
Default runs in safe DRY-RUN mode. Pass --apply to perform actual database migration.
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.app.database.migration import migration_manager


def main():
    parser = argparse.ArgumentParser(description="DODO Database Safe Migration to MongoDB")
    parser.add_argument("--uri", type=str, default=None, help="Target MongoDB URI (default: from config)")
    parser.add_argument("--db", type=str, default=None, help="Target Database Name (default: dodo_db)")
    parser.add_argument("--apply", action="store_true", help="Perform real migration (default is dry-run)")

    args = parser.parse_args()

    print("==================================================")
    print("      🦅 DODO Safe Database Migration Utility      ")
    print("==================================================")

    dry_run = not args.apply
    if dry_run:
        print("[MODE] DRY-RUN PREVIEW (no data will be written)")
    else:
        print("[MODE] LIVE MIGRATION (non-destructive upsert)")

    # 1. Audit Source
    audit = migration_manager.inspect_source_data()
    print(f"\n[Source JSON File]: {audit.get('file_path')}")
    print(f"[Total Records in Fallback]: {audit.get('total_records')}")
    for col, cnt in audit.get("collections", {}).items():
        if cnt > 0:
            print(f"  - {col}: {cnt} records")

    # 2. Execute Migration or Preview
    print("\nConnecting to target MongoDB...")
    res = migration_manager.migrate(mongo_uri=args.uri, db_name=args.db, dry_run=dry_run)

    print("\n--- Migration Results ---")
    print(json.dumps(res, indent=2, default=str))

    if not res.get("success"):
        print(f"\n❌ Migration halted: {res.get('error')}")
        sys.exit(1)

    if dry_run:
        print("\n✅ Dry run completed successfully. To execute live migration, run with --apply flag.")
    else:
        print("\n🎉 Live migration completed successfully! All records verified.")


if __name__ == "__main__":
    main()
