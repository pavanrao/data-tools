"""Settings resolution: defaults, environment, and .env precedence."""

from data_tools_core.config import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_EMBED_MODEL,
    get_settings,
)


def _clear(monkeypatch):
    for name in ("CHAT_MODEL", "EMBED_MODEL", "API_BASE", "API_KEY"):
        monkeypatch.delenv(f"DATA_TOOLS_{name}", raising=False)


def test_defaults_run_locally_on_ollama(monkeypatch, tmp_path):
    _clear(monkeypatch)
    settings = get_settings(env_file=tmp_path / "absent.env")

    assert settings.chat_model == DEFAULT_CHAT_MODEL
    assert settings.embed_model == DEFAULT_EMBED_MODEL
    assert settings.api_base is None
    assert settings.api_key is None


def test_environment_overrides_defaults(monkeypatch, tmp_path):
    _clear(monkeypatch)
    monkeypatch.setenv("DATA_TOOLS_CHAT_MODEL", "anthropic/claude-sonnet-4-5")
    monkeypatch.setenv("DATA_TOOLS_API_BASE", "http://localhost:11434")

    settings = get_settings(env_file=tmp_path / "absent.env")

    assert settings.chat_model == "anthropic/claude-sonnet-4-5"
    assert settings.api_base == "http://localhost:11434"
    assert settings.embed_model == DEFAULT_EMBED_MODEL


def test_dotenv_is_read_when_present(monkeypatch, tmp_path):
    _clear(monkeypatch)
    env = tmp_path / ".env"
    env.write_text(
        '# a comment\n\nDATA_TOOLS_CHAT_MODEL=openai/gpt-4o-mini\nDATA_TOOLS_API_KEY="sk-quoted"\n'
    )

    settings = get_settings(env_file=env)

    assert settings.chat_model == "openai/gpt-4o-mini"
    assert settings.api_key == "sk-quoted"


def test_real_environment_wins_over_dotenv(monkeypatch, tmp_path):
    _clear(monkeypatch)
    env = tmp_path / ".env"
    env.write_text("DATA_TOOLS_CHAT_MODEL=from/dotenv\n")
    monkeypatch.setenv("DATA_TOOLS_CHAT_MODEL", "from/environ")

    assert get_settings(env_file=env).chat_model == "from/environ"


def test_unprefixed_variables_are_ignored(monkeypatch, tmp_path):
    _clear(monkeypatch)
    monkeypatch.setenv("CHAT_MODEL", "should/be-ignored")

    assert get_settings(env_file=tmp_path / "absent.env").chat_model == DEFAULT_CHAT_MODEL
