"""Behaviour of the Tier 0 chunkers, and of the spec strings that name them."""

from __future__ import annotations

import pytest
from chunking_lab import from_spec
from chunking_lab.chunkers import FixedChunker, RecursiveChunker


def test_a_spec_round_trips_to_its_own_name():
    for spec in [
        "fixed:512",
        "fixed:512/64",
        "recursive:400",
        "recursive:400/200",
        "sentence:3",
        "sentence:3/1",
        "structural",
        "structural:2000",
        "sentence-window:2",
        "parent-document:200/1000",
    ]:
        assert from_spec(spec).name == spec


def test_a_zero_overlap_is_left_out_of_the_name():
    """`fixed:512/0` and `fixed:512` are the same run and must not be two rows."""
    assert from_spec("fixed:512/0").name == "fixed:512"


def test_an_unknown_strategy_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="known: .*recursive.*structural"):
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


def test_structural_does_not_mistake_a_comment_in_a_code_fence_for_a_heading(provenance):
    """Getting this wrong shreds every code example in a document."""
    text = (
        "# Real Heading\n\nSome prose.\n\n"
        "```python\n# this is a comment, not a heading\nx = 1\n```\n\n"
        "More prose in the same section.\n"
    )
    chunking = from_spec("structural").chunk(text, provenance)
    assert len(chunking) == 1, "the fence was treated as a section boundary"
    assert "x = 1" in chunking.spans[0].retrieval_text


def test_structural_splits_at_real_headings(provenance):
    text = "# One\n\nalpha\n\n## Two\n\nbeta\n\n### Three\n\ngamma\n"
    chunking = from_spec("structural").chunk(text, provenance)
    assert [s.retrieval_text.splitlines()[0] for s in chunking.spans] == [
        "# One",
        "## Two",
        "### Three",
    ]


def test_sentence_window_indexes_narrowly_and_returns_widely(provenance):
    """The family-6 property that Span exists for."""
    text = "First one. Second one. Third one. Fourth one."
    chunking = from_spec("sentence-window:1").chunk(text, provenance)
    assert chunking.augmented

    second = chunking.spans[1]
    assert second.retrieval_text == "Second one."
    assert second.return_text == "First one. Second one. Third one."
    # The span still addresses only what was indexed -- that is what gets scored.
    assert text[second.start : second.end] == "Second one."


def test_a_zero_window_returns_exactly_what_it_indexed(provenance):
    text = "First one. Second one. Third one."
    chunking = from_spec("sentence-window:0").chunk(text, provenance)
    assert all(s.retrieval_text == s.return_text for s in chunking.spans)


def test_parent_document_returns_more_than_it_indexes(provenance):
    text = "".join(f"sentence number {i}. " for i in range(40))
    chunking = from_spec("parent-document:60/240").chunk(text, provenance)
    assert chunking.augmented
    assert all(len(s.return_text) >= len(s.retrieval_text) for s in chunking.spans)
    assert any(len(s.return_text) > len(s.retrieval_text) for s in chunking.spans)


def test_parent_must_not_be_smaller_than_child():
    with pytest.raises(ValueError, match="smaller than child size"):
        from_spec("parent-document:1000/200")


def test_sentence_packing_puts_several_sentences_in_one_chunk(provenance):
    text = "One. Two. Three. Four. Five. Six."
    single = from_spec("sentence:1").chunk(text, provenance)
    packed = from_spec("sentence:3").chunk(text, provenance)
    assert len(single) == 6
    assert len(packed) == 2
    assert packed.spans[0].retrieval_text == "One. Two. Three."
