"""Compare chunking strategies on one corpus, and recommend one."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from data_tools_core.provenance import Provenance, UnitKind

from chunking_lab import benchmark, score
from chunking_lab.chunkers import STRATEGIES, from_spec
from chunking_lab.embeddings import resolve
from chunking_lab.extrinsic import precision_omega
from chunking_lab.intrinsic import measure
from chunking_lab.invariant import check
from chunking_lab.locate import locate

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
    "semantic": ("1", "PCTL[/MAXSIZE]", "cut where adjacent sentences are least alike"),
    "cluster-semantic": ("1", "MAXSIZE[/PIECE]", "globally maximise within-chunk similarity"),
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
    split.add_argument(
        "--embedder",
        default="hashing",
        choices=["hashing", "provider"],
        help="Tier 1 only: `hashing` is offline and weak; `provider` uses "
        "DATA_TOOLS_EMBED_MODEL and needs the `embeddings` extra",
    )
    split.add_argument("--limit", type=int, default=10, help="spans to show (0 for all)")
    split.set_defaults(run=run_split)

    metrics = sub.add_parser(
        "metrics",
        help="score one document against several strategies, query-free",
        description=(
            "Intrinsic metrics screen; they do not rank. A strategy with no "
            "disqualifications is eligible for a real evaluation, not good."
        ),
    )
    metrics.add_argument("path", type=Path, help="the document to measure")
    metrics.add_argument(
        "--strategy",
        action="append",
        required=True,
        dest="strategies",
        help="repeatable, e.g. --strategy recursive:400 --strategy structural",
    )
    metrics.add_argument(
        "--embedder",
        default=None,
        choices=["hashing", "provider"],
        help="add cohesion/separation, the only two signals here that cost anything",
    )
    metrics.set_defaults(run=run_metrics)

    scoring = sub.add_parser(
        "score",
        help="rank strategies against gold spans on the Chroma benchmark",
        description=(
            "Absolute values are very low by construction -- k chunks are retrieved "
            "to answer a one-sentence question. These are RELATIVE comparisons only."
        ),
    )
    scoring.add_argument(
        "--strategy", action="append", required=True, dest="strategies", help="repeatable"
    )
    scoring.add_argument(
        "--corpus",
        action="append",
        dest="corpora",
        help="benchmark corpus name, e.g. state_of_the_union.md (default: all five)",
    )
    scoring.add_argument(
        "--k",
        type=int,
        default=None,
        help="retrieval depth; default is per-question, at that question's number "
        "of gold-bearing chunks (the reference's retrieve=-1)",
    )
    scoring.add_argument("--limit", type=int, default=0, help="cap questions per corpus")
    scoring.add_argument("--out", type=Path, default=None, help="append JSONL result rows here")
    scoring.set_defaults(run=run_score)

    explain = sub.add_parser(
        "explain",
        help="show one answer against the chunks it actually landed in",
        description=(
            "The intuition-builder. A score column cannot show you the answer "
            "sentence cut in half; this can."
        ),
    )
    explain.add_argument("path", type=Path, help="the document")
    explain.add_argument("--strategy", required=True, help="strategy spec")
    explain.add_argument(
        "--answer",
        required=True,
        help="the answer, quoted verbatim from the document. Offsets are found "
        "deterministically -- exact, then whitespace-tolerant, then fuzzy",
    )
    explain.set_defaults(run=run_explain)

    return parser


def _load(path: Path) -> tuple[str, Provenance]:
    return path.read_text(), Provenance(
        source=path,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        unit_kind=UnitKind.DOCUMENT,
    )


def run_chunkers(args: argparse.Namespace) -> int:
    """List every implemented strategy with its tier and what it needs."""
    print(f"{'tier':<5} {'spec':<32} what it does")
    for name in sorted(STRATEGIES, key=lambda n: (TIERS[n][0], n)):
        tier, params, summary = TIERS[name]
        spec = f"{name}{params}" if params.startswith("[") else f"{name}:{params}"
        print(f"{tier:<5} {spec:<32} {summary}")
    print("\nTier 0 needs nothing installed. Tier 1 embeds, and defaults to an")
    print("offline hashing embedder -- deterministic but weak, so a Tier 1 result")
    print("is only evidence about semantic chunking with --embedder provider")
    print("(needs the `embeddings` extra). Every result records which ran.")
    print("Tier 2 (LLM boundaries, contextual augmentation) is not built;")
    print("see this tool's README section 8.2.")
    return 0


def run_split(args: argparse.Namespace) -> int:
    """Chunk one document and print the spans, so the cuts can be eyeballed."""
    text, provenance = _load(args.path)
    chunker = from_spec(args.strategy)
    if getattr(args, "embedder", "hashing") != "hashing" and hasattr(chunker, "embedder"):
        chunker.embedder = resolve(args.embedder)
    chunking = chunker.chunk(text, provenance)
    check(chunking, text)

    print(f"{chunking.strategy} on {provenance.locator}")
    print(f"{len(chunking)} spans, coverage {measure(chunking, text).coverage:.3f}")
    print(f"path: {chunking.code_path}")
    for note in chunking.notes:
        print(f"note: {note}")
    print()
    shown = chunking.spans if args.limit == 0 else chunking.spans[: args.limit]
    for i, span in enumerate(shown):
        body = span.retrieval_text.replace("\n", "\\n")
        print(f"  [{i:>3}] {span.start:>6}..{span.end:<6} {span.length:>5}c  {body[:72]}")
    if len(shown) < len(chunking):
        print(f"  ... {len(chunking) - len(shown)} more (--limit 0 for all)")
    return 0


def run_metrics(args: argparse.Namespace) -> int:
    """Measure several strategies on one document, with no questions involved."""
    text, provenance = _load(args.path)
    embedder = resolve(args.embedder) if args.embedder else None

    rows = []
    for spec in args.strategies:
        chunker = from_spec(spec)
        if args.embedder and hasattr(chunker, "embedder"):
            chunker.embedder = resolve(args.embedder)
        chunking = chunker.chunk(text, provenance)
        check(chunking, text)
        rows.append(measure(chunking, text, embedder=embedder))

    header = f"{'strategy':<26}{'chunks':>7}{'dup':>6}{'ret':>6}{'p95':>7}{'bfid':>6}{'orph':>6}"
    if embedder is not None:
        header += f"{'cohes':>7}{'separ':>7}"
    print(f"{provenance.locator}  ({len(text)} characters)\n")
    print(header)
    for row in rows:
        line = (
            f"{row.strategy:<26}{row.chunks:>7}{row.duplication:>6.2f}"
            f"{row.return_amplification:>6.2f}{row.p95_length:>7}"
            f"{row.boundary_fidelity:>6.2f}{row.orphan_rate:>6.2f}"
        )
        if row.cohesion is not None:
            line += f"{row.cohesion:>7.2f}{row.separation or 0.0:>7.2f}"
        print(line)

    print("\nscreening:")
    for row in rows:
        reasons = row.disqualifications()
        if reasons:
            print(f"  {row.strategy}: DISQUALIFIED")
            for reason in reasons:
                print(f"      - {reason}")
        else:
            print(f"  {row.strategy}: eligible")
    print(
        "\nIntrinsic metrics screen; they do not rank. Ranking the eligible ones\n"
        "needs questions with gold spans -- see this tool's README section 7."
    )
    return 0


def run_score(args: argparse.Namespace) -> int:
    """Rank strategies against gold spans, and say what the ranking rests on."""
    corpora = benchmark.load()
    if args.corpora:
        wanted = set(args.corpora)
        corpora = [c for c in corpora if c.name in wanted]
        if not corpora:
            raise ValueError(f"no benchmark corpus matched {sorted(wanted)}")

    results = []
    for spec in args.strategies:
        chunker = from_spec(spec)
        for corpus in corpora:
            questions = corpus.questions[: args.limit] if args.limit else None
            results.extend(score.run(chunker, corpus, k=args.k, questions=questions))

    summaries = score.summarise(results)
    total_questions = sum(
        len(c.questions[: args.limit] if args.limit else c.questions) for c in corpora
    )
    print(
        f"{len(corpora)} corpora, {total_questions} questions, retriever bm25/fts5, "
        f"k={'per-question' if args.k is None else args.k}\n"
    )
    print(f"{'strategy':<26}{'P-omega':>9}{'IoU':>8}{'recall':>8}{'prec':>8}{'k':>6}")
    for row in summaries:
        print(
            f"{row.strategy:<26}{row.precision_omega * 100:>9.2f}{row.iou * 100:>8.2f}"
            f"{row.recall * 100:>8.2f}{row.precision * 100:>8.2f}{row.mean_k:>6.1f}"
        )

    if args.out:
        written = score.write_jsonl(results, args.out)
        print(f"\n{written} rows appended to {args.out}")

    print(
        "\nRelative comparisons only. Token-level precision is single-digit by\n"
        "construction at k>1 -- see this tool's README section 4. Precision Omega\n"
        "is the column to read: it is the ceiling the cuts impose, independent of\n"
        "the retriever."
    )
    return 0


def run_explain(args: argparse.Namespace) -> int:
    """Render one answer against the chunks it landed in."""
    text, provenance = _load(args.path)
    found = locate(text, args.answer)
    if found is None:
        print(
            f"could not find that answer in {args.path}.\n"
            "Quote it verbatim from the document -- exact match is tried first, then a "
            "whitespace-tolerant match, then a fuzzy one that must score at least 98.",
            file=sys.stderr,
        )
        return 1

    chunker = from_spec(args.strategy)
    chunking = chunker.chunk(text, provenance)
    check(chunking, text)

    gold = [found.span]
    holders = [s for s in chunking.spans if s.start < found.span[1] and s.end > found.span[0]]
    omega = precision_omega(chunking, gold)

    print(f"{chunking.strategy} on {provenance.locator}")
    print(
        f"answer located by {found.how} match at {found.span[0]}..{found.span[1]} "
        f"({found.span[1] - found.span[0]} characters)"
    )
    print(
        f"Precision Omega {omega * 100:.1f}%  --  the answer is in {len(holders)} chunk"
        f"{'s' if len(holders) != 1 else ''} of {len(chunking)}"
    )
    if len(holders) > 1:
        print("\nSEVERED: no single chunk holds the whole answer.")
    print()

    for i, span in enumerate(holders):
        head = f"  chunk holding the answer [{i + 1}/{len(holders)}]  {span.start}..{span.end}"
        print(head)
        print("  " + "-" * (len(head) - 2))
        body = span.retrieval_text
        # Mark the part of the answer this chunk actually holds.
        lo = max(found.span[0], span.start) - span.start
        hi = min(found.span[1], span.end) - span.start
        marked = body[:lo] + "[" + body[lo:hi] + "]" + body[hi:]
        for line in marked.splitlines() or [""]:
            print(f"    {line}")
        if span.return_text != span.retrieval_text:
            extra = len(span.return_text) - len(span.retrieval_text)
            print(f"    ... and {extra} more characters are RETURNED but not indexed")
        print()

    print("[ ] marks the answer. Everything outside it in these chunks is padding a")
    print("retriever has to carry to deliver the answer at all.")
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
