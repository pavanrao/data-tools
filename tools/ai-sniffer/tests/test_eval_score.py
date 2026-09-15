"""Scoring: the matching rule, what counts toward recall, and what counts as a false alarm."""

from __future__ import annotations

import pytest

LONG = "It didn't degrade. It collapsed."


@pytest.fixture
def score(eval_script):
    return eval_script("score")


def label(id, quote, severity="high", draft="heldout-a.md", habit="antithesis", line=5, **extra):
    return {
        "id": id,
        "draft": draft,
        "line": line,
        "habit": habit,
        "severity": severity,
        "quote": quote,
        "source": "hand",
        **extra,
    }


def finding(quote, habit="antithesis", line=5, severity="high"):
    return {"line": line, "habit": habit, "severity": severity, "quote": quote, "why": ""}


# ---- the matching rule --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "matches"),
    [
        ("the whole argument for it in one incident", "That is the whole argument for it", True),
        ("abcdefghijklmnopqrs tail one", "head two abcdefghijklmnopqrs", False),  # 19 shared
        ("Note that", "Note that none of those three is about the protocol.", True),
        ("Note that", "Keep in mind the protocol.", False),
        ("Note that", "Note this down instead.", False),
        ("It’s  exactly — here", "it's exactly - here", True),  # normalised before comparing
    ],
)
def test_quotes_match_on_a_twenty_character_run_or_containment(score, a, b, matches):
    assert score.quotes_match(a, b) is matches


# ---- one run on one draft -----------------------------------------------------------------


def test_high_and_medium_labels_count_toward_recall_and_low_is_neutral(score, workspace):
    labels = [
        label("heldout-a-01", LONG, "high"),
        label("heldout-a-02", "Note that this matters.", "low", habit="reader-instruction", line=7),
    ]
    findings = [finding(LONG), finding("Note that this matters.", "reader-instruction", 7)]

    result = score.score_run("heldout-a.md", findings, labels, META, workspace / "drafts")

    assert result["caught"] == ["heldout-a-01"]
    assert result["recall_total"] == 1
    assert result["neutral"] == ["heldout-a-02"]
    assert result["false_alarms"] == [] and result["unlabelled"] == []


def test_a_label_found_twice_is_caught_once(score, workspace):
    labels = [label("heldout-a-01", LONG)]
    findings = [finding(LONG), finding("It collapsed.", "dramatic-beat")]

    result = score.score_run("heldout-a.md", findings, labels, META, workspace / "drafts")

    assert result["caught"] == ["heldout-a-01"]
    assert result["habit_agrees"] == 1


def test_a_catch_under_a_different_habit_counts_but_does_not_agree(score, workspace):
    labels = [label("heldout-a-01", LONG, habit="antithesis")]

    result = score.score_run(
        "heldout-a.md", [finding(LONG, "dramatic-beat")], labels, META, workspace / "drafts"
    )

    assert result["caught"] == ["heldout-a-01"]
    assert result["habit_agrees"] == 0


def test_unmatched_findings_are_false_alarms_only_on_clean_drafts(score, workspace):
    stray = [finding("Same idea, different engine.", "fragment", 1)]
    meta = {**META, "dev-b.html": {"role": "clean", "source": "t"}}

    clean = score.score_run("dev-b.html", stray, [], meta, workspace / "drafts")
    heldout = score.score_run("dev-b.html", stray, [], META, workspace / "drafts")

    assert [f["quote"] for f in clean["false_alarms"]] == ["Same idea, different engine."]
    assert clean["unlabelled"] == []
    assert heldout["false_alarms"] == []
    assert [f["quote"] for f in heldout["unlabelled"]] == ["Same idea, different engine."]


def test_findings_outside_the_scored_sections_are_set_aside(score, workspace):
    meta = {
        **META,
        "heldout-a.md": {"role": "held-out", "source": "t", "scored_line_ranges": [[7, 7]]},
    }
    findings = [finding(LONG, line=5), finding("Note that this matters.", line=7)]

    result = score.score_run("heldout-a.md", findings, [], meta, workspace / "drafts")

    assert [f["quote"] for f in result["set_aside"]] == [LONG]
    assert [f["quote"] for f in result["unlabelled"]] == ["Note that this matters."]


def test_a_finding_is_placed_by_its_quote_not_by_the_line_the_model_gave(score, workspace):
    meta = {
        **META,
        "heldout-a.md": {"role": "held-out", "source": "t", "scored_line_ranges": [[7, 7]]},
    }
    wrong_line = [finding("Note that this matters.", line=99)]

    result = score.score_run("heldout-a.md", wrong_line, [], meta, workspace / "drafts")

    assert result["set_aside"] == []
    assert result["quotes_not_in_draft"] == 0


def test_a_quote_that_is_not_in_the_draft_is_counted(score, workspace):
    result = score.score_run(
        "heldout-a.md", [finding("A sentence the draft never had.")], [], META, workspace / "drafts"
    )

    assert result["quotes_not_in_draft"] == 1


def test_model_sourced_labels_can_be_left_out(score, workspace):
    labels = [label("heldout-a-01", LONG), label("heldout-a-02", "It collapsed.", source="model")]

    with_model = score.score_run(
        "heldout-a.md", [finding(LONG)], labels, META, workspace / "drafts"
    )
    hand_only = score.score_run(
        "heldout-a.md", [finding(LONG)], labels, META, workspace / "drafts", hand_only=True
    )

    assert with_model["recall_total"] == 2
    assert hand_only["recall_total"] == 1


# ---- across runs --------------------------------------------------------------------------


def test_each_role_is_reported_as_the_lowest_and_highest_run(score):
    runs = {
        1: {"heldout-a.md": {"caught": ["x", "y"], "recall_total": 4, "false_alarms": []}},
        2: {"heldout-a.md": {"caught": ["x"], "recall_total": 4, "false_alarms": []}},
        3: {"heldout-a.md": {"caught": ["x", "y", "z"], "recall_total": 4, "false_alarms": []}},
    }

    summary = score.summarise(runs, META)

    assert summary["held-out"] == {
        "caught": {"min": 1, "max": 3},
        "of": 4,
        "false_alarms": {"min": 0, "max": 0},
        "runs": 3,
    }


def test_an_unparseable_run_is_recorded_as_catching_nothing(score, tmp_path):
    path = tmp_path / "run-1.md"
    path.write_text("I refuse to use JSON.")

    findings, ok = score.read_run(path)

    assert findings == [] and ok is False


META = {
    "heldout-a.md": {"role": "held-out", "source": "t"},
    "dev-b.html": {"role": "development", "source": "t"},
}
