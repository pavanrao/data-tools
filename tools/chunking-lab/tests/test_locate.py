"""Quote-then-locate: turning a quoted answer into exact offsets, or discarding it.

C9's mechanism. The point is not that it always succeeds -- it is that when it
fails it fails *visibly*, by producing less ground truth rather than wrong ground
truth.
"""

from __future__ import annotations

from chunking_lab.locate import FUZZY_FLOOR, locate, locate_all

DOC = (
    "The audit log records every administrative action taken against a tenant.\n"
    "It is retained for seven years and then destroyed. Other logs follow the\n"
    "standard ninety-day schedule."
)


def test_an_exact_quote_is_found_exactly():
    found = locate(DOC, "It is retained for seven years and then destroyed")
    assert found is not None
    assert found.how == "exact"
    assert DOC[found.span[0] : found.span[1]] == "It is retained for seven years and then destroyed"


def test_a_trailing_full_stop_is_forgiven():
    """Models add and drop them freely; the reference implementation strips one too."""
    assert locate(DOC, "It is retained for seven years and then destroyed.") is not None


def test_a_quote_that_collapsed_a_line_break_is_still_found():
    """The most common way a verbatim quote stops being verbatim."""
    found = locate(DOC, "Other logs follow the standard ninety-day schedule")
    assert found is not None
    assert found.how == "whitespace"
    assert "\n" in DOC[found.span[0] : found.span[1]]


def test_doubled_spaces_are_forgiven():
    found = locate(DOC, "It  is retained   for seven years and then destroyed")
    assert found is not None
    assert found.how == "whitespace"


def test_an_invented_quote_is_discarded_rather_than_approximated():
    """The property the whole design rests on: no answer beats a wrong answer."""
    assert locate(DOC, "Records are kept for three years under the retention policy") is None


def test_an_empty_quote_is_discarded():
    assert locate(DOC, "   ") is None
    assert locate(DOC, ".") is None


def test_the_fuzzy_floor_is_severe_on_purpose():
    """A near-miss quote produces a wrong gold span, which scores every strategy
    against the wrong answer. Missing ground truth is strictly better."""
    assert FUZZY_FLOOR >= 95
    # One word changed in a short sentence falls below the floor.
    assert locate(DOC, "Other logs follow the standard thirty-day schedule") is None


def test_locate_all_reports_the_yield():
    """Model quality shows up as a number instead of corrupting the results."""
    found, missing = locate_all(
        DOC,
        [
            "The audit log records every administrative action taken against a tenant",
            "It is retained for seven years and then destroyed",
            "Backups are encrypted at rest with a per-tenant key",
        ],
    )
    assert len(found) == 2
    assert missing == ["Backups are encrypted at rest with a per-tenant key"]


def test_how_is_recorded_so_a_weak_corpus_is_visible():
    """A gold set built mostly from fuzzy matches is less trustworthy, and says so."""
    exact = locate(DOC, "It is retained for seven years and then destroyed")
    loose = locate(DOC, "Other logs follow the standard ninety-day schedule")
    assert {exact.how, loose.how} == {"exact", "whitespace"}
