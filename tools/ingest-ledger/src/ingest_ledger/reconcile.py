"""Join the two counts and decide what actually happened."""

from __future__ import annotations

from ingest_ledger.extract import DEFAULT_MEMORY_MB, DEFAULT_TIMEOUT_S
from ingest_ledger.extract import run as run_extraction
from ingest_ledger.manifest import ManifestEntry
from ingest_ledger.models import Extracted, FileReconciliation, Status

#: Below this, a file is quarantined rather than indexed.
DEFAULT_THRESHOLD = 0.99


def reconcile(
    entry: ManifestEntry,
    extracted: Extracted | None = None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    memory_mb: int = DEFAULT_MEMORY_MB,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> FileReconciliation:
    if entry.declared is None:
        return FileReconciliation(
            entry.path,
            entry.sha256,
            None,
            None,
            Status.UNSUPPORTED,
            0.0,
            entry.container_path,
            entry.note,
        )

    if extracted is None:
        extracted = run_extraction(entry, memory_mb=memory_mb, timeout_s=timeout_s)

    declared_units = entry.declared.units
    if declared_units == 0:
        # Nothing declared and nothing extracted is EMPTY -- reportable, but not
        # a failure. Nothing declared and something extracted means declare()
        # is wrong, which is worth knowing loudly.
        status = Status.EMPTY if extracted.units == 0 else Status.PARTIAL
        return FileReconciliation(
            entry.path,
            entry.sha256,
            entry.declared,
            extracted,
            status,
            0.0,
            entry.container_path,
            entry.note,
        )

    coverage = min(extracted.units / declared_units, 1.0)

    if extracted.error and extracted.units == 0:
        status = Status.FAILED
    elif coverage >= threshold and not extracted.missing:
        status = Status.COMPLETE
    else:
        status = Status.PARTIAL

    return FileReconciliation(
        entry.path,
        entry.sha256,
        entry.declared,
        extracted,
        status,
        coverage,
        entry.container_path,
        entry.note,
    )


def coverage_by_kind(rows: list[FileReconciliation]) -> dict[str, float]:
    """Units recovered over units declared, computed *within* each unit kind.

    A single corpus-wide ratio is a trap: 240,000 XML nodes drown out three
    lost PDF pages and the headline reads 100% while the report below it lists
    quarantined files. Pages, sheets and rows are not interchangeable, so they
    are never summed into one number.
    """
    totals: dict[str, list[int]] = {}
    for row in rows:
        if not (row.declared and row.extracted):
            continue
        bucket = totals.setdefault(str(row.declared.unit_kind), [0, 0])
        bucket[0] += row.extracted.units
        bucket[1] += row.declared.units
    return {
        kind: (recovered / declared if declared else 0.0)
        for kind, (recovered, declared) in sorted(totals.items())
    }


def worst_coverage(rows: list[FileReconciliation]) -> float:
    """The headline number: the unit kind that fared worst. Never an average."""
    by_kind = coverage_by_kind(rows)
    return min(by_kind.values(), default=0.0)
