# 010 — MCP concepts: the reference

**Status:** current, growing · **Started:** 2026-09-09

Every MCP concept this collection has actually built something against, with the
trade-off it carries and where it lives. The companion to
[`007_chunking-concepts.md`](007_chunking-concepts.md), which does the same job
for chunking.

**This document grows.** A per-tool design record answers *why is this tool
shaped this way* and is finished when the tool is. This one answers *what does
this part of the protocol do, and what did we learn using it*, so it accumulates
as each MCP tool lands. Each concept carries a **Status** saying how far we have
actually taken it, because "read the specification" and "ran it" are different
claims and the difference is the point.

| Status | Means |
| --- | --- |
| **Built** | Used in a shipped tool, exercised by tests |
| **Verified** | Confirmed working against a running server, not yet load-bearing |
| **Present** | Confirmed in the SDK by inspection only |
| **Types only** | The protocol's message shapes exist in the SDK, but nothing implements the behaviour; building against it means writing the lifecycle yourself |
| **Unread** | On the map, nothing done |

Backlog ideas are referenced as `#N`. The protocol revision throughout is
**2026-07-28**; where a concept changed in that revision, the entry says so,
because most material online still describes the older shape.

---

## 1 · The three server primitives

**Status: Built** (tools only) · `sqlite-mcp` (#11)

A server may offer **tools**, **resources** and **prompts**. They differ by *who
decides*: a tool is called when the model decides to, a resource is included
when the client decides to, a prompt is invoked when the user decides to.

Almost every data server ships tools alone, and `sqlite-mcp` is no exception —
`query`, `schema`, `sample`. Whether that is right is genuinely unsettled, which
is why #204 `resource-or-tool` exists to measure it: the same catalogue offered
three ways, scored on which the model reaches for and what each costs.

**The trade-off.** A tool costs tokens in every turn's tool list whether or not
it is used. A resource costs nothing until something includes it, but the model
cannot reach for it on its own. A schema listing is arguably a resource that we
made a tool.

---

## 2 · Result contracts: `outputSchema` and `structuredContent`

**Status: Built** · `sqlite-mcp` (#11), and `repo-rag` (#2) learned it the hard way

A tool may declare an output schema. When it does, results carry
`structured_content`, a typed object, alongside the human-readable text. When it
does not, a consumer gets prose and has to parse English.

**The trap, and it is silent.** In the Python SDK the schema is generated from
the return annotation. A bare `-> dict` registers with **no output schema** and
the SDK then sends `structured_content=None`. Nothing errors. The tool looks
fine in a listing and returns nothing usable. `-> dict[str, object]` is the
whole difference.

**What it is worth** is not yet measured here. That is #203 `typed-result-lab`:
the same check built both ways, scored on parse-failure rate and re-prompts.

**Boundary.** This is the *tool's* promise about what it returns. Constraining
what the *model* emits is a different problem, and that is #52 `schema-guard`.

---

## 3 · Refusal as a typed result

**Status: Built** · `sqlite-mcp` (#11)

Not a protocol feature. A design pattern the protocol makes available, and the
most transferable thing learned so far.

When a call cannot be honoured, there are two options: raise a JSON-RPC error,
or return a normal result that says it was refused. An error communicates *this
broke*, which invites retrying the same thing. A structured refusal carrying a
stable `guard` token and a human `reason` communicates *what to do differently*.

```json
{"refused": true, "guard": "not-read-only", "reason": "..."}
```

`is_error` stays false, because nothing broke. The server did its job.

This is `CONVENTIONS.md` rule 5 in the protocol's vocabulary, and the same
instinct as `ingest-ledger` (#49) declining to answer a question whose evidence
never arrived. #209 `freshness-gate-mcp` takes it further: refusing on staleness
and returning the ledger evidence for why.

---

## 4 · The safety boundary belongs to the system, not the string

**Status: Built** · `sqlite-mcp` (#11)

Also not a protocol feature, and the design lesson most likely to survive
contact with a real warehouse.

The common pattern is to inspect the SQL and decide whether it looks safe. That
is a denylist made of string matching. `sqlite-mcp` instead opens the connection
read-only and installs SQLite's own **authorizer callback**, consulted before
every action with the table and column in hand.

**Why it is better:** a denylist must anticipate every dangerous shape, and is
therefore wrong as soon as the SQL dialect grows. Deny-by-default in the engine
is wrong only in the safe direction.

**It proved itself during the build.** `PRAGMA` is one authorizer action
covering both `table_info` and `journal_mode`, so it could not be allowed
wholesale. Writing `schema()` failed against its own guard, which is exactly the
failure a denylist would have missed.

The general form for a hosted warehouse is a dedicated read-only role and a
narrow set of views, with the engine enforcing rather than the server. #207
`warehouse-oauth` is where that becomes identity rather than configuration.

---

## 5 · Evidence in the result: caps and cost

**Status: Built** (caps) · **Unread** (cost) · `sqlite-mcp` (#11)

A result that has been truncated and does not say so produces confidently wrong
answers, because a first page is indistinguishable from a complete answer.
`query` returns `truncated` and `row_limit` for that reason.

`elapsed_ms` rides along as the local stand-in for what matters on a real
warehouse, where the fields would be bytes scanned and credits. A model cannot
trade accuracy against spend when it cannot see the price. That is #211
`budget-mcp`, and nothing here has measured it yet.

**On a real warehouse this is the whole game.** The token bill is noise next to
compute. The controls that matter are a dedicated small warehouse, a resource
monitor with a suspend action, an explicit statement timeout, and routing
metadata questions away from compute entirely.

---

## 6 · Cheap metadata, expensive data

**Status: Built** · `sqlite-mcp` (#11)

A large share of the early turns in any agent loop are "what is there" rather
than "what does it say". `schema()` answers from SQLite's metadata and never
reads a row.

On SQLite the saving is negligible. On a warehouse it is most of the bill, since
metadata operations need no compute while a query does. Any server built on this
one should keep the separation, and it is one input to #201
`tool-surface-budget`, which measures where a tool list stops fitting at all.

---

## 7 · Statelessness and the vanished handshake

**Status: Built** (`server/discover`) · `discover-probe` (#198)

Revision 2026-07-28 removed the `initialize` handshake and protocol-level
sessions. Every request now carries its own protocol version and client
capabilities, and a server announces itself through `server/discover`. A server
needing state across calls mints an explicit handle passed as an ordinary tool
argument.

`sqlite-mcp` needed none of this: it is stateless already, since each call opens
its own connection. The SDK also keeps both eras, with four revisions still
reachable through the old handshake, so a server can speak the current revision
without dropping older clients.

#198 `discover-probe` now drives `discover` and `initialize` separately, each
on its own connection, against real servers over stdio. What it learned is in
[`011`](011_discover-probe.md), and two things belong here.

**The SDK's default connection mode hides the answer.** Left on `auto`, the
client tries `discover`, falls back to the handshake, and gives you a session
without saying which path worked. Its own docstring calls that fallback a
denylist. Use `ClientSession.discover()` and `initialize()` directly whenever
you need to know rather than just connect.

**Capabilities are computed per era, honestly.** A server built on the SDK
claims `list_changed` and resource subscriptions through `discover` and denies
them through `initialize`, because change notification runs over
`subscriptions/listen` in the July revision only. That isn't an inconsistency.

**On 2026-09-14, the SDK's major version decided the era for all twelve
servers probed.** v1, TypeScript or Python, meant the old handshake only; v2
meant both. None of the six official reference servers had migrated; three of
five vendor servers had. TypeScript v2 ships as new packages —
`@modelcontextprotocol/server` and friends — so bumping `@modelcontextprotocol/sdk`
never gets you there. *Corrected the same day: this paragraph first said the
TypeScript SDK's newest release predated the revision. That was true only of the
old package name.*

---

## 8 · Long-running work: the Tasks extension

**Status: Types only** · nothing built against it

> **Corrected 2026-09-14.** This entry originally said **Present**, which
> overstated it. Checking the installed SDK before starting on #199 found the
> July extension's messages — `tasks/get`, `tasks/update`, the
> `io.modelcontextprotocol/tasks` identifier — only in `mcp_types`. Neither
> `MCPServer` nor the extension module gives a tool any way to return a task.
> And `tasks/list` and `tasks/result`, both removed by the July revision, are
> still defined right beside them.

A call that can exceed a few seconds should not block a connection. The Tasks
extension returns a durable `taskId`, and the client polls `tasks/get`. The
handle survives a client restart.

Every hand-rolled `run_job` plus `job_status` pair is a worse version of this,
including the one idea #14 originally proposed. #199 `run-as-task` is the entry
that will move this to Built, and it now carries more than the idea entry says:
the task lifecycle has to be implemented on the low-level server rather than
called.

---

## 9 · The rest of the map

Confirmed in the SDK, nothing built. Listed so the gaps are visible rather than
implied.

| Concept | What it is for | Moves to Built via |
| --- | --- | --- |
| Multi Round-Trip Requests | Pausing a call for human input, then retrying it with the answer | #200 `approval-gate` |
| `subscriptions/listen` | Push instead of poll for change notification | #202 `listen-lab` |
| `ttlMs` and `cacheScope` | Letting a client cache a listing instead of re-fetching | #201 `tool-surface-budget` |
| Deterministic `tools/list` order | Prompt-cache hit rate on a large tool surface | #201 |
| Authorization as a resource server | The query runs as the person, so row-level security applies | #207 `warehouse-oauth` |
| Trace context in `_meta` | One identifier spanning an agent turn and the compute it caused | #206 `trace-through` |
| MCP Apps | Interactive views rendered in the conversation | #214 `lineage-app` |

---

## Findings carried forward

Small things that cost time and are not in anyone's tutorial.

1. **A bare `-> dict` silently disables structured output.** §2. Costs nothing
   to get right and is invisible when wrong.
2. **`mcp.server._otel` is private.** #206 must read `_meta` directly rather
   than import it.
3. **The SDK's in-memory client and server pair is private.**
   `mcp.client._memory.InMemoryTransport` connects a client to a server over
   real JSON-RPC framing, which is what `discover-probe`'s tests run on.
   *Corrected 2026-09-14: this finding originally said no such pair existed, only
   a raw stream factory in `mcp.shared.memory`. The search had missed a private
   module.* It still sits behind an underscore, so depending on it is fragile, and
   a record-and-replay harness remains part of #217 `mcp-replay`'s scope, since a
   live connection is not a fixture.
4. **Deny-by-default will fail your own code first.** That is the mechanism
   working. §4.
