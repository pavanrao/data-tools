"""Loading the Chroma benchmark, and the numbers it lets us check ourselves against.

Five corpora, 472 questions, each annotated with the exact character ranges that
answer it. MIT (Brandon Smith), pinned and hash-verified by
``benchmarks/fetch.py``.

This exists for one reason (README C17). Precision Omega had already been
reconstructed wrong once, from an ambiguous code extract, in a way that flattered
chunk overlap. "Our implementation is correct" is not something to assert twice.
Because Precision Omega involves **no retrieval**, and because this benchmark is
public with a published results table, the claim can instead be a falsifiable test
that runs offline against somebody else's numbers.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from data_tools_core.provenance import Provenance, UnitKind

from chunking_lab.ranges import Range

#: src/chunking_lab/benchmark.py -> chunking_lab -> src -> tools/chunking-lab
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "benchmarks" / "chroma"

#: Precision Omega, as published in Chroma's "Evaluating Chunking Strategies for
#: Retrieval", for the RecursiveCharacterTextSplitter rows. Percentages, averaged
#: over all 472 questions. Only the rows this tool can reproduce without a model
#: are listed: Precision Omega needs no retriever, so no embeddings are required.
#:
#: (chunk size in tokens, overlap in tokens) -> published Precision Omega
PUBLISHED_PRECISION_OMEGA = {
    (800, 400): 6.7,
    (400, 200): 13.9,
    (400, 0): 17.7,
    (200, 0): 29.9,
}


@dataclass(frozen=True, slots=True)
class Question:
    """One question and the character ranges that answer it."""

    question_id: str
    text: str
    corpus: str
    gold: tuple[Range, ...]


@dataclass(frozen=True, slots=True)
class Corpus:
    """One document plus every question annotated against it."""

    name: str
    text: str
    provenance: Provenance
    questions: tuple[Question, ...]


def available(root: Path | None = None) -> bool:
    """Is the benchmark present? It is downloaded, not committed."""
    root = root or DEFAULT_ROOT
    return (root / "questions_df.csv").exists() and (root / "corpora").is_dir()


def load(root: Path | None = None) -> list[Corpus]:
    """Read every corpus and its questions.

    Raises ``FileNotFoundError`` with the command to run if the data is missing --
    the benchmark is fetched rather than committed, so this is an expected state
    rather than an error.
    """
    root = root or DEFAULT_ROOT
    if not available(root):
        raise FileNotFoundError(
            f"the Chroma benchmark is not in {root}.\n"
            "Fetch it with:  uv run python tools/chunking-lab/benchmarks/fetch.py"
        )

    grouped: dict[str, list[Question]] = {}
    with (root / "questions_df.csv").open() as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            stem = Path(row["corpus_id"]).name
            name = stem if stem.endswith(".md") else f"{stem}.md"
            gold = tuple(
                (int(reference["start_index"]), int(reference["end_index"]))
                for reference in json.loads(row["references"])
            )
            grouped.setdefault(name, []).append(
                Question(question_id=f"q{i:04d}", text=row["question"], corpus=name, gold=gold)
            )

    corpora = []
    for name, questions in sorted(grouped.items()):
        body = (root / "corpora" / name).read_text()
        corpora.append(
            Corpus(
                name=name,
                text=body,
                provenance=Provenance(
                    source=Path(name),
                    sha256=hashlib.sha256(body.encode()).hexdigest(),
                    unit_kind=UnitKind.DOCUMENT,
                ),
                questions=tuple(questions),
            )
        )
    return corpora


def token_counter():
    """The length function the published rows were produced with.

    ``tiktoken`` with ``cl100k_base``, which is the *only* reason the ``benchmark``
    extra exists: the table's sizes are in tokens, so reproducing it needs the
    tokenizer even though nothing this tool measures for itself does. Everything
    outside this function is character-based and needs no model.
    """
    import tiktoken

    encoding = tiktoken.get_encoding("cl100k_base")

    def count(text: str) -> int:
        return len(encoding.encode(text, disallowed_special=()))

    return count
