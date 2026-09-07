"""The embedding seam for Tier 1, and the record of which side of it ran.

Tier 1 (semantic chunking) is the first thing in this tool that needs a model, so
this module is where CONVENTIONS rules 2 and 3 are paid for:

* Nothing here is imported by Tier 0, and the LiteLLM backend is imported inside
  the call, so ``import chunking_lab`` never drags in a model stack.
* Every provider reports an ``id``, and the chunker records it on the
  ``Chunking``. A semantic run against a hosted encoder and one against the
  hashing fallback are **not** comparable, and the result must say which it was
  rather than quietly substituting.

``HashingEmbedder`` deserves a word. It is deterministic, offline and about as
good as a bag of words, which is to say **not competitive with a trained
encoder**. It exists so Tier 1 can be exercised, tested and demonstrated on a
machine with no key -- and so the difference between "semantic chunking helps"
and "semantic chunking helps *with a real encoder*" is a value in a column rather
than an assumption. `ingest-ledger` ships one for the same reason; tools do not
import each other (rule 1), so this is a deliberate thirty-line duplicate.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

DIMENSIONS = 512
_TOKEN = re.compile(r"[a-z0-9]+")


@runtime_checkable
class Embedder(Protocol):
    """What a Tier 1 chunker needs. Deliberately narrower than a full provider."""

    @property
    def id(self) -> str:
        """Stable identifier recorded on every result produced with this embedder."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch. Batched rather than per-text because Tier 1 embeds every
        sentence in the corpus and a per-call round trip would dominate."""
        ...


class HashingEmbedder:
    """Hashed bag-of-words, L2-normalised. Deterministic, offline, and weak.

    Weak on purpose and labelled as such: it makes Tier 1 runnable with nothing
    installed, which is what lets the semantic chunkers be tested at all
    (CONVENTIONS rule 6). Never quote a semantic-chunking result produced with it
    as evidence about semantic chunking.
    """

    def __init__(self, dimensions: int = DIMENSIONS) -> None:
        self.dimensions = dimensions

    @property
    def id(self) -> str:
        return f"hashing-bow-v1/{self.dimensions}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        counts: dict[int, float] = {}
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            bucket = int.from_bytes(digest, "little") % self.dimensions
            counts[bucket] = counts.get(bucket, 0.0) + 1.0

        vector = [0.0] * self.dimensions
        for bucket, count in counts.items():
            # Sublinear tf: a word repeated 50 times is not 50x the signal.
            vector[bucket] = 1.0 + math.log(count)
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class ProviderEmbedder:
    """Adapts ``data_tools_core.llm.EmbeddingProvider`` to what Tier 1 needs.

    The provider is resolved lazily so that constructing a chunker never requires
    the ``llm`` extra -- only calling it does.
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model
        self._provider = None

    @property
    def id(self) -> str:
        return f"provider/{self._model or 'configured'}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._provider is None:
            from data_tools_core.llm import get_embedding_provider

            self._provider = get_embedding_provider()
            self._model = self._model or getattr(self._provider, "model", None)
        return self._provider.embed(list(texts))


def resolve(name: str = "hashing") -> Embedder:
    """Build an embedder by name.

    ``hashing`` is the offline default. ``provider`` reads the configured model
    from ``DATA_TOOLS_EMBED_MODEL`` and needs the ``llm`` extra installed; the
    failure, if it is not, comes from ``data_tools_core.llm`` and names the extra.
    """
    if name == "hashing":
        return HashingEmbedder()
    if name == "provider":
        return ProviderEmbedder()
    raise ValueError(f"unknown embedder {name!r}; known: hashing, provider")


def cosine(left: list[float], right: list[float]) -> float:
    """Cosine similarity. Inputs are unit vectors in practice, but do not assume it."""
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0
