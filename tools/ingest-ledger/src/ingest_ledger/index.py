"""Index reconciled content -- and, just as importantly, index the gaps.

You cannot search text you failed to extract. But you are never fully blind to
it either: you still have the filename, the archive it sat in, the sheet names,
the declared unit count, and whatever the failure said. That residue is enough
to tell whether a gap is *relevant to the question being asked*, which is the
whole basis for abstaining honestly instead of answering confidently.

So two tables. ``chunks`` holds what was read. ``gaps`` holds a searchable
descriptor of what was not.
"""

from __future__ import annotations

import sqlite3

from ingest_ledger.chunk import Chunk, chunks_for
from ingest_ledger.embed import Embedder, HashingEmbedder, pack
from ingest_ledger.models import FileReconciliation

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    run_id     TEXT NOT NULL REFERENCES runs(run_id),
    locator    TEXT NOT NULL,
    source     TEXT NOT NULL,
    unit_kind  TEXT NOT NULL,
    text       TEXT NOT NULL,
    embedder   TEXT NOT NULL,
    vector     BLOB NOT NULL,
    PRIMARY KEY (run_id, locator)
);

CREATE TABLE IF NOT EXISTS gaps (
    run_id     TEXT NOT NULL REFERENCES runs(run_id),
    locator    TEXT NOT NULL,
    status     TEXT NOT NULL,
    coverage   REAL NOT NULL,
    descriptor TEXT NOT NULL,
    reason     TEXT,
    embedder   TEXT NOT NULL,
    vector     BLOB NOT NULL,
    PRIMARY KEY (run_id, locator)
);
"""


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def describe_gap(row: FileReconciliation) -> str:
    """Everything we still know about a file we could not fully read.

    Deliberately keyword-shaped rather than prose: sheet names and filenames
    are the signal, and they are frequently the exact words a question uses.
    """
    parts: list[str] = [*row.container_path, row.path.stem.replace("_", " "), row.path.name]

    if row.declared:
        parts.append(f"{row.declared.units} {row.declared.unit_kind}s")
        parts.extend(str(uid) for uid in row.declared.unit_ids)
        parts.extend(row.declared.notes)

    if row.extracted:
        parts.extend(str(unit) for unit in row.extracted.missing)
        if row.extracted.error:
            parts.append(row.extracted.error)
        # Partial text is still evidence of subject matter, capped so a large
        # partial file cannot dominate the descriptor.
        parts.append(row.extracted.text[:2000])

    if row.note:
        parts.append(row.note)

    return " ".join(part for part in parts if part)


def build(
    conn: sqlite3.Connection,
    run_id: str,
    rows: list[FileReconciliation],
    *,
    embedder: Embedder | None = None,
) -> tuple[int, int]:
    """Index reconciled chunks and gap descriptors. Returns (chunks, gaps)."""
    embedder = embedder or HashingEmbedder()
    init(conn)

    indexed: list[Chunk] = []
    for row in rows:
        indexed.extend(chunks_for(row))

    for chunk in indexed:
        conn.execute(
            "INSERT OR REPLACE INTO chunks"
            " (run_id, locator, source, unit_kind, text, embedder, vector)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                chunk.locator,
                str(chunk.provenance.source),
                str(chunk.provenance.unit_kind),
                chunk.text,
                embedder.name,
                pack(embedder.encode(chunk.text)),
            ),
        )

    gaps = [row for row in rows if row.quarantined]
    for row in gaps:
        descriptor = describe_gap(row)
        conn.execute(
            "INSERT OR REPLACE INTO gaps"
            " (run_id, locator, status, coverage, descriptor, reason, embedder, vector)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                "!".join((*row.container_path, row.path.name)),
                str(row.status),
                row.coverage,
                descriptor,
                _reason(row),
                embedder.name,
                pack(embedder.encode(descriptor)),
            ),
        )

    return len(indexed), len(gaps)


def _reason(row: FileReconciliation) -> str:
    if row.extracted and row.extracted.error:
        return row.extracted.error
    if row.extracted and row.extracted.missing:
        kind = row.declared.unit_kind if row.declared else "unit"
        missing = list(row.extracted.missing)
        shown = ", ".join(str(unit) for unit in missing[:6])
        more = f" (+{len(missing) - 6} more)" if len(missing) > 6 else ""
        return f"missing {kind}s: {shown}{more}"
    return row.note or str(row.status)
