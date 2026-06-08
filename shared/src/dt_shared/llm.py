"""Model-pluggable LLM/embeddings interfaces, backed by LiteLLM.

Tools depend only on the :class:`EmbeddingProvider` / :class:`ChatProvider`
protocols, never on LiteLLM or any specific vendor. The concrete
implementations here wrap LiteLLM, so switching providers is a config change
(a model string like ``ollama/llama3.1`` -> ``anthropic/claude-3-5-sonnet``),
not a code change. This is the seed of the `model-router` idea in IDEAS.md.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import litellm

from .config import Settings, get_settings


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turns text into vectors. The only embedding contract tools may rely on."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class ChatProvider(Protocol):
    """Turns a prompt into a completion. The only chat contract tools may rely on."""

    def complete(self, prompt: str, **opts: Any) -> str: ...


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
        resp = litellm.embedding(
            model=self.model, input=list(texts), **self._passthrough()
        )
        return [item["embedding"] for item in resp.data]


class LiteLLMChat(_LiteLLMBase):
    def complete(self, prompt: str, **opts: Any) -> str:
        resp = litellm.completion(
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
