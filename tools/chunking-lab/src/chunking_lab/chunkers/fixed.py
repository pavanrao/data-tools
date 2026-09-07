"""Fixed-size chunking: cut every N characters, optionally overlapping.

The cheapest strategy there is, and the one every other strategy has to beat.
It has no idea what a sentence is, which is precisely the failure the hostile
corpus is built to expose.
"""

from __future__ import annotations

from data_tools_core.provenance import Provenance

from chunking_lab.chunkers.base import trim
from chunking_lab.spans import Chunking, Span


class FixedChunker:
    """Cut the document into equal character windows.

    ``overlap`` characters of each window are repeated at the start of the next,
    which is the direct cause of the duplication factor the intrinsic metrics
    report -- and, per README section 4, of a materially worse Precision Omega.
    """

    def __init__(self, size: int, overlap: int = 0) -> None:
        if size <= 0:
            raise ValueError(f"chunk size must be positive, got {size}")
        if not 0 <= overlap < size:
            raise ValueError(f"overlap {overlap} must be in [0, {size})")
        self.size = size
        self.overlap = overlap

    @property
    def name(self) -> str:
        return f"fixed:{self.size}" + (f"/{self.overlap}" if self.overlap else "")

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        stride = self.size - self.overlap
        spans: list[Span] = []
        start = 0
        while start < len(text):
            bounds = trim(text, start, min(start + self.size, len(text)))
            if bounds is not None:
                spans.append(Span.over(text, *bounds))
            start += stride
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            declared_overlap=self.overlap,
            lossless=False,
        )
