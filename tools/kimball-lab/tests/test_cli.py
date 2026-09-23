"""The CLI end to end, on the plain DuckDB engine."""

from __future__ import annotations

import json

from kimball_lab.cli import main


def test_seed_load_demo(tmp_path, capsys):
    out, db = tmp_path / "bank", tmp_path / "lab.duckdb"
    assert main(["seed", "--out", str(out), "--scale", "1"]) == 0
    assert (
        main(["load", str(out), "--db", str(db), "--engine", "duckdb", "--through", "2025-03"]) == 0
    )
    capsys.readouterr()
    main(["demo", "02", "--db", str(db), "--json"])
    record = json.loads(capsys.readouterr().out)[0]
    assert record["technique"] == "02"
    assert record["engine"] == "duckdb"


def test_list(capsys):
    assert main(["list"]) == 0
    assert "02  Surrogate keys" in capsys.readouterr().out
