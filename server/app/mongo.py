"""
MongoDB connection manager for FinAdvisor AI.

Usage
-----
from app.mongo import mongo_db, get_db

db = get_db()          # returns the pymongo Database object
# or
from app.mongo import mongo_db
col = mongo_db.users   # access a collection directly
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ConfigurationError


_client: MongoClient | None = None
_db: Database | None = None


def init_mongo(app=None) -> Database:
    """
    Initialise and return the MongoDB database.
    Called once at application startup from create_app().

    If MONGODB_URI is not set, the function raises a RuntimeError so the
    problem is visible immediately rather than silently falling back to SQLite.
    """
    global _client, _db

    uri = os.environ.get("MONGODB_URI", "")
    db_name = os.environ.get("MONGODB_DB_NAME", "finadvisor")

    if not uri:
        # MongoDB is optional — warn but do not crash.
        print(
            "[FinAdvisor] MONGODB_URI is not set. "
            "Running in SQLite-only mode.",
            file=sys.stderr,
        )
        return None  # type: ignore

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Trigger actual connection to validate credentials / host
        _client.admin.command("ping")
        _db = _client[db_name]
        print(f"[FinAdvisor] Connected to MongoDB database '{db_name}'.", file=sys.stderr)
        _ensure_indexes(_db)
        return _db
    except (ConnectionFailure, ConfigurationError) as exc:
        print(
            f"[FinAdvisor] WARNING: Could not connect to MongoDB — {exc}\n"
            "  Set MONGODB_URI in your .env to enable MongoDB features.",
            file=sys.stderr,
        )
        return None  # type: ignore


def get_db() -> Database | None:
    """Return the initialised MongoDB database, or None if unavailable."""
    return _db


class _MongoProxy:
    """Attribute-access proxy so `mongo_db.users` works like the real db."""

    def __getattr__(self, name: str):
        if _db is None:
            raise RuntimeError(
                "MongoDB is not available. "
                "Set MONGODB_URI in your .env file and restart the server."
            )
        return getattr(_db, name)

    def __getitem__(self, name: str):
        if _db is None:
            raise RuntimeError("MongoDB is not available.")
        return _db[name]

    def __bool__(self):
        return _db is not None


mongo_db = _MongoProxy()


# ---------------------------------------------------------------------------
# Index definitions
# ---------------------------------------------------------------------------

def _ensure_indexes(db: Database) -> None:
    """Create required indexes if they do not already exist."""
    from pymongo import ASCENDING, DESCENDING

    # users
    db.users.create_index([("email", ASCENDING)], unique=True, background=True)

    # transactions
    db.transactions.create_index([("user_id", ASCENDING)], background=True)
    db.transactions.create_index([("user_id", ASCENDING), ("date", DESCENDING)], background=True)
    db.transactions.create_index([("family_group_id", ASCENDING)], background=True)

    # budgets
    db.budgets.create_index([("user_id", ASCENDING), ("month", ASCENDING), ("year", ASCENDING)], background=True)
    db.budgets.create_index(
        [("user_id", ASCENDING), ("category", ASCENDING), ("month", ASCENDING), ("year", ASCENDING)],
        unique=True, background=True,
    )

    # savings_goals
    db.savings_goals.create_index([("user_id", ASCENDING)], background=True)

    # bills
    db.bills.create_index([("user_id", ASCENDING)], background=True)

    # financial_insights
    db.financial_insights.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], background=True)
    db.financial_insights.create_index(
        [("user_id", ASCENDING), ("title", ASCENDING), ("month", ASCENDING), ("year", ASCENDING)],
        background=True,
    )

    # chat_messages
    db.chat_messages.create_index([("user_id", ASCENDING), ("advisor_type", ASCENDING)], background=True)
    db.chat_messages.create_index([("conversation_id", ASCENDING)], background=True)

    # family_groups
    db.family_groups.create_index([("created_by", ASCENDING)], background=True)

    # family_invitations
    db.family_invitations.create_index([("invited_email", ASCENDING)], background=True)
    db.family_invitations.create_index([("group_id", ASCENDING)], background=True)

    # family_savings_goals
    db.family_savings_goals.create_index([("group_id", ASCENDING)], background=True)

    # notifications
    db.notifications.create_index([("user_id", ASCENDING)], background=True)

    print("[FinAdvisor] MongoDB indexes verified.", file=sys.stderr)
