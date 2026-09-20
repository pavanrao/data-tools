"""Servers to probe, over a real JSON-RPC wire.

The SDK's in-process modern path skips JSON-RPC framing entirely, which would
make a probe test prove nothing. Every fixture here goes through
``InMemoryTransport`` so each request is serialised and parsed as it would be
over stdio.

Passed as fixtures rather than imported: the suite runs under
``--import-mode=importlib``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import anyio
import mcp_types as types
import pytest
from mcp.client._memory import InMemoryTransport
from mcp.server.mcpserver import MCPServer
from mcp.shared.exceptions import MCPError
from mcp_types.jsonrpc import METHOD_NOT_FOUND


def _server_with_a_tool(name: str) -> MCPServer:
    server = MCPServer(name)

    @server.tool()
    def ping() -> dict[str, object]:
        """Answer, so there is one tool to list."""
        return {"ok": True}

    return server


def _opener(server: MCPServer):
    """A factory, not a transport: each negotiation path needs its own connection."""

    def open_transport():
        return InMemoryTransport(server._lowlevel_server)

    return open_transport


@pytest.fixture
def both_eras():
    """The SDK's own server, which answers discover and the handshake."""
    return _opener(_server_with_a_tool("both-eras"))


@pytest.fixture
def legacy_only():
    """A server that answers the handshake and rejects discover.

    Uses the documented seam: ``add_request_handler`` replaces the discover
    handler wholesale. ``initialize`` is reserved and cannot be replaced the
    same way, which is why there is no modern-only wire fixture; that case is
    covered by the classification tests instead.
    """
    server = _server_with_a_tool("legacy-only")

    async def reject(ctx, params):
        raise MCPError(METHOD_NOT_FOUND, "Method not found: server/discover")

    server._lowlevel_server.add_request_handler("server/discover", types.RequestParams, reject)
    return _opener(server)


@pytest.fixture
def refuses_to_connect():
    """A transport that fails before a single message is exchanged."""

    def open_transport():
        @asynccontextmanager
        async def broken():
            raise ConnectionRefusedError("nothing listening")
            yield  # pragma: no cover

        return broken()

    return open_transport


@asynccontextmanager
async def _silent_transport():
    """Connects, then never delivers a byte in either direction."""
    send, receive = anyio.create_memory_object_stream(0)
    back_send, back_receive = anyio.create_memory_object_stream(0)
    async with send, receive, back_send, back_receive:
        yield back_receive, send


@pytest.fixture
def never_answers():
    """A transport that connects and then goes silent forever."""
    return _silent_transport


@pytest.fixture
def cold_start():
    """Silent on the first connection, then an ordinary server.

    The shape of a first ``npx``/``uvx`` run: discover goes first, so it absorbs the
    package download, and the handshake that follows finds a warm cache. Found when
    dbt-mcp timed out on discover once and answered normally on every run after.
    """
    server = _server_with_a_tool("cold-start")
    opened = 0

    def open_transport():
        nonlocal opened
        opened += 1
        if opened == 1:
            return _silent_transport()
        return InMemoryTransport(server._lowlevel_server)

    return open_transport


@pytest.fixture
def hangs_on_discover():
    """Alive and answering the handshake, but never replying to discover at all."""
    server = _server_with_a_tool("hangs-on-discover")

    async def hang(ctx, params):
        await anyio.sleep_forever()

    server._lowlevel_server.add_request_handler("server/discover", types.RequestParams, hang)
    return _opener(server)
