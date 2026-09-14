# discover-probe

Ask an MCP server what it is, one negotiation path at a time, and check what it
claims against what it does.

Idea [#198](../../IDEAS.md).

## Why not just connect

The SDK's client, left on its default, tries `server/discover` and falls back to
the old `initialize` handshake if that fails. You get a working session and no
record of which path succeeded, or why the other one didn't. The SDK's own
docstring calls that fallback a denylist. It's the right behaviour when you only
want to connect, and the wrong one when the point is to find out.

So this drives each path on a **separate connection** and records the outcome.
Separate matters: a connection that has answered `discover` is locked into the
modern era, and reusing it for the handshake would measure the lock rather than
the server.

## What it checks

| Check | Question | Fails when |
| --- | --- | --- |
| `discover` | Does `server/discover` succeed at revision 2026-07-28? | the server rejects it, or never answers |
| `handshake` | Does the pre-July `initialize` handshake still work? | same |
| `claims-modern`, `claims-legacy` | Does every listing the server advertises actually succeed? | a listing it advertised errors |
| `capabilities-by-era` | Do the two eras advertise different capabilities? | never — see below |
| `deprecated-logging` | Does it advertise the deprecated Logging capability? | never; it's a note |

An empty listing passes. Advertising a capability with nothing in it yet is
honest; only a listing that errors counts against a server.

**Differences between eras are notes, not failures.** A server legitimately
computes capabilities per protocol version, because change notification works
through `subscriptions/listen` in the July revision and not before it. The same
server can truthfully claim `list_changed` in one era and deny it in the other.

**Only Logging is detectable.** Roots and Sampling are also deprecated, but they
are features a server asks the *client* for during a call, so no probe that
doesn't make calls can see whether a server relies on them.

**A silent server is not a server that said no.** Each path is `ok`, `rejected`
(it answered and refused) or `unreachable` (nothing usable came back). The SDK
reports a server process that died, and a request nobody answered, as errors too;
the probe counts both as `unreachable`, never as a refusal. An outage is never
evidence about which protocol something speaks.

**When a server never connects, you see why.** Server stderr stays out of a
healthy report, but if either path fails to connect, its last lines are kept —
usually the only explanation there is:

```console
server stderr (last lines):
Error: In-memory databases require the --read-write flag.
```

**A cold start gets one retry.** Discover runs first, so on a first `npx` or `uvx`
run it also absorbs the package download and can time out while the handshake
after it succeeds. If discover got no answer and the handshake then worked, the
probe retries discover once and says so in the evidence. A server that really
never answers times out twice and is reported that way.

## Use

```bash
discover-probe stdio -- uvx mcp-server-time
discover-probe --json stdio -- npx -y @modelcontextprotocol/server-everything
discover-probe --timeout 30 stdio -- uv run sqlite-mcp serve chinook.db
```

```console
$ discover-probe stdio -- npx -y @modelcontextprotocol/server-everything
target   npx -y @modelcontextprotocol/server-everything
server   mcp-servers/everything
era      legacy-only

  FAIL  discover             rejected: error -32601: Method not found
  pass  handshake            negotiated 2025-11-25
  skip  claims-modern        this path did not connect
  pass  claims-legacy        tools 13, resources 7, prompts 4
  skip  capabilities-by-era  needs both paths to connect
  note  deprecated-logging   advertises logging in legacy; deprecated as of 2026-07-28
```

Everything after `--` is the server command, passed through untouched — including
any `--` in the server's own arguments.

**Exit codes** encode the one thing worth failing a script over:

| Code | Meaning |
| --- | --- |
| `0` | probed, and every advertised listing worked |
| `1` | the server advertised a listing that failed |
| `2` | the server never answered, including one that crashed on startup |

A legacy-only server exits `0`. Not speaking the July revision is a fact about
the server, reported in the output. It isn't a lie the server told.

## What it found

Probed on 2026-09-14, across twelve servers — the six official reference servers,
five vendor servers and `sqlite-mcp` as a control — the SDK's major version
decided the era every time. v1 meant the old handshake only; v2 meant both. None
of the reference servers had migrated. Upstash, MotherDuck and AWS Labs had;
Microsoft's Playwright server and dbt Labs' had not.

The full table, the finding about error codes, and two claims the design record's
first version made and got wrong are in
[`docs/011_discover-probe.md`](../../docs/011_discover-probe.md). The evidence card
is [`evidence/discover-probe.jsonl`](../../evidence/discover-probe.jsonl).

## Scope

Stdio only. HTTP servers are deferred, and so is anything hosted by a third
party: this was built to probe servers running locally, and making requests to
other people's endpoints is a separate decision.

## Tests

30 tests, model-free and network-free. The wire tests run real servers through
`InMemoryTransport` rather than the SDK's in-process shortcut, which skips
JSON-RPC framing and would make a probe test prove nothing. Two tests spawn real
subprocesses over stdio, one of which crashes on startup.

```bash
uv run pytest tools/discover-probe/tests/
```
