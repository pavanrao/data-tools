"""The invariant every chunker must satisfy.

Written before the chunkers, and run against all of them, because the bug it
exists to catch -- a splitter that quietly drops a trailing paragraph -- produces
a run that succeeds and scores that look plausible.
"""

from __future__ import annotations

import pytest
from chunking_lab import Chunking, InvariantViolation, Span, check, coverage, from_spec
from data_tools_core.provenance import Provenance, UnitKind


def test_every_strategy_satisfies_the_invariant(prose, provenance, specs):
    for spec in specs:
        chunking = from_spec(spec).chunk(prose, provenance)
        check(chunking, prose)  # raises on violation
        assert len(chunking) > 0


def test_no_strategy_drops_a_single_non_whitespace_character(prose, provenance, specs):
    for spec in specs:
        chunking = from_spec(spec).chunk(prose, provenance)
        seen = "".join(prose[s.start : s.end] for s in chunking.spans)
        for character in set(prose) - set(" \n\t"):
            assert prose.count(character) <= seen.count(character), (
                f"{spec} lost occurrences of {character!r}"
            )


def test_a_dropped_paragraph_is_caught(prose, provenance):
    """The regression this whole module exists for."""
    full = from_spec("recursive:120").chunk(prose, provenance)
    truncated = Chunking(
        spans=full.spans[:-1],
        provenance=provenance,
        strategy="recursive:120 (with its tail dropped)",
        lossless=False,
    )
    with pytest.raises(InvariantViolation, match="non-whitespace characters are in no span"):
        check(truncated, prose)


def test_undeclared_overlap_is_caught(prose, provenance):
    overlapping = from_spec("fixed:120/30").chunk(prose, provenance)
    undeclared = Chunking(
        spans=overlapping.spans,
        provenance=provenance,
        strategy="fixed:120/30 (not declaring its overlap)",
        declared_overlap=0,
        lossless=False,
    )
    with pytest.raises(InvariantViolation, match="overlap by"):
        check(undeclared, prose)


def test_a_span_past_the_end_is_caught(provenance):
    text = "short document"
    runaway = Chunking(
        spans=(Span(start=0, end=99, retrieval_text=text, return_text=text),),
        provenance=provenance,
        strategy="runaway",
    )
    with pytest.raises(InvariantViolation, match="runs past the document"):
        check(runaway, text)


def test_return_text_must_match_the_offsets_unless_augmentation_is_declared(provenance):
    """Family 6 changes what is returned. It has to say so."""
    text = "the answer is 42"
    lying = Chunking(
        spans=(Span(start=0, end=len(text), retrieval_text=text, return_text="something else"),),
        provenance=provenance,
        strategy="not-declaring-augmentation",
    )
    with pytest.raises(InvariantViolation, match="does not declare augmentation"):
        check(lying, text)

    honest = Chunking(
        spans=lying.spans,
        provenance=provenance,
        strategy="declaring-augmentation",
        augmented=True,
    )
    check(honest, text)


def test_a_degenerate_span_cannot_be_constructed():
    with pytest.raises(ValueError, match="degenerate span"):
        Span(start=5, end=5, retrieval_text="", return_text="")


def test_coverage_is_reported_not_asserted(prose, provenance):
    """Trimming loses whitespace, and that is allowed -- but it must be visible."""
    chunking = from_spec("recursive:120").chunk(prose, provenance)
    fraction = coverage(chunking, prose)
    assert 0.9 < fraction <= 1.0

    whole = Chunking(
        spans=(Span.over(prose, 0, len(prose)),),
        provenance=Provenance(
            source=provenance.source, sha256=provenance.sha256, unit_kind=UnitKind.DOCUMENT
        ),
        strategy="whole-document",
    )
    assert coverage(whole, prose) == 1.0
