"""Probe an MCP server from the shell.

Exit codes are the contract a script branches on, so they encode the one thing
worth failing a pipeline over — a server claiming something it does not do —
and nothing else:

    0   probed, and every advertised listing worked
    1   the server advertised a listing that failed
    2   the server never answered at all

A legacy-only server exits 0. Not speaking the July revision is a fact about the
server, reported in the output, not a lie it told.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Sequence

import anyio
from mcp.client.stdio import StdioServerParameters, stdio_client

from .probe import Report, probe

_MARK = {"pass": "pass", "fail": "FAIL", "note": "note", "skip": "skip"}


def exit_code(report: Report) -> int:
    if report.era == "unreachable":
        return 2
    if any(c.name.startswith("claims-") and c.verdict == "fail" for c in report.checks):
        return 1
    return 0


def render(report: Report) -> str:
    lines = [
        f"target   {report.target}",
        f"server   {report.server_name or '(did not identify itself)'}",
        f"era      {report.era}",
        "",
    ]
    width = max((len(c.name) for c in report.checks), default=0)
    lines += [f"  {_MARK[c.verdict]}  {c.name:<{width}}  {c.evidence}" for c in report.checks]
    return "\n".join(lines)


def _stdio_opener(command: str, args: list[str], errlog):
    params = StdioServerParameters(command=command, args=args)

    def open_transport():
        return stdio_client(params, errlog=errlog)

    return open_transport


def main(argv: Sequence[str] | None = None) -> int:
    """Ask an MCP server what it is, one negotiation path at a time."""
    parser = argparse.ArgumentParser(prog="discover-probe", description=main.__doc__)
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="seconds per negotiation path (default 10)"
    )
    sub = parser.add_subparsers(dest="transport", required=True)

    p_stdio = sub.add_parser("stdio", help="spawn a server and probe it over stdio")
    p_stdio.add_argument("command", nargs=argparse.REMAINDER, help="-- COMMAND [ARGS...]")

    args = parser.parse_args(argv)

    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("stdio needs a server command after --")

    target = " ".join(command)
    # Server stderr stays out of a healthy report, but when a path never connected
    # it is usually the only explanation there is, so it is kept and shown then.
    with tempfile.TemporaryFile("w+") as errlog:
        opener = _stdio_opener(command[0], command[1:], errlog)
        report = anyio.run(lambda: probe(opener, target=target, timeout=args.timeout))
        errlog.seek(0)
        stderr_tail = _tail(errlog.read()) if _any_unreachable(report) else ""

    if args.json:
        payload = report.to_dict()
        if stderr_tail:
            payload["server_stderr"] = stderr_tail
        print(json.dumps(payload, indent=2))
    else:
        print(render(report))
        if stderr_tail:
            print("\nserver stderr (last lines):\n" + stderr_tail)
    return exit_code(report)


def _any_unreachable(report: Report) -> bool:
    return "unreachable" in (report.discover.status, report.handshake.status)


def _tail(text: str, lines: int = 12) -> str:
    # Each negotiation path starts the server afresh, so a server that fails at
    # startup prints the same complaint once per path. Show each line once.
    kept = list(dict.fromkeys(line for line in text.splitlines() if line.strip()))
    return "\n".join(kept[-lines:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
