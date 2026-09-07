"""The query-free metrics, and the line they must not cross.

These screen. They do not rank -- and the tests are written so that a future
change trying to make them rank has to delete an assertion that says so.
"""

from __future__ import annotations

import pytest
from chunking_lab import from_spec, measure
from chunking_lab.embeddings import HashingEmbedder
from chunking_lab.intrinsic import ORPHAN_OPENER, Intrinsic

TABLE_DOC = """## Rates

| Region | Q1 | Q2 |
|--------|----|----|
| North  | 12 | 19 |
| South  |  7 |  4 |

Totals exclude the Northeast.
"""

FENCE_DOC = """Install it, then run:

```python
def split(text, size):
    return [text[i : i + size] for i in range(0, len(text), size)]
```

That is the whole of fixed-size chunking.
"""


def test_duplication_measures_exactly_what_overlap_costs(prose, provenance):
    tight = measure(from_spec("fixed:100").chunk(prose, provenance), prose)
    loose = measure(from_spec("fixed:100/50").chunk(prose, provenance), prose)
    assert tight.duplication == pytest.approx(1.0, abs=0.02)
    assert loose.duplication > 1.8


def test_return_amplification_separates_family_6_from_everything_else(prose, provenance):
    """The number that makes the trade sentence-window is making visible."""
    plain = measure(from_spec("sentence:1").chunk(prose, provenance), prose)
    window = measure(from_spec("sentence-window:1").chunk(prose, provenance), prose)

    # Both index the same text ...
    assert window.duplication == pytest.approx(plain.duplication, abs=0.01)
    # ... and one of them returns more than twice as much of it. (Not 3x: the
    # first and last sentences have only one neighbour each.)
    assert window.return_amplification > 2.0 * plain.return_amplification


def test_boundary_fidelity_separates_fixed_size_from_structure_aware(prose, provenance):
    """The signal that motivates every strategy past fixed-size."""
    blind = measure(from_spec("fixed:100").chunk(prose, provenance), prose)
    aware = measure(from_spec("sentence:2").chunk(prose, provenance), prose)
    assert aware.boundary_fidelity > 0.9
    assert blind.boundary_fidelity < 0.4


def test_a_cut_inside_a_table_row_is_counted(provenance):
    """The table-shredding failure, caught with no questions and no model."""
    shredder = measure(from_spec("fixed:30").chunk(TABLE_DOC, provenance), TABLE_DOC)
    intact = measure(from_spec("structural").chunk(TABLE_DOC, provenance), TABLE_DOC)
    assert shredder.mid_table_rate > 0
    assert intact.mid_table_rate == 0


def test_a_code_fence_cut_in_half_is_counted(provenance):
    shredder = measure(from_spec("fixed:60").chunk(FENCE_DOC, provenance), FENCE_DOC)
    intact = measure(from_spec("structural").chunk(FENCE_DOC, provenance), FENCE_DOC)
    assert shredder.split_fence_rate > 0
    assert intact.split_fence_rate == 0


def test_orphaned_openers_are_detected(provenance):
    text = (
        "The pipeline reconciles what it was given. "
        "As described above, this is not the same as reading every byte. "
        "Therefore the ledger records both numbers."
    )
    metrics = measure(from_spec("sentence:1").chunk(text, provenance), text)
    assert metrics.orphan_rate == pytest.approx(2 / 3)


@pytest.mark.parametrize(
    "opener",
    [
        "As described above, the ledger records both.",
        "The table below lists every probe.",
        "This is why the number matters.",
        "It reconciles the two counts.",
        "Therefore the run is rejected.",
        "The latter is what we measure.",
    ],
)
def test_known_anaphora_are_matched(opener):
    assert ORPHAN_OPENER.match(opener)


@pytest.mark.parametrize(
    "opener",
    [
        "The pipeline read every file it was given.",
        "Reconciliation compares two counts.",
        "Chunking decides what a retriever can find.",
    ],
)
def test_self_contained_openers_are_not_matched(opener):
    assert not ORPHAN_OPENER.match(opener)


def test_content_coverage_ignores_whitespace_but_never_content(prose, provenance):
    """The false positive that made plain coverage useless for screening."""
    trimming = measure(from_spec("recursive:120").chunk(prose, provenance), prose)
    assert trimming.coverage < 1.0  # whitespace lost at the boundaries
    assert trimming.content_coverage == 1.0  # and no content at all
    assert "content" not in " ".join(trimming.disqualifications())


def test_oversize_chunks_are_screened_out(provenance):
    text = "word " * 2000
    metrics = measure(from_spec("fixed:5000").chunk(text, provenance), text)
    assert metrics.oversize_rate > 0
    assert any("silent truncation" in reason for reason in metrics.disqualifications())


def test_a_clean_configuration_is_eligible_not_good(prose, provenance):
    """Screening says 'not disqualified'. It never says 'best'."""
    metrics = measure(from_spec("sentence:3").chunk(prose, provenance), prose)
    assert metrics.disqualifications() == []


def test_cohesion_and_separation_are_absent_unless_an_embedder_is_given(prose, provenance):
    """Everything else in this module is free. These two are not, and it shows."""
    free = measure(from_spec("sentence:2").chunk(prose, provenance), prose)
    assert free.cohesion is None and free.separation is None
    assert free.code_path == "tier-0/model-free"

    paid = measure(
        from_spec("sentence:2").chunk(prose, provenance), prose, embedder=HashingEmbedder()
    )
    assert paid.cohesion is not None and paid.separation is not None
    assert "hashing-bow-v1" in paid.code_path


def test_metrics_serialise_flat_for_a_result_row(prose, provenance):
    row = measure(from_spec("recursive:200").chunk(prose, provenance), prose).as_dict()
    assert row["strategy"] == "recursive:200"
    assert row["code_path"] == "tier-0/model-free"
    assert set(row) == {field for field in Intrinsic.__dataclass_fields__}


def test_an_empty_chunking_is_refused_rather_than_scored(provenance):
    from chunking_lab.spans import Chunking

    empty = Chunking(spans=(), provenance=provenance, strategy="nothing")
    with pytest.raises(ValueError, match="the chunking is empty"):
        measure(empty, "some text")
