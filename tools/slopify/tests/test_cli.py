"""The CLI is the seam the eval uses, so its outputs are the thing under test."""

import json

import pytest
from slopify.cli import main

DRAFT = """The retriever ranks every chunk against the question and returns the top few of
them. It is a simple component and it never changes between runs of the tool.

We measured 472 questions on the corpus and the score was 17.7 for that run. The
boundaries were fixed before the retriever ever saw them.
"""


@pytest.fixture
def draft(tmp_path):
    path = tmp_path / "draft.md"
    path.write_text(DRAFT, encoding="utf-8")
    return path


def test_inject_writes_the_slopped_draft_to_stdout(draft, capsys):
    assert main(["inject", str(draft), "--seed", "4", "--count", "2"]) == 0
    assert capsys.readouterr().out.strip()


def test_inject_writes_labels_when_asked(draft, tmp_path, capsys):
    labels = tmp_path / "labels.jsonl"
    out = tmp_path / "slopped.md"
    code = main(
        [
            "inject",
            str(draft),
            "--seed",
            "4",
            "--count",
            "3",
            "--out",
            str(out),
            "--labels",
            str(labels),
        ]
    )
    assert code == 0
    records = [json.loads(line) for line in labels.read_text().splitlines()]
    assert records
    text = out.read_text()
    for record in records:
        assert record["source"] == "injected"
        assert record["draft"] == out.name
        assert " ".join(record["quote"].split()[:4]) in " ".join(text.split())


def test_the_same_seed_twice_gives_identical_files(draft, tmp_path):
    outs = []
    for run in ("a", "b"):
        out = tmp_path / f"{run}.md"
        main(["inject", str(draft), "--seed", "9", "--count", "3", "--out", str(out)])
        outs.append(out.read_text())
    assert outs[0] == outs[1]


def test_habit_can_be_restricted(draft, tmp_path):
    labels = tmp_path / "labels.jsonl"
    main(
        [
            "inject",
            str(draft),
            "--seed",
            "2",
            "--count",
            "4",
            "--habit",
            "hedge",
            "--labels",
            str(labels),
        ]
    )
    records = [json.loads(line) for line in labels.read_text().splitlines()]
    assert {r["habit"] for r in records} == {"hedge"}


def test_an_unknown_habit_is_refused_by_name(draft, capsys):
    assert main(["inject", str(draft), "--habit", "purple-prose"]) == 2
    assert "purple-prose" in capsys.readouterr().err


def test_habits_lists_the_catalogue(capsys):
    assert main(["habits"]) == 0
    out = capsys.readouterr().out
    assert "antithesis" in out and "reader-instruction" in out


def test_a_missing_file_is_an_error_not_a_traceback(tmp_path, capsys):
    assert main(["inject", str(tmp_path / "nope.md")]) == 2
    assert "nope.md" in capsys.readouterr().err
