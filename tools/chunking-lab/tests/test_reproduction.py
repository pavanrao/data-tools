"""C17: our Precision Omega reproduces Chroma's published column, or it is wrong.

This is the correctness proof for the headline metric, and it is the reason the
benchmark is fetched at all. Everything else in this suite tests the tool against
the author's own understanding of what it should do -- which is exactly the kind
of test that passed happily while Precision Omega was implemented from a
misreading of the report.

Skipped unless the benchmark has been fetched and the `benchmark` extra is
installed, so the default suite stays model-free and offline (CONVENTIONS rule 6):

    uv run python tools/chunking-lab/benchmarks/fetch.py
    uv sync --extra benchmark
    uv run pytest tools/chunking-lab/tests/test_reproduction.py
"""

from __future__ import annotations

import statistics

import pytest
from chunking_lab.benchmark import PUBLISHED_PRECISION_OMEGA, available, load, token_counter
from chunking_lab.chunkers.recursive import RecursiveChunker
from chunking_lab.extrinsic import precision_omega
from chunking_lab.ranges import difference, intersect, total, union

pytestmark = pytest.mark.skipif(
    not available(), reason="benchmark not fetched; see benchmarks/fetch.py"
)


@pytest.fixture(scope="module")
def corpora():
    pytest.importorskip("tiktoken", reason="the `benchmark` extra is not installed")
    return load()


@pytest.fixture(scope="module")
def count():
    pytest.importorskip("tiktoken", reason="the `benchmark` extra is not installed")
    return token_counter()


def _mean_precision_omega(corpora, count, size: int, overlap: int) -> float:
    scores = []
    for corpus in corpora:
        chunking = RecursiveChunker(size=size, overlap=overlap, length=count).chunk(
            corpus.text, corpus.provenance
        )
        scores.extend(
            precision_omega(chunking, list(question.gold)) for question in corpus.questions
        )
    return statistics.mean(scores) * 100


def test_the_benchmark_is_the_one_the_paper_describes(corpora):
    """472 questions over five corpora, in the published per-corpus counts."""
    assert sum(len(corpus.questions) for corpus in corpora) == 472
    assert {corpus.name: len(corpus.questions) for corpus in corpora} == {
        "chatlogs.md": 56,
        "finance.md": 97,
        "pubmed.md": 99,
        "state_of_the_union.md": 76,
        "wikitexts.md": 144,
    }


@pytest.mark.parametrize(("config", "published"), sorted(PUBLISHED_PRECISION_OMEGA.items()))
def test_precision_omega_reproduces_the_published_value(corpora, count, config, published):
    size, overlap = config
    ours = _mean_precision_omega(corpora, count, size, overlap)
    assert ours == pytest.approx(published, abs=0.05), (
        f"recursive {size}/{overlap}: we score {ours:.2f}, the paper publishes {published}"
    )


def _minimal_cover_omega(chunking, gold):
    """The reading this project's design record originally assumed.

    Kept only so the regression below can fail. Takes the *smallest* set of chunks
    covering the gold spans, rather than *every* chunk that touches them.
    """
    wanted = union(list(gold))
    remaining, chosen = list(wanted), []
    while remaining:
        best, best_gain = None, 0
        for span in chunking.spans:
            gain = sum(
                total([overlap])
                for target in remaining
                if (overlap := intersect((span.start, span.end), target)) is not None
            )
            if gain > best_gain:
                best, best_gain = span, gain
        if best is None:
            break
        chosen.append((best.start, best.end))
        for target in list(remaining):
            overlap = intersect((best.start, best.end), target)
            if overlap is not None:
                remaining = difference(remaining, overlap)
    denominator = total(union(chosen + remaining))
    covered = total(
        union(
            [
                overlap
                for span in chosen
                for target in wanted
                if (overlap := intersect(span, target)) is not None
            ]
        )
    )
    return covered / denominator if denominator else 0.0


def test_the_original_misreading_would_not_have_reproduced_the_table(corpora, count):
    """The regression that justifies re-fetching a blocked source.

    "The minimal set of chunks covering the gold spans" and "every chunk containing
    a gold character" coincide for a non-overlapping partition and diverge as soon
    as chunks overlap. Both are plausible readings of the report's prose. Only one
    reproduces the published numbers, and the gap is ~28% relative on the
    overlapping configurations -- precisely the ones this tool exists to compare.
    """
    corpus = next(c for c in corpora if c.name == "state_of_the_union.md")
    chunking = RecursiveChunker(size=400, overlap=200, length=count).chunk(
        corpus.text, corpus.provenance
    )
    correct = statistics.mean(precision_omega(chunking, list(q.gold)) for q in corpus.questions)
    misread = statistics.mean(_minimal_cover_omega(chunking, q.gold) for q in corpus.questions)
    assert misread > correct * 1.15, (
        "the two readings no longer diverge on an overlapping chunker, which means "
        "this regression has stopped testing anything"
    )
