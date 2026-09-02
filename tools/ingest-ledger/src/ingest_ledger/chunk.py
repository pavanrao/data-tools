"""Split reconciled content into chunks that remember where they came from.

Only reconciled content reaches this module. A quarantined file is never
chunked -- indexing partial content is how a gap becomes invisible.
"""

from __future__ import annotations

from dataclasses import dataclass

from data_tools_core.provenance import Provenance, UnitKind

from ingest_ledger.models import FileReconciliation

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP = 120


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    provenance: Provenance
    ordinal: int

    @property
    def locator(self) -> str:
        return f"{self.provenance.locator}@{self.ordinal}"


def split(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Paragraph-greedy split with a character overlap between neighbours."""
    paragraphs = [block.strip() for block in text.split("\n\n") if block.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = (current[-overlap:] + "\n\n" + paragraph) if overlap else paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph

    if current:
        chunks.append(current)

    # A single paragraph longer than the budget still has to be broken up.
    out: list[str] = []
    for block in chunks:
        while len(block) > max_chars:
            out.append(block[:max_chars])
            block = block[max_chars - overlap :]
        out.append(block)
    return out


def chunks_for(row: FileReconciliation, **kwargs) -> list[Chunk]:
    """Chunk one reconciled file. Returns nothing for a quarantined file."""
    if row.quarantined or not row.extracted or not row.extracted.text.strip():
        return []

    kind = row.declared.unit_kind if row.declared else UnitKind.DOCUMENT
    return [
        Chunk(
            text=text,
            provenance=Provenance(
                source=row.path,
                sha256=row.sha256,
                unit_kind=kind,
                container_path=row.container_path,
            ),
            ordinal=ordinal,
        )
        for ordinal, text in enumerate(split(row.extracted.text, **kwargs))
    ]
