"""The CLI end to end, on the plain DuckDB engine."""

from __future__ import annotations

import json

from kimball_lab.cli import main
from kimball_lab.engine import open_engine


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


def test_load_twice_loads_once(tmp_path, seed_dir):
    db = tmp_path / "lab.duckdb"
    assert (
        main(["load", str(seed_dir), "--db", str(db), "--engine", "duckdb", "--through", "2025-02"])
        == 0
    )
    assert (
        main(["load", str(seed_dir), "--db", str(db), "--engine", "duckdb", "--through", "2025-03"])
        == 0
    )
    engine = open_engine(db)
    try:
        batches = engine.rows("SELECT batch_id FROM etl_batch_log ORDER BY 1")
        total, distinct = engine.rows(
            "SELECT count(*), count(DISTINCT txn_id) FROM fact_transaction"
        )[0]
    finally:
        engine.close()
    assert [b[0] for b in batches] == ["2025-01", "2025-02", "2025-03"]
    assert total == distinct


def test_list(capsys):
    assert main(["list"]) == 0
    assert "02  Surrogate keys" in capsys.readouterr().out
