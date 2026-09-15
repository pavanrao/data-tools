"""The label build: ids that never move, and a file that refuses to be wrong quietly."""

from __future__ import annotations

import pytest

META = {
    "heldout-a.md": {"role": "held-out", "source": "test 0000000"},
    "dev-b.html": {"role": "development", "source": "test 0000000"},
}


def label(id, draft, quote, habit="antithesis", severity="high", **extra):
    return {
        "id": id,
        "draft": draft,
        "habit": habit,
        "severity": severity,
        "quote": quote,
        "source": "hand",
        **extra,
    }


def test_ids_come_from_the_file_not_from_position(eval_script, workspace):
    build = eval_script("build_labels").build
    labels = [
        label(
            "heldout-a-07", "heldout-a.md", "Note that this matters.", habit="reader-instruction"
        ),
        label("heldout-a-02", "heldout-a.md", "It didn't degrade. It collapsed."),
    ]

    out = build(META, labels, workspace / "drafts")

    assert [(x["id"], x["line"]) for x in out["labels"]] == [
        ("heldout-a-07", 7),
        ("heldout-a-02", 5),
    ]


@pytest.mark.parametrize(
    ("labels", "problem"),
    [
        (
            [
                label("heldout-a-01", "heldout-a.md", "It collapsed."),
                label("heldout-a-01", "heldout-a.md", "Note that"),
            ],
            "heldout-a-01 is used twice",
        ),
        (
            [label("dev-b-01", "heldout-a.md", "It collapsed.")],
            "dev-b-01 doesn't start with heldout-a-",
        ),
        (
            [label("heldout-a-1", "heldout-a.md", "It collapsed.")],
            "heldout-a-1 isn't <draft>-<number>",
        ),
        ([label("heldout-a-01", "heldout-a.md", "Not in the draft.")], "0 matches"),
        (
            [label("heldout-a-01", "heldout-a.md", "It collapsed.", habit="vibes")],
            "unknown habit 'vibes'",
        ),
        (
            [label("heldout-a-01", "heldout-a.md", "It collapsed.", status="gone")],
            "unknown status 'gone'",
        ),
        ([label("dev-c-01", "dev-c.md", "x")], "dev-c.md isn't in drafts.json"),
    ],
)
def test_a_bad_label_fails_the_build_and_names_the_problem(eval_script, workspace, labels, problem):
    build = eval_script("build_labels").build

    with pytest.raises(SystemExit, match=problem):
        build(META, labels, workspace / "drafts")


def test_a_draft_without_a_known_role_fails(eval_script, workspace):
    build = eval_script("build_labels").build
    meta = {**META, "dev-b.html": {"role": "training", "source": "x"}}

    with pytest.raises(SystemExit, match="dev-b.html has role 'training'"):
        build(meta, [], workspace / "drafts")


def test_dropped_labels_are_kept_out_of_scoring_but_still_checked(eval_script, workspace):
    build = eval_script("build_labels").build
    labels = [
        label("dev-b-01", "dev-b.html", "Same idea, different engine.", habit="fragment"),
        label(
            "dev-b-02", "dev-b.html", "Sit with that.", habit="reader-instruction", status="dropped"
        ),
    ]

    out = build(META, labels, workspace / "drafts")

    assert [x["id"] for x in out["labels"]] == ["dev-b-01"]
    assert [x["id"] for x in out["dropped"]] == ["dev-b-02"]


def test_the_next_id_skips_retired_numbers(eval_script):
    next_id = eval_script("build_labels").next_id
    labels = [
        label("heldout-a-01", "heldout-a.md", "x"),
        label("heldout-a-04", "heldout-a.md", "y", status="dropped"),
        label("dev-b-09", "dev-b.html", "z"),
    ]

    assert next_id(labels, "heldout-a.md") == "heldout-a-05"
    assert next_id(labels, "new-draft.md") == "new-draft-01"


def test_label_files_round_trip_one_label_per_line(eval_script, tmp_path):
    script = eval_script("build_labels")
    labels = [label("heldout-a-01", "heldout-a.md", "It’s “quoted” — here.")]
    path = tmp_path / "labels.jsonl"

    script.save_labels(path, labels)

    assert path.read_text(encoding="utf-8").count("\n") == 1
    assert script.load_labels(path) == labels


def test_the_committed_labels_build(eval_script):
    script = eval_script("build_labels")

    out = script.build(script.load_meta(), script.load_labels(script.LABELS_FILE), script.DRAFTS)

    assert len(out["labels"]) + len(out["dropped"]) == len(script.load_labels(script.LABELS_FILE))
