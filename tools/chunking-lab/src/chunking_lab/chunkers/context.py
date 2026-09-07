"""Family 6: strategies that change the *unit*, not the boundaries.

README section 3 argues this family is what most write-ups get wrong, by listing
it alongside fixed-size and semantic as though it were another way to cut. It is
not. The cuts are unchanged. What changes is either what gets embedded or what
gets handed to the model.

Both strategies here retrieve on a small unit and return a larger one, so
``retrieval_text`` and ``return_text`` genuinely diverge -- which is the whole
reason ``Span`` carries both. Score the wrong one and the family is unmeasurable:
you would be crediting a strategy for context the model never saw, or penalising
it for padding that was never indexed.

Neither needs a model. They are Tier 0.
"""

from __future__ import annotations

from data_tools_core.provenance import Provenance

from chunking_lab.chunkers.base import trim
from chunking_lab.chunkers.structural import _sentence_bounds
from chunking_lab.spans import Chunking, Span


class SentenceWindowChunker:
    """Index one sentence; return it with its neighbours.

    The retrieval unit is as precise as the corpus allows, so the embedding is not
    diluted by surrounding text -- but the model still gets enough context for the
    sentence to mean anything.
    """

    def __init__(self, window: int = 1) -> None:
        if window < 0:
            raise ValueError(f"window must not be negative, got {window}")
        self.window = window

    @property
    def name(self) -> str:
        return f"sentence-window:{self.window}"

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        sentences = _sentence_bounds(text)
        spans = []
        for i, (start, end) in enumerate(sentences):
            low = max(0, i - self.window)
            high = min(len(sentences), i + self.window + 1)
            window_start = sentences[low][0]
            window_end = sentences[high - 1][1]
            spans.append(
                Span(
                    start=start,
                    end=end,
                    retrieval_text=text[start:end],
                    return_text=text[window_start:window_end],
                )
            )
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            lossless=False,
            augmented=True,
            notes=(f"returns +/-{self.window} sentences around each retrieved one",),
        )


class ParentDocumentChunker:
    """Index a small child chunk; return the whole section it belongs to.

    The same trade as sentence-window, one level up. The scoring consequence is
    the one worth stating: measured on ``return_text`` this looks like a very
    imprecise chunker, and measured on ``retrieval_text`` it looks like a very
    precise one. Both are true of different things, and the metric has to say
    which it measured -- CONVENTIONS rule 5.
    """

    def __init__(self, child: int, parent: int) -> None:
        if child <= 0 or parent <= 0:
            raise ValueError("child and parent sizes must both be positive")
        if parent < child:
            raise ValueError(f"parent size {parent} is smaller than child size {child}")
        self.child = child
        self.parent = parent

    @property
    def name(self) -> str:
        return f"parent-document:{self.child}/{self.parent}"

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        spans = []
        for start in range(0, len(text), self.child):
            bounds = trim(text, start, min(start + self.child, len(text)))
            if bounds is None:
                continue
            child_start, child_end = bounds
            # The parent is the enclosing block of `parent` characters, aligned so
            # the child sits inside it rather than at its edge.
            parent_index = (start // self.parent) * self.parent
            parent_start = parent_index
            parent_end = min(parent_index + self.parent, len(text))
            spans.append(
                Span(
                    start=child_start,
                    end=child_end,
                    retrieval_text=text[child_start:child_end],
                    return_text=text[parent_start:parent_end],
                )
            )
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            lossless=False,
            augmented=True,
            notes=(f"retrieves {self.child}c children, returns {self.parent}c parents",),
        )
