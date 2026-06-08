from docs_rag.query import Answer, answer, build_prompt
from docs_rag.store import SearchResult


def test_build_prompt_includes_question_numbered_context_and_sources():
    results = [
        SearchResult("apples are red", "fruit.txt", 0, 0.1),
        SearchResult("sky is blue", "sky.txt", 0, 0.2),
    ]

    prompt = build_prompt("what colour are apples?", results)

    assert "what colour are apples?" in prompt
    assert "[1]" in prompt and "[2]" in prompt
    assert "fruit.txt" in prompt and "sky.txt" in prompt
    assert "apples are red" in prompt


class _FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)
        return [[1.0, 0.0, 0.0] for _ in texts]


class _FakeStore:
    def search(self, query_embedding, k=5):
        return [SearchResult("grounded context", "doc.txt", 0, 0.05)]


class _FakeChat:
    def __init__(self):
        self.prompt = None

    def complete(self, prompt, **opts):
        self.prompt = prompt
        return "Apples are red [1]."


def test_answer_retrieves_then_grounds_chat_in_context():
    chat = _FakeChat()
    embedder = _FakeEmbedder()

    result = answer(
        "what colour are apples?", store=_FakeStore(), embedder=embedder, chat=chat
    )

    assert isinstance(result, Answer)
    assert result.text == "Apples are red [1]."
    assert result.sources == ["doc.txt"]
    # the chat was grounded in retrieved context, not the bare question
    assert "grounded context" in chat.prompt
    assert embedder.calls == [["what colour are apples?"]]


def test_answer_dedupes_sources():
    class MultiStore:
        def search(self, query_embedding, k=5):
            return [
                SearchResult("a", "doc.txt", 0, 0.1),
                SearchResult("b", "doc.txt", 1, 0.2),
                SearchResult("c", "other.txt", 0, 0.3),
            ]

    result = answer("q", store=MultiStore(), embedder=_FakeEmbedder(), chat=_FakeChat())

    assert result.sources == ["doc.txt", "other.txt"]
