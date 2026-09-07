"""The retriever, held fixed on purpose.

`chunking-lab` varies the **chunker** with the retriever fixed. `retrieval-bench`
(#53) does the opposite. Neither subsumes the other, and saying which one you are
varying is the whole reason either number means anything (README C5).

BM25 over SQLite FTS5: deterministic, offline, no model, and already the pattern
used by `repo-rag`. That determinism is load-bearing here -- an embedding
retriever would make every comparison depend on the encoder, and the point is to
isolate the cuts.

One thing carried over from `docs/LEARNINGS.md`: building the FTS5 query as an OR
of *every* token pulls stopwords in, so common words dominate BM25 and the
ranking degenerates. That was logged as an open gotcha in `repo-rag`. It matters
more here -- a polluted retriever returns near-random chunks for every strategy,
which makes them all look equally mediocre and hides exactly the differences this
tool exists to show. So stopwords are dropped.
"""

from __future__ import annotations

import re
import sqlite3

from chunking_lab.spans import Chunking, Span

_WORD = re.compile(r"[A-Za-z0-9_]+")

#: Dropped from queries. Short, and only words that carry no retrieval signal --
#: this is not stemming and is not meant to be.
STOPWORDS = frozenset(
    [
        "a",
        "about",
        "all",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "both",
        "but",
        "by",
        "can",
        "did",
        "do",
        "does",
        "doing",
        "each",
        "few",
        "for",
        "from",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "him",
        "his",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "just",
        "me",
        "more",
        "most",
        "my",
        "no",
        "nor",
        "not",
        "now",
        "of",
        "on",
        "only",
        "or",
        "other",
        "our",
        "own",
        "same",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "these",
        "they",
        "this",
        "those",
        "to",
        "too",
        "very",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "why",
        "will",
        "with",
        "you",
        "your",
    ]
)


class BM25Retriever:
    """BM25 over the chunk texts, backed by an in-memory FTS5 index.

    Indexes ``retrieval_text``, which is the field that actually reaches an index
    in a real pipeline -- and for the family-6 strategies is deliberately not the
    same as what gets returned.
    """

    name = "bm25/fts5"

    def __init__(self, chunking: Chunking) -> None:
        self.chunking = chunking
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE VIRTUAL TABLE chunks USING fts5(body)")
        self.db.executemany(
            "INSERT INTO chunks (rowid, body) VALUES (?, ?)",
            [(i, span.retrieval_text) for i, span in enumerate(chunking.spans)],
        )
        self.db.commit()

    @staticmethod
    def to_match(query: str) -> str:
        """Turn a question into a safe FTS5 OR-query, minus the stopwords."""
        tokens = [t for t in _WORD.findall(query.lower()) if t not in STOPWORDS]
        # If a question is nothing but stopwords, fall back to using them rather
        # than returning nothing -- a degenerate ranking beats an empty one, and
        # the alternative would silently score that question zero for every
        # strategy alike.
        tokens = tokens or _WORD.findall(query.lower())
        return " OR ".join(f'"{token}"' for token in tokens)

    def search(self, query: str, k: int) -> list[Span]:
        """The k best-matching chunks, in rank order."""
        match = self.to_match(query)
        if not match or k <= 0:
            return []
        rows = self.db.execute(
            "SELECT rowid FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
            (match, k),
        ).fetchall()
        return [self.chunking.spans[row[0]] for row in rows]

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> BM25Retriever:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
