"""Shared, model-pluggable building blocks for data-tools.

Tools depend only on the interfaces exported here, never on a specific LLM
provider. See :mod:`dt_shared.llm` for the provider protocols and factory.
"""

__version__ = "0.1.0"

from .config import Settings, get_settings
from .llm import (
    ChatProvider,
    EmbeddingProvider,
    LiteLLMChat,
    LiteLLMEmbeddings,
    get_chat_provider,
    get_embedding_provider,
)

__all__ = [
    "Settings",
    "get_settings",
    "ChatProvider",
    "EmbeddingProvider",
    "LiteLLMChat",
    "LiteLLMEmbeddings",
    "get_chat_provider",
    "get_embedding_provider",
]
