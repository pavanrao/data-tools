"""Chunkers that take their boundaries from the document's own structure.

Family 3 in the taxonomy (README section 3): the boundary signal is markup the
author already wrote -- headings, sentence ends -- rather than a length budget or
an embedding. Free to compute, and the only family that can keep a table or a
code fence intact, which is the failure the hostile corpus is built around.
"""

from __future__ import annotations

import re

from data_tools_core.provenance import Provenance

from chunking_lab.chunkers.base import trim
from chunking_lab.spans import Chunking, Span

#: End of a sentence: terminal punctuation, optional closing quote or bracket,
#: then whitespace. Deliberately simple and deliberately not perfect -- it splits
#: "Dr. Smith" and it is supposed to, because that is a real chunking failure and
#: the intrinsic metrics exist to make it visible rather than to hide it.
SENTENCE_END = re.compile(r'(?<=[.!?])["\')\]]*\s+')

#: An ATX Markdown heading at the start of a line.
HEADING = re.compile(r"^(#{1,6})\s+.*$", re.MULTILINE)

#: A fenced code block. Matched first so a heading-like line *inside* a fence
#: cannot be mistaken for a real heading -- the "code block containing blank
#: lines" failure from README section 8.4.
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def _sentence_bounds(text: str) -> list[tuple[int, int]]:
    """Cut points between sentences, as ranges covering the whole document."""
    cuts = [0, *(m.end() for m in SENTENCE_END.finditer(text)), len(text)]
    ranges = []
    for start, end in zip(cuts, cuts[1:], strict=False):
        bounds = trim(text, start, end)
        if bounds is not None:
            ranges.append(bounds)
    return ranges


class SentenceChunker:
    """One chunk per sentence, packed up to a size budget.

    The finest boundary a document offers for free. On its own it produces chunks
    far below any useful retrieval unit, which is why ``size`` packs several
    together -- and why sentence-window exists.
    """

    def __init__(self, size: int = 1, overlap: int = 0) -> None:
        if size <= 0:
            raise ValueError(f"chunk size must be positive, got {size}")
        if overlap < 0:
            raise ValueError(f"overlap must not be negative, got {overlap}")
        self.size = size
        self.overlap = overlap

    @property
    def name(self) -> str:
        return f"sentence:{self.size}" + (f"/{self.overlap}" if self.overlap else "")

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        sentences = _sentence_bounds(text)
        stride = max(1, self.size - self.overlap)
        spans = []
        realised = 0
        for i in range(0, len(sentences), stride):
            group = sentences[i : i + self.size]
            if not group:
                continue
            start, end = group[0][0], group[-1][1]
            if spans:
                realised = max(realised, spans[-1].end - start)
            spans.append(Span.over(text, start, end))
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            declared_overlap=max(realised, 0),
            lossless=False,
        )


class MarkdownHeaderChunker:
    """One chunk per section, split at ATX headings.

    Respects fenced code blocks: a ``#`` inside a fence is a comment, not a
    heading. Getting this wrong shreds every code example in a document, and it is
    the kind of defect that never shows up in an average chunk size.
    """

    def __init__(self, max_size: int | None = None) -> None:
        if max_size is not None and max_size <= 0:
            raise ValueError(f"max size must be positive, got {max_size}")
        self.max_size = max_size

    @property
    def name(self) -> str:
        return "structural" + (f":{self.max_size}" if self.max_size else "")

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        fences = [(m.start(), m.end()) for m in FENCE.finditer(text)]

        def inside_a_fence(offset: int) -> bool:
            return any(start <= offset < end for start, end in fences)

        cuts = [0]
        cuts.extend(m.start() for m in HEADING.finditer(text) if not inside_a_fence(m.start()))
        cuts.append(len(text))

        spans = []
        for start, end in zip(cuts, cuts[1:], strict=False):
            bounds = trim(text, start, end)
            if bounds is None:
                continue
            spans.extend(self._cap(text, *bounds))
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            lossless=False,
            notes=("respects fenced code blocks",),
        )

    def _cap(self, text: str, start: int, end: int) -> list[Span]:
        """Break a section that blows the size budget, on sentence boundaries."""
        if self.max_size is None or end - start <= self.max_size:
            return [Span.over(text, start, end)]
        spans, cursor = [], start
        for sentence_start, sentence_end in _sentence_bounds(text[start:end]):
            absolute_end = start + sentence_end
            if absolute_end - cursor >= self.max_size:
                bounds = trim(text, cursor, start + sentence_start or absolute_end)
                if bounds is not None:
                    spans.append(Span.over(text, *bounds))
                cursor = start + sentence_start
        bounds = trim(text, cursor, end)
        if bounds is not None:
            spans.append(Span.over(text, *bounds))
        return spans
