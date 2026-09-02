"""DOCX probe.

python-docx's ``document.paragraphs`` walks the main body only. Content parked
in text boxes, headers, footers, footnotes and endnotes is invisible to it --
and to most extractors built on it. That content is frequently the part that
matters: the caveat in the footnote, the figure in the text box.

We declare body blocks *and* those side channels by reading the package parts
directly, so an extractor that only walks the body reconciles as PARTIAL.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from data_tools_core.provenance import UnitKind

from ingest_ledger.models import Declared, Extracted

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

#: Package parts that hold text an extractor is likely to skip.
SIDE_CHANNELS = ("word/footnotes.xml", "word/endnotes.xml")
SIDE_PREFIXES = ("word/header", "word/footer")


def _paragraph_texts(xml: bytes) -> list[str]:
    """Every ``w:p`` in a part, including ones nested inside text boxes."""
    root = ET.fromstring(xml)
    out = []
    for para in root.iter(f"{W}p"):
        text = "".join(node.text or "" for node in para.iter(f"{W}t")).strip()
        if text:
            out.append(text)
    return out


class DocxProbe:
    suffixes = (".docx",)
    name = "docx"

    def _parts(self, archive: zipfile.ZipFile) -> list[str]:
        names = [n for n in archive.namelist() if n in SIDE_CHANNELS]
        names += [
            n for n in archive.namelist() if n.startswith(SIDE_PREFIXES) and n.endswith(".xml")
        ]
        return ["word/document.xml", *sorted(names)]

    def declare(self, path: Path) -> Declared:
        with zipfile.ZipFile(path) as archive:
            parts = self._parts(archive)
            total = 0
            ids: list[str] = []
            for part in parts:
                try:
                    blocks = _paragraph_texts(archive.read(part))
                except (KeyError, ET.ParseError):
                    continue
                total += len(blocks)
                if blocks:
                    ids.append(f"{part}:{len(blocks)}")
        notes = ("side channels present",) if len(ids) > 1 else ()
        return Declared(units=total, unit_kind=UnitKind.BLOCK, unit_ids=tuple(ids), notes=notes)

    def extract(self, path: Path) -> Extracted:
        chunks: list[str] = []
        recovered = 0
        per_part: dict[str, int] = {}
        with zipfile.ZipFile(path) as archive:
            for part in self._parts(archive):
                try:
                    blocks = _paragraph_texts(archive.read(part))
                except (KeyError, ET.ParseError):
                    continue
                per_part[part] = len(blocks)
                recovered += len(blocks)
                if blocks:
                    chunks.append("\n".join(blocks))

        return Extracted(
            units=recovered,
            text="\n\n".join(chunks),
            evidence={"auditor": "docx-package-walk", "blocks_per_part": per_part},
        )
