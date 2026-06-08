"""A small vector store over SQLite using the sqlite-vec extension.

Chunk text/metadata lives in an ordinary table; embeddings live in a vec0
virtual table joined by rowid. The embedding dimension is persisted in a meta
table so a store can be reopened for querying without re-specifying it.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import sqlite_vec

from .ingest import Chunk


@dataclass(frozen=True)
class SearchResult:
    text: str
    source: str
    ordinal: int
    distance: float


class VectorStore:
    def __init__(self, path: str | Path, dim: int | None = None) -> None:
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)

        existing = self._read_dim()
        if existing is not None:
            self.dim = existing
        elif dim is not None:
            self.dim = dim
            self._init_schema()
        else:
            raise ValueError("dim is required when creating a new store")

    def _read_dim(self) -> int | None:
        row = self.db.execute(
            "SELECT value FROM meta WHERE key = 'dim'"
        ).fetchone() if self._has_meta() else None
        return int(row[0]) if row else None

    def _has_meta(self) -> bool:
        row = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'"
        ).fetchone()
        return row is not None

    def _init_schema(self) -> None:
        self.db.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        self.db.execute(
            "CREATE TABLE chunks "
            "(id INTEGER PRIMARY KEY, text TEXT, source TEXT, ordinal INTEGER)"
        )
        self.db.execute(
            f"CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[{self.dim}])"
        )
        self.db.execute("INSERT INTO meta (key, value) VALUES ('dim', ?)", (str(self.dim),))
        self.db.commit()

    def add(
        self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]
    ) -> None:
        for chunk, embedding in zip(chunks, embeddings):
            cur = self.db.execute(
                "INSERT INTO chunks (text, source, ordinal) VALUES (?, ?, ?)",
                (chunk.text, chunk.source, chunk.ordinal),
            )
            self.db.execute(
                "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
                (cur.lastrowid, sqlite_vec.serialize_float32(list(embedding))),
            )
        self.db.commit()

    def search(
        self, query_embedding: Sequence[float], k: int = 5
    ) -> list[SearchResult]:
        # sqlite-vec requires the KNN limit (`k = ?`) on the vec0 scan itself,
        # so do the match in a subquery, then join the chunk metadata.
        rows = self.db.execute(
            "SELECT c.text, c.source, c.ordinal, v.distance FROM ("
            "  SELECT rowid, distance FROM vec_chunks "
            "  WHERE embedding MATCH ? AND k = ?"
            ") v JOIN chunks c ON c.id = v.rowid ORDER BY v.distance",
            (sqlite_vec.serialize_float32(list(query_embedding)), k),
        ).fetchall()
        return [SearchResult(t, s, o, d) for (t, s, o, d) in rows]

    def close(self) -> None:
        self.db.close()
