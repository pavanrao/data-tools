"""The chunkers, and the spec strings that name them.

A *spec* is how a strategy is written on the command line and recorded in a
result row: ``fixed:512``, ``recursive:400/200``. One string names the strategy
and every parameter that changes its output, so two rows can never be compared
unless they really did run the same thing (CONVENTIONS rule 5).
"""

from __future__ import annotations

from chunking_lab.chunkers.base import Chunker, LengthFn, char_length, trim
from chunking_lab.chunkers.fixed import FixedChunker
from chunking_lab.chunkers.recursive import DEFAULT_SEPARATORS, RecursiveChunker

__all__ = [
    "DEFAULT_SEPARATORS",
    "Chunker",
    "FixedChunker",
    "LengthFn",
    "RecursiveChunker",
    "char_length",
    "from_spec",
    "trim",
]

#: Strategy name -> the class that implements it. Tier 1 and Tier 2 strategies
#: register here too; nothing about the spec syntax knows which tier it is in.
SIZED = {"fixed": FixedChunker, "recursive": RecursiveChunker}


def from_spec(spec: str) -> Chunker:
    """Build a chunker from its spec string.

    >>> from_spec("recursive:400/200").name
    'recursive:400/200'
    """
    name, _, params = spec.partition(":")
    name = name.strip()
    if name not in SIZED:
        known = ", ".join(sorted(SIZED))
        raise ValueError(f"unknown strategy {name!r} in spec {spec!r}; known: {known}")
    if not params:
        raise ValueError(f"strategy {name!r} needs a size, as in {name}:400 or {name}:400/200")

    size_text, _, overlap_text = params.partition("/")
    try:
        size = int(size_text)
        overlap = int(overlap_text) if overlap_text else 0
    except ValueError as exc:
        raise ValueError(f"could not read a size and overlap from spec {spec!r}") from exc
    return SIZED[name](size=size, overlap=overlap)
