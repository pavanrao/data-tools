# 011 — `discover-probe` (#198): what an MCP server actually speaks

**Status:** current · **Date:** 2026-09-14

The first tool in section M, and the first client in the collection. It closes
the gap `docs/009` left open: `sqlite-mcp` had been run over stdio, but nothing
other than its own SDK had ever negotiated with it through `server/discover`.

## The decision the whole tool rests on

The SDK already has a function that probes `discover` and falls back to the
handshake. It lives in `mcp/client/_probe.py`, and its docstring describes the
fallback, in its own words, as a denylist: anything that isn't positive evidence
of a modern server falls back to `initialize`. You end up with a working session
and no record of which path succeeded or why the other failed.

That's correct for a client that wants to connect. It's useless for a tool whose
job is reporting what happened, so `discover-probe` doesn't use it. `ClientSession`
exposes `discover()` and `initialize()` as separate calls, and the probe makes
each one on **its own connection**. The separate connection isn't fussiness. A
connection that has answered `discover` is locked into the modern era — the same
docstring warns about exactly this — so asking it for a handshake afterwards would
measure the lock.

Every path ends in one of three states. `ok`. `rejected`, meaning the server
answered and said no, with the error code kept as evidence. Or `unreachable`,
meaning nothing usable came back. The distinction between the last two is the
reason the module exists: an outage is never evidence about which protocol
something speaks. The SDK's own probe draws the same line for the same reason.

## What I got wrong on the way, in order

Five of these, and they're worth keeping because each one would have shipped as
a false claim.

**1. A capability "mismatch" that wasn't one.** The first spike asked the SDK's
own server for its capabilities both ways. Through `discover` it claimed
`list_changed` on tools, prompts and resources, plus resource subscriptions.
Through `initialize` it denied all of it. I reported that to the user as a
finding and planned a check around it. Then I read `_handle_discover` in the
lowlevel server: it passes the request's protocol version into
`get_capabilities`, which enables those flags only when the server serves
`subscriptions/listen` — a July-only mechanism. The server was telling the truth
twice. `capabilities-by-era` now records differences as a **note** and never
fails on them.

**2. A check I promised and can't build.** The design I proposed said the probe
would detect reliance on Roots, Sampling and Logging. Only Logging is a server
capability. Roots and Sampling are things a server asks the *client* for in the
middle of handling a call, so a probe that doesn't make calls can't see them. The
check is `deprecated-logging`, and the README says why it stops there.

**3. Three checks written before their tests.** In one pass I implemented the
era-difference, claims and deprecation checks with nothing driving them, which is
exactly what the repo's TDD rule (D5) forbids. The recovery was to write the tests
afterwards and then prove each one could fail, by applying the regression it
claims to catch and running the suite. Five of six mutations went red. The sixth
didn't:

| Mutation | Result |
| --- | --- |
| era difference reported as a failure | caught |
| a failed listing ignored | caught |
| an empty listing treated as a false claim | caught |
| an unconnected path's claims failed instead of skipped | caught |
| deprecated logging passed | caught |
| **a rejection classified as unreachable** | **missed** |

The miss was the important one. The legacy-only test checked the era and the
error code, and a mis-classified rejection still produces both, because
`unreachable` plus `ok` also classifies as legacy-only and the evidence string
still contains `-32601`. So the one distinction the module is built on had no
test guarding it. The test now asserts the status directly, and the rerun caught
all six.

**4. A separator that ate the server's arguments.** The first CLI stripped every
`--` from the command instead of only the leading one. Any server with `--` in
its own arguments would have been spawned as a different command. There's a
regression test, confirmed to fail against the original code.

**5. A false positive found only by running it.** Probing `sqlite-mcp` over real
stdio reported `experimental` as differing between eras. One side omitted the key
and the other sent `{}`. Those mean the same thing, and every server would have
carried that line. The comparison now treats absent and empty as equal.

## Findings

Probed 2026-09-14, locally over stdio, every server at its latest published
version:

| Server | Built on | Era | How it refused `discover` |
| --- | --- | --- | --- |
| `server-everything` 2026.8.31 | TypeScript SDK 1.30.0 | legacy-only | `-32601` Method not found |
| `server-filesystem` | TypeScript SDK 1.30.0 | legacy-only | `-32601` Method not found |
| `server-memory` | TypeScript SDK 1.30.0 | legacy-only | `-32601` Method not found |
| `mcp-server-fetch` | Python SDK 1.30.0 | legacy-only | `-32602` "Invalid request" |
| `mcp-server-time` | Python SDK 1.30.0 | legacy-only | `-32602` "Invalid request" |
| `mcp-server-git` | Python SDK 1.30.0 | legacy-only | `-32602` "Invalid request" |
| `sqlite-mcp` (control) | Python SDK 2.2.0 | both | — |

**None of the official reference servers speaks the July revision.** Before
believing that, I checked whether `npx` had run a stale cached copy of
`server-everything`. It hadn't: the version that ran is the latest on npm,
published 31 August, a month after the revision. The explanation is underneath
it. The TypeScript SDK's newest release is 1.30.0, which declares
`LATEST_PROTOCOL_VERSION = "2025-11-25"` and contains no reference to
`2026-07-28` anywhere in its build. The Python SDK's 2.x line does implement the
revision; the Python reference servers just haven't moved to it.

**Every advertised listing worked.** No server claimed something it couldn't do.
`server-everything` is the only one still advertising Logging.

**The two SDK families refuse differently, and one of them is wrong.** TypeScript
servers answer an unknown method with `-32601`, which is what JSON-RPC specifies.
Python v1 servers answer with code `-32602` and the message "Invalid request".
`-32602` means invalid *params*; "Invalid request" is `-32600`'s name. So the
code and the message disagree with each other, and neither is the answer for a
method the server doesn't know. The Python v1 SDK models client requests as a
closed union of known types, which fits an unknown method failing validation
before it's ever routed. I haven't traced that path in the v1 source, so treat it
as the likely mechanism rather than a demonstrated one.

It matters for any client doing its own negotiation. Fall back to the handshake
only on `-32601` and you'd fail against every Python v1 server. The v2 SDK's
probe falls back on nearly any error, which reads differently once you've seen
this table.

These numbers expire. The evidence card says so, and should be re-run before
anyone quotes it.

## Testing

26 tests, no network and no model.

The wire tests use `InMemoryTransport` deliberately. The SDK's in-process modern
path hands requests straight to the server with no JSON-RPC framing, so a probe
test built on it would pass without ever exercising the protocol. Two test
servers cover the real cases: the SDK's own server, which speaks both eras, and
one with its discover handler replaced through `add_request_handler` — the
documented seam — to reject the method. There's no modern-only wire fixture,
because `initialize` is reserved and the only hook that can wrap it, server
middleware, is marked provisional in the SDK. That case is covered by testing the
era classification directly. One test spawns a real subprocess over stdio.

## Scope

Stdio only. HTTP is deferred rather than half-built: the servers probed here are
all stdio, and an HTTP transport with nothing real to verify it against would be
untested code. Hosted endpoints are out entirely until that's a deliberate
decision, since it means sending requests to other people's infrastructure.

## Next

The concepts reference moves `server/discover` from present to built. The
natural successor is a post, since a table showing the reference servers don't
speak the current revision is more useful to people than the tool that produced
it. After that, #199 `run-as-task`, which `docs/010` now warns will mean
implementing the task lifecycle rather than calling it.
