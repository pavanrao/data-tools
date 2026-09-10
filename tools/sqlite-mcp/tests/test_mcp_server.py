"""The MCP surface: three tools, typed results, and refusals that are data.

Model-free. The server is driven directly, as repo-rag's tests do.
"""

from __future__ import annotations

import asyncio

from sqlite_mcp.mcp_server import build_server, query_impl


def test_registers_exactly_the_three_read_tools(db):
    server = build_server(db)

    tools = asyncio.run(server.list_tools())

    assert sorted(t.name for t in tools) == ["query", "sample", "schema"]


def test_every_tool_declares_an_output_schema(db):
    server = build_server(db)

    tools = asyncio.run(server.list_tools())

    missing = [t.name for t in tools if not t.output_schema]
    assert missing == [], f"tools with no output schema: {missing}"


def test_query_returns_rows_and_the_evidence_of_its_cap(db):
    result = query_impl(db, "SELECT customer FROM orders ORDER BY id")

    assert result["columns"] == ["customer"]
    assert result["rows"] == [["ada"], ["bob"]]
    assert result["truncated"] is True
    assert result["row_limit"] == 2
    assert "elapsed_ms" in result


def test_a_refusal_comes_back_as_data_not_an_exception(db):
    result = query_impl(db, "DELETE FROM orders")

    assert result["refused"] is True
    assert result["guard"] == "not-read-only"
    assert "read-only" in result["reason"]


def test_a_client_gets_structured_content_over_the_protocol(db):
    """The round trip, not just the registration.

    Everything above drives the server object directly. This one goes through a
    real client and asserts on `structured_content`, which is what a consumer
    actually reads. Drop the parameterised return annotations in mcp_server and
    this is the test that fails; the registration tests would not notice.
    """
    from mcp.client.client import Client

    async def exchange():
        async with Client(build_server(db)._lowlevel_server) as client:
            ok = await client.call_tool("query", {"sql": "SELECT customer FROM orders ORDER BY id"})
            denied = await client.call_tool("query", {"sql": "DROP TABLE orders"})
            return ok, denied

    ok, denied = asyncio.run(exchange())

    assert ok.structured_content["rows"] == [["ada"], ["bob"]]
    assert ok.structured_content["truncated"] is True
    # A refusal is a normal result. An error would tell the model something
    # broke; this tells it what to do differently.
    assert denied.is_error is False
    assert denied.structured_content["guard"] == "not-read-only"
