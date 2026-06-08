from types import SimpleNamespace

from dt_shared import llm


def test_embeddings_provider_calls_litellm_and_unwraps_vectors(monkeypatch):
    captured = {}

    def fake_embedding(model, input, **kwargs):
        captured["model"] = model
        captured["input"] = input
        captured["kwargs"] = kwargs
        return SimpleNamespace(data=[{"embedding": [0.1, 0.2]} for _ in input])

    monkeypatch.setattr(llm.litellm, "embedding", fake_embedding)

    provider = llm.LiteLLMEmbeddings("ollama/nomic-embed-text", api_base="http://x")
    out = provider.embed(["a", "b"])

    assert out == [[0.1, 0.2], [0.1, 0.2]]
    assert captured["model"] == "ollama/nomic-embed-text"
    assert captured["input"] == ["a", "b"]
    assert captured["kwargs"]["api_base"] == "http://x"


def test_chat_provider_calls_litellm_and_returns_content(monkeypatch):
    captured = {}

    def fake_completion(model, messages, **kwargs):
        captured["model"] = model
        captured["messages"] = messages
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hi"))]
        )

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    provider = llm.LiteLLMChat("ollama/llama3.1")
    out = provider.complete("hello", temperature=0)

    assert out == "hi"
    assert captured["model"] == "ollama/llama3.1"
    assert captured["messages"] == [{"role": "user", "content": "hello"}]
    assert captured["kwargs"]["temperature"] == 0


def test_providers_satisfy_protocols():
    assert isinstance(llm.LiteLLMEmbeddings("m"), llm.EmbeddingProvider)
    assert isinstance(llm.LiteLLMChat("m"), llm.ChatProvider)


def test_factory_builds_providers_from_settings(monkeypatch):
    monkeypatch.setenv("DATA_TOOLS_CHAT_MODEL", "anthropic/claude-3-5-sonnet")
    monkeypatch.setenv("DATA_TOOLS_EMBED_MODEL", "openai/text-embedding-3-small")

    chat = llm.get_chat_provider()
    emb = llm.get_embedding_provider()

    assert chat.model == "anthropic/claude-3-5-sonnet"
    assert emb.model == "openai/text-embedding-3-small"
