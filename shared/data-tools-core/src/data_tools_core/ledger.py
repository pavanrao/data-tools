"""SQLite ledger shared by tools that need an audit trail.

One database per run directory. Tools own their own tables; this module owns
the ``runs`` table and the connection conventions, so several tools writing to
the same ledger stay consistent.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    tool        TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    argv        TEXT NOT NULL
);
"""


@contextmanager
def connect(path: Path) -> Iterator[sqlite3.Connection]:
    """Open the ledger with the settings every tool should be using."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    try:
        yield conn
    finally:
        conn.close()


def start_run(conn: sqlite3.Connection, tool: str, argv: list[str]) -> str:
    run_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO runs (run_id, tool, started_at, argv) VALUES (?, ?, ?, ?)",
        (run_id, tool, datetime.now(UTC).isoformat(), " ".join(argv)),
    )
    return run_id


def finish_run(conn: sqlite3.Connection, run_id: str) -> None:
    conn.execute(
        "UPDATE runs SET finished_at = ? WHERE run_id = ?",
        (datetime.now(UTC).isoformat(), run_id),
    )
