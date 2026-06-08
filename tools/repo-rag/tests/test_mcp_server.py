import asyncio

from repo_rag.mcp_server import build_server, get_chunk_impl, search_code_impl
from repo_rag.store import CodeHit


class _FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class _FakeStore:
    def __init__(self):
        self.hit = CodeHit(7, "def authenticate(): return 1", "auth.py", 1, 2,
                           "authenticate", "function", 0.1)

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
