"""XML probe.

This is the file from the podcast: a multi-megabyte XML inside an RFP archive
that the extractor choked on, recovered a fragment of, and never mentioned.

Both passes stream. ``declare()`` counts top-level children with iterparse and
clears as it goes, so counting a 20 MB document costs almost nothing -- which
means the declared count survives even when the extract pass is the thing that
gets killed for using too much memory.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from data_tools_core.provenance import UnitKind

from ingest_ledger.models import Declared, Extracted


class XmlProbe:
    suffixes = (".xml",)
    name = "xml"

    def declare(self, path: Path) -> Declared:
        count = 0
        depth = 0
        try:
            for event, _elem in ET.iterparse(path, events=("start", "end")):
                if event == "start":
                    depth += 1
                else:
                    depth -= 1
                    if depth == 1:  # direct child of the root closed
                        count += 1
                        _elem.clear()
        except ET.ParseError as exc:
            # Malformed XML declares what it managed to parse, plus the reason.
            return Declared(count, UnitKind.NODE, notes=(f"parse error: {exc}",))
        return Declared(units=count, unit_kind=UnitKind.NODE)

    def extract(self, path: Path) -> Extracted:
        texts: list[str] = []
        count = 0
        depth = 0
        error: str | None = None
        try:
            for event, elem in ET.iterparse(path, events=("start", "end")):
                if event == "start":
                    depth += 1
                    continue
                depth -= 1
                if depth == 1:
                    count += 1
                    text = " ".join(t.strip() for t in elem.itertext() if t.strip())
                    if text:
                        texts.append(text)
                    elem.clear()
        except ET.ParseError as exc:
            error = f"parse error: {exc}"

        return Extracted(
            units=count,
            text="\n".join(texts),
            evidence={"auditor": "elementtree-iterparse"},
            error=error,
        )
