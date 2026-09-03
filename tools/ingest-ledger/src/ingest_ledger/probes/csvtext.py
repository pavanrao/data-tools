"""CSV and plain-text probes.

Cheap formats, but they carry a real silent failure: a BOM or a mixed encoding
turns the first field name into ``\\ufeffid`` or drops rows on decode, and the
pipeline reports success. We count lines by bytes -- decoding-independent --
then compare against what actually decoded.
"""

from __future__ import annotations

from pathlib import Path

from data_tools_core.provenance import UnitKind

from ingest_ledger.models import Declared, Extracted


def _count_lines(path: Path) -> int:
    """Non-blank lines, counted on raw bytes so encoding cannot change the answer.

    Blank lines are excluded deliberately: the extract pass drops them, and a
    declared count that measures something the extract pass never returns
    manufactures a shortfall on every well-formed file. Both sides must count
    the same thing or the reconciliation is noise.
    """
    count = 0
    with path.open("rb") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


class _LineProbe:
    unit_kind = UnitKind.LINE

    def declare(self, path: Path) -> Declared:
        notes = []
        with path.open("rb") as handle:
            if handle.read(3) == b"\xef\xbb\xbf":
                notes.append("utf-8 BOM present")
        return Declared(_count_lines(path), self.unit_kind, notes=tuple(notes))

    def extract(self, path: Path) -> Extracted:
        raw = path.read_bytes()
        errors = 0
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            # Never fail closed on encoding -- decode lossily and report how
            # much was lost, so the loss shows up in the ledger.
            text = raw.decode("utf-8", errors="replace")
            errors = text.count("�")
        text = text.lstrip("﻿")
        lines = [line for line in text.splitlines() if line.strip()]
        return Extracted(
            units=len(lines),
            text=text,
            evidence={"auditor": self.name, "replacement_chars": errors},
        )


class CsvProbe(_LineProbe):
    suffixes = (".csv", ".tsv")
    name = "csv"
    unit_kind = UnitKind.ROW


class TextProbe(_LineProbe):
    suffixes = (".txt", ".md", ".log")
    name = "text"
