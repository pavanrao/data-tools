"""The claim this repo makes, as executable assertions.

Each fixture is a document a naive pipeline reads *successfully* and gets wrong.
For every one of them the ledger must produce a non-COMPLETE status. A test
here failing means the tool silently accepted a file it should have flagged --
which is the exact failure the tool exists to prevent.
"""

from __future__ import annotations

import pytest
from ingest_ledger.manifest import walk
from ingest_ledger.models import Status
from ingest_ledger.probes import for_path
from ingest_ledger.reconcile import reconcile

pytestmark = pytest.mark.hostile


def status_of(path):
    """Reconcile a single file in-process (subprocess isolation is tested separately)."""
    (entry,) = list(walk(path))
    probe = for_path(entry.path)
    extracted = probe.extract(entry.path) if probe and entry.declared is not None else None
    return reconcile(entry, extracted)


def test_xlsx_declares_every_sheet_not_just_the_active_one(fixture_path):
    (entry,) = list(walk(fixture_path("multi_sheet.xlsx")))
    assert entry.declared.units == 4
    assert "Appendix C" in entry.declared.unit_ids


def test_xlsx_empty_sheet_is_reported_not_ignored(fixture_path):
    row = status_of(fixture_path("multi_sheet.xlsx"))
    assert row.status is Status.PARTIAL
    assert "Notes" in row.extracted.missing


def test_docx_counts_footnotes_that_body_walkers_skip(fixture_path):
    (entry,) = list(walk(fixture_path("textbox_footnote.docx")))
    # 8 body paragraphs + 3 footnotes; a body-only walker would declare 8.
    assert entry.declared.units == 11
    assert any("footnotes" in str(uid) for uid in entry.declared.unit_ids)


def test_csv_bom_and_bad_encoding_are_recorded(fixture_path):
    row = status_of(fixture_path("bom_mixed.csv"))
    assert "utf-8 BOM present" in row.declared.notes
    assert row.extracted.evidence["replacement_chars"] > 0


def test_nested_zip_is_descended_into(fixture_path):
    entries = list(walk(fixture_path("nested.zip")))
    names = {e.path.name for e in entries}
    assert "terms.txt" in names, "content inside the inner archive was never seen"
    terms = next(e for e in entries if e.path.name == "terms.txt")
    assert terms.container_path[-1] == "inner.zip"


def test_file_lying_about_its_extension_is_not_silently_clean(fixture_path):
    row = status_of(fixture_path("liar.pdf"))
    assert row.status is not Status.COMPLETE


def test_scanned_pdf_pages_count_as_missing_not_empty(fixture_path):
    row = status_of(fixture_path("scanned.pdf"))
    assert row.status is Status.PARTIAL
    assert row.coverage == 0.0
    assert len(row.extracted.missing) == 3


def test_whitebox_pdf_yields_text_that_is_invisible_in_print(fixture_path):
    """Extraction reads what the page hides -- the ledger should show full
    coverage here, and that is precisely the point: a 'redacted' document
    reconciles as COMPLETE while leaking."""
    row = status_of(fixture_path("whitebox.pdf"))
    assert "SECRET" in row.extracted.text


@pytest.mark.xfail(reason="TODO: subprocess memory cap not yet wired into the walk")
def test_oversized_xml_under_a_small_cap_is_failed_not_partial(fixture_path):
    from ingest_ledger.extract import run
    from ingest_ledger.manifest import walk as walk_one

    (entry,) = list(walk_one(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=64, timeout_s=30)
    row = reconcile(entry, extracted)
    assert row.status is Status.FAILED
    assert "memory" in (row.extracted.error or "")


def test_extension_mismatch_is_named_in_the_ledger(fixture_path):
    (entry,) = list(walk(fixture_path("liar.pdf")))
    assert entry.declared is None
    assert "content is html" in entry.note
