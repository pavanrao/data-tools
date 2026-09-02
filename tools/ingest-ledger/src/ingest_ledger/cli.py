"""Reconcile what a document pipeline was given against what it actually read."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_tools_core import ledger

from ingest_ledger import report as report_mod
from ingest_ledger import store
from ingest_ledger.extract import DEFAULT_MEMORY_MB, DEFAULT_TIMEOUT_S
from ingest_ledger.manifest import walk
from ingest_ledger.models import FileReconciliation, Status
from ingest_ledger.probes import for_path
from ingest_ledger.reconcile import DEFAULT_THRESHOLD, reconcile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingest-ledger", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="manifest, extract, reconcile, print the table")
    report.add_argument("path", type=Path, help="file, directory, or archive")
    report.add_argument("--ledger", type=Path, default=Path("ingest.ledger.db"))
    report.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    report.add_argument("--memory-mb", type=int, default=DEFAULT_MEMORY_MB)
    report.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    report.add_argument(
        "--in-process",
        action="store_true",
        help="skip subprocess isolation (faster; loses OOM detection)",
    )
    report.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any file is quarantined - use this in CI",
    )

    manifest = sub.add_parser("manifest", help="declare units only; never extracts")
    manifest.add_argument("path", type=Path)

    return parser


def _reconcile_all(args) -> list[FileReconciliation]:
    rows = []
    for entry in walk(args.path):
        extracted = None
        if args.in_process and entry.declared is not None:
            probe = for_path(entry.path)
            extracted = probe.extract(entry.path) if probe else None
        rows.append(reconcile(entry, extracted, threshold=args.threshold))
    return rows


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "manifest":
        for entry in walk(args.path):
            declared = entry.declared
            summary = f"{declared.units} {declared.unit_kind}s" if declared else (entry.note or "?")
            print(f"{entry.path.name:<44} {summary}")
        return 0

    rows = _reconcile_all(args)

    with ledger.connect(args.ledger) as conn:
        store.init(conn)
        run_id = ledger.start_run(conn, "ingest-ledger", sys.argv[1:])
        for row in rows:
            store.record(conn, run_id, row)
        ledger.finish_run(conn, run_id)

    print(report_mod.render(rows))

    if args.strict and any(r.quarantined for r in rows):
        return 1
    return 0 if all(r.status is not Status.FAILED for r in rows) else 1
