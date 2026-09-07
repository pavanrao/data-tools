"""Recursive separator splitting -- the baseline that keeps winning.

Chroma's report, verbatim: *"We find that the heuristic
`RecursiveCharacterTextSplitter` with chunk size 200 and no overlap performs
well. While it does not achieve the best result, it is consistently high
performing across all evaluation metrics."* That is the number every expensive
strategy in this tool has to beat.

This is a port of the reference implementation's ``RecursiveTokenChunker``
(itself adapted from LangChain, MIT), with one deliberate change: **it carries
character ranges the whole way down instead of strings.** The reference splits
into strings and then searches the corpus to find each one again, which is both
slower and ambiguous when a chunk's text occurs more than once. Ranges are exact
by construction, and they are what the metrics need anyway (README C1).

The algorithm is otherwise reproduced faithfully, including the behaviours that
look like quirks, because reproducing the published Precision Omega column is
this tool's correctness proof (README C17) and it cannot survive an improvement.
"""

from __future__ import annotations

import re

from data_tools_core.provenance import Provenance

from chunking_lab.chunkers.base import LengthFn, char_length, trim
from chunking_lab.spans import Chunking, Span

#: The reference separator list, in priority order. The empty string is the
#: terminal case: split into individual characters rather than emit a chunk over
#: the size budget.
DEFAULT_SEPARATORS: tuple[str, ...] = ("\n\n", "\n", ".", "?", "!", " ", "")

type Range = tuple[int, int]


class RecursiveChunker:
    """Split on the highest-priority separator that appears, then merge back up."""

    def __init__(
        self,
        size: int,
        overlap: int = 0,
        separators: tuple[str, ...] = DEFAULT_SEPARATORS,
        length: LengthFn = char_length,
    ) -> None:
        if size <= 0:
            raise ValueError(f"chunk size must be positive, got {size}")
        if not 0 <= overlap < size:
            raise ValueError(f"overlap {overlap} must be in [0, {size})")
        self.size = size
        self.overlap = overlap
        self.separators = separators
        self.length = length

    @property
    def name(self) -> str:
        return f"recursive:{self.size}" + (f"/{self.overlap}" if self.overlap else "")

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        ranges = self._split(text, (0, len(text)), self.separators)
        spans = [Span.over(text, start, end) for start, end in ranges]
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            # The merge step repeats whole pieces, so the realised overlap is
            # bounded by the budget rather than equal to it. The invariant checks
            # the bound, which is the property that matters.
            declared_overlap=self.overlap,
            lossless=False,
        )

    def _split(self, text: str, span: Range, separators: tuple[str, ...]) -> list[Range]:
        """Recursively split one range, returning merged ranges."""
        separator, remaining = self._choose(text, span, separators)
        pieces = self._split_on(text, span, separator)

        chunks: list[Range] = []
        pending: list[Range] = []
        for piece in pieces:
            if self.length(text[piece[0] : piece[1]]) < self.size:
                pending.append(piece)
                continue
            # A single piece already exceeds the budget: flush what we have, then
            # break the oversized piece up with the next separator down.
            if pending:
                chunks.extend(self._merge(text, pending))
                pending = []
            if remaining:
                chunks.extend(self._split(text, piece, remaining))
            else:
                chunks.append(piece)  # nothing left to split on; emit it oversized
        if pending:
            chunks.extend(self._merge(text, pending))
        return chunks

    def _choose(
        self, text: str, span: Range, separators: tuple[str, ...]
    ) -> tuple[str, tuple[str, ...]]:
        """First separator that actually occurs in this range, and what follows it."""
        body = text[span[0] : span[1]]
        for i, candidate in enumerate(separators):
            if candidate == "":
                return "", ()
            if re.search(re.escape(candidate), body):
                return candidate, separators[i + 1 :]
        return separators[-1], ()

    def _split_on(self, text: str, span: Range, separator: str) -> list[Range]:
        """Cut a range on a separator, keeping the separator with the piece it *starts*.

        This reproduces the reference's ``keep_separator=True``, which is easy to
        get backwards: it re-joins each delimiter onto the text that *follows* it,
        so a piece begins with ". " rather than ending with it. Cutting the other
        way is defensible but produces different chunks, and different chunks mean
        the published Precision Omega column stops reproducing (README C17).

        Either way no character is lost at a boundary, which is what the invariant
        cares about -- so only a differential test against the reference catches
        the difference. There is one.
        """
        start, end = span
        if not separator:
            return [(i, i + 1) for i in range(start, end)]

        pieces: list[Range] = []
        cursor = start
        for match in re.finditer(re.escape(separator), text[start:end]):
            cut = start + match.start()
            if cut > cursor:
                pieces.append((cursor, cut))
                cursor = cut
        if cursor < end:
            pieces.append((cursor, end))
        return pieces

    def _merge(self, text: str, pieces: list[Range]) -> list[Range]:
        """Greedily pack consecutive pieces up to the size budget, then re-overlap.

        Ported from the reference's ``_merge_splits``. The trailing while-loop is
        what produces overlap: after emitting a chunk it pops pieces off the front
        only until the retained tail is within the overlap budget, so the next
        chunk starts inside the one before it.
        """
        merged: list[Range] = []
        window: list[Range] = []
        total = 0

        def emit(window: list[Range]) -> None:
            bounds = trim(text, window[0][0], window[-1][1])
            if bounds is not None:
                merged.append(bounds)

        for piece in pieces:
            size = self.length(text[piece[0] : piece[1]])
            if total + size > self.size and window:
                emit(window)
                while window and (total > self.overlap or (total + size > self.size and total > 0)):
                    total -= self.length(text[window[0][0] : window[0][1]])
                    window = window[1:]
            window.append(piece)
            total += size
        if window:
            emit(window)
        return merged
