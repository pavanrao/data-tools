"""The chunkers, and the spec strings that name them.

A *spec* is how a strategy is written on the command line and recorded in a
result row: ``fixed:512``, ``recursive:400/200``, ``parent-document:200/1000``.
One string names the strategy and every parameter that changes its output, so two
rows can never be compared unless they really did run the same thing
(CONVENTIONS rule 5). ``fixed:512/0`` normalises to ``fixed:512`` so that one
configuration cannot appear twice under two names.
"""

from __future__ import annotations

from collections.abc import Callable

from chunking_lab.chunkers.base import Chunker, LengthFn, char_length, trim
from chunking_lab.chunkers.context import ParentDocumentChunker, SentenceWindowChunker
from chunking_lab.chunkers.fixed import FixedChunker
from chunking_lab.chunkers.recursive import DEFAULT_SEPARATORS, RecursiveChunker
from chunking_lab.chunkers.structural import MarkdownHeaderChunker, SentenceChunker

__all__ = [
    "DEFAULT_SEPARATORS",
    "STRATEGIES",
    "Chunker",
    "FixedChunker",
    "LengthFn",
    "MarkdownHeaderChunker",
    "ParentDocumentChunker",
    "RecursiveChunker",
    "SentenceChunker",
    "SentenceWindowChunker",
    "char_length",
    "from_spec",
    "trim",
]


def _sized(cls: type) -> Callable[[str, str], Chunker]:
    """Builder for ``NAME:SIZE[/OVERLAP]``."""

    def build(name: str, params: str) -> Chunker:
        if not params:
            raise ValueError(f"strategy {name!r} needs a size, as in {name}:400 or {name}:400/200")
        size, overlap = _two_numbers(name, params, default=0)
        return cls(size=size, overlap=overlap)

    return build


def _structural(name: str, params: str) -> Chunker:
    """Builder for ``structural`` or ``structural:MAXSIZE``."""
    if not params:
        return MarkdownHeaderChunker()
    return MarkdownHeaderChunker(max_size=_one_number(name, params))


def _sentence_window(name: str, params: str) -> Chunker:
    """Builder for ``sentence-window:W``."""
    if not params:
        raise ValueError(f"strategy {name!r} needs a window, as in {name}:2")
    return SentenceWindowChunker(window=_one_number(name, params))


def _parent_document(name: str, params: str) -> Chunker:
    """Builder for ``parent-document:CHILD/PARENT``."""
    if "/" not in params:
        raise ValueError(f"strategy {name!r} needs a child and parent size, as in {name}:200/1000")
    child, parent = _two_numbers(name, params, default=None)
    return ParentDocumentChunker(child=child, parent=parent)


#: Strategy name -> the builder that reads its parameters. Tier 1 and Tier 2
#: strategies register here too; nothing about the spec syntax knows which tier a
#: strategy is in, only whether it is installed.
STRATEGIES: dict[str, Callable[[str, str], Chunker]] = {
    "fixed": _sized(FixedChunker),
    "recursive": _sized(RecursiveChunker),
    "sentence": _sized(SentenceChunker),
    "structural": _structural,
    "sentence-window": _sentence_window,
    "parent-document": _parent_document,
}


def _one_number(name: str, params: str) -> int:
    try:
        return int(params)
    except ValueError as exc:
        raise ValueError(f"could not read a number from {name}:{params!r}") from exc


def _two_numbers(name: str, params: str, default: int | None) -> tuple[int, int]:
    first, _, second = params.partition("/")
    if not second and default is None:
        raise ValueError(f"strategy {name!r} needs two values, as in {name}:200/1000")
    try:
        return int(first), (int(second) if second else default)
    except ValueError as exc:
        raise ValueError(f"could not read a size and overlap from {name}:{params!r}") from exc


def from_spec(spec: str) -> Chunker:
    """Build a chunker from its spec string.

    >>> from_spec("recursive:400/200").name
    'recursive:400/200'
    >>> from_spec("structural").name
    'structural'
    """
    name, _, params = spec.partition(":")
    name = name.strip()
    if name not in STRATEGIES:
        known = ", ".join(sorted(STRATEGIES))
        raise ValueError(f"unknown strategy {name!r} in spec {spec!r}; known: {known}")
    return STRATEGIES[name](name, params.strip())
