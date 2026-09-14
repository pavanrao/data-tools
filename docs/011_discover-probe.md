# 011 — `discover-probe` (#198): what an MCP server actually speaks

**Status:** current · **Date:** 2026-09-14 · **Revised:** 2026-09-14, the same
day, after probing vendor servers — see *Corrections* below

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
something speaks.

## Findings

Probed 2026-09-14, locally over stdio, every server at its latest published
version, all twelve on a single build of the probe:

| Server | Publisher | Built on | Era | How it refused `discover` |
| --- | --- | --- | --- | --- |
| `server-everything` 2026.8.31 | MCP project | TypeScript `@modelcontextprotocol/sdk` 1.30.0 | legacy-only | `-32601` Method not found |
| `server-filesystem` | MCP project | TypeScript `@modelcontextprotocol/sdk` 1.30.0 | legacy-only | `-32601` Method not found |
| `server-memory` | MCP project | TypeScript `@modelcontextprotocol/sdk` 1.30.0 | legacy-only | `-32601` Method not found |
| `mcp-server-fetch` | MCP project | Python `mcp` 1.30.0 | legacy-only | `-32602` Invalid request parameters |
| `mcp-server-time` | MCP project | Python `mcp` 1.30.0 | legacy-only | `-32602` Invalid request parameters |
| `mcp-server-git` | MCP project | Python `mcp` 1.30.0 | legacy-only | `-32602` Invalid request parameters |
| `@playwright/mcp` 0.0.80 | Microsoft | TypeScript v1, bundled in `playwright-core` | legacy-only | `-32601` Method not found |
| `dbt-mcp` 2.3.1 | dbt Labs | Python `mcp` 1.26.0 | legacy-only | `-32602` Invalid request parameters |
| `@upstash/context7-mcp` 4.1.1 | Upstash | TypeScript `@modelcontextprotocol/server` 2.0.0 | both | — |
| `mcp-server-motherduck` 1.0.8 | MotherDuck | Python `mcp` 2.2.0 | both | — |
| `awslabs.aws-documentation-mcp-server` 1.2.1 | AWS Labs | Python `mcp` 2.2.0 | both | — |
| `sqlite-mcp` (control) | this collection | Python `mcp` 2.2.0 | both | — |

**The SDK's major version decides the era, for every one of the twelve.** On a
v1 SDK, TypeScript or Python, a server speaks the old handshake only. On v2 it
speaks both. There's no server here that implements `discover` on its own or
fails to despite its SDK.

**Both SDK families shipped the July revision on day one.** The Python `mcp`
package's 2.x line implements it. The TypeScript side published v2 as *new
packages* — `@modelcontextprotocol/server`, `/client` and `/node` — with 2.0.0 out
on 2026-07-27, defining `MODERN_PROTOCOL_VERSION = "2026-07-28"`. The old
`@modelcontextprotocol/sdk` package stops at 1.30.0 and never gains it, which is
what makes the TypeScript upgrade easy to miss: bumping the version you already
depend on doesn't get you there.

**The official reference servers haven't migrated. Three of five vendors have.**
All six MCP-project servers are still on v1 SDKs, including `server-everything`,
published 31 August, a month after the revision. Among the vendors, Upstash,
MotherDuck and AWS Labs are on v2; Microsoft's Playwright server and dbt Labs'
server are not.

**Every advertised listing worked.** No server claimed a capability it couldn't
back. `server-everything` and MotherDuck are the two still advertising the
deprecated Logging capability.

**The two v1 SDKs refuse an unknown method with different codes.** TypeScript v1
answers `-32601` Method not found, which is what JSON-RPC specifies for a method
the server doesn't have. Python v1 answers `-32602` Invalid request parameters,
the code for a known method called with bad arguments. The Python v1 SDK models
client requests as a closed union of known types, which fits an unknown method
failing validation before it's routed; I haven't traced that path in the v1
source, so treat it as the likely mechanism rather than a demonstrated one.

It matters for any client doing its own negotiation. Fall back to the handshake
only on `-32601` and you'd fail against every Python v1 server here, dbt Labs'
included. The v2 SDK's own probe falls back on nearly any error.

These numbers expire as servers migrate. The evidence card carries the date and
says to re-run before quoting it.

## Corrections

**What the first version of this record said, the same morning, and why it was
wrong.** It had probed only the six reference servers, and made two claims that
didn't survive probing vendors:

- *"The TypeScript SDK's newest release is 1.30.0, which declares
  `LATEST_PROTOCOL_VERSION = "2025-11-25"` and contains no reference to
  `2026-07-28`."* True of the `@modelcontextprotocol/sdk` package, and false as a
  statement about the TypeScript SDK. I only checked the old package name. v2
  exists under new names, and I found it only because Context7 — an npm package —
  answered `discover`, and I went looking for how. Separately, the
  `LATEST_PROTOCOL_VERSION` constant I quoted turns out to be v2's *handshake-era*
  constant too; v2 keeps a separate `MODERN_PROTOCOL_VERSION`, the same split the
  Python SDK uses.
- *"Python v1 servers answer with code `-32602` and the message 'Invalid request'
  … the code and the message disagree with each other."* They don't. My summary
  script truncated each error at 40 characters, and "Invalid request parameters"
  lost its last word. The raw report on disk had the full message the whole time.
  The narrower finding — Python v1 uses the invalid-params code for an unknown
  method — stands.

## What I got wrong on the way, in order

Nine of these. Each would have shipped as a false claim or a wrong verdict.

**1. A capability "mismatch" that wasn't one.** The first spike asked the SDK's
own server for its capabilities both ways. Through `discover` it claimed
`list_changed` on tools, prompts and resources, plus resource subscriptions.
Through `initialize` it denied all of it. I reported that as a finding and
planned a check around it. Then I read `_handle_discover` in the lowlevel server:
it passes the request's protocol version into `get_capabilities`, which enables
those flags only when the server serves `subscriptions/listen` — a July-only
mechanism. The server was telling the truth twice. `capabilities-by-era` now
records differences as a **note** and never fails on them.

**2. A check I promised and can't build.** The design I proposed said the probe
would detect reliance on Roots, Sampling and Logging. Only Logging is a server
capability. Roots and Sampling are things a server asks the *client* for in the
middle of handling a call, so a probe that doesn't make calls can't see them.

**3. Three checks written before their tests.** In one pass I implemented the
era-difference, claims and deprecation checks with nothing driving them, which is
what the repo's TDD rule (D5) forbids. The recovery was to write the tests
afterwards and prove each could fail, by applying the regression it claims to
catch. Five of six mutations went red. The one that didn't was *a rejection
classified as unreachable*: the legacy-only test checked the era and the error
code, and a mis-classified rejection still produces both. So the one distinction
the module is built on had no test guarding it. The test now asserts the status
directly, and the rerun caught all six.

**4. A separator that ate the server's arguments.** The first CLI stripped every
`--` from the command instead of only the leading one. There's a regression test,
confirmed to fail against the original code.

**5. A false positive found only by running it.** Probing `sqlite-mcp` over real
stdio reported `experimental` as differing between eras. One side omitted the key
and the other sent `{}`. The comparison now treats absent and empty as equal.

**6. A crashed server reported as a refusal, with its explanation discarded.**
`mcp-server-motherduck` came back `neither` — answered and refused both paths —
and exited 0. It hadn't answered anything. It exited on startup with *"In-memory
databases require the --read-write flag"*, because I'd started it without that
flag, and the SDK reports a dead process as `MCPError(-32000, "Connection
closed")`. The probe counted every `MCPError` as a refusal. It had also sent the
server's stderr to `/dev/null`, which is where that one explanatory line went.
Now `CONNECTION_CLOSED` and `REQUEST_TIMEOUT` count as `unreachable`, a server
that never connects exits 2, and the tail of its stderr is kept whenever a path
fails to connect.

**7. A cold start that looked like a legacy-only verdict.** `dbt-mcp` timed out
on `discover` the first time and answered normally on every run after. Discover
runs first, so on a first `uvx` run it absorbed the package download; the
handshake that followed found a warm cache and succeeded. That bias would make
any first probe of an uncached server look more legacy than it is. A discover
that got no answer, from a server whose handshake then succeeded, now gets one
retry, disclosed in the evidence. A server that really never answers times out
twice and says so.

**8. A finding that was my own truncation.** See *Corrections*.

**9. The TypeScript v2 SDK I didn't find.** See *Corrections*.

## Testing

30 tests, no network and no model.

The wire tests use `InMemoryTransport` deliberately. The SDK's in-process modern
path hands requests straight to the server with no JSON-RPC framing, so a probe
test built on it would pass without ever exercising the protocol. The fixtures
cover each real behaviour met in the field: the SDK's own server, which speaks
both eras; one whose discover handler rejects the method; one silent on its first
connection and ordinary afterwards, for the cold start; one alive but hanging on
discover forever; a connection refused outright; and one that goes silent. Two
tests spawn real subprocesses over stdio, one of which crashes on startup the way
MotherDuck did.

There's no modern-only wire fixture, because `initialize` is reserved and the
only hook that can wrap it, server middleware, is marked provisional in the SDK.
That case is covered by testing the era classification directly.

## Scope

Stdio only. HTTP is deferred rather than half-built. Hosted endpoints are out
entirely until that's a deliberate decision, since it means sending requests to
other people's infrastructure. Every vendor server above was run locally through
`npx` or `uvx`, with no credentials, and the probe never called a tool.

## Next

The concepts reference moves `server/discover` from present to built. The write-up
is [Which Protocol Is Your MCP Server Speaking?](https://pavanrao.github.io/posts/which-protocol-is-your-mcp-server-speaking/).
After that, #199 `run-as-task`, which `docs/010` warns will mean implementing the
task lifecycle rather than calling it.
