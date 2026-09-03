"""Render the baseline against the reconciler, side by side.

This is the demo that makes the case: the same corpus, read two ways, with the
disagreements called out. A row where the baseline reports success and the
ledger reports a gap is a file that would have entered your index silently.

The two are compared on the *inputs a pipeline is actually handed* -- top-level
files and archives -- not on unpacked members. A naive extractor never sees the
inside of an archive, and giving it one would be scoring it on a question it
was never asked.
"""

from __future__ import annotations

from pathlib import Path

from ingest_ledger import naive
from ingest_ledger.models import FileReconciliation, Status


def inputs_of(path: Path) -> list[Path]:
    """The files a pipeline is handed: top level only, archives unopened."""
    if path.is_file():
        return [path]
    return sorted(child for child in path.iterdir() if child.is_file())


def render(rows: list[FileReconciliation], inputs: list[Path]) -> str:
    #: Ledger rows grouped by the top-level input they came from.
    by_input: dict[str, list[FileReconciliation]] = {}
    for row in rows:
        key = row.container_path[0] if row.container_path else row.path.name
        by_input.setdefault(key, []).append(row)

    width = min(max((len(p.name) for p in inputs), default=4), 34)
    lines = [
        f"{'input':<{width}}  {'naive extractor':<24}  {'ingest-ledger':<26}",
        "-" * (width + 56),
    ]

    missed = 0
    for path in inputs:
        result = naive.extract(path)
        baseline = f"ok, {result.chars} chars" if result.looks_fine else f"error: {result.note}"

        group = by_input.get(path.name, [])
        verdict = _verdict(group)
        silent = result.looks_fine and _understated(result, group)
        missed += silent
        lines.append(
            f"{_clip(path.name, width):<{width}}  {baseline:<24}  {verdict:<26}"
            f"{'  <--' if silent else ''}"
        )

    lines += [
        "",
        f"{missed} of {len(inputs)} inputs would enter the index silently damaged"
        " under the naive extractor.",
    ]
    return "\n".join(lines)


#: Below this fraction of the reconciled character count, the baseline read
#: materially less than the file contained -- the dropped footnote, the inner
#: archive it never opened -- while reporting success.
UNDERCOUNT_RATIO = 0.9


def _understated(result: naive.NaiveResult, group: list[FileReconciliation]) -> bool:
    """Did the baseline miss something the ledger caught?"""
    if any(row.status is not Status.COMPLETE for row in group):
        return True
    reconciled = sum(len(row.extracted.text.strip()) for row in group if row.extracted)
    return bool(reconciled) and result.chars < reconciled * UNDERCOUNT_RATIO


def _verdict(group: list[FileReconciliation]) -> str:
    if not group:
        return "not reached"
    worst = min(group, key=lambda row: (row.status is Status.COMPLETE, row.coverage))
    if len(group) == 1:
        return f"{worst.status.upper()} ({worst.coverage:.0%})"
    bad = sum(1 for row in group if row.status is not Status.COMPLETE)
    chars = sum(len(row.extracted.text.strip()) for row in group if row.extracted)
    if bad:
        return f"{len(group)} members, {bad} flagged"
    return f"{len(group)} members, {chars} chars"


def _clip(text: str, width: int) -> str:
    return text if len(text) <= width else "..." + text[-(width - 3) :]
