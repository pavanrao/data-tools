"""The CLI seam: usable without an agent, and it must not be able to write."""

from __future__ import annotations

import json

from sqlite_mcp.cli import main


def test_schema_command_lists_tables(db, capsys):
    assert main(["schema", str(db.path)]) == 0

    out = capsys.readouterr().out
    assert "orders" in out and "customer" in out


def test_query_command_prints_json_rows(db, capsys):
    assert main(["query", str(db.path), "SELECT customer FROM orders LIMIT 1", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == [["ada"]]


def test_write_from_the_cli_exits_nonzero_and_names_the_guard(db, capsys):
    assert main(["query", str(db.path), "DROP TABLE orders"]) == 1

    assert "not-read-only" in capsys.readouterr().err
