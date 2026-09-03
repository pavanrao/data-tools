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


def test_pdf_yield_and_fidelity_are_different_questions(fixture_path):
    """pdfmux audits fidelity; this tool measures yield. Both are needed.

    On a scanned page pdfmux correctly returns PASS -- no text layer existed,
    so the extractor dropped nothing. Against the declared page count that same
    file recovered nothing at all, which is the gap an index would inherit.
    A page is missing if either signal says so.
    """
    pdfmux = pytest.importorskip("pdfmux")
    assert pdfmux  # the evidence line below depends on it being installed

    row = status_of(fixture_path("scanned.pdf"))

    assert row.extracted.evidence["pdfmux_verdict"] == "PASS"
    assert row.extracted.evidence["pdfmux_coverage"] == 1.0
    assert row.extracted.evidence["pdfmux_silent_drops"] == ()
    # ...and yet:
    assert row.status is Status.PARTIAL
    assert row.extracted.evidence["zero_yield_pages"] == (1, 2, 3)


def test_pdf_records_when_the_fidelity_audit_is_unavailable(fixture_path, monkeypatch):
    """A missing auditor must be stated in the ledger, never silently skipped."""
    import builtins

    real_import = builtins.__import__

    def no_pdfmux(name, *args, **kwargs):
        if name == "pdfmux":
            raise ImportError("simulated")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_pdfmux)
    row = status_of(fixture_path("whitebox.pdf"))
    assert row.extracted.evidence["fidelity_audit"] == "unavailable"
