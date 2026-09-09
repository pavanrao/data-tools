"""Shared fixtures.

The suite runs under --import-mode=importlib, where a bare
``from test_guard import db`` does not resolve. CONVENTIONS rule 6: shared test
state is passed as a fixture, not imported.
"""

from __future__ import annotations

import sqlite3

import pytest
from sqlite_mcp.store import ReadOnlyDatabase


@pytest.fixture
def db(tmp_path):
    """A two-table database, written before the read-only connection opens.

    `secrets` exists so the allow-list has something real to exclude.
    """
    path = tmp_path / "shop.db"
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT, total REAL);
        CREATE TABLE secrets (id INTEGER PRIMARY KEY, token TEXT);
        INSERT INTO orders (customer, total) VALUES
            ('ada', 10.0), ('bob', 20.0), ('cy', 30.0), ('dee', 40.0);
        INSERT INTO secrets (token) VALUES ('hunter2');
        """
    )
    con.commit()
    con.close()
    return ReadOnlyDatabase(path, max_rows=2)
