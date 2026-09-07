"""The load-bearing type: a chunk is a *range*, not a string.

Everything in this tool follows from that choice (README C1). Character-level
IoU and Precision Omega are only computable if every chunk can be addressed back
into the document it came from, and the context-augmenting strategies -- late
chunking, contextual retrieval, sentence-window, parent-document -- are only
expressible if what gets *indexed* can differ from what gets *returned*.

Offsets are characters, not tokens. That matches the reference implementation
this tool is validated against, and it means the metrics need no tokenizer and
therefore no model (README section 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from data_tools_core.provenance import Provenance


@dataclass(frozen=True, slots=True)
class Span:
    """One chunk, addressed back into the normalized document.

    ``start``/``end`` are half-open character offsets. ``retrieval_text`` is what
    gets indexed and ``return_text`` is what reaches the model; for every Tier 0
    strategy they are the same, and the family-6 strategies are exactly the ones
    where they diverge.
    """

    start: int
    end: int
    retrieval_text: str
    return_text: str

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError(f"degenerate span ({self.start}, {self.end})")

    @property
    def length(self) -> int:
        """Width of the span in characters -- the unit every metric is measured in."""
        return self.end - self.start

    @classmethod
    def over(cls, text: str, start: int, end: int) -> Span:
        """A plain span whose indexed and returned text are both the source range."""
        body = text[start:end]
        return cls(start=start, end=end, retrieval_text=body, return_text=body)


@dataclass(frozen=True, slots=True)
class Chunking:
    """The complete output of one chunker on one document.

    Carries ``Provenance`` so a score traces back to bytes, and ``strategy`` so a
    result row can never be compared against a run of something else -- the data
    seam, and CONVENTIONS rule 5.
    """

    spans: tuple[Span, ...]
    provenance: Provenance
    strategy: str
    #: Overlap the strategy declares in characters. The invariant permits
    #: consecutive spans to overlap by up to this much and no more.
    declared_overlap: int = 0
    #: False for strategies that trim whitespace off their boundaries, as the
    #: reference implementation does. Non-whitespace is never droppable.
    lossless: bool = True
    #: True where ``return_text`` is deliberately not ``text[start:end]``
    #: (family 6). Checked by the invariant so the divergence must be declared.
    augmented: bool = False
    #: Which lane actually ran -- CONVENTIONS rule 2. Tier 0 is model-free, so its
    #: value is constant; Tier 1 records the embedder, because a semantic run
    #: against a hosted encoder and one against the offline hashing fallback are
    #: not comparable and must never be silently ranked against each other.
    code_path: str = "tier-0/model-free"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __len__(self) -> int:
        return len(self.spans)
