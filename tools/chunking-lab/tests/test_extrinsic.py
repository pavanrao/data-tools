"""The query-dependent metrics, on examples small enough to check by hand.

The reproduction test proves these agree with a published table. These prove they
do the arithmetic you think they do -- which is the part that was got wrong last
time, on a formula that looked entirely reasonable.
"""

from __future__ import annotations

import pytest
from chunking_lab.extrinsic import gold_bearing_chunks, precision_omega, score
from chunking_lab.ranges import difference, intersect, total, union
from chunking_lab.spans import Chunking, Span


def _chunking(text: str, cuts: list[tuple[int, int]], provenance, **kwargs) -> Chunking:
    return Chunking(
        spans=tuple(Span.over(text, a, b) for a, b in cuts),
        provenance=provenance,
        strategy=kwargs.pop("strategy", "hand-built"),
        **kwargs,
    )


# --------------------------------------------------------------------- ranges


def test_union_counts_each_character_once():
    assert union([(0, 10), (5, 15)]) == [(0, 15)]
    assert union([(0, 5), (10, 15)]) == [(0, 5), (10, 15)]
    assert union([]) == []


def test_total_counts_overlapping_ranges_twice():
    """Not a bug. `precision` wants this and `precision_omega` does not."""
    assert total([(0, 10), (5, 15)]) == 20
    assert total(union([(0, 10), (5, 15)])) == 15


def test_intersect_returns_none_when_ranges_do_not_touch():
    assert intersect((0, 10), (5, 15)) == (5, 10)
    assert intersect((0, 5), (10, 15)) is None


def test_difference_splits_a_range_when_the_target_lands_inside_it():
    assert difference([(0, 100)], (40, 60)) == [(0, 40), (60, 100)]
    assert difference([(0, 100)], (0, 100)) == []
    assert difference([(0, 100)], (200, 300)) == [(0, 100)]


# ----------------------------------------------------------- precision omega


def test_precision_omega_is_the_gold_over_the_chunks_that_hold_it(provenance):
    """A 10-character answer inside one 100-character chunk caps precision at 10%."""
    text = "x" * 300
    chunking = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    assert precision_omega(chunking, [(40, 50)]) == pytest.approx(0.10)


def test_tighter_chunks_raise_the_ceiling(provenance):
    """The whole argument for the metric, in two lines."""
    text = "x" * 300
    loose = _chunking(text, [(0, 300)], provenance)
    tight = _chunking(text, [(i, i + 20) for i in range(0, 300, 20)], provenance)
    assert precision_omega(tight, [(40, 50)]) > precision_omega(loose, [(40, 50)])


def test_overlap_lowers_the_ceiling(provenance):
    """The behaviour the original misreading would have hidden.

    A gold span touched by two overlapping chunks puts *both* chunks' full width
    in the denominator, not just enough of them to cover it.
    """
    text = "x" * 300
    disjoint = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    overlapping = _chunking(
        text,
        [(0, 100), (50, 150), (100, 200), (150, 250), (200, 300)],
        provenance,
        declared_overlap=50,
    )
    # Gold sitting inside the first chunk is touched by one chunk when they are
    # disjoint and by two when they overlap -- so the denominator grows from 100
    # characters to 150 for exactly the same answer.
    gold = [(60, 70)]
    assert precision_omega(disjoint, gold) == pytest.approx(10 / 100)
    assert precision_omega(overlapping, gold) == pytest.approx(10 / 150)


def test_precision_omega_ignores_retrieval_entirely(provenance):
    """Which is what makes it reproducible with no retriever and no model."""
    text = "x" * 300
    chunking = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    # No retrieved list is passed at all -- there is nowhere to put one.
    assert precision_omega(chunking, [(40, 50)]) > 0


def test_gold_spans_are_treated_as_a_set(provenance):
    """The paper defines the gold as a set of tokens, so overlapping excerpts merge."""
    text = "x" * 300
    chunking = _chunking(text, [(0, 300)], provenance)
    once = precision_omega(chunking, [(0, 100)])
    twice = precision_omega(chunking, [(0, 100), (50, 100)])
    assert once == pytest.approx(twice)


def test_no_gold_scores_zero_rather_than_dividing_by_zero(provenance):
    chunking = _chunking("x" * 100, [(0, 100)], provenance)
    assert precision_omega(chunking, []) == 0.0


# ------------------------------------------------------------------ scoring


def test_k_defaults_to_the_number_of_gold_bearing_chunks(provenance):
    """The reference's `retrieve=-1`, which is adaptive per question."""
    text = "x" * 300
    chunking = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    assert gold_bearing_chunks(chunking, [(40, 50)]) == 1
    assert gold_bearing_chunks(chunking, [(40, 50), (240, 250)]) == 2

    result = score(chunking, [(40, 50)], list(chunking.spans), question_id="q1")
    assert result.k == 1


def test_an_explicit_k_is_honoured_and_recorded(provenance):
    text = "x" * 300
    chunking = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    result = score(chunking, [(40, 50)], list(chunking.spans), question_id="q1", k=3)
    assert result.k == 3
    # Three chunks retrieved for a ten-character answer: precision is 10/300.
    assert result.precision == pytest.approx(10 / 300)
    assert result.recall == 1.0


def test_recall_falls_when_the_answer_is_not_in_the_retrieved_chunks(provenance):
    text = "x" * 300
    chunking = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    missed = score(chunking, [(240, 250)], [chunking.spans[0]], question_id="q1", k=1)
    assert missed.recall == 0.0
    assert missed.precision == 0.0
    # But the ceiling is unchanged: the cuts are the same wherever the retriever looked.
    assert missed.precision_omega == pytest.approx(0.10)


def test_an_answer_severed_across_two_chunks_is_only_half_recalled(provenance):
    """The failure a chunk-level metric cannot see at all (README section 6)."""
    text = "x" * 300
    chunking = _chunking(text, [(0, 100), (100, 200), (200, 300)], provenance)
    result = score(chunking, [(90, 110)], [chunking.spans[0]], question_id="q1", k=1)
    assert result.recall == pytest.approx(0.5)


def test_every_result_carries_the_strategy_and_the_path_that_produced_it(provenance):
    text = "x" * 300
    chunking = _chunking(
        text, [(0, 300)], provenance, strategy="fixed:300", code_path="tier-0/model-free"
    )
    result = score(chunking, [(0, 10)], list(chunking.spans), question_id="q7")
    assert result.strategy == "fixed:300"
    assert result.code_path == "tier-0/model-free"
    assert result.question_id == "q7"
    assert set(result.as_dict()) >= {"recall", "precision", "iou", "precision_omega", "k"}
