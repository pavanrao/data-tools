"""The optional model layer: narrow interfaces, swappable backends.

Tools depend only on the :class:`EmbeddingProvider` / :class:`ChatProvider`
protocols — never on LiteLLM, and never on a specific vendor. The concrete
implementations here wrap LiteLLM, so switching providers is a config change (a
model string like ``ollama/llama3.1`` -> ``anthropic/claude-sonnet-4-5``), not a
code change.

Two properties this file exists to protect:

* **The protocols import with nothing installed.** ``litellm`` is imported
  lazily, inside the call, so a tool's deterministic core stays testable on a
  machine that has no model stack (CONVENTIONS rules 2 and 3). Install the
  backend with the ``llm`` extra: ``uv sync --extra llm``.
* **The indirection is two layers deep.** Tools talk to protocols; protocols are
  satisfied by LiteLLM today. Replacing LiteLLM touches this module only.

This is the seed of the ``model-router`` idea (#24) in IDEAS.md.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from data_tools_core.config import Settings, get_settings


class BackendUnavailable(RuntimeError):
    """Raised when the optional model backend is not installed."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turns text into vectors. The only embedding contract tools may rely on."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class ChatProvider(Protocol):
    """Turns a prompt into a completion. The only chat contract tools may rely on."""

    def complete(self, prompt: str, **opts: Any) -> str: ...


def _litellm() -> Any:
    """Import litellm on demand, turning a missing extra into a clear error."""
    try:
        import litellm
    except ModuleNotFoundError as exc:  # pragma: no cover - trivial guard
        raise BackendUnavailable(
            "the litellm backend is not installed; run `uv sync --extra llm` "
            "or install data-tools-core[llm]"
        ) from exc
    return litellm


class _LiteLLMBase:
    def __init__(
        self,
        model: str,
        *,
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.api_base = api_base
        self.api_key = api_key

    def _passthrough(self) -> dict[str, Any]:
        kw: dict[str, Any] = {}
        if self.api_base:
            kw["api_base"] = self.api_base
        if self.api_key:
            kw["api_key"] = self.api_key
        return kw


class LiteLLMEmbeddings(_LiteLLMBase):
    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = _litellm().embedding(model=self.model, input=list(texts), **self._passthrough())
        return [item["embedding"] for item in resp.data]


class LiteLLMChat(_LiteLLMBase):
    def complete(self, prompt: str, **opts: Any) -> str:
        resp = _litellm().completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **self._passthrough(),
            **opts,
        )
        return resp.choices[0].message.content


def get_embedding_provider(settings: Settings | None = None) -> LiteLLMEmbeddings:
    s = settings or get_settings()
    return LiteLLMEmbeddings(s.embed_model, api_base=s.api_base, api_key=s.api_key)


def get_chat_provider(settings: Settings | None = None) -> LiteLLMChat:
    s = settings or get_settings()
    return LiteLLMChat(s.chat_model, api_base=s.api_base, api_key=s.api_key)
