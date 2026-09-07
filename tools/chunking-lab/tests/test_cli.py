"""The command line surface, which is deliberately smaller than the design.

`score`, `suggest`, `explain` and `annotate` are specified in the README but not
built. They are absent from the parser rather than stubbed, so `--help` describes
what the tool can actually do today.
"""

from __future__ import annotations

import pytest
from chunking_lab.cli import main


def test_chunkers_lists_what_is_implemented(capsys):
    assert main(["chunkers"]) == 0
    out = capsys.readouterr().out
    assert "recursive" in out and "fixed" in out
    # and is honest about what is not
    assert "not built" in out


def test_split_shows_where_the_cuts_landed(tmp_path, prose, capsys):
    document = tmp_path / "notes.md"
    document.write_text(prose)

    assert main(["split", str(document), "--strategy", "recursive:120"]) == 0
    out = capsys.readouterr().out
    assert "recursive:120" in out
    assert "coverage" in out
    assert "notes.md" in out


def test_split_reports_an_unknown_strategy_without_a_traceback(tmp_path, prose, capsys):
    document = tmp_path / "notes.md"
    document.write_text(prose)

    assert main(["split", str(document), "--strategy", "magic:99"]) == 2
    assert "unknown strategy" in capsys.readouterr().err


def test_split_reports_a_missing_file_without_a_traceback(capsys):
    assert main(["split", "no-such-file.md", "--strategy", "fixed:100"]) == 2
    assert "No such file" in capsys.readouterr().err


def test_a_command_is_required(capsys):
    with pytest.raises(SystemExit):
        main([])


def test_main_has_a_one_line_docstring_for_dt_ls():
    """`dt ls` prints the first line of main.__doc__ as the tool's summary."""
    summary = (main.__doc__ or "").strip().splitlines()
    assert summary and len(summary[0]) < 80


def test_metrics_compares_several_strategies_on_one_document(tmp_path, prose, capsys):
    document = tmp_path / "notes.md"
    document.write_text(prose)

    exit_code = main(
        [
            "metrics",
            str(document),
            "--strategy",
            "fixed:100",
            "--strategy",
            "sentence:2",
        ]
    )
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "fixed:100" in out and "sentence:2" in out
    # The line the tool must never stop printing.
    assert "screen; they do not rank" in out


def test_metrics_reports_the_screening_verdict_for_each_strategy(tmp_path, capsys):
    document = tmp_path / "wide.md"
    document.write_text("word " * 2000)

    assert main(["metrics", str(document), "--strategy", "fixed:5000"]) == 0
    out = capsys.readouterr().out
    assert "DISQUALIFIED" in out
    assert "silent truncation" in out


def test_metrics_adds_cohesion_only_when_an_embedder_is_asked_for(tmp_path, prose, capsys):
    document = tmp_path / "notes.md"
    document.write_text(prose)

    assert main(["metrics", str(document), "--strategy", "sentence:2"]) == 0
    assert "cohes" not in capsys.readouterr().out

    assert (
        main(["metrics", str(document), "--strategy", "sentence:2", "--embedder", "hashing"]) == 0
    )
    assert "cohes" in capsys.readouterr().out


def test_split_reports_the_path_that_ran(tmp_path, prose, capsys):
    """Rule 2, visible at the command line rather than only in a result file."""
    document = tmp_path / "notes.md"
    document.write_text(prose)

    assert main(["split", str(document), "--strategy", "semantic:95"]) == 0
    assert "tier-1/embeddings:hashing-bow-v1" in capsys.readouterr().out

    assert main(["split", str(document), "--strategy", "recursive:200"]) == 0
    assert "tier-0/model-free" in capsys.readouterr().out
