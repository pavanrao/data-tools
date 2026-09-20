"""Candidate labels: unmatched findings grouped across runs, for a person to accept or reject."""

from __future__ import annotations

import pytest

META = {
    "heldout-a.md": {"role": "held-out", "source": "t"},
    "dev-b.html": {"role": "development", "source": "t"},
}


@pytest.fixture
def candidates(eval_script):
    return eval_script("candidates")


def stray(quote, habit="antithesis", severity="high"):
    return {"quote": quote, "habit": habit, "severity": severity, "line": 1, "why": ""}


def results(**by_setup):
    """{setup: [(run, draft, [findings])]} in the shape score.py writes."""
    out = {}
    for setup, entries in by_setup.items():
        runs: dict = {}
        for run, draft, findings in entries:
            runs.setdefault(str(run), {})[draft] = {"unlabelled": findings, "false_alarms": []}
        out[setup] = {"runs": runs}
    return out


def test_matching_findings_across_runs_and_setups_become_one_candidate(candidates, workspace):
    data = results(
        haiku=[(1, "heldout-a.md", [stray("It didn't degrade. It collapsed.")])],
        sonnet=[
            (1, "heldout-a.md", [stray("It collapsed.", habit="dramatic-beat")]),
            (2, "heldout-a.md", [stray("It didn't degrade. It collapsed.")]),
        ],
    )

    (only,) = candidates.gather(data, META, workspace / "drafts")

    assert only["draft"] == "heldout-a.md"
    assert only["quote"] == "It didn't degrade. It collapsed."
    assert only["line"] == 5
    assert only["habits"] == {"antithesis": 2, "dramatic-beat": 1}
    assert only["raised_by"] == {"haiku": 1, "sonnet": 2}


def test_candidate_ids_depend_only_on_draft_and_quote(candidates, workspace):
    one = results(haiku=[(1, "heldout-a.md", [stray("It didn't degrade. It collapsed.")])])
    other = results(sonnet=[(3, "heldout-a.md", [stray("It didn't  degrade. It collapsed.")])])

    (a,) = candidates.gather(one, META, workspace / "drafts")
    (b,) = candidates.gather(other, META, workspace / "drafts")

    assert a["id"] == b["id"]
    assert a["id"].startswith("heldout-a-c")


def test_a_quote_that_is_not_in_the_draft_cannot_be_a_candidate(candidates, workspace):
    data = results(haiku=[(1, "heldout-a.md", [stray("Words the draft never had.")])])

    assert candidates.gather(data, META, workspace / "drafts") == []


def test_false_alarms_on_clean_drafts_are_candidates_too(candidates, workspace):
    meta = {**META, "dev-b.html": {"role": "clean", "source": "t"}}
    data = {
        "haiku": {
            "runs": {
                "1": {
                    "dev-b.html": {
                        "unlabelled": [],
                        "false_alarms": [stray("Same idea, different engine.", "fragment")],
                    }
                }
            }
        }
    }

    (only,) = candidates.gather(data, meta, workspace / "drafts")

    assert only["draft"] == "dev-b.html"


def test_pattern_based_tools_are_not_a_source_of_candidates(candidates, workspace):
    for setup in ("linter", "vale", "wsc", "slopless"):
        data = results(**{setup: [(1, "heldout-a.md", [stray("Note that this matters.")])]})

        assert candidates.gather(data, META, workspace / "drafts") == [], setup


def test_candidates_raised_most_often_come_first(candidates, workspace):
    data = results(
        haiku=[(1, "heldout-a.md", [stray("Note that this matters."), stray("It collapsed.")])],
        sonnet=[(1, "heldout-a.md", [stray("It collapsed.")])],
    )

    found = candidates.gather(data, META, workspace / "drafts")

    assert [c["quote"] for c in found] == ["It collapsed.", "Note that this matters."]


def test_candidates_already_accepted_as_labels_are_left_out(candidates, workspace):
    data = results(haiku=[(1, "heldout-a.md", [stray("It didn't degrade. It collapsed.")])])

    still_open = candidates.gather(data, META, workspace / "drafts")
    accepted = candidates.gather(data, META, workspace / "drafts", exclude={still_open[0]["id"]})

    assert len(still_open) == 1 and accepted == []
