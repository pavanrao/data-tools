"""The baseline comparison -- the claim the README leads with."""

from __future__ import annotations

import pytest
from ingest_ledger import naive
from ingest_ledger.compare import inputs_of, render
from ingest_ledger.manifest import walk
from ingest_ledger.models import Status
from ingest_ledger.probes import for_path
from ingest_ledger.reconcile import reconcile

pytestmark = pytest.mark.hostile


def reconcile_dir(root):
    rows = []
    for entry in walk(root, workdir=root / "_unpacked"):
        probe = for_path(entry.path) if entry.declared is not None else None
        rows.append(reconcile(entry, probe.extract(entry.path) if probe else None))
    return rows


def test_naive_extractor_reports_success_on_a_scanned_pdf(fixture_path):
    """Zero characters, no exception -- the pipeline ships it."""
    result = naive.extract(fixture_path("scanned.pdf"))
    assert result.looks_fine
    assert result.chars == 0


def test_naive_extractor_reads_only_the_active_sheet(fixture_path):
    result = naive.extract(fixture_path("multi_sheet.xlsx"))
    ledger_text = _ledger_text(fixture_path("multi_sheet.xlsx"))
    assert result.looks_fine
    assert result.chars < len(ledger_text) / 2


def test_naive_extractor_drops_footnotes(fixture_path):
    path = fixture_path("textbox_footnote.docx")
    assert "Footnote" not in naive.extract(path).note
    assert "Footnote" not in _naive_text(path)
    assert "Footnote" in _ledger_text(path)


def test_comparison_flags_every_silently_damaged_input(hostile):
    root = next(iter(hostile.values())).parent
    rows = reconcile_dir(root)
    table = render(rows, inputs_of(root))

    assert "would enter the index silently damaged" in table
    flagged = table.count("  <--")
    assert flagged >= 3, table


def test_comparison_does_not_flag_a_file_both_read_fully(hostile):
    rows = reconcile_dir(next(iter(hostile.values())).parent)
    csv_row = next(row for row in rows if row.path.name == "bom_mixed.csv")
    assert csv_row.status is Status.COMPLETE


def _naive_text(path):
    return naive._dispatch(path)


def _ledger_text(path):
    probe = for_path(path)
    return probe.extract(path).text
