"""The chunker protocol, and the length function that keeps Tier 0 model-free.

A chunker turns a document into a :class:`~chunking_lab.spans.Chunking`. That is
the whole contract. Tier 0 implementations need nothing but the standard library
(CONVENTIONS rule 3); Tier 1 and 2 reach a model through ``data_tools_core.llm``
and are registered the same way.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from data_tools_core.provenance import Provenance

from chunking_lab.spans import Chunking

#: How a chunker measures "how big is this piece".
#:
#: The default is :func:`len` -- characters -- which is what keeps the whole Tier
#: 0 lane deterministic, offline and dependency-free. A token-counting
#: implementation lives behind the ``benchmark`` extra and is needed only to
#: reproduce a published table whose sizes were expressed in tokens; nothing in
#: the tool's own measurements depends on it. See README section 4.
type LengthFn = Callable[[str], int]


def char_length(text: str) -> int:
    """Measure size in characters. The model-free default."""
    return len(text)


@runtime_checkable
class Chunker(Protocol):
    """Turns a document into addressable spans."""

    @property
    def name(self) -> str:
        """The strategy spec that produced this chunker, e.g. ``recursive:400/200``."""
        ...

    def chunk(self, text: str, provenance: Provenance) -> Chunking:
        """Split ``text``, returning spans that satisfy ``invariant.check``."""
        ...


def trim(text: str, start: int, end: int) -> tuple[int, int] | None:
    """Shrink a range past leading and trailing whitespace.

    The reference implementation strips its chunks before locating them, which is
    where the small gaps between its spans come from. Reproducing its numbers
    means reproducing that, so the trim is explicit and shared rather than
    reimplemented per chunker.

    Returns ``None`` when the range is entirely whitespace -- such a chunk is
    dropped, exactly as ``_join_docs`` drops an empty join.
    """
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if end > start else None
