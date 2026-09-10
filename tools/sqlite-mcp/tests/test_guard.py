"""The safety boundary, tested without a model and without MCP.

Every refusal has to name the guard that produced it -- CONVENTIONS rule 5.
"""

from __future__ import annotations

import pytest
from sqlite_mcp.store import ReadOnlyDatabase, Refused


def test_insert_is_refused_and_names_the_guard(db):
    with pytest.raises(Refused) as excinfo:
        db.query("INSERT INTO orders (customer, total) VALUES ('mallory', 0)")

    assert excinfo.value.guard == "not-read-only"


def test_result_caps_rows_and_says_it_truncated(db):
    result = db.query("SELECT customer FROM orders ORDER BY id")

    assert result.columns == ["customer"]
    assert result.rows == [("ada",), ("bob",)]
    assert result.truncated is True
    assert result.row_limit == 2


def test_result_is_not_marked_truncated_when_it_fits(db):
    result = db.query("SELECT customer FROM orders WHERE customer = 'ada'")

    assert result.rows == [("ada",)]
    assert result.truncated is False


def test_second_statement_cannot_ride_along(db):
    with pytest.raises(Refused) as excinfo:
        db.query("SELECT 1; DROP TABLE orders")

    assert excinfo.value.guard == "multiple-statements"


def test_table_outside_the_allow_list_is_refused(tmp_path, db):
    scoped = ReadOnlyDatabase(db.path, max_rows=10, allowed_tables=["orders"])

    assert scoped.query("SELECT customer FROM orders").rows == [
        ("ada",),
        ("bob",),
        ("cy",),
        ("dee",),
    ]

    with pytest.raises(Refused) as excinfo:
        scoped.query("SELECT token FROM secrets")

    assert excinfo.value.guard == "table-not-allowed"
