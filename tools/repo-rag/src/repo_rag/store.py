"""Hybrid code search over SQLite: sqlite-vec for semantics, FTS5 for keywords.

Vector search captures "what does this mean"; keyword (BM25) search captures
exact identifiers like a function name. ``search`` fuses the two ranked lists
with Reciprocal Rank Fusion (RRF), which needs no score calibration between the
two very different scales.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import sqlite_vec

from .chunk import CodeChunk

_RRF_K = 60
_WORD = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class CodeHit:
    chunk_id: int
    text: str
    path: str
    start_line: int
    end_line: int
    symbol: str | None
    kind: str
    score: float


class CodeStore:
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

    # -- schema ----------------------------------------------------------
    def _has_table(self, name: str) -> bool:
        return (
            self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (name,),
            ).fetchone()
            is not None
        )

    def _read_dim(self) -> int | None:
        if not self._has_table("meta"):
            return None
        row = self.db.execute("SELECT value FROM meta WHERE key='dim'").fetchone()
        return int(row[0]) if row else None

    def _init_schema(self) -> None:
        self.db.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        self.db.execute(
            "CREATE TABLE chunks (id INTEGER PRIMARY KEY, text TEXT, path TEXT, "
            "start_line INTEGER, end_line INTEGER, symbol TEXT, kind TEXT)"
        )
        self.db.execute(
            f"CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[{self.dim}])"
        )
        # External-content FTS5 index over chunk text + symbol.
        self.db.execute(
            "CREATE VIRTUAL TABLE fts USING fts5(text, symbol, "
            "content='chunks', content_rowid='id')"
        )
        self.db.execute("INSERT INTO meta VALUES ('dim', ?)", (str(self.dim),))
        self.db.commit()

    # -- writes ----------------------------------------------------------
    def add(
        self, chunks: Sequence[CodeChunk], embeddings: Sequence[Sequence[float]]
    ) -> None:
        for chunk, embedding in zip(chunks, embeddings):
            cur = self.db.execute(
                "INSERT INTO chunks (text, path, start_line, end_line, symbol, kind) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (chunk.text, chunk.path, chunk.start_line, chunk.end_line,
                 chunk.symbol, chunk.kind),
            )
            rowid = cur.lastrowid
            self.db.execute(
                "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
                (rowid, sqlite_vec.serialize_float32(list(embedding))),
            )
            self.db.execute(
                "INSERT INTO fts (rowid, text, symbol) VALUES (?, ?, ?)",
                (rowid, chunk.text, chunk.symbol or ""),
            )
        self.db.commit()

    # -- reads -----------------------------------------------------------
    def _hit(self, row, score: float) -> CodeHit:
        cid, text, path, start, end, symbol, kind = row
        return CodeHit(cid, text, path, start, end, symbol, kind, score)

    def get_chunk(self, chunk_id: int) -> CodeHit:
        row = self.db.execute(
            "SELECT id, text, path, start_line, end_line, symbol, kind "
            "FROM chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"no chunk with id {chunk_id}")
        return self._hit(row, 0.0)

    def search_vector(self, query_embedding: Sequence[float], k: int = 5) -> list[CodeHit]:
        rows = self.db.execute(
            "SELECT c.id, c.text, c.path, c.start_line, c.end_line, c.symbol, "
            "c.kind, v.distance FROM ("
            "  SELECT rowid, distance FROM vec_chunks "
            "  WHERE embedding MATCH ? AND k = ?"
            ") v JOIN chunks c ON c.id = v.rowid ORDER BY v.distance",
            (sqlite_vec.serialize_float32(list(query_embedding)), k),
        ).fetchall()
        return [self._hit(r[:7], r[7]) for r in rows]

    def search_keyword(self, query: str, k: int = 5) -> list[CodeHit]:
        match = self._to_match(query)
        if not match:
            return []
        rows = self.db.execute(
            "SELECT c.id, c.text, c.path, c.start_line, c.end_line, c.symbol, "
            "c.kind, f.rank FROM fts f JOIN chunks c ON c.id = f.rowid "
            "WHERE fts MATCH ? ORDER BY f.rank LIMIT ?",
            (match, k),
        ).fetchall()
        return [self._hit(r[:7], r[7]) for r in rows]

    def search(
        self, query_embedding: Sequence[float], query_text: str, k: int = 5
    ) -> list[CodeHit]:
        """Hybrid search: RRF over the vector and keyword rankings."""
        vector = self.search_vector(query_embedding, k=k)
        keyword = self.search_keyword(query_text, k=k)

        fused: dict[int, float] = {}
        hits: dict[int, CodeHit] = {}
        for ranking in (vector, keyword):
            for rank, hit in enumerate(ranking):
                fused[hit.chunk_id] = fused.get(hit.chunk_id, 0.0) + 1.0 / (
                    _RRF_K + rank
                )
                hits[hit.chunk_id] = hit

        ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
        return [
            CodeHit(**{**hits[cid].__dict__, "score": score})
            for cid, score in ordered[:k]
        ]

    @staticmethod
    def _to_match(query: str) -> str:
        """Turn free text into a safe FTS5 OR-query of bare word tokens."""
        tokens = _WORD.findall(query)
        return " OR ".join(tokens)

    def close(self) -> None:
        self.db.close()
