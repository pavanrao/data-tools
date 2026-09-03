"""Reconcile what a document pipeline was given against what it actually read."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from data_tools_core import ledger

from ingest_ledger import compare as compare_mod
from ingest_ledger import index as index_mod
from ingest_ledger import report as report_mod
from ingest_ledger import store
from ingest_ledger.extract import DEFAULT_MEMORY_MB, DEFAULT_TIMEOUT_S
from ingest_ledger.manifest import walk
from ingest_ledger.models import FileReconciliation, Status
from ingest_ledger.probes import for_path
from ingest_ledger.query import DEFAULT_TOP_K, Verdict, ask
from ingest_ledger.reconcile import DEFAULT_THRESHOLD, reconcile

DEFAULT_LEDGER = Path("ingest.ledger.db")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingest-ledger", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def with_ingest_options(p):
        p.add_argument("path", type=Path, help="file, directory, or archive")
        p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
        p.add_argument("--memory-mb", type=int, default=DEFAULT_MEMORY_MB)
        p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
        p.add_argument(
            "--in-process",
            action="store_true",
            help="skip subprocess isolation (faster; loses OOM detection)",
        )
        return p

    report = with_ingest_options(
        sub.add_parser("report", help="manifest, extract, reconcile, print the table")
    )
    report.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    report.add_argument(
        "--strict", action="store_true", help="exit non-zero if any file is quarantined"
    )

    manifest = sub.add_parser("manifest", help="declare units only; never extracts")
    manifest.add_argument("path", type=Path)

    with_ingest_options(
        sub.add_parser("compare", help="naive extractor vs. reconciler, side by side")
    )

    build = with_ingest_options(
        sub.add_parser("index", help="index reconciled content and the gaps")
    )
    build.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)

    query = sub.add_parser("ask", help="query the index; refuses when a gap is relevant")
    query.add_argument("question")
    query.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    query.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    query.add_argument("--run-id", default=None, help="defaults to the latest index run")

    return parser


def _reconcile_all(args, workdir: Path | None = None) -> list[FileReconciliation]:
    rows = []
    for entry in walk(args.path, workdir=workdir):
        extracted = None
        if args.in_process and entry.declared is not None:
            probe = for_path(entry.path)
            extracted = probe.extract(entry.path) if probe else None
        rows.append(
            reconcile(
                entry,
                extracted,
                threshold=args.threshold,
                memory_mb=args.memory_mb,
                timeout_s=args.timeout,
            )
        )
    return rows


def _latest_run(conn, table: str) -> str | None:
    row = conn.execute(
        f"SELECT run_id FROM runs WHERE run_id IN (SELECT run_id FROM {table})"  # noqa: S608
        " ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return row["run_id"] if row else None


def main(argv: list[str] | None = None) -> int:
    """Reconcile what a document pipeline was given against what it read."""
    args = build_parser().parse_args(argv)

    if args.command == "manifest":
        for entry in walk(args.path):
            declared = entry.declared
            summary = f"{declared.units} {declared.unit_kind}s" if declared else (entry.note or "?")
            print(f"{entry.path.name:<44} {summary}")
        return 0

    if args.command == "ask":
        return _ask(args)

    # Archive members are unpacked into this directory, which must outlive the
    # walk so later stages can still re-open them.
    with tempfile.TemporaryDirectory(prefix="ingest-ledger-") as tmp:
        rows = _reconcile_all(args, workdir=Path(tmp))

        if args.command == "compare":
            print(compare_mod.render(rows, compare_mod.inputs_of(args.path)))
            return 0

        return _persist(args, rows)


def _persist(args, rows: list[FileReconciliation]) -> int:
    with ledger.connect(args.ledger) as conn:
        store.init(conn)
        run_id = ledger.start_run(conn, "ingest-ledger", sys.argv[1:])
        for row in rows:
            store.record(conn, run_id, row)

        if args.command == "index":
            chunks, gaps = index_mod.build(conn, run_id, rows)
        ledger.finish_run(conn, run_id)

    print(report_mod.render(rows))

    if args.command == "index":
        print(f"\nindexed {chunks} chunks; {gaps} gap descriptor(s)")
        print(f"run: {run_id}")
        return 0

    if args.strict and any(row.quarantined for row in rows):
        return 1
    return 0 if all(row.status is not Status.FAILED for row in rows) else 1


def _ask(args) -> int:
    with ledger.connect(args.ledger) as conn:
        index_mod.init(conn)
        run_id = args.run_id or _latest_run(conn, "chunks")
        if run_id is None:
            print("nothing indexed yet; run `ingest-ledger index <path>` first", file=sys.stderr)
            return 2

        answer = ask(conn, run_id, args.question, top_k=args.top_k)

    print(f"Q: {answer.question}\n")
    print(f"[{answer.verdict.upper()}] {answer.statement}\n")

    if answer.grounded:
        for passage in answer.passages:
            preview = " ".join(passage.text.split())[:160]
            print(f"  {passage.score:.3f}  {passage.locator}")
            print(f"         {preview}...")
    for gap in answer.gaps:
        print(f"  GAP {gap.score:.3f}  {gap.locator} - {gap.reason}")

    # A refusal is a meaningful outcome, not an error; 3 distinguishes it from
    # a crash (1) and bad usage (2) so a caller can branch on it.
    return 3 if answer.verdict is Verdict.ABSTAINED else 0
