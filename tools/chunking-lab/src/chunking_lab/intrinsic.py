"""Query-free metrics: what can be said about a chunking with no questions at all.

README section 7 draws the line this module sits on. **Intrinsic metrics screen;
extrinsic metrics rank.** Coverage below 1.0, chunks past the embedding window, or
40% of cuts landing mid-sentence disqualify a configuration with no evaluation set
in existence — real value delivered before a pipeline does. But they cannot rank
two reasonable configurations, because "good chunking" is only defined relative to
the questions people ask. Any tool claiming a universal chunk-quality score
without queries is overselling, and this one says so in its own README.

**On prior art.** These signals are not new, and the docstrings below name their
published counterparts individually. Adaptive Chunking (LREC 2026) selects a
chunking method per document from five intrinsic metrics — References
Completeness, Intrachunk Cohesion, Document Contextual Coherence, Block Integrity
and Size Compliance — with no retrieval run at all, and MoC (ACL 2025) and
ChunkScore have both correlated query-free signals against downstream QA. The one
thing this set does differently is need **no model**: everything above
``cohesion`` is arithmetic over character offsets, so it runs offline, in
milliseconds, with nothing installed. That is the whole of the distinction, and
naming it here keeps it from growing in the retelling.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from chunking_lab.embeddings import Embedder, cosine
from chunking_lab.invariant import content_coverage, coverage
from chunking_lab.spans import Chunking

#: Roughly a 512-token embedding window at ~4 characters per token. A proxy, and
#: deliberately a crude one: the true limit depends on the tokenizer, and reaching
#: for a real one would drag a model dependency into the deterministic core for a
#: number whose job is only to say "this chunk is at risk of silent truncation".
DEFAULT_MAX_CHARS = 2000

#: Below this a chunk is a runt: too little context to be worth retrieving, but it
#: still occupies an index slot and can outrank a useful chunk on a short query.
DEFAULT_RUNT_CHARS = 50

#: Openers that refer to something outside the chunk. A chunk starting this way has
#: been severed from what it depends on, which is the failure that motivated late
#: chunking and contextual retrieval -- detected here deterministically instead.
#: Adaptive Chunking calls its version References Completeness.
ORPHAN_OPENER = re.compile(
    r"""^\W*(
        (as\s+(described|noted|shown|mentioned|discussed|explained)\s+(above|below|earlier|previously))
      | (the\s+(table|figure|chart|list|section|example|code)\s+(above|below))
      | (this|these|those|that|it|they|he|she|such)\b
      | (the\s+(former|latter))\b
      | (therefore|thus|hence|consequently|however|nevertheless|instead|otherwise)\b
      | (in\s+(this|that)\s+case)
      | (doing\s+so)
    )""",
    re.IGNORECASE | re.VERBOSE,
)

#: A Markdown table row. A cut inside a run of these severs the table from its
#: header, which is the "table split mid-row" failure in README section 8.4.
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")

_SENTENCE_TAIL = re.compile(r'[.!?]["\')\]]*\s*$')


@dataclass(frozen=True, slots=True)
class Intrinsic:
    """Everything measurable about a chunking without asking a question of it."""

    strategy: str
    code_path: str
    chunks: int

    #: Fraction of the document present in at least one span. Dips below 1.0
    #: whenever a strategy trims whitespace at its boundaries, which is harmless
    #: -- so this is reported, not screened on.
    coverage: float
    #: Fraction of the document's **non-whitespace** characters present in a span.
    #: Below 1.0 this is silent data loss -- `ingest-ledger`'s thesis applied to
    #: chunking -- and it is what `disqualifications` actually tests.
    content_coverage: float
    #: Characters indexed / characters in the source. The direct index cost of
    #: overlap, and above 1.0 only because of it.
    duplication: float
    #: Characters returned to the model / characters in the source. Diverges from
    #: `duplication` only for family 6, and is the number that makes the trade
    #: those strategies are making visible.
    return_amplification: float

    median_length: int
    p95_length: int
    max_length: int
    #: Fraction of chunks past the embedding window -- the silent-truncation risk.
    #: Adaptive Chunking's Size Compliance.
    oversize_rate: float
    #: Fraction of chunks too small to carry usable context.
    runt_rate: float

    #: Fraction of cuts landing at a sentence or block boundary rather than inside
    #: a sentence. Adaptive Chunking's Block Integrity.
    boundary_fidelity: float
    #: Fraction of cuts landing inside a Markdown table.
    mid_table_rate: float
    #: Fraction of chunks holding an odd number of code fences, i.e. a fence was
    #: cut in half.
    split_fence_rate: float
    #: Fraction of chunks opening with a reference to something outside themselves.
    orphan_rate: float

    #: Mean within-chunk similarity, and mean similarity across a boundary. Both
    #: need an embedder, so both are None unless one was supplied -- the only
    #: fields in this class that are not free.
    cohesion: float | None = None
    separation: float | None = None

    def as_dict(self) -> dict[str, object]:
        """Flat mapping, for the result rows in README section 8.6."""
        return asdict(self)

    def disqualifications(self, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
        """The screening verdict: reasons this configuration is not worth ranking.

        Deliberately short, and every entry is a *fault* rather than a preference.
        A configuration with none of these is not thereby good -- it is merely
        eligible for the extrinsic metrics to have an opinion about.
        """
        reasons = []
        if self.content_coverage < 1.0:
            lost = (1.0 - self.content_coverage) * 100
            reasons.append(f"loses {lost:.1f}% of the document's content to no chunk at all")
        if self.oversize_rate > 0:
            reasons.append(
                f"{self.oversize_rate:.0%} of chunks exceed ~{max_chars} characters and "
                f"risk silent truncation at embedding time"
            )
        if self.split_fence_rate > 0:
            reasons.append(f"{self.split_fence_rate:.0%} of chunks cut a code fence in half")
        return reasons


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * percentile / 100.0)))
    return ordered[index]


def _is_clean_boundary(text: str, offset: int) -> bool:
    """Does a cut at ``offset`` fall where the document itself breaks?"""
    if offset <= 0 or offset >= len(text):
        return True
    before = text[:offset]
    if _SENTENCE_TAIL.search(before):
        return True
    # A block boundary: the cut sits at the start of a line.
    return before.endswith("\n")


def _is_inside_a_table(text: str, offset: int) -> bool:
    """Is ``offset`` strictly inside a Markdown table row?"""
    if offset <= 0 or offset >= len(text):
        return False
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    line = text[line_start : line_end if line_end != -1 else len(text)]
    if not TABLE_ROW.match(line):
        return False
    return offset not in (line_start, line_end)


def measure(
    chunking: Chunking,
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    runt_chars: int = DEFAULT_RUNT_CHARS,
    embedder: Embedder | None = None,
) -> Intrinsic:
    """Compute every query-free signal for one chunking.

    Pure arithmetic over character offsets unless ``embedder`` is supplied, in
    which case cohesion and separation are added and the returned ``code_path``
    says so.
    """
    spans = chunking.spans
    if not spans:
        raise ValueError(f"{chunking.strategy}: nothing to measure, the chunking is empty")

    lengths = [span.length for span in spans]
    source = len(text) or 1

    cuts = sorted({span.start for span in spans} | {span.end for span in spans})
    clean = sum(1 for cut in cuts if _is_clean_boundary(text, cut))
    in_table = sum(1 for cut in cuts if _is_inside_a_table(text, cut))

    metrics = Intrinsic(
        strategy=chunking.strategy,
        code_path=chunking.code_path,
        chunks=len(spans),
        coverage=coverage(chunking, text),
        content_coverage=content_coverage(chunking, text),
        duplication=sum(len(s.retrieval_text) for s in spans) / source,
        return_amplification=sum(len(s.return_text) for s in spans) / source,
        median_length=_percentile(lengths, 50),
        p95_length=_percentile(lengths, 95),
        max_length=max(lengths),
        oversize_rate=sum(1 for s in spans if len(s.retrieval_text) > max_chars) / len(spans),
        runt_rate=sum(1 for s in spans if len(s.retrieval_text) < runt_chars) / len(spans),
        boundary_fidelity=clean / len(cuts),
        mid_table_rate=in_table / len(cuts),
        split_fence_rate=sum(1 for s in spans if s.retrieval_text.count("```") % 2) / len(spans),
        orphan_rate=sum(1 for s in spans if ORPHAN_OPENER.match(s.retrieval_text)) / len(spans),
    )
    if embedder is None:
        return metrics

    cohesion, separation = _cohesion_and_separation(chunking, text, embedder)
    return Intrinsic(
        **{
            **metrics.as_dict(),
            "cohesion": cohesion,
            "separation": separation,
            "code_path": f"{chunking.code_path}+intrinsic:{embedder.id}",
        }
    )


def _cohesion_and_separation(
    chunking: Chunking, text: str, embedder: Embedder
) -> tuple[float | None, float | None]:
    """Mean similarity within chunks, and across chunk boundaries.

    The one pair of signals here that costs anything. A good chunking should hold
    similar material together (high cohesion) and cut where material changes (low
    separation); MoC's Boundary Clarity is the same intuition computed with a
    language model's perplexity instead.

    Worth knowing before trusting these: MoC reports that plain semantic
    dissimilarity metrics of exactly this shape did *not* track RAG performance,
    while their perplexity-based ones did. Included because the correlation
    experiment in README section 9 needs them, not because they are known to work.
    """
    from chunking_lab.chunkers.structural import _sentence_bounds

    within: list[float] = []
    across: list[float] = []
    for span in chunking.spans:
        sentences = _sentence_bounds(text[span.start : span.end])
        if len(sentences) < 2:
            continue
        vectors = embedder.embed([text[span.start + a : span.start + b] for a, b in sentences])
        within.extend(cosine(vectors[i], vectors[i + 1]) for i in range(len(vectors) - 1))

    for left, right in zip(chunking.spans, chunking.spans[1:], strict=False):
        vectors = embedder.embed([left.retrieval_text, right.retrieval_text])
        across.append(cosine(vectors[0], vectors[1]))

    return (
        sum(within) / len(within) if within else None,
        sum(across) / len(across) if across else None,
    )
