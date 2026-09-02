"""XLSX probe.

The classic silent failure: an extractor opens the workbook, reads the active
sheet, and returns text. Sheets 2..N never happened, and nothing says so.

We declare every sheet -- and every used row within it -- so a workbook that
extracts to one sheet's worth of content reconciles as PARTIAL with the missing
sheets named.
"""

from __future__ import annotations

from pathlib import Path

from data_tools_core.provenance import UnitKind

from ingest_ledger.models import Declared, Extracted
from ingest_ledger.probes.base import ProbeUnavailable


def _openpyxl():
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover
        raise ProbeUnavailable("install data-tools-ingest-ledger[xlsx]") from exc
    return openpyxl


class XlsxProbe:
    suffixes = (".xlsx", ".xlsm")
    name = "xlsx"

    def declare(self, path: Path) -> Declared:
        openpyxl = _openpyxl()
        # read_only + values_only keeps a large workbook from being fully
        # materialised just to be counted.
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            names = tuple(book.sheetnames)
            notes = []
            hidden = tuple(n for n in names if book[n].sheet_state != "visible")
            if hidden:
                # Hidden sheets still hold data an extractor may skip.
                notes.append(f"hidden sheets: {', '.join(hidden)}")
            return Declared(
                units=len(names),
                unit_kind=UnitKind.SHEET,
                unit_ids=names,
                notes=tuple(notes),
            )
        finally:
            book.close()

    def extract(self, path: Path) -> Extracted:
        openpyxl = _openpyxl()
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            chunks: list[str] = []
            recovered: list[str] = []
            missing: list[str] = []
            row_counts: dict[str, int] = {}

            for name in book.sheetnames:
                sheet = book[name]
                rows = [
                    "\t".join("" if cell is None else str(cell) for cell in row)
                    for row in sheet.iter_rows(values_only=True)
                ]
                rows = [line for line in rows if line.strip()]
                row_counts[name] = len(rows)
                if rows:
                    recovered.append(name)
                    chunks.append(f"# sheet: {name}\n" + "\n".join(rows))
                else:
                    # An empty sheet is legitimate, but it is also what a
                    # truncated read looks like. Report it, decide upstream.
                    missing.append(name)

            return Extracted(
                units=len(recovered),
                text="\n\n".join(chunks),
                missing=tuple(missing),
                evidence={"auditor": "openpyxl", "rows_per_sheet": row_counts},
            )
        finally:
            book.close()
