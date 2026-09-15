"""Applying review-page marks to labels.jsonl: nothing lost, nothing applied twice."""

from __future__ import annotations

import json

import pytest

META = {
    "heldout-a.md": {"role": "held-out", "source": "t"},
    "dev-b.html": {"role": "development", "source": "t"},
}
AT = "2026-09-15T12:00:00.000Z"
SIT = {
    "draft": "dev-b.html",
    "quote": "Sit with that.",
    "habit": "reader-instruction",
    "severity": "high",
    "note": "",
    "createdAt": AT,
}


@pytest.fixture
def apply(eval_script, workspace):
    script = eval_script("apply_marks")

    def run(labels, decisions=None, missed=None):
        return script.apply(labels, decisions or {}, missed or {}, META, workspace / "drafts")

    return run


def labels():
    return [
        {"id": "heldout-a-01", "draft": "heldout-a.md", "habit": "antithesis", "severity": "high",
         "quote": "It didn't degrade. It collapsed.", "source": "hand"},
        {"id": "heldout-a-02", "draft": "heldout-a.md", "habit": "reader-instruction",
         "severity": "medium", "quote": "Note that this matters.", "source": "hand"},
        {"id": "dev-b-01", "draft": "dev-b.html", "habit": "fragment", "severity": "high",
         "quote": "Same idea, different engine.", "source": "hand"},
    ]  # fmt: skip


def mark(verdict, note="", **extra):
    return {"verdict": verdict, "draft": "heldout-a.md", "note": note, "updatedAt": AT, **extra}


def by_id(result):
    return {x["id"]: x for x in result.labels}


def test_keep_records_the_review_and_changes_nothing_else(apply):
    result = apply(labels(), {"heldout-a-01": mark("keep")})

    got = by_id(result)["heldout-a-01"]
    assert got["review"] == {"verdict": "keep", "at": AT}
    assert {k: v for k, v in got.items() if k != "review"} == labels()[0]


def test_unmarked_labels_are_left_exactly_as_they_were(apply):
    result = apply(labels(), {"heldout-a-01": mark("keep")})

    assert by_id(result)["dev-b-01"] == labels()[2]


def test_change_keeps_the_original_values_under_was(apply):
    decisions = {
        "heldout-a-01": mark("change", habit="fragment", severity="low", note="borderline")
    }

    got = by_id(apply(labels(), decisions))["heldout-a-01"]

    assert (got["habit"], got["severity"]) == ("fragment", "low")
    assert got["was"] == {"habit": "antithesis", "severity": "high"}
    assert got["review"] == {"verdict": "change", "at": AT, "note": "borderline"}


def test_applying_the_same_export_twice_gives_the_same_labels(apply):
    decisions = {"heldout-a-01": mark("change", habit="fragment", severity="low")}
    missed = {"m1": SIT}

    once = apply(labels(), decisions, missed).labels
    twice = apply(once, decisions, missed).labels

    assert twice == once
    assert by_id(apply(once, decisions, missed))["heldout-a-01"]["was"]["habit"] == "antithesis"


def test_drop_keeps_the_label_in_the_file_marked_dropped(apply):
    got = by_id(apply(labels(), {"heldout-a-02": mark("drop", note="it's fine")}))["heldout-a-02"]

    assert got["status"] == "dropped"
    assert got["review"]["verdict"] == "drop"


def test_a_later_keep_restores_a_dropped_label(apply):
    dropped = apply(labels(), {"heldout-a-02": mark("drop")}).labels

    got = by_id(apply(dropped, {"heldout-a-02": mark("keep")}))["heldout-a-02"]

    assert "status" not in got


def test_a_note_without_a_mark_is_attached_and_counts_as_keep(apply):
    got = by_id(apply(labels(), {"heldout-a-01": mark("", note="quote should stop at degrade")}))[
        "heldout-a-01"
    ]

    assert got["review"] == {"at": AT, "note": "quote should stop at degrade"}
    assert "status" not in got


def test_a_missed_habit_becomes_a_label_with_the_next_id(apply):
    missed = {"m1": {**SIT, "note": "classic"}}

    result = apply(labels(), {}, missed)

    new = by_id(result)["dev-b-02"]
    assert new == {
        "id": "dev-b-02",
        "draft": "dev-b.html",
        "habit": "reader-instruction",
        "severity": "high",
        "quote": "Sit with that.",
        "source": "hand",
        "missed_id": "m1",
        "review": {"verdict": "added", "at": AT, "note": "classic"},
    }


@pytest.mark.parametrize(
    ("item", "reason"),
    [
        ({"quote": "Not in the draft."}, "0 matches"),
        ({"habit": "other", "note": "a rhetorical question"}, "habit 'other'"),
    ],
)
def test_a_missed_habit_that_cannot_be_added_is_skipped_with_a_reason(apply, item, reason):
    result = apply(labels(), {}, {"m1": {**SIT, **item}})

    assert len(result.labels) == 3
    assert any(reason in line for line in result.skipped)


def test_a_mark_for_a_label_that_does_not_exist_stops_everything(apply):
    with pytest.raises(SystemExit, match="heldout-a-99"):
        apply(labels(), {"heldout-a-99": mark("keep")})


def test_the_summary_says_what_happened(apply):
    decisions = {
        "heldout-a-01": mark("keep"),
        "heldout-a-02": mark("drop"),
        "dev-b-01": mark("change", habit="triad", severity="high"),
    }

    summary = apply(labels(), decisions).summary

    assert summary == {
        "keep": 1, "change": 1, "drop": 1, "note": 0, "added": 0, "accepted": 0, "rejected": 0
    }  # fmt: skip


def test_marks_are_read_from_a_database_export(eval_script, tmp_path):
    read_marks = eval_script("apply_marks").read_marks
    (tmp_path / "decisions").mkdir()
    (tmp_path / "decisions" / "heldout-a-01.json").write_text(json.dumps(mark("keep")))

    decisions, missed, candidates = read_marks(tmp_path)

    assert decisions == {"heldout-a-01": mark("keep")}
    assert missed == {} and candidates == {}


# ---- candidates from model runs -----------------------------------------------------------

CANDIDATE = {
    "verdict": "accept",
    "draft": "dev-b.html",
    "quote": "Sit with that.",
    "habit": "reader-instruction",
    "severity": "high",
    "note": "",
    "updatedAt": AT,
}


def test_an_accepted_candidate_becomes_a_model_sourced_label(eval_script, workspace):
    script = eval_script("apply_marks")

    result = script.apply(
        labels(), {}, {}, META, workspace / "drafts", candidates={"dev-b-c1a2b3": CANDIDATE}
    )

    new = by_id(result)["dev-b-02"]
    assert new["source"] == "model"
    assert new["candidate_id"] == "dev-b-c1a2b3"
    assert new["review"] == {"verdict": "accepted", "at": AT}
    assert result.summary["accepted"] == 1


def test_rejecting_a_candidate_adds_nothing_and_accepting_twice_adds_once(eval_script, workspace):
    script = eval_script("apply_marks")

    def run(existing, marks):
        return script.apply(existing, {}, {}, META, workspace / "drafts", candidates=marks)

    rejected = run(labels(), {"dev-b-c1a2b3": {**CANDIDATE, "verdict": "reject"}})
    once = run(labels(), {"dev-b-c1a2b3": CANDIDATE}).labels
    twice = run(once, {"dev-b-c1a2b3": CANDIDATE}).labels

    assert len(rejected.labels) == 3 and rejected.summary["rejected"] == 1
    assert twice == once


def test_rejecting_a_candidate_that_was_accepted_earlier_drops_its_label(eval_script, workspace):
    script = eval_script("apply_marks")
    accepted = script.apply(
        labels(), {}, {}, META, workspace / "drafts", candidates={"dev-b-c1a2b3": CANDIDATE}
    ).labels

    result = script.apply(
        accepted,
        {},
        {},
        META,
        workspace / "drafts",
        candidates={"dev-b-c1a2b3": {**CANDIDATE, "verdict": "reject"}},
    )

    assert by_id(result)["dev-b-02"]["status"] == "dropped"
