"""Read a SQLite file from the shell, or serve it over MCP.

The same guards apply on both seams. A tool whose safety depended on which
entry point you came in through would not have safety.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from .mcp_server import DEFAULT_MAX_ROWS, create_server
from .store import ReadOnlyDatabase, Refused


def _render_schema(tables) -> str:
    if not tables:
        return "no tables exposed"
    lines = []
    for table in tables:
        lines.append(table.name)
        for column in table.columns:
            flags = " PK" if column.primary_key else ""
            null = "" if column.nullable else " NOT NULL"
            lines.append(f"    {column.name:<24} {column.type or 'ANY'}{null}{flags}")
    return "\n".join(lines)


def _render_rows(result) -> str:
    if not result.columns:
        return "(no columns)"
    widths = [len(c) for c in result.columns]
    for row in result.rows:
        widths = [max(w, len(str(v))) for w, v in zip(widths, row, strict=False)]
    head = "  ".join(c.ljust(w) for c, w in zip(result.columns, widths, strict=False))
    body = [
        "  ".join(str(v).ljust(w) for v, w in zip(row, widths, strict=False)) for row in result.rows
    ]
    out = [head, "-" * len(head), *body]
    if result.truncated:
        out.append(f"\n-- truncated at {result.row_limit} rows; this answer is partial.")
    return "\n".join(out)


def main(argv: Sequence[str] | None = None) -> int:
    """Read-only SQL over a SQLite file, from the shell or as an MCP server."""
    parser = argparse.ArgumentParser(prog="sqlite-mcp", description=main.__doc__)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument(
        "--table",
        action="append",
        dest="tables",
        help="expose only this table; repeatable. Omit to expose all of them.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_schema = sub.add_parser("schema", help="list exposed tables and columns")
    p_schema.add_argument("database")

    p_query = sub.add_parser("query", help="run one read-only statement")
    p_query.add_argument("database")
    p_query.add_argument("sql")
    p_query.add_argument("--json", action="store_true", help="emit the raw result record")

    p_serve = sub.add_parser("serve", help="serve this database over MCP on stdio")
    p_serve.add_argument("database")

    args = parser.parse_args(argv)

    if args.command == "serve":
        create_server(args.database, max_rows=args.max_rows, allowed_tables=args.tables).run(
            transport="stdio"
        )
        return 0

    db = ReadOnlyDatabase(args.database, max_rows=args.max_rows, allowed_tables=args.tables)
    try:
        if args.command == "schema":
            print(_render_schema(db.schema()))
        else:
            result = db.query(args.sql)
            if args.json:
                print(
                    json.dumps(
                        {
                            "columns": result.columns,
                            "rows": [list(r) for r in result.rows],
                            "truncated": result.truncated,
                            "row_limit": result.row_limit,
                            "elapsed_ms": result.elapsed_ms,
                        },
                        indent=2,
                    )
                )
            else:
                print(_render_rows(result))
    except Refused as exc:
        # The guard name goes to stderr so a script can branch on it without
        # parsing the sentence that follows.
        print(f"refused [{exc.guard}]: {exc.reason}", file=sys.stderr)
        return 1
    return 0
