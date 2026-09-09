"""Schema and sample: the two reads that are not arbitrary SQL."""

from __future__ import annotations

import pytest
from sqlite_mcp.store import ReadOnlyDatabase, Refused


def test_schema_lists_tables_and_columns(db):
    tables = {t.name: t for t in db.schema()}

    assert sorted(tables) == ["orders", "secrets"]
    orders = [(c.name, c.primary_key) for c in tables["orders"].columns]
    assert orders == [("id", True), ("customer", False), ("total", False)]


def test_schema_hides_tables_outside_the_allow_list(db):
    scoped = ReadOnlyDatabase(db.path, allowed_tables=["orders"])

    assert [t.name for t in scoped.schema()] == ["orders"]


def test_sample_returns_rows_from_one_table(db):
    result = db.sample("orders", limit=1)

    assert result.rows == [(1, "ada", 10.0)]


def test_sample_refuses_a_table_it_does_not_expose(db):
    scoped = ReadOnlyDatabase(db.path, allowed_tables=["orders"])

    with pytest.raises(Refused) as excinfo:
        scoped.sample("secrets")

    assert excinfo.value.guard == "table-not-allowed"
