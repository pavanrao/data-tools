"""Expose repo-rag retrieval as an MCP server — read-only, no mutation tools.

Any MCP client (Claude Desktop, an agent) can call ``search_code`` to find
relevant snippets and ``get_chunk`` to pull a full chunk by id. The logic lives
in plain ``*_impl`` functions so it is testable without a transport.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from mcp.server.fastmcp import FastMCP

from .store import CodeHit, CodeStore

_PREVIEW_CHARS = 200
DEFAULT_DB = ".data/repo-rag.db"


class _Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class _Store(Protocol):
    def search(
        self, query_embedding: Sequence[float], query_text: str, k: int = 5
    ) -> list[CodeHit]: ...

    def get_chunk(self, chunk_id: int) -> CodeHit: ...


def _summary(hit: CodeHit) -> dict:
    return {
        "chunk_id": hit.chunk_id,
        "path": hit.path,
        "start_line": hit.start_line,
        "end_line": hit.end_line,
        "symbol": hit.symbol,
        "kind": hit.kind,
        "preview": hit.text[:_PREVIEW_CHARS],
    }


def _full(hit: CodeHit) -> dict:
    return {
        "chunk_id": hit.chunk_id,
        "path": hit.path,
        "start_line": hit.start_line,
        "end_line": hit.end_line,
        "symbol": hit.symbol,
        "kind": hit.kind,
        "text": hit.text,
    }


def search_code_impl(store: _Store, embedder: _Embedder, query: str, k: int = 5) -> list[dict]:
    query_embedding = embedder.embed([query])[0]
    return [_summary(h) for h in store.search(query_embedding, query, k=k)]


def get_chunk_impl(store: _Store, chunk_id: int) -> dict:
    return _full(store.get_chunk(chunk_id))


def create_server(db: str | Path = DEFAULT_DB) -> FastMCP:
    """Zero-argument factory for the ``data_tools.mcp`` entry point.

    Deferred on purpose: a gateway can discover this tool without a model stack
    loading at import time. The providers are built only when it is called.
    """
    from data_tools_core.llm import get_embedding_provider

    return build_server(CodeStore(db), get_embedding_provider())


def build_server(store: _Store, embedder: _Embedder) -> FastMCP:
    server = FastMCP("repo-rag")

    @server.tool()
    def search_code(query: str, k: int = 5) -> list[dict]:
        """Search the indexed codebase. Returns ranked snippets with file:line and a chunk_id."""
        return search_code_impl(store, embedder, query, k)

    @server.tool()
    def get_chunk(chunk_id: int) -> dict:
        """Return the full text and metadata for a chunk_id returned by search_code."""
        return get_chunk_impl(store, chunk_id)

    return server
