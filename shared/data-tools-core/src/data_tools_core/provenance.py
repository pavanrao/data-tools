"""The one type every tool in the collection agrees on.

A value without provenance is a value you cannot audit. Every record that
crosses a tool boundary carries one of these.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class UnitKind(StrEnum):
    """The addressable subdivision of a source file.

    Chosen per format so that "how many are there?" has an answer that can be
    computed *without* extracting content — that independence is what makes
    reconciliation meaningful.
    """

    PAGE = "page"  # PDF
    SHEET = "sheet"  # XLSX workbook
    ROW = "row"  # XLSX sheet, CSV
    BLOCK = "block"  # DOCX body element (paragraph, table, text box, note)
    NODE = "node"  # XML top-level child
    LINE = "line"  # plain text
    MEMBER = "member"  # archive entry
    DOCUMENT = "document"  # whole file, not subdivisible


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a piece of extracted content came from."""

    source: Path
    sha256: str
    unit_kind: UnitKind
    unit_id: str | int | None = None
    #: Path of enclosing archives, outermost first. Empty for a loose file.
    container_path: tuple[str, ...] = field(default_factory=tuple)

    @property
    def locator(self) -> str:
        """Stable human-readable address, e.g. ``rfp.zip!appendix.xlsx#sheet=4``."""
        prefix = "!".join((*self.container_path, self.source.name))
        if self.unit_id is None:
            return prefix
        return f"{prefix}#{self.unit_kind}={self.unit_id}"


def hash_file(path: Path, _chunk: int = 1 << 20) -> str:
    """SHA-256 of a file, streamed so a large input cannot blow up memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(_chunk):
            digest.update(block)
    return digest.hexdigest()
