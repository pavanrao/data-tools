"""Answer with a coverage statement -- or refuse.

The abstention literature is mostly about *retrieval* gaps: the corpus does not
contain the answer, so say so. This module handles a different failure, the one
this tool exists for: the corpus *did* contain the answer, in a file ingestion
could not read, and nothing downstream knows that.

Retrieval alone cannot see it -- an unread file has no chunks to rank. So every
query is scored twice: against what was read, and against the descriptors of
what was not. When the best thing we have is something we failed to read, we
refuse rather than answer from the remainder.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import StrEnum

from ingest_ledger.embed import Embedder, HashingEmbedder, cosine, unpack

#: A gap must clear this to count as related to the question at all.
GAP_RELEVANCE = 0.15
#: If a gap scores at least this fraction of the best evidence, refuse. Below
#: it we answer and disclose; at or above it the honest answer is "I can't".
ABSTAIN_RATIO = 0.9
DEFAULT_TOP_K = 5


class Verdict(StrEnum):
    ANSWERED = "answered"  # nothing unread bears on the question
    ANSWERED_WITH_GAPS = "answered_with_gaps"  # answered, gaps disclosed
    ABSTAINED = "abstained"  # the most relevant material was unread


@dataclass(frozen=True, slots=True)
class Passage:
    locator: str
    source: str
    text: str
    score: float


@dataclass(frozen=True, slots=True)
class Gap:
    locator: str
    status: str
    coverage: float
    reason: str
    score: float


@dataclass(frozen=True, slots=True)
class Answer:
    question: str
    verdict: Verdict
    passages: list[Passage]
    gaps: list[Gap]
    statement: str

    @property
    def grounded(self) -> bool:
        """Whether a caller may generate from this. False means refuse."""
        return self.verdict is not Verdict.ABSTAINED


def ask(
    conn: sqlite3.Connection,
    run_id: str,
    question: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    embedder: Embedder | None = None,
    abstain_ratio: float = ABSTAIN_RATIO,
) -> Answer:
    embedder = embedder or HashingEmbedder()
    query = embedder.encode(question)

    passages = _rank_passages(conn, run_id, query, top_k)
    gaps = _rank_gaps(conn, run_id, query)

    best_passage = passages[0].score if passages else 0.0
    related = [gap for gap in gaps if gap.score >= GAP_RELEVANCE]
    best_gap = related[0].score if related else 0.0

    if related and (best_passage == 0.0 or best_gap >= best_passage * abstain_ratio):
        verdict = Verdict.ABSTAINED
    elif related:
        verdict = Verdict.ANSWERED_WITH_GAPS
    else:
        verdict = Verdict.ANSWERED

    return Answer(
        question=question,
        verdict=verdict,
        passages=passages,
        gaps=related,
        statement=_statement(conn, run_id, verdict, related),
    )


def _rank_passages(conn, run_id, query, top_k) -> list[Passage]:
    rows = conn.execute(
        "SELECT locator, source, text, vector FROM chunks WHERE run_id = ?", (run_id,)
    ).fetchall()
    scored = [
        Passage(row["locator"], row["source"], row["text"], cosine(query, unpack(row["vector"])))
        for row in rows
    ]
    scored.sort(key=lambda passage: passage.score, reverse=True)
    return [passage for passage in scored[:top_k] if passage.score > 0]


def _rank_gaps(conn, run_id, query) -> list[Gap]:
    rows = conn.execute(
        "SELECT locator, status, coverage, reason, vector FROM gaps WHERE run_id = ?",
        (run_id,),
    ).fetchall()
    scored = [
        Gap(
            row["locator"],
            row["status"],
            row["coverage"],
            row["reason"] or "",
            cosine(query, unpack(row["vector"])),
        )
        for row in rows
    ]
    scored.sort(key=lambda gap: gap.score, reverse=True)
    return scored


def _statement(conn, run_id, verdict: Verdict, gaps: list[Gap]) -> str:
    total = conn.execute("SELECT COUNT(*) AS n FROM gaps WHERE run_id = ?", (run_id,)).fetchone()[
        "n"
    ]
    chunks = conn.execute(
        "SELECT COUNT(*) AS n FROM chunks WHERE run_id = ?", (run_id,)
    ).fetchone()["n"]

    if verdict is Verdict.ANSWERED:
        suffix = f"; {total} unread file(s) in this corpus do not bear on it" if total else ""
        return f"Answered from {chunks} indexed passages{suffix}."

    listed = "; ".join(f"{gap.locator} ({gap.reason})" for gap in gaps[:3])
    if verdict is Verdict.ANSWERED_WITH_GAPS:
        return (
            f"Answered from {chunks} indexed passages, but this corpus has "
            f"unread content related to the question: {listed}. "
            "Treat the answer as incomplete."
        )
    return (
        "Refused: the most relevant material for this question was not "
        f"successfully read. {listed}. Re-run ingestion for these files "
        "before trusting an answer."
    )
