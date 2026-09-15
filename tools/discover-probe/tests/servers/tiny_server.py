"""A minimal stdio MCP server, spawned by the CLI test as a real subprocess.

Lives in the test tree rather than importing another tool, so this tool's tests
depend on nothing but this tool (CONVENTIONS rule 1).
"""

from mcp.server.mcpserver import MCPServer

server = MCPServer("tiny")


@server.tool()
def ping() -> dict[str, object]:
    """Answer, so there is one tool to list."""
    return {"ok": True}


if __name__ == "__main__":
    server.run(transport="stdio")
