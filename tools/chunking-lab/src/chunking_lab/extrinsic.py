"""Query-dependent metrics: scoring a chunking against gold spans.

The method is Chroma's, and README section 4 records it in full along with the
four things their report's prose does not say. The short version, because getting
any of it wrong changes the numbers:

* **Characters, not tokens.** The report says tokens; the implementation counts
  characters. We count characters, which is also what removes the tokenizer and
  therefore the last model dependency from the measurement path.
* **Precision Omega touches no retrieval.** It is computed over *every* chunk in
  the corpus that overlaps a gold span. That is what makes it the chunking
  decision isolated from everything downstream -- and what makes it reproducible
  against a published table with no retriever, no embeddings and no network.
* **Overlap is treated differently by two metrics in the same set.** ``precision``
  divides by the *sum* of the retrieved chunks' widths, so an overlapping chunker
  is charged twice for the same characters. Precision Omega divides by their
  *union*, so it is not. Both are reproduced as they are: this is a faithful port,
  not a redesign, and the published numbers depend on the asymmetry.
* **k is per-question by default.** With ``k=None`` each question is scored at its
  own number of gold-bearing chunks, which is what the reference does with
  ``retrieve=-1``. Pass an integer for a fixed k. Either way the value used is
  recorded, because two runs at different k are not comparable.

Absolute values here are *very* low -- Chroma reports single-digit precision --
because k chunks are retrieved to answer a one-sentence question. **These are
relative comparisons only.** Any report built on them has to say so or it looks
broken (README C15).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from chunking_lab.ranges import Range, difference, intersect, total, union
from chunking_lab.spans import Chunking, Span


@dataclass(frozen=True, slots=True)
class Extrinsic:
    """One question scored against one chunking."""

    strategy: str
    code_path: str
    question_id: str
    #: How many chunks were scored. Recorded because it is adaptive by default.
    k: int

    #: Fraction of the gold spans covered by the retrieved chunks.
    recall: float
    #: Gold characters retrieved, over all characters retrieved. Overlapping
    #: chunks are charged twice, as in the reference.
    precision: float
    #: Intersection over union of gold and retrieved.
    iou: float
    #: The ceiling: precision if every gold-bearing chunk were retrieved. Depends
    #: on the cuts alone, so it is the number this tool exists to produce.
    precision_omega: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _gold_ranges(gold: list[Range]) -> list[Range]:
    """Normalise gold spans to a set of characters.

    The paper defines the gold as "the set of tokens among all relevant excerpts",
    and a set is a union. The reference implementation sums instead, which differs
    only if two excerpts for one question overlap -- they do not in the benchmark,
    so the reproduction is unaffected and this is the definition that generalises.
    """
    return union(gold)


def precision_omega(chunking: Chunking, gold: list[Range]) -> float:
    """The precision ceiling implied by where this chunker put its cuts.

    Take every chunk in the corpus that overlaps a gold span -- not the minimal set
    that covers the gold, which is what an earlier reading of the report assumed
    (README section 4). With overlap the two differ, and the report's own table is
    the evidence: recursive at 400 with 200 overlap scores 13.9 against 17.7 with
    no overlap. Nothing is retrieved and no model runs.
    """
    wanted = _gold_ranges(gold)
    if not wanted:
        return 0.0

    touching: list[Range] = []
    covered: list[Range] = []
    missed = list(wanted)
    for span in chunking.spans:
        hit = False
        for target in wanted:
            overlap = intersect((span.start, span.end), target)
            if overlap is not None:
                hit = True
                covered = union([overlap, *covered])
                missed = difference(missed, overlap)
        if hit:
            touching = union([(span.start, span.end), *touching])

    denominator = total(union(touching + missed))
    return total(covered) / denominator if denominator else 0.0


def gold_bearing_chunks(chunking: Chunking, gold: list[Range]) -> int:
    """How many chunks hold any gold character. The default retrieval depth."""
    wanted = _gold_ranges(gold)
    return sum(
        1
        for span in chunking.spans
        if any(intersect((span.start, span.end), target) is not None for target in wanted)
    )


def score(
    chunking: Chunking,
    gold: list[Range],
    retrieved: list[Span],
    *,
    question_id: str,
    k: int | None = None,
) -> Extrinsic:
    """Score one question's gold spans against a ranked list of retrieved chunks.

    ``retrieved`` is in rank order. ``k`` defaults to this question's number of
    gold-bearing chunks, matching the reference's ``retrieve=-1``.
    """
    wanted = _gold_ranges(gold)
    depth = k if k is not None else gold_bearing_chunks(chunking, gold)
    top = retrieved[:depth]

    covered: list[Range] = []
    missed = list(wanted)
    for span in top:
        for target in wanted:
            overlap = intersect((span.start, span.end), target)
            if overlap is not None:
                covered = union([overlap, *covered])
                missed = difference(missed, overlap)

    hit = total(covered)
    # Summed, not union'd: an overlapping chunker pays twice for the same
    # characters here, and once in precision_omega. Faithful to the reference.
    retrieved_width = total([(span.start, span.end) for span in top])
    gold_width = total(wanted)

    return Extrinsic(
        strategy=chunking.strategy,
        code_path=chunking.code_path,
        question_id=question_id,
        k=depth,
        recall=hit / gold_width if gold_width else 0.0,
        precision=hit / retrieved_width if retrieved_width else 0.0,
        iou=hit / (retrieved_width + total(missed)) if (retrieved_width + total(missed)) else 0.0,
        precision_omega=precision_omega(chunking, gold),
    )
