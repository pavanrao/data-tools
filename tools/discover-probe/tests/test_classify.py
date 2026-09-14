"""Era classification, tested as pure logic.

A server that never answered is not a server that said no. Conflating the two is
the error this module exists to avoid.
"""

from __future__ import annotations

import pytest
from discover_probe.probe import classify_era


@pytest.mark.parametrize(
    ("discover", "handshake", "era"),
    [
        ("ok", "ok", "both"),
        ("ok", "rejected", "modern-only"),
        ("ok", "unreachable", "modern-only"),
        ("rejected", "ok", "legacy-only"),
        ("unreachable", "ok", "legacy-only"),
        ("rejected", "rejected", "neither"),
        ("rejected", "unreachable", "neither"),
        ("unreachable", "unreachable", "unreachable"),
    ],
)
def test_era_follows_from_what_each_path_actually_did(discover, handshake, era):
    assert classify_era(discover, handshake) == era


def test_errors_the_client_raises_on_its_own_behalf_are_not_refusals():
    # Found probing real servers. The SDK reports a server process that died, and a
    # request nobody answered, as MCPError too. Neither is the server saying no:
    # MotherDuck exited on a bad flag, and dbt-mcp never replied to discover.
    from discover_probe.probe import status_for_error
    from mcp.shared.exceptions import MCPError
    from mcp_types.jsonrpc import CONNECTION_CLOSED, METHOD_NOT_FOUND, REQUEST_TIMEOUT

    assert status_for_error(MCPError(CONNECTION_CLOSED, "Connection closed")) == "unreachable"
    assert status_for_error(MCPError(REQUEST_TIMEOUT, "timed out")) == "unreachable"
    assert status_for_error(MCPError(METHOD_NOT_FOUND, "Method not found")) == "rejected"
    assert status_for_error(MCPError(-32602, "Invalid request")) == "rejected"
