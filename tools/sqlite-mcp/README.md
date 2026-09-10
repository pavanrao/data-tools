# sqlite-mcp

Read-only SQL over a SQLite file, from the shell or as an MCP server — with the
limits enforced by the database rather than by reading the SQL.

Idea [#11](../../IDEAS.md). The first MCP server in this collection written
against protocol revision **2026-07-28**.

## The point

Most "database MCP server" write-ups are a thin wrapper that passes a string to
a driver. That wrapper is not the product. **The guards are the product**, and
this one does not implement them by inspecting the SQL:

- The connection is opened **read-only** (`file:...?mode=ro`).
- An **authorizer callback** vetoes every action that is not a read, so a
  statement shape nobody anticipated is refused rather than pattern-matched.
- One statement per call, so a second cannot ride along after a semicolon.
- A **row cap** that reports when it truncated, because a caller who cannot see
  the cap has no way to know the answer is partial.
- An optional **table allow-list**, enforced before a row is touched.

Every refusal names the guard that produced it, per `CONVENTIONS.md` rule 5.

## Install

```bash
# just this tool
uvx --from "git+https://github.com/pavanrao/data-tools#subdirectory=tools/sqlite-mcp" \
    sqlite-mcp schema ./shop.db

# in the workspace
uv sync --all-extras && uv run sqlite-mcp schema ./shop.db
```

## Use from the shell

```bash
sqlite-mcp schema shop.db
sqlite-mcp --max-rows 2 query shop.db "SELECT customer, total FROM orders ORDER BY id"
sqlite-mcp query shop.db "SELECT * FROM orders" --json
```

Anything that would change the database exits non-zero and names the guard on
stderr, so a script can branch on it without parsing the sentence:

```console
$ sqlite-mcp query shop.db "DROP TABLE orders"
refused [not-read-only]: this database is served read-only; the statement asked to change it

$ sqlite-mcp query shop.db "SELECT 1; DELETE FROM orders"
refused [multiple-statements]: only one statement may be sent at a time; a second statement cannot ride along

$ sqlite-mcp --table orders query shop.db "SELECT secret FROM api_keys"
refused [table-not-allowed]: that table is outside the tables this server exposes
```

## Use as an MCP server

```bash
sqlite-mcp serve shop.db --max-rows 50 --table orders --table customers
```

Three tools, each with a declared output schema:

| Tool | Returns |
| --- | --- |
| `query(sql)` | rows, columns, and whether the row cap truncated them |
| `schema()` | exposed tables and their columns, read from metadata not rows |
| `sample(table, limit)` | a few rows from one table, to see its shape |

**A refusal is a result, not an error.** A denied call comes back with
`refused: true` and a `guard`, and `is_error` stays false. A JSON-RPC error
tells a model something broke. A typed refusal tells it what to do differently,
which is the difference between a retry loop and a correction.

```json
{"refused": true,
 "guard": "not-read-only",
 "reason": "this database is served read-only; the statement asked to change it"}
```

Client configuration, for a host that launches servers over stdio:

```json
{
  "mcpServers": {
    "shop": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/pavanrao/data-tools#subdirectory=tools/sqlite-mcp",
               "sqlite-mcp", "serve", "/absolute/path/shop.db", "--max-rows", "50"]
    }
  }
}
```

The server is also advertised in the `data_tools.mcp` entry-point group as a
zero-argument factory, so `mcp-gateway` (#16) can mount it without opening a
database at import time.

## Tests

Model-free and network-free, as `CONVENTIONS.md` rule 6 requires. The suite
includes a real protocol round trip through a client, not only tool
registration, because registration passing tells you nothing about what a
consumer actually reads.

```bash
uv run pytest tools/sqlite-mcp/tests/
```

## Prior art, and what is different

There are many SQL-over-MCP servers. Almost all of them enforce read-only by
checking whether the statement starts with `SELECT`. That check is defeated by a
CTE, a pragma, a nested write in some dialects, and by whatever the next SQL
feature turns out to be. Handing the decision to the database's own authorizer
means the guard does not need to anticipate anything.

The design record is [`docs/009_sqlite-mcp.md`](../../docs/009_sqlite-mcp.md).
The protocol concepts it exercises are in
[`docs/010_mcp-concepts.md`](../../docs/010_mcp-concepts.md).
