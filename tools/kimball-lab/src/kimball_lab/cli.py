"""Seed a bank, load it batch by batch, and show what each Kimball technique fixes."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import runner, seed
from .engine import EngineUnavailable, open_engine


def _cmd_seed(args) -> int:
    bank = seed.generate(seed=args.seed, scale=args.scale)
    manifest = seed.write(bank, Path(args.out))
    print(
        f"wrote {len(manifest['batches'])} batches to {args.out}: "
        f"{manifest['customers']} customers, {manifest['accounts']} accounts, "
        f"{manifest['transactions']} transactions"
    )
    for case, ids in manifest["planted"].items():
        if isinstance(ids, dict):
            n = ", ".join(f"{k} {v}" for k, v in ids.items())
        else:
            n = ids if isinstance(ids, int) else len(ids)
        print(f"  planted {case}: {n}")
    return 0


def _cmd_load(args) -> int:
    engine = open_engine(args.db, kind=args.engine)
    try:
        results = runner.load(engine, Path(args.seed_dir), through=args.through)
    finally:
        engine.close()
    for r in results:
        snap = "" if r.snapshot_id is None else f"  snapshot {r.snapshot_id}"
        staged, loaded = r.staged_transactions, r.loaded_transactions
        print(f"{r.batch_id}  staged {staged:>7}  loaded {loaded:>7}{snap}")
    print(f"engine: {engine.kind}")
    return 0


def _pick(number: str | None) -> list[runner.Technique]:
    ts = runner.techniques()
    if number is None:
        return ts
    chosen = [t for t in ts if t.number == number.zfill(2)]
    if not chosen:
        raise SystemExit(f"no technique {number}; `kimball-lab list` shows them")
    return chosen


def _render(d: runner.Demo) -> str:
    t = d.technique
    lines = [f"{t.number}  {t.title}", f"    {t.question}"]
    if d.skipped:
        lines.append(f"    skipped: {d.skipped}")
        return "\n".join(lines)
    keys = sorted(set(d.truth) | set(d.naive or {}) | set(d.correct or {}))
    width = max((len(k) for k in keys), default=10)
    lines.append(f"    {'figure':<{width}}  {'naive':>16}  {'correct':>16}  {'truth':>16}")
    for k in keys:
        n, c, g = (str(x.get(k, "-")) for x in (d.naive or {}, d.correct or {}, d.truth))
        lines.append(f"    {k:<{width}}  {n:>16}  {c:>16}  {g:>16}")
    verdict = "correct matches truth" if d.correct_matches_truth else "CORRECT DOES NOT MATCH TRUTH"
    naive = "naive is wrong" if d.naive_differs else "naive happens to agree"
    lines.append(f"    {verdict}; {naive}; engine {d.engine}")
    return "\n".join(lines)


def _cmd_demo(args) -> int:
    engine = open_engine(args.db, install=False)
    try:
        demos = [runner.demo(engine, t) for t in _pick(args.technique)]
    finally:
        engine.close()
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "technique": d.technique.number,
                        "title": d.technique.title,
                        "engine": d.engine,
                        "naive": d.naive,
                        "correct": d.correct,
                        "truth": d.truth,
                        "skipped": d.skipped,
                    }
                    for d in demos
                ],
                indent=2,
            )
        )
    else:
        print("\n\n".join(_render(d) for d in demos))
    failed = [d for d in demos if not d.skipped and not d.correct_matches_truth]
    return 1 if failed else 0


def _cmd_list(_args) -> int:
    for t in runner.techniques():
        req = f"  (needs {t.requires})" if t.requires else ""
        print(f"{t.number}  {t.title}{req}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Seed a bank, load it with plain SQL, and show the number each Kimball technique fixes."""
    parser = argparse.ArgumentParser(prog="kimball-lab", description=main.__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser(
        "seed", help="write 18 monthly batches of bank extracts and their ground truth"
    )
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--scale", type=int, default=10, help="200 customers per unit (default 10)")
    p.set_defaults(func=_cmd_seed)

    p = sub.add_parser("load", help="load the batches into a warehouse, then build the techniques")
    p.add_argument("seed_dir")
    p.add_argument("--db", required=True)
    p.add_argument("--engine", choices=("ducklake", "duckdb"), default="ducklake")
    p.add_argument("--through", metavar="YYYY-MM", help="stop after this batch")
    p.set_defaults(func=_cmd_load)

    p = sub.add_parser("demo", help="naive vs correct vs ground truth, per technique")
    p.add_argument("technique", nargs="?", help="technique number; omit for all")
    p.add_argument("--db", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_demo)

    p = sub.add_parser("list", help="list the techniques")
    p.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except EngineUnavailable as e:
        print(f"kimball-lab: {e}. Use --engine duckdb to run without snapshots.", file=sys.stderr)
        return 2
