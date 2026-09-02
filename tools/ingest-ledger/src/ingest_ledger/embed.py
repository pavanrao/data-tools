"""Embeddings behind a swappable interface.

The default is deterministic, dependency-free, and offline: hashed bag-of-words
into a fixed-width unit vector. It is not competitive with a trained encoder and
is not meant to be -- it exists so the reconciliation and gating logic can be
tested without a model, on any machine, in milliseconds.

Swap in a real encoder by passing any object with the same ``encode`` shape.
The point of this tool is what it refuses to answer, and that must not depend
on which embedder is installed.
"""

from __future__ import annotations

import hashlib
import math
import re
from array import array
from typing import Protocol

DIMENSIONS = 512
_TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dimensions: int
    name: str

    def encode(self, text: str) -> list[float]: ...


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class HashingEmbedder:
    """Hashed bag-of-words with sublinear term frequency, L2-normalised."""

    name = "hashing-bow-v1"

    def __init__(self, dimensions: int = DIMENSIONS) -> None:
        self.dimensions = dimensions

    def encode(self, text: str) -> list[float]:
        counts: dict[int, float] = {}
        for token in tokenize(text):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            bucket = int.from_bytes(digest, "little") % self.dimensions
            counts[bucket] = counts.get(bucket, 0.0) + 1.0

        vector = [0.0] * self.dimensions
        for bucket, count in counts.items():
            # Sublinear tf: a word repeated 50 times is not 50x the signal.
            vector[bucket] = 1.0 + math.log(count)

        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


def cosine(left: list[float], right: list[float]) -> float:
    """Both sides are unit vectors, so the dot product is the cosine."""
    return sum(a * b for a, b in zip(left, right, strict=True))


def pack(vector: list[float]) -> bytes:
    return array("f", vector).tobytes()


def unpack(blob: bytes) -> list[float]:
    vector = array("f")
    vector.frombytes(blob)
    return list(vector)
