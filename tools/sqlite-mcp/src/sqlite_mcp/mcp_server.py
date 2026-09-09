"""Expose a SQLite file as an MCP server -- read-only, three tools, no model.

The logic lives in plain ``*_impl`` functions so it is testable without a
transport, which is how ``repo-rag`` is arranged too.

Two decisions worth knowing, both of which are the protocol doing work a
hand-rolled integration would have to invent:

**Refusals are results, not errors.** A denied query comes back as a normal
result carrying ``refused``, ``guard`` and ``reason``. A JSON-RPC error tells a
model that something broke; a typed refusal tells it *what to do differently*,
which is the difference between a retry loop and a correction.

**Every return annotation is parameterised.** ``dict[str, object]`` rather than
a bare ``dict``. A bare ``dict`` registers with no output schema and the SDK
then sends ``structured_content=None``, so a client reading structured output
gets nothing. That is not cosmetic; it is the tool's contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from mcp.server.mcpserver import MCPServer

from .store import QueryResult, ReadOnlyDatabase, Refused, Table

DEFAULT_DB = ".data/app.db"
DEFAULT_MAX_ROWS = 100


class _Database(Protocol):
    max_rows: int

    def query(self, sql: str) -> QueryResult: ...

    def schema(self) -> list[Table]: ...

    def sample(self, table: str, limit: int = 5) -> QueryResult: ...


def _refusal(exc: Refused) -> dict[str, object]:
    return {"refused": True, "guard": exc.guard, "reason": exc.reason}


def _result(result: QueryResult) -> dict[str, object]:
    return {
        "refused": False,
        "columns": result.columns,
        # Lists rather than tuples: JSON has no tuple, and letting the
        # serializer decide invites a client-side surprise.
        "rows": [list(row) for row in result.rows],
        "truncated": result.truncated,
        "row_limit": result.row_limit,
        "elapsed_ms": result.elapsed_ms,
    }


def query_impl(db: _Database, sql: str) -> dict[str, object]:
    try:
        return _result(db.query(sql))
    except Refused as exc:
        return _refusal(exc)


def schema_impl(db: _Database) -> dict[str, object]:
    try:
        tables = db.schema()
    except Refused as exc:
        return _refusal(exc)
    return {
        "refused": False,
        "tables": [
            {
                "name": table.name,
                "columns": [
                    {
                        "name": column.name,
                        "type": column.type,
                        "nullable": column.nullable,
                        "primary_key": column.primary_key,
                    }
                    for column in table.columns
                ],
            }
            for table in tables
        ],
    }


def sample_impl(db: _Database, table: str, limit: int = 5) -> dict[str, object]:
    try:
        return _result(db.sample(table, limit))
    except Refused as exc:
        return _refusal(exc)


def create_server(
    db: str | Path = DEFAULT_DB,
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    allowed_tables: list[str] | None = None,
) -> MCPServer:
    """Zero-argument factory for the ``data_tools.mcp`` entry point.

    Deferred on purpose: a gateway can discover this tool without opening a
    database at import time.
    """
    return build_server(ReadOnlyDatabase(db, max_rows=max_rows, allowed_tables=allowed_tables))


def build_server(db: _Database) -> MCPServer:
    server = MCPServer("sqlite-mcp")

    @server.tool()
    def query(sql: str) -> dict[str, object]:
        """Run one read-only SQL statement. Returns rows, plus whether the row cap truncated them.

        Writes, schema changes and chained statements are refused by the
        database itself, and come back as a result with `refused` set rather
        than as an error.
        """
        return query_impl(db, sql)

    @server.tool()
    def schema() -> dict[str, object]:
        """List the tables this server exposes and their columns. Reads metadata, not rows."""
        return schema_impl(db)

    @server.tool()
    def sample(table: str, limit: int = 5) -> dict[str, object]:
        """Return a few rows from one table, to see its shape before querying it."""
        return sample_impl(db, table, limit)

    return server
