"""Query-time gating: the behaviour this tool exists to make possible.

Retrieval alone cannot see an ingestion gap -- an unread file contributes no
chunks to rank, so it is invisible to similarity search and the system answers
confidently from whatever else it has. These tests pin the alternative.
"""

from __future__ import annotations

import pytest
from ingest_ledger.query import Verdict, ask

pytestmark = pytest.mark.hostile


def test_refuses_when_the_answer_lived_in_a_sheet_that_never_read(indexed_rfp):
    conn, run_id, _ = indexed_rfp
    answer = ask(conn, run_id, "what are the payment schedule milestones?")

    assert answer.verdict is Verdict.ABSTAINED
    assert not answer.grounded
    assert any("pricing.xlsx" in gap.locator for gap in answer.gaps)
    assert "Payment Schedule" in answer.statement


def test_answers_normally_when_no_gap_bears_on_the_question(indexed_rfp):
    conn, run_id, _ = indexed_rfp
    answer = ask(conn, run_id, "who owns the intellectual property?")

    assert answer.verdict is Verdict.ANSWERED
    assert answer.grounded
    assert answer.passages
    assert "general_terms" in answer.passages[0].locator


def test_every_answer_carries_a_coverage_statement(indexed_rfp):
    conn, run_id, _ = indexed_rfp
    for question in ("payment schedule", "staffing on site", "acceptance pilot"):
        assert ask(conn, run_id, question).statement.strip()


def test_passages_are_traceable_to_their_source(indexed_rfp):
    conn, run_id, _ = indexed_rfp
    answer = ask(conn, run_id, "what staffing is required on site?")
    assert answer.passages
    for passage in answer.passages:
        assert passage.source.endswith(".md")
        assert passage.locator


def test_a_relaxed_ratio_discloses_instead_of_refusing(indexed_rfp):
    """The abstain threshold is a policy, not a law -- but silence is never an
    option: below it the gap is still disclosed in the statement."""
    conn, run_id, _ = indexed_rfp
    answer = ask(conn, run_id, "payment schedule milestones", abstain_ratio=99.0)

    assert answer.verdict is Verdict.ANSWERED_WITH_GAPS
    assert answer.grounded
    assert "incomplete" in answer.statement
    assert answer.gaps


def test_an_empty_index_with_gaps_refuses_rather_than_answering_nothing(indexed_rfp):
    conn, run_id, _ = indexed_rfp
    conn.execute("DELETE FROM chunks WHERE run_id = ?", (run_id,))
    answer = ask(conn, run_id, "payment schedule")

    assert answer.verdict is Verdict.ABSTAINED
    assert not answer.passages
