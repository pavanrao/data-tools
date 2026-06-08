"""Load documents from a folder and split them into overlapping chunks.

Pure, deterministic, no model calls — easy to test and free to run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


@dataclass(frozen=True)
class Chunk:
    """A unit of retrievable text and where it came from."""

    text: str
    source: str
    ordinal: int


def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split ``text`` into <=``chunk_size`` slices that overlap by ``overlap`` chars."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += step
    return chunks


def load_file(path: str | Path) -> str:
    """Return the text content of a supported file (md/txt/pdf)."""
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")


def iter_files(folder: str | Path) -> Iterator[Path]:
    """Yield supported files under ``folder`` in a stable order."""
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            yield p


def ingest_folder(
    folder: str | Path, *, chunk_size: int = 800, overlap: int = 100
) -> list[Chunk]:
    """Load every supported file under ``folder`` and return its chunks."""
    chunks: list[Chunk] = []
    for path in iter_files(folder):
        text = load_file(path)
        for ordinal, piece in enumerate(
            chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        ):
            chunks.append(Chunk(text=piece, source=str(path), ordinal=ordinal))
    return chunks
