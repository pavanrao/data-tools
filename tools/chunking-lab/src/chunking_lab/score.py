"""Run every strategy over a corpus and produce one result row per question.

The row shape is the design constraint from README section 8.6 and open question
4: **intrinsic and extrinsic metrics are computed over the same runs and stored
together**, keyed by strategy, corpus and question. That makes the correlation
experiment in section 9 a group-by over accumulated rows rather than a separate
script -- cheap to honour now, expensive to retrofit.

Every row also carries the provenance of the document, the code path that ran,
and the retrieval depth. Two runs at different k, or against different embedders,
are not comparable, and a row that cannot say which it was is not evidence.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from chunking_lab.benchmark import Corpus, Question
from chunking_lab.chunkers.base import Chunker
from chunking_lab.extrinsic import Extrinsic
from chunking_lab.extrinsic import score as score_one
from chunking_lab.intrinsic import Intrinsic, measure
from chunking_lab.invariant import check
from chunking_lab.retrieve import BM25Retriever


@dataclass(frozen=True, slots=True)
class Result:
    """One (strategy, corpus, question) measurement, with everything needed to
    interpret it later without the run that produced it."""

    strategy: str
    corpus: str
    question_id: str
    code_path: str
    retriever: str
    source_sha256: str
    locator: str
    intrinsic: Intrinsic
    extrinsic: Extrinsic

    def as_row(self) -> dict[str, object]:
        """Flat JSON-serialisable row, ready for JSONL."""
        return {
            "strategy": self.strategy,
            "corpus": self.corpus,
            "question_id": self.question_id,
            "code_path": self.code_path,
            "retriever": self.retriever,
            "source_sha256": self.source_sha256,
            "locator": self.locator,
            "intrinsic": {
                key: value
                for key, value in self.intrinsic.as_dict().items()
                if key not in {"strategy", "code_path"}
            },
            "extrinsic": {
                key: value
                for key, value in self.extrinsic.as_dict().items()
                if key not in {"strategy", "code_path", "question_id"}
            },
        }


def run(
    chunker: Chunker,
    corpus: Corpus,
    *,
    k: int | None = None,
    questions: Iterable[Question] | None = None,
) -> Iterator[Result]:
    """Score one chunker over one corpus, one row per question.

    The chunking and its intrinsic metrics are computed **once** and repeated on
    every row. That is deliberate redundancy: a row has to be interpretable on its
    own, months later, without the run that produced it.
    """
    chunking = chunker.chunk(corpus.text, corpus.provenance)
    check(chunking, corpus.text)
    intrinsic = measure(chunking, corpus.text)

    with BM25Retriever(chunking) as retriever:
        for question in questions if questions is not None else corpus.questions:
            depth = k if k is not None else None
            # Retrieve generously, then let `score_one` truncate to the depth it
            # is scoring at -- so an adaptive k never asks for fewer chunks than
            # it needs and a fixed k never scores fewer than it asked for.
            retrieved = retriever.search(question.text, k=depth or 20)
            yield Result(
                strategy=chunking.strategy,
                corpus=corpus.name,
                question_id=question.question_id,
                code_path=chunking.code_path,
                retriever=retriever.name,
                source_sha256=corpus.provenance.sha256,
                locator=corpus.provenance.locator,
                intrinsic=intrinsic,
                extrinsic=score_one(
                    chunking,
                    list(question.gold),
                    retrieved,
                    question_id=question.question_id,
                    k=depth,
                ),
            )


@dataclass(frozen=True, slots=True)
class Summary:
    """One strategy's mean scores across every question it was measured on."""

    strategy: str
    code_path: str
    questions: int
    mean_k: float
    recall: float
    precision: float
    iou: float
    precision_omega: float


def summarise(results: list[Result]) -> list[Summary]:
    """Mean each metric per strategy. Relative comparisons only -- see C15."""
    grouped: dict[str, list[Result]] = {}
    for result in results:
        grouped.setdefault(result.strategy, []).append(result)

    summaries = [
        Summary(
            strategy=strategy,
            code_path=rows[0].code_path,
            questions=len(rows),
            mean_k=statistics.mean(row.extrinsic.k for row in rows),
            recall=statistics.mean(row.extrinsic.recall for row in rows),
            precision=statistics.mean(row.extrinsic.precision for row in rows),
            iou=statistics.mean(row.extrinsic.iou for row in rows),
            precision_omega=statistics.mean(row.extrinsic.precision_omega for row in rows),
        )
        for strategy, rows in grouped.items()
    ]
    return sorted(summaries, key=lambda s: s.precision_omega, reverse=True)


def write_jsonl(results: Iterable[Result], path: Path) -> int:
    """Append result rows as JSONL. Returns how many were written."""
    written = 0
    with path.open("a", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result.as_row()) + "\n")
            written += 1
    return written
