"""The CLI seam: exit codes a script can branch on, and a real subprocess probe."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from discover_probe.cli import exit_code, main
from discover_probe.probe import Check, PathOutcome, Report

TINY = Path(__file__).parent / "servers" / "tiny_server.py"


def report(era, *checks):
    return Report(
        target="t",
        era=era,
        server_name="s",
        checks=list(checks),
        discover=PathOutcome(status="ok"),
        handshake=PathOutcome(status="ok"),
    )


def test_an_unreachable_server_exits_two():
    assert exit_code(report("unreachable")) == 2


def test_a_server_whose_advertised_listing_fails_exits_one():
    assert exit_code(report("both", Check("claims-modern", "fail", "tools error"))) == 1


def test_a_legacy_only_server_is_information_not_a_failure():
    # Not speaking the July revision is a fact about the server, not a lie.
    failed_discover = Check("discover", "fail", "rejected: error -32601")
    assert exit_code(report("legacy-only", failed_discover)) == 0


def test_probing_a_real_subprocess_over_stdio(capsys):
    code = main(["--json", "stdio", "--", sys.executable, str(TINY)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["era"] == "both"
    assert payload["server_name"] == "tiny"


def test_a_double_dash_inside_the_server_command_is_passed_through(capsys):
    # Only the separator is consumed. A server whose own arguments contain "--"
    # must receive them intact, or the probe spawns a different command.
    main(["--json", "stdio", "--", sys.executable, str(TINY), "--", "extra"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["target"].endswith("-- extra")
    assert payload["era"] == "both"
