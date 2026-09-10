# 009 — `sqlite-mcp` (#11): read-only SQL as an MCP server

**Status:** current · **Date:** 2026-09-09

The collection's first MCP server written against protocol revision
**2026-07-28**, and the first tool built after the section M backlog landed.
`repo-rag` (#2) also serves MCP, but it was written against the older protocol
and is parked; `docs/004` records it.

## Why this one first

`docs/FINDINGS.md` **F2** settled the general question: a server earns nothing
when the host can already do the job itself, so retrieval over a folder of files
is redundant next to a client with file tools. The same finding named the
alternative — *a system-access MCP such as `sqlite-mcp` (#11), which touches a
system the model cannot reach*. This is that tool.

The learning case is separate from the utility case, and worth stating plainly.
For one developer with a terminal and credentials, this server is overhead: you
can write the SQL yourself. It earns its keep when the consumer is not you, when
the access needs governing, or when the work is a loop of fifteen dependent
queries rather than one. **F1** measured that last point already — driving a
server in a loop beat a single-shot command, because the client iterates.

## The design decision that matters

Almost every SQL-over-MCP server enforces read-only by inspecting the statement:
does it start with `SELECT`, does it contain `DROP`. That is a denylist made of
string matching, and it has the failure mode every denylist has. A CTE, a
pragma, a dialect that permits a write inside a read, or simply the next SQL
feature, and the guard is silently wrong.

**This tool never inspects the SQL to decide whether it is safe.** Two mechanisms
belonging to SQLite do the work:

1. **A read-only connection.** `sqlite3.connect("file:...?mode=ro", uri=True)`.
   The file is not opened for writing, so a write is impossible rather than
   forbidden.
2. **An authorizer callback.** `con.set_authorizer(...)` is consulted for every
   action SQLite is about to take, with the table and column in hand. It returns
   `SQLITE_OK` for reads and `SQLITE_DENY` for everything else.

The authorizer is also where the table allow-list lives, because it sees the
table name on each `SQLITE_READ` before a row is touched. Scoping done there
cannot be evaded by a join, a subquery or a view.

**Deny-by-default proved itself during the build.** `PRAGMA` is a single
authorizer action covering both `table_info` and `journal_mode`, so it could not
be allowed wholesale. Writing `schema()` failed against its own guard, and the
fix was to name the one introspection pragma it needs. A denylist would have let
every pragma through and nobody would have noticed.

## Decisions

### D-A — Refusals are results, not errors

A denied call returns a normal result carrying `refused`, `guard` and `reason`,
and `is_error` stays false.

A JSON-RPC error tells a model that something broke, which invites a retry of the
same thing. A typed refusal tells it *what to do differently*. `guard` is a
stable token a caller can branch on; `reason` is the sentence for a human. This
is `CONVENTIONS.md` rule 5 — every non-obvious status is evidence-bearing —
expressed in the protocol's vocabulary, and it is the same instinct as
`ingest-ledger` (#49) refusing to answer a question whose evidence is missing.

### D-B — The row cap reports itself

`query` returns `truncated` and `row_limit` alongside the rows. A cap that is
invisible produces confidently wrong answers, because neither a human nor a model
can tell a complete result from the first page of one.

`elapsed_ms` rides along for the same reason. It is the cheap local stand-in for
the thing that matters on a real warehouse, where the equivalent field would
carry bytes scanned and cost. That is idea #211 in the backlog, and this is the
shape it will take.

### D-C — Parameterised return annotations are the contract

Every tool returns `dict[str, object]`, never a bare `dict`. A bare `dict`
registers with **no output schema**, and the SDK then sends
`structured_content=None`, so a client reading structured output gets nothing.

`docs/004` recorded this for `repo-rag` as a code comment. It is promoted here to
a decision because it is the whole basis of the result contract, and because a
test now enforces it. Removing the parameter makes the round-trip test fail; the
registration tests alone would not notice.

### D-D — The guards do not depend on the entry point

The CLI and the MCP server share one `ReadOnlyDatabase`. A tool whose safety
depended on which seam you arrived through would not have safety. The CLI exists
because `CONVENTIONS.md` requires it, and because being able to reproduce a
refusal in a shell is what makes the server debuggable.

## What the tests cover

Seventeen tests, model-free and network-free.

- Each guard, asserted by the **guard name** rather than by the message.
- The row cap, in both directions: truncated and not.
- `schema` and `sample` under an allow-list.
- Three tools registered, each with an output schema.
- **A real protocol round trip** through a client, asserting on
  `structured_content` and on a refusal arriving with `is_error` false.

That last one is the test the others cannot replace. Everything else drives the
server object directly, which proves registration and nothing about what a
consumer reads. It was verified honest by making the change it claims to catch:
dropping a return-type parameter turns `structured_content` into `None` and the
test fails.

## Verified over a real transport

D10 in `docs/001` recorded that the SDK's mechanisms had been confirmed present
but never exercised over a transport. That gap is now closed for the parts this
tool uses. The server was run as a subprocess over stdio and driven by a client:
tools discovered, a query returning structured content with its truncation flag,
and a refusal arriving as data.

Still unexercised, and still waiting on #198 `discover-probe`: `server/discover`
negotiation against a foreign server, the multi-round-trip pattern, the tasks
extension, and subscriptions. This tool needs none of them.

## What it deliberately is not

- **Not a query builder.** It takes SQL. Making the model's life easier by
  generating SQL is #74 `sql-safeguard` and #210 `surface-synth`.
- **Not multi-database.** One file. A gateway over many is #16 `mcp-gateway`.
- **Not cost-aware.** `elapsed_ms` is not a budget. That is #211 `budget-mcp`.
- **Not identity-aware.** It has whatever access the process has. Carrying the
  human's identity through to the engine is #207 `warehouse-oauth`, and on a
  real warehouse that is the entry that matters most.

## Next

The natural successors, in order: #198 `discover-probe` pointed at this server,
then #203 `typed-result-lab` using its result contract as the specimen, then
#207 once there is a warehouse rather than a file.
