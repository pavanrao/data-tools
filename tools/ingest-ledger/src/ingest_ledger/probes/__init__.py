"""Probe registry.

Probes are resolved by suffix at runtime. A probe whose optional dependency is
missing is skipped rather than crashing the run -- but the file it would have
claimed is recorded as ``unsupported``, never as clean.
"""

from __future__ import annotations

from pathlib import Path

from ingest_ledger.probes.base import Probe, ProbeUnavailable
from ingest_ledger.probes.csvtext import CsvProbe, TextProbe
from ingest_ledger.probes.docx import DocxProbe
from ingest_ledger.probes.pdf import PdfProbe
from ingest_ledger.probes.xlsx import XlsxProbe
from ingest_ledger.probes.xml import XmlProbe

#: Order matters only for readability; suffixes are disjoint.
ALL_PROBES: tuple[Probe, ...] = (
    PdfProbe(),
    XlsxProbe(),
    DocxProbe(),
    XmlProbe(),
    CsvProbe(),
    TextProbe(),
)


def for_path(path: Path) -> Probe | None:
    suffix = path.suffix.lower()
    for probe in ALL_PROBES:
        if suffix in probe.suffixes:
            return probe
    return None


__all__ = ["ALL_PROBES", "Probe", "ProbeUnavailable", "for_path"]
