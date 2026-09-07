"""Compare chunking strategies on one corpus, and recommend one."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from data_tools_core.provenance import Provenance, UnitKind

from chunking_lab.chunkers import STRATEGIES, from_spec
from chunking_lab.invariant import check, coverage

#: Which strategies are implemented, and what each needs installed. Printed by
#: `chunkers` so the gap between what is designed and what is built is visible
#: from the command line rather than only in the README.
TIERS = {
    "fixed": ("0", "SIZE[/OVERLAP]", "cut every N characters, optionally overlapping"),
    "recursive": ("0", "SIZE[/OVERLAP]", "split on the best separator present, then merge"),
    "sentence": ("0", "N[/OVERLAP]", "pack N sentences per chunk"),
    "structural": ("0", "[:MAXSIZE]", "split at Markdown headings, respecting code fences"),
    "sentence-window": ("0", "WINDOW", "index one sentence, return it with its neighbours"),
    "parent-document": ("0", "CHILD/PARENT", "index small children, return the parent block"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chunking-lab", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("chunkers", help="list the strategies that are implemented")
    listing.set_defaults(run=run_chunkers)

    split = sub.add_parser("split", help="chunk one document and show where the cuts landed")
    split.add_argument("path", type=Path, help="the document to split")
    split.add_argument(
        "--strategy",
        required=True,
        help="strategy spec, e.g. recursive:400/200 (see `chunking-lab chunkers`)",
    )
    split.add_argument("--limit", type=int, default=10, help="spans to show (0 for all)")
    split.set_defaults(run=run_split)

    return parser


def run_chunkers(args: argparse.Namespace) -> int:
    """List every implemented strategy with its tier and what it needs."""
    print(f"{'tier':<5} {'spec':<32} what it does")
    for name in sorted(STRATEGIES):
        tier, params, summary = TIERS[name]
        spec = f"{name}{params}" if params.startswith("[") else f"{name}:{params}"
        print(f"{tier:<5} {spec:<32} {summary}")
    print("\nTier 0 needs nothing installed. Tier 2 (LLM boundaries, contextual")
    print("augmentation) is designed but not built; see README section 8.2.")
    return 0


def run_split(args: argparse.Namespace) -> int:
    """Chunk one document and print the spans, so the cuts can be eyeballed."""
    text = args.path.read_text()
    provenance = Provenance(
        source=args.path,
        sha256=hashlib.sha256(args.path.read_bytes()).hexdigest(),
        unit_kind=UnitKind.DOCUMENT,
    )
    chunking = from_spec(args.strategy).chunk(text, provenance)
    check(chunking, text)

    print(f"{chunking.strategy} on {provenance.locator}")
    print(f"{len(chunking)} spans, coverage {coverage(chunking, text):.3f}\n")
    shown = chunking.spans if args.limit == 0 else chunking.spans[: args.limit]
    for i, span in enumerate(shown):
        body = span.retrieval_text.replace("\n", "\\n")
        print(f"  [{i:>3}] {span.start:>6}..{span.end:<6} {span.length:>5}c  {body[:72]}")
    if len(shown) < len(chunking):
        print(f"  ... {len(chunking) - len(shown)} more (--limit 0 for all)")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Compare chunking strategies on one corpus, and recommend one."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.run(args))
    except (ValueError, OSError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
