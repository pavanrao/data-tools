"""A baseline extractor, written the way these are usually written.

This is not a straw man. Every shortcut here is one you will find in shipped
RAG ingestion code: take the active sheet, walk ``document.paragraphs``, trust
the file extension, read the archive's top level, swallow the exception and
carry on with whatever came back.

The point of ``ingest-ledger compare`` is that this baseline reports success on
all of it. Run it beside the reconciler to see the difference.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@dataclass(frozen=True, slots=True)
class NaiveResult:
    path: Path
    chars: int
    ok: bool
    note: str = ""

    @property
    def looks_fine(self) -> bool:
        """What the surrounding pipeline would conclude: no exception, so ship it."""
        return self.ok


def extract(path: Path) -> NaiveResult:
    try:
        text = _dispatch(path)
    except Exception as exc:  # noqa: BLE001 - swallowing is the behaviour being modelled
        return NaiveResult(path, 0, False, f"{type(exc).__name__}")
    return NaiveResult(path, len(text.strip()), True)


def _dispatch(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf(path)
    if suffix in {".xlsx", ".xlsm"}:
        return _xlsx(path)
    if suffix == ".docx":
        return _docx(path)
    if suffix == ".xml":
        return _xml(path)
    if suffix == ".zip":
        return _zip(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def _pdf(path: Path) -> str:
    import pymupdf

    with pymupdf.open(path) as doc:
        # No per-page yield check: three empty pages concatenate to "".
        return "\n".join(page.get_text() for page in doc)


def _xlsx(path: Path) -> str:
    import openpyxl

    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = book.active  # sheets 2..N never happen
        return "\n".join(
            "\t".join("" if cell is None else str(cell) for cell in row)
            for row in sheet.iter_rows(values_only=True)
        )
    finally:
        book.close()


def _docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    # Body only: footnotes, headers and text boxes in other parts are invisible.
    return "\n".join(
        "".join(node.text or "" for node in para.iter(f"{W}t")) for para in root.iter(f"{W}p")
    )


def _xml(path: Path) -> str:
    # Eager parse: the whole tree in memory at once.
    root = ET.parse(path).getroot()
    return " ".join(text.strip() for text in root.itertext() if text.strip())


def _zip(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        # Top level only, and only things that look like text.
        return "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith((".txt", ".md", ".csv"))
        )
