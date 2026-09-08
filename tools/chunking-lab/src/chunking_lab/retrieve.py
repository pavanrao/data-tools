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

from chunking_lab.embeddings import Embedder, cosine
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


class VectorRetriever:
    """Rank by embedding similarity instead of by shared words.

    Catches what BM25 cannot: a question asking about "retries" matching text that
    says "backoff". Costs an embedding pass over every chunk, and -- unlike BM25 --
    the answer now depends on which encoder ran, which is why the name carries it.

    **A warning about the offline fallback.** Built on ``HashingEmbedder`` this is a
    bag of words with extra steps, and will underperform BM25 at the thing BM25 is
    already good at. Any comparison between retrievers made on the hashing embedder
    is a statement about the hashing embedder, not about vector retrieval. Point it
    at a real encoder -- local is the default (``ollama/nomic-embed-text``) -- or do
    not quote the result.
    """

    def __init__(self, chunking: Chunking, embedder: Embedder) -> None:
        self.chunking = chunking
        self.embedder = embedder
        self.name = f"vector/{embedder.id}"
        self._vectors = embedder.embed([span.retrieval_text for span in chunking.spans])
        self._matrix = _as_matrix(self._vectors)

    def search(self, query: str, k: int) -> list[Span]:
        if k <= 0 or not self.chunking.spans:
            return []
        (vector,) = self.embedder.embed([query])
        ranked = _rank(self._matrix, self._vectors, vector)
        return [self.chunking.spans[i] for i in ranked[:k]]

    def close(self) -> None:  # symmetry with BM25Retriever; nothing to release
        return None

    def __enter__(self) -> VectorRetriever:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


#: Reciprocal-rank fusion constant. 60 is the value from the original paper and the
#: one `repo-rag` already uses; RRF needs no score calibration between the two
#: rankings, which is the whole reason to prefer it over a weighted score sum when
#: the scales are as different as BM25 and cosine.
RRF_K = 60


class HybridRetriever:
    """Fuse the lexical and semantic rankings, without calibrating their scores.

    BM25 scores and cosine similarities are not on comparable scales, and making
    them comparable requires tuning that then has to be re-tuned per corpus.
    Reciprocal-rank fusion sidesteps it by using only the *positions*: a chunk
    ranked highly by either retriever scores well, and one ranked highly by both
    scores best.
    """

    def __init__(self, chunking: Chunking, embedder: Embedder) -> None:
        self.lexical = BM25Retriever(chunking)
        self.semantic = VectorRetriever(chunking, embedder)
        self.name = f"hybrid-rrf/{embedder.id}"

    def search(self, query: str, k: int) -> list[Span]:
        if k <= 0:
            return []
        # Fuse over a wider window than we return, or the fusion has nothing to do.
        depth = max(k, 10)
        fused: dict[int, float] = {}
        found: dict[int, Span] = {}
        for ranking in (self.lexical.search(query, depth), self.semantic.search(query, depth)):
            for rank, span in enumerate(ranking):
                key = span.start
                fused[key] = fused.get(key, 0.0) + 1.0 / (RRF_K + rank)
                found[key] = span
        order = sorted(fused, key=lambda key: -fused[key])
        return [found[key] for key in order[:k]]

    def close(self) -> None:
        self.lexical.close()
        self.semantic.close()

    def __enter__(self) -> HybridRetriever:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _as_matrix(vectors: list[list[float]]):
    """Stack the chunk vectors for fast scoring, when numpy is available.

    Pure Python cosine over a few thousand chunks times a few hundred questions is
    minutes of arithmetic per configuration, which turns a comparison into an
    overnight job. numpy comes with the `embeddings` extra for exactly this; BM25
    stays free of it so Tier 0 keeps needing nothing.
    """
    try:
        import numpy
    except ModuleNotFoundError:
        return None
    if not vectors:
        return None
    matrix = numpy.asarray(vectors, dtype=numpy.float32)
    norms = numpy.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / numpy.where(norms == 0, 1, norms)


def _rank(matrix, vectors: list[list[float]], query: list[float]) -> list[int]:
    """Indices of the chunks most similar to ``query``, best first."""
    if matrix is None:
        scored = sorted(range(len(vectors)), key=lambda i: -cosine(vectors[i], query))
        return scored

    import numpy

    q = numpy.asarray(query, dtype=numpy.float32)
    norm = numpy.linalg.norm(q)
    if norm:
        q = q / norm
    return list(numpy.argsort(-(matrix @ q)))


#: Name -> how to build it. `bm25` needs nothing; the other two need an embedder,
#: and every result row records which one, because a vector run against the offline
#: hashing fallback and one against a real encoder are not the same experiment.
RETRIEVERS = ("bm25", "vector", "hybrid")


def build(name: str, chunking: Chunking, embedder: Embedder | None = None):
    """Construct a retriever by name, refusing the combinations that make no sense."""
    if name == "bm25":
        return BM25Retriever(chunking)
    if name not in RETRIEVERS:
        raise ValueError(f"unknown retriever {name!r}; known: {', '.join(RETRIEVERS)}")
    if embedder is None:
        raise ValueError(f"the {name!r} retriever needs an embedder; pass --embedder")
    return (
        VectorRetriever(chunking, embedder)
        if name == "vector"
        else HybridRetriever(chunking, embedder)
    )
