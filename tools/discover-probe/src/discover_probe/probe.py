"""Probe an MCP server one negotiation path at a time.

The SDK's own client, left on its default, probes ``server/discover`` and then
falls back to the ``initialize`` handshake without saying which path it took or
why. Its docstring calls that fallback a denylist. That is the right behaviour
for a client that only wants a working session and the wrong one for a tool
whose job is to report what a server is, so this module drives each path on its
own connection and records what happened.

Each path gets a fresh connection. A connection that has answered ``discover``
is locked into the modern era, so reusing it for the handshake would measure the
lock rather than the server.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import anyio
from mcp.client.session import ClientSession
from mcp.shared.exceptions import MCPError
from mcp.shared.jsonrpc_dispatcher import JSONRPCDispatcher

Status = Literal["ok", "rejected", "unreachable"]
"""What one negotiation path did. ``rejected`` means the server answered and
said no; ``unreachable`` means nothing usable came back at all. An outage is
never evidence about which protocol a server speaks."""

Era = Literal["both", "modern-only", "legacy-only", "neither", "unreachable"]
Verdict = Literal["pass", "fail", "note", "skip"]

_LISTABLE = ("tools", "resources", "prompts")


@dataclass(frozen=True, slots=True)
class Check:
    """One claim tested, with the evidence that decided it (CONVENTIONS rule 5)."""

    name: str
    verdict: Verdict
    evidence: str


@dataclass(frozen=True, slots=True)
class PathOutcome:
    """What a single negotiation path observed, before any judgement is made."""

    status: Status
    versions: list[str] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    server_name: str | None = None
    listings: dict[str, str] = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Report:
    target: str
    era: Era
    server_name: str | None
    checks: list[Check]
    discover: PathOutcome
    handshake: PathOutcome

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_era(discover: Status, handshake: Status) -> Era:
    if discover == "ok" and handshake == "ok":
        return "both"
    if discover == "ok":
        return "modern-only"
    if handshake == "ok":
        return "legacy-only"
    if "rejected" in (discover, handshake):
        return "neither"
    return "unreachable"


# -- the wire ------------------------------------------------------------------


def _leaf(exc: BaseException) -> BaseException:
    """The exception that actually happened, out of any task-group wrapping."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


async def _listings(session: ClientSession, capabilities: dict[str, Any]) -> dict[str, str]:
    """Call every listing the server advertised, and record what came back.

    An empty list is not a false claim: advertising a capability with nothing in
    it yet is honest. Only a listing that fails counts against the server.
    """
    out: dict[str, str] = {}
    for kind in _LISTABLE:
        if capabilities.get(kind) is None:
            continue
        try:
            result = await getattr(session, f"list_{kind}")()
            out[kind] = str(len(getattr(result, kind)))
        except Exception as exc:  # noqa: BLE001 - recorded as evidence, not swallowed
            leaf = _leaf(exc)
            out[kind] = f"error: {type(leaf).__name__}: {leaf}"
    return out


async def _run_path(open_transport, path: Literal["discover", "handshake"], timeout: float):
    try:
        with anyio.fail_after(timeout):
            async with (
                open_transport() as (read, write),
                ClientSession(dispatcher=JSONRPCDispatcher(read, write)) as session,
            ):
                if path == "discover":
                    result = await session.discover()
                    session.adopt(result)
                    versions = list(result.supported_versions)
                    info = (result.meta or {}).get("io.modelcontextprotocol/serverInfo") or {}
                    name = info.get("name")
                else:
                    result = await session.initialize()
                    versions = [result.protocol_version]
                    name = result.server_info.name if result.server_info else None
                capabilities = result.capabilities.model_dump(exclude_none=True)
                return PathOutcome(
                    status="ok",
                    versions=versions,
                    capabilities=capabilities,
                    server_name=name,
                    listings=await _listings(session, capabilities),
                )
    except TimeoutError:
        return PathOutcome(status="unreachable", error=f"timed out after {timeout:g}s")
    except BaseException as exc:  # noqa: BLE001
        leaf = _leaf(exc)
        if isinstance(leaf, TimeoutError):
            return PathOutcome(status="unreachable", error=f"timed out after {timeout:g}s")
        if isinstance(leaf, MCPError):
            return PathOutcome(status="rejected", error=f"error {leaf.code}: {leaf}")
        if not isinstance(leaf, Exception):
            raise  # KeyboardInterrupt and friends are the operator's, not evidence
        return PathOutcome(status="unreachable", error=f"{type(leaf).__name__}: {leaf}")


# -- judgement -------------------------------------------------------------------


def _path_check(name: str, outcome: PathOutcome, describe) -> Check:
    if outcome.status == "ok":
        return Check(name, "pass", describe(outcome))
    return Check(name, "fail", f"{outcome.status}: {outcome.error}")


def _claims_check(name: str, outcome: PathOutcome) -> Check:
    if outcome.status != "ok":
        return Check(name, "skip", "this path did not connect")
    if not outcome.listings:
        return Check(name, "pass", "advertises no listings")
    failed = [k for k, v in outcome.listings.items() if v.startswith("error")]
    summary = ", ".join(f"{k} {v}" for k, v in outcome.listings.items())
    return Check(name, "fail" if failed else "pass", summary)


def _era_difference_check(discover: PathOutcome, handshake: PathOutcome) -> Check:
    """Report where the two eras' advertisements differ, without calling it a lie.

    A server legitimately computes capabilities per protocol version: change
    notification works through ``subscriptions/listen`` in the modern era and not
    in the legacy one, so the same server can truthfully claim ``list_changed`` in
    one and deny it in the other. That is recorded as a note, never a failure.
    """
    if discover.status != "ok" or handshake.status != "ok":
        return Check("capabilities-by-era", "skip", "needs both paths to connect")

    def present(caps: dict[str, Any], key: str) -> Any:
        # An omitted capability and an empty one both mean "nothing here".
        value = caps.get(key)
        return None if value in ({}, None) else value

    keys = sorted(set(discover.capabilities) | set(handshake.capabilities))
    diffs = [
        f"{k}: modern={present(discover.capabilities, k)!r} "
        f"legacy={present(handshake.capabilities, k)!r}"
        for k in keys
        if present(discover.capabilities, k) != present(handshake.capabilities, k)
    ]
    if not diffs:
        return Check("capabilities-by-era", "pass", "identical in both eras")
    return Check("capabilities-by-era", "note", "; ".join(diffs))


def _deprecated_check(discover: PathOutcome, handshake: PathOutcome) -> Check:
    """Only Logging is detectable up front.

    Roots and Sampling are features a server asks the *client* for during a
    call, so no static probe can see whether a server depends on them.
    """
    eras = [
        era
        for era, o in (("modern", discover), ("legacy", handshake))
        if o.status == "ok" and "logging" in o.capabilities
    ]
    if eras:
        return Check(
            "deprecated-logging",
            "note",
            f"advertises logging in {' and '.join(eras)}; deprecated as of 2026-07-28",
        )
    return Check("deprecated-logging", "pass", "does not advertise logging")


def build_checks(discover: PathOutcome, handshake: PathOutcome) -> list[Check]:
    return [
        _path_check("discover", discover, lambda o: "supports " + ", ".join(o.versions)),
        _path_check("handshake", handshake, lambda o: "negotiated " + ", ".join(o.versions)),
        _claims_check("claims-modern", discover),
        _claims_check("claims-legacy", handshake),
        _era_difference_check(discover, handshake),
        _deprecated_check(discover, handshake),
    ]


async def probe(open_transport, *, target: str, timeout: float = 10.0) -> Report:
    """Probe ``target`` down each negotiation path, on separate connections.

    ``open_transport`` is a zero-argument factory returning an async context
    manager that yields ``(read_stream, write_stream)``.
    """
    discover = await _run_path(open_transport, "discover", timeout)
    handshake = await _run_path(open_transport, "handshake", timeout)
    return Report(
        target=target,
        era=classify_era(discover.status, handshake.status),
        server_name=discover.server_name or handshake.server_name,
        checks=build_checks(discover, handshake),
        discover=discover,
        handshake=handshake,
    )
