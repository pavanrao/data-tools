"""The CLI seam: output a script can parse, and exit codes it can branch on."""

from __future__ import annotations

import json

from ai_sniffer.cli import main

HABITS = "Note that it failed.\n\nIt didn't degrade.\n"
CLEAN = "I ran it twice on 14 September. Both runs matched, so I stopped there.\n"


def test_check_prints_json_with_findings_metrics_and_closers(tmp_path, capsys):
    draft = tmp_path / "post.md"
    draft.write_text(HABITS)

    code = main(["check", "--json", str(draft)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["path"] == str(draft)
    assert payload["format"] == "markdown"
    assert {f["signal"] for f in payload["findings"]} == {
        "reader-instruction",
        "one-sentence-paragraph",
    }
    assert set(payload["findings"][0]) == {"signal", "line", "quote", "sentence"}
    assert "contractions_per_100_words" in payload["metrics"]
    assert payload["closers"]


def test_findings_exit_zero_by_default_and_one_under_strict(tmp_path):
    draft = tmp_path / "post.md"
    draft.write_text(HABITS)

    assert main(["check", str(draft)]) == 0
    assert main(["check", "--strict", str(draft)]) == 1


def test_strict_on_clean_text_exits_zero(tmp_path):
    draft = tmp_path / "post.md"
    draft.write_text(CLEAN)

    assert main(["check", "--strict", str(draft)]) == 0


def test_an_unreadable_file_exits_two_and_says_why(tmp_path, capsys):
    code = main(["check", str(tmp_path / "missing.md")])

    assert code == 2
    assert "missing.md" in capsys.readouterr().err


def test_an_unsupported_extension_exits_two(tmp_path, capsys):
    draft = tmp_path / "post.docx"
    draft.write_text("x")

    assert main(["check", str(draft)]) == 2
    assert ".docx" in capsys.readouterr().err


def test_the_text_report_names_each_finding_by_line(tmp_path, capsys):
    draft = tmp_path / "post.md"
    draft.write_text(HABITS)

    main(["check", str(draft)])

    out = capsys.readouterr().out
    assert "1  reader-instruction  Note that" in out
    assert "3  one-sentence-paragraph  It didn't degrade." in out
