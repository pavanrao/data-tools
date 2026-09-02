"""Render the reconciliation table.

This output is the product. If it is not immediately obvious which files were
not fully read, the tool has failed at its one job.
"""

from __future__ import annotations

from ingest_ledger.models import FileReconciliation, Status
from ingest_ledger.reconcile import coverage_by_kind

MARK = {
    Status.COMPLETE: " ",
    Status.PARTIAL: "!",
    Status.FAILED: "X",
    Status.UNSUPPORTED: "?",
    Status.EMPTY: "-",
}


def render(rows: list[FileReconciliation]) -> str:
    if not rows:
        return "no files found"

    names = [_name(r) for r in rows]
    width = min(max(len(n) for n in names), 44)
    declared_col = [_units(r) for r in rows]
    dwidth = max(len("declared"), *(len(d) for d in declared_col))
    lines = [
        f"{'file':<{width}}  {'declared':>{dwidth}}  {'read':>7}  {'cov':>5}  status",
        "-" * (width + dwidth + 27),
    ]

    for row, name, declared in zip(rows, names, declared_col, strict=True):
        read = row.extracted.units if row.extracted else "-"
        lines.append(
            f"{_clip(name, width):<{width}}  {declared:>{dwidth}}  {read:>7}  "
            f"{row.coverage:>4.0%}  {row.status.upper()} {MARK[row.status]}"
        )
        if detail := _detail(row):
            lines.append(f"{'':<{width}}  -> {detail}")

    quarantined = [r for r in rows if r.quarantined]
    complete = len(rows) - len(quarantined)
    lines += ["", f"files: {complete} of {len(rows)} complete, {len(quarantined)} quarantined"]

    # Per unit kind, never averaged into one number -- see coverage_by_kind.
    for kind, coverage in coverage_by_kind(rows).items():
        flag = "" if coverage == 1.0 else "   <-- gap"
        lines.append(f"  {kind + 's':<10} {coverage:>6.1%}{flag}")
    return "\n".join(lines)


def _units(row: FileReconciliation) -> str:
    if not row.declared:
        return "-"
    kind = str(row.declared.unit_kind)
    plural = kind if row.declared.units == 1 else f"{kind}s"
    return f"{row.declared.units} {plural}"


def _name(row: FileReconciliation) -> str:
    return "!".join((*row.container_path, row.path.name))


def _clip(text: str, width: int) -> str:
    return text if len(text) <= width else "..." + text[-(width - 3) :]


def _detail(row: FileReconciliation) -> str:
    if row.status is Status.COMPLETE:
        return ""
    if row.extracted and row.extracted.error:
        return row.extracted.error
    if row.extracted and row.extracted.missing:
        missing = list(row.extracted.missing)
        shown = ", ".join(str(m) for m in missing[:6])
        more = f" (+{len(missing) - 6} more)" if len(missing) > 6 else ""
        kind = row.declared.unit_kind if row.declared else "unit"
        return f"missing {kind}s: {shown}{more}"
    if row.status is Status.UNSUPPORTED:
        return f"{row.note or 'no probe claims this format'} - content not indexed"
    return ""
