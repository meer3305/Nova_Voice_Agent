"""SQLite-backed persistent memory for Nova."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(category, key)
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT NOT NULL,
    intent TEXT,
    result_summary TEXT,
    created_at TEXT NOT NULL
);
"""


@dataclass
class MemoryRecord:
    category: str
    key: str
    value: Dict[str, Any]


class MemoryDB:
    """Persistent memory and action history using SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or get_settings().sqlite_path
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)
        logger.info("Memory database initialized at %s", self.db_path)

    def upsert_memory(self, category: str, key: str, value: Dict[str, Any]) -> None:
        payload = json.dumps(value)
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memories (category, key, value, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(category, key)
                DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (category, key, payload, now),
            )
        logger.info("Memory updated: %s/%s", category, key)

    def get_memory(self, category: str, key: str) -> Optional[MemoryRecord]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT category, key, value FROM memories WHERE category=? AND key=?",
                (category, key),
            ).fetchone()
        if not row:
            return None
        return MemoryRecord(category=row["category"], key=row["key"], value=json.loads(row["value"]))

    def get_category(self, category: str, limit: int = 25) -> List[MemoryRecord]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT category, key, value FROM memories WHERE category=? ORDER BY updated_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        return [MemoryRecord(category=r["category"], key=r["key"], value=json.loads(r["value"])) for r in rows]

    def log_action(self, user_input: str, intent: str, result_summary: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO actions (user_input, intent, result_summary, created_at) VALUES (?, ?, ?, ?)",
                (user_input, intent, result_summary, datetime.utcnow().isoformat()),
            )

    def recent_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT user_input, intent, result_summary, created_at FROM actions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def build_context(self) -> Dict[str, Any]:
        """Assemble memory context used by the planner."""

        return {
            "frequent_contacts": [r.value for r in self.get_category("contacts")],
            "tone_preference": next((r.value for r in self.get_category("tone", limit=1)), {"tone": "professional"}),
            "time_patterns": [r.value for r in self.get_category("time_patterns")],
            "food_patterns": [r.value for r in self.get_category("food_patterns")],
            "recent_actions": self.recent_actions(),
        }
