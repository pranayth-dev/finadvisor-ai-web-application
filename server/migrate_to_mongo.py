#!/usr/bin/env python3
"""
SQLite → MongoDB migration utility for FinAdvisor AI.

Usage
-----
# Dry run (inspect + count, no writes)
python migrate_to_mongo.py --dry-run

# Full migration
python migrate_to_mongo.py

# Validate counts after migration
python migrate_to_mongo.py --validate-only

Environment variables required
-------------------------------
MONGODB_URI         e.g. mongodb://localhost:27017 or Atlas URI
MONGODB_DB_NAME     default: finadvisor
DATABASE_URL        default: sqlite:///instance/finadvisor.db
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Resolve project root so this script can be run from any directory.
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv
load_dotenv()

import pymongo
from bson import ObjectId
from pymongo import MongoClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sqlite_path() -> Path:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///instance/finadvisor.db")
    if db_url.startswith("sqlite:///"):
        rel = db_url[len("sqlite:///"):]
        p = SCRIPT_DIR / rel
    elif db_url.startswith("sqlite://"):
        p = Path(db_url[len("sqlite://"):])
    else:
        p = SCRIPT_DIR / "instance" / "finadvisor.db"
    return p


def _connect_sqlite(path: Path) -> sqlite3.Connection:
    if not path.exists():
        print(f"  ERROR: SQLite database not found at {path}")
        sys.exit(1)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def _connect_mongo() -> pymongo.database.Database:
    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        print("  ERROR: MONGODB_URI environment variable is not set.")
        sys.exit(1)
    db_name = os.environ.get("MONGODB_DB_NAME", "finadvisor")
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        print(f"  ERROR: Cannot connect to MongoDB — {exc}")
        sys.exit(1)
    print(f"  Connected to MongoDB database '{db_name}'.")
    return client[db_name]


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def _to_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return None


def _to_date(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val.isoformat()[:10]
    if isinstance(val, str) and len(val) >= 10:
        return val[:10]
    return None


# ---------------------------------------------------------------------------
# Table migrators
# ---------------------------------------------------------------------------

TABLES = [
    "users",
    "transactions",
    "budgets",
    "savings_goals",
    "bills",
    "financial_insights",
    "chat_messages",
    "family_groups",
    "family_invitations",
    "family_savings_goals",
    "notifications",
]

# Mapping: SQLite table name → MongoDB collection name (same by default)
COLLECTION_MAP: dict[str, str] = {
    "financial_insights": "financial_insights",
}


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    cur = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def _migrate_table(
    con: sqlite3.Connection,
    mdb: pymongo.database.Database,
    table: str,
    dry_run: bool,
    errors: list,
) -> tuple[int, int]:
    """Migrate one SQLite table → MongoDB collection.
    Returns (sqlite_count, inserted_count).
    """
    if not _table_exists(con, table):
        print(f"  [SKIP] Table '{table}' does not exist in SQLite.")
        return 0, 0

    coll_name = COLLECTION_MAP.get(table, table)
    collection = mdb[coll_name]

    rows = con.execute(f"SELECT * FROM {table}").fetchall()
    sqlite_count = len(rows)

    if sqlite_count == 0:
        print(f"  {table}: 0 rows — nothing to migrate.")
        return 0, 0

    # Build a set of existing sqlite_ids for deduplication
    existing_ids: set[int] = set()
    for doc in collection.find({}, {"_sqlite_id": 1}):
        if "sqlite_id" in doc:
            existing_ids.add(doc["sqlite_id"])

    docs_to_insert = []
    skipped = 0
    for row in rows:
        d = _row_to_dict(row)
        sqlite_id = d.get("id")
        if sqlite_id in existing_ids:
            skipped += 1
            continue

        doc = _transform(table, d)
        docs_to_insert.append(doc)

    if skipped:
        print(f"  {table}: {skipped} rows already exist — skipping duplicates.")

    inserted = 0
    if docs_to_insert and not dry_run:
        try:
            result = collection.insert_many(docs_to_insert, ordered=False)
            inserted = len(result.inserted_ids)
        except Exception as exc:
            errors.append(f"{table}: {exc}")
            print(f"  ERROR in {table}: {exc}")
    elif docs_to_insert:
        inserted = len(docs_to_insert)  # dry-run: count as "would insert"

    status = "(DRY RUN)" if dry_run else ""
    print(f"  {table}: {sqlite_count} in SQLite, {inserted} {'would be inserted' if dry_run else 'inserted'} {status}")
    return sqlite_count, inserted


def _transform(table: str, d: dict) -> dict:
    """Convert a SQLite row dict to a MongoDB document."""
    doc = dict(d)
    # Preserve original integer id for deduplication on re-run
    if "id" in doc:
        doc["sqlite_id"] = doc.pop("id")

    # Normalise datetime fields
    for field in ("created_at", "updated_at", "responded_at"):
        if field in doc:
            doc[field] = _to_datetime(doc[field])

    # Normalise date fields
    for field in ("date", "target_date", "next_due_date"):
        if field in doc:
            doc[field] = _to_date(doc[field])

    # Table-specific tweaks
    if table == "users":
        # Remove SQLAlchemy internal fields if present
        doc.pop("_sa_instance_state", None)

    if table == "transactions":
        doc["is_shared"] = bool(doc.get("is_shared", 0))

    if table == "savings_goals":
        doc["is_completed"] = bool(doc.get("is_completed", 0))

    if table == "bills":
        doc["is_active"] = bool(doc.get("is_active", 1))
        doc["auto_pay"] = bool(doc.get("auto_pay", 0))

    if table == "financial_insights":
        doc["is_read"] = bool(doc.get("is_read", 0))

    if table == "notifications":
        doc["is_read"] = bool(doc.get("is_read", 0))

    if table == "family_savings_goals":
        doc["is_completed"] = bool(doc.get("is_completed", 0))

    return doc


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate(
    con: sqlite3.Connection,
    mdb: pymongo.database.Database,
) -> bool:
    print("\n── Validation ──────────────────────────────────────────────────")
    all_ok = True
    for table in TABLES:
        if not _table_exists(con, table):
            continue
        coll_name = COLLECTION_MAP.get(table, table)
        sqlite_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        mongo_count = mdb[coll_name].count_documents({})
        status = "✓" if mongo_count >= sqlite_count else "✗ MISMATCH"
        print(f"  {table:30s} SQLite={sqlite_count:6d}  MongoDB={mongo_count:6d}  {status}")
        if mongo_count < sqlite_count:
            all_ok = False
    print()
    return all_ok


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Migrate FinAdvisor AI SQLite data to MongoDB.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect without writing to MongoDB.")
    parser.add_argument("--validate-only", action="store_true", help="Only validate counts; do not migrate.")
    args = parser.parse_args()

    sqlite_path = _get_sqlite_path()
    print(f"\n── FinAdvisor AI SQLite → MongoDB Migration ────────────────────")
    print(f"  SQLite source : {sqlite_path}")
    print(f"  MongoDB target: {os.environ.get('MONGODB_URI', '(not set)')[:40]}…")
    print(f"  DB name       : {os.environ.get('MONGODB_DB_NAME', 'finadvisor')}")
    if args.dry_run:
        print("  Mode          : DRY RUN — no data will be written\n")
    elif args.validate_only:
        print("  Mode          : VALIDATE ONLY\n")
    else:
        print("  Mode          : LIVE MIGRATION\n")

    con = _connect_sqlite(sqlite_path)
    mdb = _connect_mongo()

    if args.validate_only:
        ok = _validate(con, mdb)
        sys.exit(0 if ok else 1)

    errors: list[str] = []
    total_sqlite = 0
    total_inserted = 0

    print("\n── Migrating tables ────────────────────────────────────────────")
    for table in TABLES:
        sc, ins = _migrate_table(con, mdb, table, args.dry_run, errors)
        total_sqlite += sc
        total_inserted += ins

    print(f"\n── Summary ─────────────────────────────────────────────────────")
    print(f"  Total SQLite rows : {total_sqlite}")
    verb = "would be inserted" if args.dry_run else "inserted/skipped"
    print(f"  Total {verb:22s}: {total_inserted}")

    if errors:
        print(f"\n  ✗ {len(errors)} error(s):")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  ✓ No errors.")

    if not args.dry_run:
        _validate(con, mdb)

    con.close()
    print("Done.\n")


if __name__ == "__main__":
    main()
