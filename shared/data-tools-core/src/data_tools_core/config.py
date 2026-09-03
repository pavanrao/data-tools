"""Environment-driven configuration for the optional model layer.

Settings are read from ``DATA_TOOLS_*`` environment variables, or from a local
``.env`` file when one is present. The defaults run fully locally against
Ollama; point the model strings at any LiteLLM-supported provider to switch
backends without touching code.

Deliberately stdlib-only. ``data-tools-core`` carries no base dependencies
(CONVENTIONS rule 2), so this cannot reach for pydantic-settings — a tool must
be able to import the core contracts with nothing else installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_PREFIX = "DATA_TOOLS_"

DEFAULT_CHAT_MODEL = "ollama/llama3.1"
DEFAULT_EMBED_MODEL = "ollama/nomic-embed-text"


@dataclass(frozen=True, slots=True)
class Settings:
    """Resolved model configuration.

    ``chat_model`` and ``embed_model`` are LiteLLM model strings, e.g.
    ``ollama/llama3.1`` or ``anthropic/claude-sonnet-4-5``.
    """

    chat_model: str = DEFAULT_CHAT_MODEL
    embed_model: str = DEFAULT_EMBED_MODEL
    #: Optional overrides passed through to the backend, e.g. a local server URL.
    api_base: str | None = None
    api_key: str | None = None


def _read_dotenv(path: Path) -> dict[str, str]:
    """Parse a minimal ``KEY=value`` .env file. Missing file yields nothing."""
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("\"'")
    return values


def get_settings(env_file: Path | str = ".env") -> Settings:
    """Load settings fresh from the environment.

    Real environment variables win over ``.env`` entries, so an explicit
    ``DATA_TOOLS_CHAT_MODEL=...`` on the command line always takes effect.
    """
    merged = {**_read_dotenv(Path(env_file)), **os.environ}

    def get(name: str, default: str | None = None) -> str | None:
        value = merged.get(f"{ENV_PREFIX}{name}")
        return value if value else default

    return Settings(
        chat_model=get("CHAT_MODEL", DEFAULT_CHAT_MODEL) or DEFAULT_CHAT_MODEL,
        embed_model=get("EMBED_MODEL", DEFAULT_EMBED_MODEL) or DEFAULT_EMBED_MODEL,
        api_base=get("API_BASE"),
        api_key=get("API_KEY"),
    )
