"""slopify — inject the habits ai-sniffer looks for, and record where each one went."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from slopify.habits import INJECTORS
from slopify.inject import slop


def _inject(args: argparse.Namespace) -> int:
    source = Path(args.file)
    if not source.is_file():
        print(f"slopify: no such file: {source}", file=sys.stderr)
        return 2
    try:
        text, labels = slop(
            source.read_text(encoding="utf-8"),
            seed=args.seed,
            count=args.count,
            habits=args.habit or None,
            width=args.width,
        )
    except ValueError as exc:
        print(f"slopify: {exc}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else None
    if out:
        out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    if args.labels:
        name = out.name if out else source.name
        lines = [label.as_json(name) for label in labels]
        Path(args.labels).write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.count and not labels:
        print("slopify: no paragraph in this draft accepted an injection", file=sys.stderr)
    return 0


def _habits(_: argparse.Namespace) -> int:
    for name in sorted(INJECTORS):
        doc = (INJECTORS[name].__doc__ or "").strip().split("\n")[0]
        print(f"  {name:<20}{doc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Put the tells back into a draft, on purpose, and say where they went."""
    parser = argparse.ArgumentParser(prog="slopify", description=main.__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inject = sub.add_parser("inject", help="inject habits into a draft")
    inject.add_argument("file", help="a Markdown draft")
    inject.add_argument("--seed", type=int, default=0, help="same seed, same output")
    inject.add_argument("--count", type=int, default=8, help="how many habits to inject")
    inject.add_argument(
        "--habit",
        action="append",
        metavar="NAME",
        help="restrict to this habit; repeatable. `slopify habits` lists them",
    )
    inject.add_argument("--out", help="write the draft here instead of stdout")
    inject.add_argument("--labels", help="write one JSONL label per injection here")
    inject.add_argument("--width", type=int, default=88, help="wrap width for rewritten paragraphs")
    inject.set_defaults(func=_inject)

    listing = sub.add_parser("habits", help="list the injectable habits")
    listing.set_defaults(func=_habits)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
