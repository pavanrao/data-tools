"""End-to-end CLI behaviour, including the exit codes callers branch on."""

from __future__ import annotations

import pytest
from ingest_ledger.cli import main

pytestmark = pytest.mark.hostile


def test_report_strict_exits_nonzero_when_anything_is_quarantined(hostile, tmp_path, capsys):
    root = next(iter(hostile.values())).parent
    code = main(
        ["report", "--in-process", "--strict", "--ledger", str(tmp_path / "l.db"), str(root)]
    )
    assert code == 1
    assert "quarantined" in capsys.readouterr().out


def test_manifest_never_extracts(hostile, capsys):
    """`manifest` must be safe to run on anything -- it only reads structure."""
    root = next(iter(hostile.values())).parent
    assert main(["manifest", str(root)]) == 0
    out = capsys.readouterr().out
    assert "sheets" in out and "pages" in out


def test_index_then_ask_refuses_with_exit_code_three(rfp, tmp_path, capsys):
    root = next(iter(rfp.values())).parent
    db = str(tmp_path / "rfp.db")

    assert main(["index", "--in-process", "--ledger", db, str(root)]) == 0
    capsys.readouterr()

    assert main(["ask", "--ledger", db, "what are the payment schedule milestones?"]) == 3
    out = capsys.readouterr().out
    assert "ABSTAINED" in out
    assert "pricing.xlsx" in out


def test_ask_answers_when_no_gap_is_relevant(rfp, tmp_path, capsys):
    root = next(iter(rfp.values())).parent
    db = str(tmp_path / "rfp.db")
    main(["index", "--in-process", "--ledger", db, str(root)])
    capsys.readouterr()

    assert main(["ask", "--ledger", db, "who owns the intellectual property?"]) == 0
    assert "ANSWERED" in capsys.readouterr().out


def test_ask_without_an_index_says_so(tmp_path, capsys):
    assert main(["ask", "--ledger", str(tmp_path / "empty.db"), "anything"]) == 2
    assert "index" in capsys.readouterr().err
