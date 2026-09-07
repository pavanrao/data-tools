"""Behaviour of the Tier 0 chunkers, and of the spec strings that name them."""

from __future__ import annotations

import pytest
from chunking_lab import from_spec
from chunking_lab.chunkers import FixedChunker, RecursiveChunker


def test_a_spec_round_trips_to_its_own_name():
    for spec in ["fixed:512", "fixed:512/64", "recursive:400", "recursive:400/200"]:
        assert from_spec(spec).name == spec


def test_a_zero_overlap_is_left_out_of_the_name():
    """`fixed:512/0` and `fixed:512` are the same run and must not be two rows."""
    assert from_spec("fixed:512/0").name == "fixed:512"


def test_an_unknown_strategy_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="known: fixed, recursive"):
        from_spec("magic:512")


def test_a_spec_without_a_size_is_refused():
    with pytest.raises(ValueError, match="needs a size"):
        from_spec("fixed")


def test_a_spec_with_a_non_numeric_size_is_refused():
    with pytest.raises(ValueError, match="could not read a size"):
        from_spec("fixed:big")


def test_overlap_must_be_smaller_than_the_chunk():
    with pytest.raises(ValueError, match=r"must be in \[0, 100\)"):
        FixedChunker(size=100, overlap=100)
    with pytest.raises(ValueError, match="must be positive"):
        RecursiveChunker(size=0)


def test_fixed_chunks_are_the_requested_size(prose, provenance):
    chunking = FixedChunker(size=100).chunk(prose, provenance)
    # Trimming shortens a span, never lengthens it; the last one is whatever is left.
    assert all(span.length <= 100 for span in chunking.spans)
    assert max(span.length for span in chunking.spans) > 80


def test_overlap_makes_the_index_bigger(prose, provenance):
    """The duplication factor overlap costs, visible before any metric exists."""
    tight = FixedChunker(size=100).chunk(prose, provenance)
    loose = FixedChunker(size=100, overlap=50).chunk(prose, provenance)
    assert sum(s.length for s in loose.spans) > sum(s.length for s in tight.spans)
    assert len(loose) > len(tight)


def test_recursive_prefers_paragraph_boundaries_over_arbitrary_cuts(provenance):
    """The whole point of the strategy: cut where the document already breaks."""
    text = "First paragraph, quite short.\n\nSecond paragraph, also short.\n\nThird one."
    chunking = RecursiveChunker(size=40).chunk(text, provenance)
    assert [text[s.start : s.end] for s in chunking.spans] == [
        "First paragraph, quite short.",
        "Second paragraph, also short.",
        "Third one.",
    ]


def test_a_size_larger_than_the_document_yields_one_span(prose, provenance):
    for chunker in (FixedChunker(size=100_000), RecursiveChunker(size=100_000)):
        chunking = chunker.chunk(prose, provenance)
        assert len(chunking) == 1
        assert chunking.spans[0].retrieval_text == prose.strip()


def test_a_document_with_no_separators_still_gets_split(provenance):
    """The terminal case: split into characters rather than emit an oversized chunk."""
    text = "x" * 250
    chunking = RecursiveChunker(size=100).chunk(text, provenance)
    assert len(chunking) > 1
    assert all(span.length <= 100 for span in chunking.spans)
