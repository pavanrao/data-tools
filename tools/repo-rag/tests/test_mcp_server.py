import asyncio

from repo_rag.mcp_server import build_server, get_chunk_impl, search_code_impl
from repo_rag.store import CodeHit


class _FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class _FakeStore:
    def __init__(self):
        self.hit = CodeHit(
            7, "def authenticate(): return 1", "auth.py", 1, 2, "authenticate", "function", 0.1
        )

    def search(self, query_embedding, query_text, k=5):
        return [self.hit]

    def get_chunk(self, chunk_id):
        assert chunk_id == 7
        return self.hit


def test_search_code_impl_returns_ranked_summaries():
    results = search_code_impl(_FakeStore(), _FakeEmbedder(), "auth", k=3)

    assert results[0]["chunk_id"] == 7
    assert results[0]["path"] == "auth.py"
    assert results[0]["start_line"] == 1
    assert results[0]["symbol"] == "authenticate"


def test_get_chunk_impl_returns_full_text():
    result = get_chunk_impl(_FakeStore(), 7)

    assert result["chunk_id"] == 7
    assert result["text"] == "def authenticate(): return 1"


def test_build_server_exposes_only_readonly_tools():
    server = build_server(_FakeStore(), _FakeEmbedder())

    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}

    assert names == {"search_code", "get_chunk"}


def test_tools_dispatch_through_the_server():
    """Registration passing does not prove dispatch works.

    The mcp 1.x -> 2.x break was invisible to a registration-only assertion, so
    this drives a real call through the server and reads the result back.
    """
    server = build_server(_FakeStore(), _FakeEmbedder())

    result = asyncio.run(server.call_tool("search_code", {"query": "auth", "k": 3}))

    assert not result.is_error
    assert result.structured_content["result"][0]["chunk_id"] == 7
    assert result.structured_content["result"][0]["symbol"] == "authenticate"


def test_get_chunk_dispatches_and_returns_full_text():
    server = build_server(_FakeStore(), _FakeEmbedder())

    result = asyncio.run(server.call_tool("get_chunk", {"chunk_id": 7}))

    assert not result.is_error
    assert result.structured_content["text"] == "def authenticate(): return 1"


def test_tools_work_against_a_real_store_from_a_worker_thread(tmp_path):
    """Guards the mcp 2.x thread-affinity trap.

    The SDK dispatches tool calls on a worker thread while the store's SQLite
    connection is opened on the main one. A fake store cannot catch that, so
    this drives a real CodeStore through the server; before CodeStore took
    check_same_thread=False plus a lock, this raised "SQLite objects created in
    a thread can only be used in that same thread" for every call.
    """
    from repo_rag.chunk import CodeChunk
    from repo_rag.store import CodeStore

    store = CodeStore(tmp_path / "t.db", dim=3)
    store.add(
        [CodeChunk("def authenticate(): return 1", "auth.py", 1, 2, "authenticate", "function")],
        [[1.0, 0.0, 0.0]],
    )

    server = build_server(store, _FakeEmbedder())

    chunk = asyncio.run(server.call_tool("get_chunk", {"chunk_id": 1}))
    assert not chunk.is_error
    assert chunk.structured_content["path"] == "auth.py"

    found = asyncio.run(server.call_tool("search_code", {"query": "authenticate", "k": 2}))
    assert not found.is_error
    assert found.structured_content["result"][0]["symbol"] == "authenticate"

    store.close()
