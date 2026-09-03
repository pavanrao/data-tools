from repo_rag.query import Answer, answer, build_prompt
from repo_rag.store import CodeHit


def _hit(cid, path, start, end, symbol, text):
    return CodeHit(cid, text, path, start, end, symbol, "function", 0.1)


def test_build_prompt_shows_file_line_spans_and_question():
    hits = [_hit(1, "auth.py", 1, 5, "authenticate", "def authenticate(): ...")]

    prompt = build_prompt("where is auth handled?", hits)

    assert "where is auth handled?" in prompt
    assert "auth.py:1-5" in prompt
    assert "authenticate" in prompt
    assert "def authenticate" in prompt


class _FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class _FakeStore:
    def __init__(self, hits):
        self._hits = hits
        self.called_with = None

    def search(self, query_embedding, query_text, k=5):
        self.called_with = (query_text, k)
        return self._hits


class _FakeChat:
    def __init__(self):
        self.prompt = None

    def complete(self, prompt, **opts):
        self.prompt = prompt
        return "Auth is in auth.py:1-5."


def test_answer_runs_hybrid_search_and_cites_file_lines():
    hits = [_hit(1, "auth.py", 1, 5, "authenticate", "def authenticate(): ...")]
    store = _FakeStore(hits)
    chat = _FakeChat()

    result = answer("where is auth?", store=store, embedder=_FakeEmbedder(), chat=chat, k=7)

    assert isinstance(result, Answer)
    assert result.text == "Auth is in auth.py:1-5."
    assert result.citations == ["auth.py:1-5"]
    assert store.called_with == ("where is auth?", 7)  # hybrid uses the text too
    assert "def authenticate" in chat.prompt
