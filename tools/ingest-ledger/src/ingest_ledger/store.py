"""Persist reconciliation rows to the shared ledger."""

from __future__ import annotations

import json
import sqlite3

from ingest_ledger.models import FileReconciliation

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingest_files (
    run_id        TEXT NOT NULL REFERENCES runs(run_id),
    locator       TEXT NOT NULL,
    sha256        TEXT NOT NULL,
    probe         TEXT,
    unit_kind     TEXT,
    declared      INTEGER,
    extracted     INTEGER,
    coverage      REAL    NOT NULL,
    status        TEXT    NOT NULL,
    missing       TEXT    NOT NULL DEFAULT '[]',
    evidence      TEXT    NOT NULL DEFAULT '{}',
    error         TEXT,
    PRIMARY KEY (run_id, locator)
);
CREATE INDEX IF NOT EXISTS ingest_files_status ON ingest_files(status);
"""


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def record(conn: sqlite3.Connection, run_id: str, row: FileReconciliation) -> None:
    locator = "!".join((*row.container_path, row.path.name))
    conn.execute(
        """
        INSERT OR REPLACE INTO ingest_files
            (run_id, locator, sha256, probe, unit_kind, declared, extracted,
             coverage, status, missing, evidence, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            locator,
            row.sha256,
            str((row.extracted.evidence or {}).get("auditor")) if row.extracted else None,
            str(row.declared.unit_kind) if row.declared else None,
            row.declared.units if row.declared else None,
            row.extracted.units if row.extracted else None,
            row.coverage,
            str(row.status),
            json.dumps(list(row.extracted.missing)) if row.extracted else "[]",
            json.dumps(row.extracted.evidence, default=str) if row.extracted else "{}",
            row.extracted.error if row.extracted else None,
        ),
    )


def quarantined(conn: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
    """Files a downstream consumer must not treat as fully indexed."""
    return conn.execute(
        "SELECT * FROM ingest_files WHERE run_id = ? AND status != 'complete'"
        " ORDER BY coverage ASC",
        (run_id,),
    ).fetchall()
