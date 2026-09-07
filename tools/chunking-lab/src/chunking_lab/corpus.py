"""Corpora and their gold spans, and how to build one whose spans are exact.

Two things live here.

**The types.** ``Corpus`` and ``Question`` are what every scoring path consumes,
whether the corpus came from the Chroma benchmark, from a generated fixture, or
from a directory you point at.

**The builder.** ``DocumentBuilder`` is the technique that makes ground truth free
(README C11): write the answer text through ``answer()`` and the span is exact
*because the generator wrote it*. No annotation pass, no model, no fuzzy matching,
and no possibility of a gold span that does not match the document -- the failure
that would silently score every strategy against the wrong text.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from data_tools_core.provenance import Provenance, UnitKind

from chunking_lab.ranges import Range


@dataclass(frozen=True, slots=True)
class Question:
    """A question and the character ranges that answer it."""

    question_id: str
    text: str
    corpus: str
    gold: tuple[Range, ...]
    #: Free-form note on what this question is testing, carried through to the
    #: gold file so a corpus explains itself.
    about: str = ""


@dataclass(frozen=True, slots=True)
class Corpus:
    """One document plus every question annotated against it."""

    name: str
    text: str
    provenance: Provenance
    questions: tuple[Question, ...]


def provenance_for(name: str, text: str) -> Provenance:
    return Provenance(
        source=Path(name),
        sha256=hashlib.sha256(text.encode()).hexdigest(),
        unit_kind=UnitKind.DOCUMENT,
    )


class DocumentBuilder:
    """Assemble a document while recording exactly where each answer landed.

    ``add`` appends text. ``answer`` appends text *and* opens a question over it.
    Because the builder holds the running length, the span is exact by
    construction -- which is the whole reason a generated corpus needs no
    annotation and can be regenerated forever without drift.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._parts: list[str] = []
        self._questions: list[Question] = []

    @property
    def text(self) -> str:
        return "".join(self._parts)

    def add(self, text: str) -> DocumentBuilder:
        self._parts.append(text)
        return self

    def answer(self, text: str, *, question: str, about: str = "") -> DocumentBuilder:
        """Append ``text`` and record a question whose gold span is exactly it."""
        start = len(self.text)
        self._parts.append(text)
        self._questions.append(
            Question(
                question_id=f"{self.name}:{len(self._questions):03d}",
                text=question,
                corpus=self.name,
                gold=((start, start + len(text)),),
                about=about,
            )
        )
        return self

    def build(self) -> Corpus:
        body = self.text
        return Corpus(
            name=self.name,
            text=body,
            provenance=provenance_for(self.name, body),
            questions=tuple(self._questions),
        )


def write_dir(corpora: list[Corpus], destination: Path) -> Path:
    """Write documents plus a ``gold.jsonl`` that ``load_dir`` can read back."""
    destination.mkdir(parents=True, exist_ok=True)
    gold_path = destination / "gold.jsonl"
    with gold_path.open("w", encoding="utf-8") as handle:
        for corpus in corpora:
            (destination / corpus.name).write_text(corpus.text, encoding="utf-8")
            for question in corpus.questions:
                handle.write(
                    json.dumps(
                        {
                            "question_id": question.question_id,
                            "question": question.text,
                            "corpus": question.corpus,
                            "gold": [list(span) for span in question.gold],
                            "about": question.about,
                        }
                    )
                    + "\n"
                )
    return gold_path


def load_dir(path: Path) -> list[Corpus]:
    """Read a directory of documents plus ``gold.jsonl``.

    The bring-your-own-corpus path: any directory in this shape can be scored,
    whether it was generated here or annotated by hand.

    Gold spans are validated against the documents on load. A span that runs past
    the end of its document is refused rather than silently clamped -- a wrong gold
    span scores every strategy against the wrong text, which is worse than no
    corpus at all.
    """
    gold_path = path / "gold.jsonl"
    if not gold_path.exists():
        raise FileNotFoundError(f"no gold.jsonl in {path}")

    grouped: dict[str, list[Question]] = {}
    with gold_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            grouped.setdefault(row["corpus"], []).append(
                Question(
                    question_id=row["question_id"],
                    text=row["question"],
                    corpus=row["corpus"],
                    gold=tuple((int(a), int(b)) for a, b in row["gold"]),
                    about=row.get("about", ""),
                )
            )

    corpora = []
    for name, questions in sorted(grouped.items()):
        document = path / name
        if not document.exists():
            raise FileNotFoundError(f"{gold_path} references {name}, which is not in {path}")
        body = document.read_text(encoding="utf-8")
        for question in questions:
            for start, end in question.gold:
                if not 0 <= start < end <= len(body):
                    raise ValueError(
                        f"{question.question_id}: gold span ({start}, {end}) is outside "
                        f"{name}, which is {len(body)} characters"
                    )
        corpora.append(
            Corpus(
                name=name,
                text=body,
                provenance=provenance_for(name, body),
                questions=tuple(questions),
            )
        )
    return corpora
