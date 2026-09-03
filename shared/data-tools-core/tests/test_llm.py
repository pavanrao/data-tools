"""The model layer's contract, asserted without litellm installed.

Every test here patches ``llm._litellm``, the single lazy accessor, rather than
a module-level import. That is not just convenience: it is the property the
optional ``llm`` extra exists to guarantee — the interfaces and every tool's
deterministic core must import and be exercised on a machine with no model
stack at all.
"""

from types import SimpleNamespace

import pytest
from data_tools_core import llm


def test_protocols_import_without_a_backend_installed():
    """The headline guarantee: no import of this module reaches for litellm."""
    assert isinstance(llm.LiteLLMEmbeddings("m"), llm.EmbeddingProvider)
    assert isinstance(llm.LiteLLMChat("m"), llm.ChatProvider)


def test_missing_backend_raises_a_named_error(monkeypatch):
    def explode():
        raise llm.BackendUnavailable("not installed")

    monkeypatch.setattr(llm, "_litellm", explode)

    with pytest.raises(llm.BackendUnavailable):
        llm.LiteLLMChat("ollama/llama3.1").complete("hello")


def test_embeddings_provider_calls_backend_and_unwraps_vectors(monkeypatch):
    captured = {}

    def fake_embedding(model, input, **kwargs):
        captured.update(model=model, input=input, kwargs=kwargs)
        return SimpleNamespace(data=[{"embedding": [0.1, 0.2]} for _ in input])

    monkeypatch.setattr(llm, "_litellm", lambda: SimpleNamespace(embedding=fake_embedding))

    provider = llm.LiteLLMEmbeddings("ollama/nomic-embed-text", api_base="http://x")
    out = provider.embed(["a", "b"])

    assert out == [[0.1, 0.2], [0.1, 0.2]]
    assert captured["model"] == "ollama/nomic-embed-text"
    assert captured["input"] == ["a", "b"]
    assert captured["kwargs"]["api_base"] == "http://x"


def test_chat_provider_calls_backend_and_returns_content(monkeypatch):
    captured = {}

    def fake_completion(model, messages, **kwargs):
        captured.update(model=model, messages=messages, kwargs=kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="hi"))])

    monkeypatch.setattr(llm, "_litellm", lambda: SimpleNamespace(completion=fake_completion))

    out = llm.LiteLLMChat("ollama/llama3.1").complete("hello", temperature=0)

    assert out == "hi"
    assert captured["model"] == "ollama/llama3.1"
    assert captured["messages"] == [{"role": "user", "content": "hello"}]
    assert captured["kwargs"]["temperature"] == 0


def test_api_key_and_base_are_only_passed_when_set(monkeypatch):
    captured = {}

    def fake_completion(model, messages, **kwargs):
        captured.update(kwargs=kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=""))])

    monkeypatch.setattr(llm, "_litellm", lambda: SimpleNamespace(completion=fake_completion))

    llm.LiteLLMChat("m").complete("hello")

    assert "api_base" not in captured["kwargs"]
    assert "api_key" not in captured["kwargs"]


def test_factory_builds_providers_from_settings(monkeypatch):
    """A provider swap is a config change, not a code change."""
    monkeypatch.setenv("DATA_TOOLS_CHAT_MODEL", "anthropic/claude-sonnet-4-5")
    monkeypatch.setenv("DATA_TOOLS_EMBED_MODEL", "openai/text-embedding-3-small")

    assert llm.get_chat_provider().model == "anthropic/claude-sonnet-4-5"
    assert llm.get_embedding_provider().model == "openai/text-embedding-3-small"
