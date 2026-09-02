"""The reconciliation contract: two counts in, one honest status out."""

from __future__ import annotations

from pathlib import Path

import pytest
from data_tools_core.provenance import UnitKind
from ingest_ledger.manifest import ManifestEntry
from ingest_ledger.models import Declared, Extracted, Status
from ingest_ledger.reconcile import coverage_by_kind, reconcile, worst_coverage


def entry(declared: Declared | None) -> ManifestEntry:
    return ManifestEntry(Path("f.pdf"), "deadbeef", (), declared, "pdf")


def test_full_recovery_is_complete():
    row = reconcile(entry(Declared(10, UnitKind.PAGE)), Extracted(10))
    assert row.status is Status.COMPLETE
    assert row.coverage == 1.0
    assert not row.quarantined


def test_shortfall_is_partial_and_quarantined():
    row = reconcile(entry(Declared(10, UnitKind.PAGE)), Extracted(7, missing=(8, 9, 10)))
    assert row.status is Status.PARTIAL
    assert row.coverage == pytest.approx(0.7)
    assert row.quarantined


def test_full_count_with_named_gaps_still_partial():
    """Counts alone can lie; a probe naming a missing unit overrides them."""
    row = reconcile(entry(Declared(3, UnitKind.SHEET)), Extracted(3, missing=("Notes",)))
    assert row.status is Status.PARTIAL


def test_killed_extraction_is_failed_not_empty():
    row = reconcile(
        entry(Declared(5, UnitKind.NODE)),
        Extracted(0, error="killed (SIGKILL) - likely out of memory"),
    )
    assert row.status is Status.FAILED
    assert row.quarantined


def test_unsupported_format_is_never_silently_clean():
    row = reconcile(entry(None))
    assert row.status is Status.UNSUPPORTED
    assert row.quarantined


def test_coverage_is_never_summed_across_unit_kinds():
    """A page is not a row. Mixing them lets a large clean file hide a loss."""
    rows = [
        reconcile(entry(Declared(3, UnitKind.PAGE)), Extracted(0, error="oom")),
        *[reconcile(entry(Declared(40_000, UnitKind.ROW)), Extracted(40_000)) for _ in range(2)],
    ]
    by_kind = coverage_by_kind(rows)
    assert by_kind == {"page": pytest.approx(0.0), "row": pytest.approx(1.0)}
    # The headline reports the worst kind, so the lost pages cannot be diluted.
    assert worst_coverage(rows) == pytest.approx(0.0)
