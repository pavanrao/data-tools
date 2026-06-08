"""Environment-driven configuration for the model-pluggable LLM layer.

All settings are read from ``DATA_TOOLS_*`` environment variables (or a local
``.env``). The defaults run fully locally against Ollama; point the model
strings at any LiteLLM-supported provider to switch — no code changes.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DATA_TOOLS_",
        env_file=".env",
        extra="ignore",
    )

    # LiteLLM model strings (e.g. "ollama/llama3.1", "anthropic/claude-3-5-sonnet").
    chat_model: str = "ollama/llama3.1"
    embed_model: str = "ollama/nomic-embed-text"

    # Optional overrides passed through to the provider (e.g. a local server URL).
    api_base: str | None = None
    api_key: str | None = None


def get_settings() -> Settings:
    """Load settings fresh from the environment."""
    return Settings()
