"""The section 9 experiment, and the two ways its numbers could mislead.

Statistics that are almost right are worse than none, because they arrive with an
air of authority. Two failure modes are tested explicitly here: reporting a
correlation for a signal that never varies, and reporting a mechanical
relationship as though it were a discovery.
"""

from __future__ import annotations

import json

import pytest
from chunking_lab.correlate import (
    Point,
    correlate,
    critical_rho,
    load,
    partial_spearman,
    spearman,
    summarise,
)

# ------------------------------------------------------------------ statistics


def test_spearman_is_one_for_a_monotonic_relationship():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_measures_order_not_scale():
    """Why rank correlation: the question is about ordering, not magnitude."""
    linear = spearman([1, 2, 3, 4], [1, 2, 3, 4])
    exponential = spearman([1, 2, 3, 4], [1, 100, 10_000, 1_000_000])
    assert linear == pytest.approx(exponential) == pytest.approx(1.0)


def test_ties_share_an_average_rank():
    """Naive ranking would invent an ordering between equal values and report a
    correlation for it. Several strategies really do tie on a zero-valued signal."""
    assert spearman([1, 1, 1, 1], [1, 2, 3, 4]) == pytest.approx(0.0)
    # One tied pair should not produce a perfect correlation.
    assert abs(spearman([1, 1, 3, 4], [10, 20, 30, 40])) < 1.0


def test_a_constant_series_correlates_with_nothing():
    assert spearman([5, 5, 5], [1, 2, 3]) == pytest.approx(0.0)


def test_partial_correlation_removes_a_shared_driver():
    """The confound this experiment exists to handle.

    y is driven entirely by z, and x merely tracks z. The raw correlation between
    x and y is strong; once z is partialled out, nothing is left.
    """
    z = [1, 2, 3, 4, 5, 6]
    x = [v * 2 for v in z]
    y = [v * 3 for v in z]
    assert spearman(x, y) == pytest.approx(1.0)
    assert partial_spearman(x, y, z) == pytest.approx(0.0, abs=1e-9)


def test_critical_values_get_harder_to_beat_with_fewer_points():
    assert critical_rho(4) is None
    assert critical_rho(6) > critical_rho(14) > critical_rho(20)


# ---------------------------------------------------------------------- points


def _point(corpus, strategy, median, fidelity, omega, retriever="bm25/fts5"):
    return Point(
        corpus=corpus,
        strategy=strategy,
        retriever=retriever,
        questions=10,
        intrinsic={"median_length": median, "boundary_fidelity": fidelity, "mid_table_rate": 0.0},
        extrinsic={"precision_omega": omega, "iou": omega / 2, "recall": 0.5, "precision": 0.1},
    )


def test_rows_collapse_to_one_point_per_corpus_and_strategy(tmp_path):
    """Extrinsic scores are per question; intrinsic values are per chunking."""
    path = tmp_path / "results.jsonl"
    rows = [
        {
            "strategy": "fixed:400",
            "corpus": "a.md",
            "question_id": f"q{i}",
            "code_path": "tier-0/model-free",
            "retriever": "bm25/fts5",
            "source_sha256": "x",
            "locator": "a.md",
            "intrinsic": {"median_length": 400, "boundary_fidelity": 0.1, "chunks": 9},
            "extrinsic": {"precision_omega": p, "iou": 0.2, "recall": 0.5, "precision": 0.1},
        }
        for i, p in enumerate([0.2, 0.4, 0.6])
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    points = load(path)
    assert len(points) == 1
    assert points[0].questions == 3
    assert points[0].extrinsic["precision_omega"] == pytest.approx(0.4)  # averaged
    assert points[0].intrinsic["median_length"] == 400  # not averaged; it is a property


# ----------------------------------------------------------------- correlating


def test_a_signal_that_never_varies_is_marked_constant_not_zero():
    """The most misleading number this tool could print.

    `mid_table_rate` is 0.0 for every strategy on a corpus with no tables. Reporting
    that as "rho = 0.00, no relationship" would claim the signal was tested and
    found useless. It was not tested at all.
    """
    points = [
        _point("a.md", f"s{i}", median=100 * i, fidelity=0.1 * i, omega=1.0 / i)
        for i in range(1, 6)
    ]
    results = {r.signal: r for r in correlate(points, control=None)}

    assert results["mid_table_rate"].constant is True
    assert results["mid_table_rate"].significant is False
    assert results["median_length"].constant is False


def test_correlating_across_two_retrievers_keeps_only_one():
    """Correlating over a mixed file would blend two experiments.

    A results file can legitimately hold several retrievers -- that is how the two
    axes are compared -- so `correlate` has to pick one rather than pool them.
    """
    points = [
        _point("a.md", f"s{i}", 100 * i, 0.1 * i, 1.0 / i, retriever=retriever)
        for retriever in ("bm25/fts5", "vector/fake")
        for i in range(1, 6)
    ]
    results = correlate(points, control=None)
    assert all(r.n == 5 for r in results), "pooled two retrievers into one correlation"


def test_correlation_is_computed_per_corpus_not_pooled():
    """Pooling would let a between-corpus difference look like a within-corpus one."""
    points = [
        _point(corpus, f"s{i}", median=100 * i, fidelity=0.1, omega=1.0 / i)
        for corpus in ("a.md", "b.md")
        for i in range(1, 5)
    ]
    results = correlate(points, control=None)
    assert {r.corpus for r in results} == {"a.md", "b.md"}
    assert all(r.n == 4 for r in results)


def test_size_is_excluded_from_its_own_partial_correlation():
    points = [
        _point("a.md", f"s{i}", median=100 * i, fidelity=0.1 * i, omega=1.0 / i)
        for i in range(1, 6)
    ]
    results = {r.signal: r for r in correlate(points, control="median_length")}
    assert results["median_length"].partial is None
    assert results["boundary_fidelity"].partial is not None


def test_a_signal_needs_at_least_three_points_to_be_correlated():
    points = [_point("a.md", f"s{i}", 100 * i, 0.1 * i, 1.0 / i) for i in range(1, 3)]
    assert correlate(points, control=None) == []


def test_summaries_exclude_constant_rows_rather_than_averaging_them_as_zero():
    points = [
        _point("a.md", f"s{i}", median=100 * i, fidelity=0.1 * i, omega=1.0 / i)
        for i in range(1, 6)
    ]
    summary = summarise(correlate(points, control=None))
    assert summary["mid_table_rate"]["constant_everywhere"] is True
    assert summary["median_length"]["constant_everywhere"] is False
    assert summary["median_length"]["mean_rho"] < -0.9
