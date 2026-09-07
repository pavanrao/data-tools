"""Tier 1: boundaries chosen by embedding similarity.

Family 4 in the taxonomy. The document is cut into sentences, each is embedded,
and the cuts are placed where meaning changes rather than where a byte counter
happens to land. One embedding pass over the corpus, so it is the first strategy
in this tool that costs anything.

**Read README section 5 before drawing conclusions from these.** The evidence is
not that semantic chunking is better. Qu, Tu & Bao found no consistent gain over
fixed-size splitting -- and, importantly, measured no cost at all, so the paper's
title overstates its own result. What they did find is that semantic chunking
wins *decisively* on topically heterogeneous documents (F1@5 81.89 vs 69.45 on
stitched Miracl) and loses on natural ones, because evidence sentences in a real
document cluster by position anyway.

That is why these are Tier 1 rather than the default, and it is the tool's whole
premise in one result: **the ranking depends on your corpus, so measure on your
corpus.**
"""

from __future__ import annotations

from data_tools_core.provenance import Provenance

from chunking_lab.chunkers.base import trim
from chunking_lab.chunkers.structural import _sentence_bounds
from chunking_lab.embeddings import Embedder, cosine, resolve
from chunking_lab.spans import Chunking, Span

type Range = tuple[int, int]


def _percentile(values: list[float], percentile: float) -> float:
    """Linear-interpolated percentile, so a short document does not degenerate."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (percentile / 100.0)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


class PercentileSemanticChunker:
    """Cut where adjacent sentences are least alike.

    Embed each sentence, measure the distance to its neighbour, and break wherever
    that distance sits above the ``percentile``-th of all distances in the
    document. Because the threshold is a percentile of the document's *own*
    distances, the number of cuts scales with the document rather than with an
    absolute similarity that has no meaning across corpora.

    ``buffer`` widens the text each sentence is embedded with -- a lone sentence
    often has too little signal to place, and its neighbours disambiguate it. The
    span boundaries are unaffected; only the embedding input is.
    """

    def __init__(
        self,
        percentile: float = 95.0,
        max_size: int | None = None,
        buffer: int = 1,
        embedder: Embedder | None = None,
    ) -> None:
        if not 0 < percentile < 100:
            raise ValueError(f"percentile must be in (0, 100), got {percentile}")
        if max_size is not None and max_size <= 0:
            raise ValueError(f"max size must be positive, got {max_size}")
        if buffer < 0:
            raise ValueError(f"buffer must not be negative, got {buffer}")
        self.percentile = percentile
        self.max_size = max_size
        self.buffer = buffer
        self.embedder = embedder or resolve("hashing")

    @property
    def name(self) -> str:
        base = f"semantic:{self.percentile:g}"
        return f"{base}/{self.max_size}" if self.max_size else base

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        sentences = _sentence_bounds(text)
        if len(sentences) < 2:
            spans = [Span.over(text, *s) for s in sentences] or [Span.over(text, 0, len(text))]
            return self._result(spans, provenance, len(sentences))

        vectors = self.embedder.embed(
            [self._context(text, sentences, i) for i in range(len(sentences))]
        )
        distances = [1.0 - cosine(vectors[i], vectors[i + 1]) for i in range(len(sentences) - 1)]
        # Strictly greater, which matters more than it looks. A uniform passage has
        # every distance equal, so the percentile *is* that distance -- and `>=`
        # would cut between every pair of sentences in the most coherent document
        # it could be given. The flip side is that a document where every sentence
        # is unrelated has an equally flat distribution and yields one chunk; that
        # is inherent to a relative threshold, and `max_size` is the safety valve.
        threshold = _percentile(distances, self.percentile)

        groups: list[list[Range]] = [[sentences[0]]]
        for i, distance in enumerate(distances):
            over_budget = self.max_size is not None and (
                sentences[i + 1][1] - groups[-1][0][0] > self.max_size
            )
            if distance > threshold or over_budget:
                groups.append([sentences[i + 1]])
            else:
                groups[-1].append(sentences[i + 1])

        spans = []
        for group in groups:
            bounds = trim(text, group[0][0], group[-1][1])
            if bounds is not None:
                spans.append(Span.over(text, *bounds))
        return self._result(spans, provenance, len(sentences))

    def _context(self, text: str, sentences: list[Range], index: int) -> str:
        """The text one sentence is embedded with: itself plus `buffer` neighbours."""
        low = max(0, index - self.buffer)
        high = min(len(sentences), index + self.buffer + 1)
        return text[sentences[low][0] : sentences[high - 1][1]]

    def _result(self, spans: list[Span], provenance: Provenance, sentences: int) -> Chunking:
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            lossless=False,
            code_path=f"tier-1/embeddings:{self.embedder.id}",
            notes=(f"{sentences} sentences embedded with buffer={self.buffer}",),
        )


class ClusterSemanticChunker:
    """Choose the cuts that maximise similarity *within* chunks, globally.

    The percentile chunker is greedy and local: it looks at one gap at a time. This
    one solves for the whole document at once -- of every way to partition the
    sentences into chunks no larger than ``max_size``, take the partition whose
    total within-chunk pairwise similarity is highest. That is a dynamic program,
    not a threshold, which is why it can beat the greedy version even using exactly
    the same embeddings.

    It is the strategy that led Chroma's table: at max size 200 it took the highest
    precision (8.0), Precision Omega (34.0) and IoU (8.0) of everything they tested.
    Note what that comparison held fixed -- a strong hosted encoder. With the
    hashing fallback the ranking means nothing, which is what ``code_path`` records.
    """

    def __init__(
        self,
        max_size: int,
        piece: int = 200,
        embedder: Embedder | None = None,
    ) -> None:
        if max_size <= 0:
            raise ValueError(f"max size must be positive, got {max_size}")
        if piece <= 0:
            raise ValueError(f"piece size must be positive, got {piece}")
        self.max_size = max_size
        self.piece = piece
        self.embedder = embedder or resolve("hashing")

    @property
    def name(self) -> str:
        return f"cluster-semantic:{self.max_size}" + (f"/{self.piece}" if self.piece != 200 else "")

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        pieces = self._pieces(text)
        if len(pieces) < 2:
            spans = [Span.over(text, *p) for p in pieces] or [Span.over(text, 0, len(text))]
            return self._result(spans, provenance, len(pieces))

        vectors = self.embedder.embed([text[a:b] for a, b in pieces])
        similarity = [
            [cosine(vectors[i], vectors[j]) for j in range(len(pieces))] for i in range(len(pieces))
        ]

        # best[i] = the highest achievable score for pieces[:i], and cut[i] is the
        # start of the chunk that ends at i. O(n^2), which is fine for a document
        # and is the price of a globally optimal partition rather than a greedy one.
        best = [0.0] * (len(pieces) + 1)
        cut = [0] * (len(pieces) + 1)
        for end in range(1, len(pieces) + 1):
            best[end] = float("-inf")
            for start in range(end - 1, -1, -1):
                if pieces[end - 1][1] - pieces[start][0] > self.max_size and start < end - 1:
                    break  # any earlier start is only longer
                score = best[start] + self._reward(similarity, start, end)
                if score > best[end]:
                    best[end], cut[end] = score, start

        boundaries: list[Range] = []
        end = len(pieces)
        while end > 0:
            start = cut[end]
            boundaries.append((pieces[start][0], pieces[end - 1][1]))
            end = start
        boundaries.reverse()

        spans = []
        for start, end_offset in boundaries:
            bounds = trim(text, start, end_offset)
            if bounds is not None:
                spans.append(Span.over(text, *bounds))
        return self._result(spans, provenance, len(pieces))

    def _reward(self, similarity: list[list[float]], start: int, end: int) -> float:
        """Total pairwise similarity among the pieces of one candidate chunk.

        Summing pairs rewards larger chunks -- there are more of them -- which is
        exactly why ``max_size`` is not optional. The cap is what makes the
        objective well posed.
        """
        return sum(similarity[i][j] for i in range(start, end) for j in range(i + 1, end))

    def _pieces(self, text: str) -> list[Range]:
        """Sentences, further split if one is longer than a piece on its own."""
        pieces: list[Range] = []
        for start, end in _sentence_bounds(text):
            if end - start <= self.piece:
                pieces.append((start, end))
                continue
            for offset in range(start, end, self.piece):
                bounds = trim(text, offset, min(offset + self.piece, end))
                if bounds is not None:
                    pieces.append(bounds)
        return pieces

    def _result(self, spans: list[Span], provenance: Provenance, pieces: int) -> Chunking:
        return Chunking(
            spans=tuple(spans),
            provenance=provenance,
            strategy=self.name,
            lossless=False,
            code_path=f"tier-1/embeddings:{self.embedder.id}",
            notes=(f"{pieces} pieces partitioned by dynamic programming",),
        )
