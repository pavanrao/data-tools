from dt_shared import config

ENV_VARS = [
    "DATA_TOOLS_CHAT_MODEL",
    "DATA_TOOLS_EMBED_MODEL",
    "DATA_TOOLS_API_BASE",
    "DATA_TOOLS_API_KEY",
]


def test_defaults_are_local_ollama(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    s = config.get_settings()

    assert s.chat_model == "ollama/llama3.1"
    assert s.embed_model == "ollama/nomic-embed-text"
    assert s.api_base is None
    assert s.api_key is None


def test_env_overrides_select_any_provider(monkeypatch):
    monkeypatch.setenv("DATA_TOOLS_CHAT_MODEL", "anthropic/claude-3-5-sonnet")
    monkeypatch.setenv("DATA_TOOLS_EMBED_MODEL", "openai/text-embedding-3-small")
    monkeypatch.setenv("DATA_TOOLS_API_BASE", "http://localhost:1234")

    s = config.get_settings()

    assert s.chat_model == "anthropic/claude-3-5-sonnet"
    assert s.embed_model == "openai/text-embedding-3-small"
    assert s.api_base == "http://localhost:1234"
