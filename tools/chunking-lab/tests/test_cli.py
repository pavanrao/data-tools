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
