"""Compare chunking strategies on one corpus, and recommend one."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from data_tools_core.provenance import Provenance, UnitKind

from chunking_lab import annotate as annotate_mod
from chunking_lab import benchmark, score
from chunking_lab import corpus as corpus_mod
from chunking_lab import correlate as correlate_mod
from chunking_lab.chunkers import STRATEGIES, from_spec
from chunking_lab.correlate import TARGETS
from chunking_lab.embeddings import resolve
from chunking_lab.extrinsic import precision_omega
from chunking_lab.intrinsic import measure
from chunking_lab.invariant import check
from chunking_lab.locate import locate
from chunking_lab.retrieve import RETRIEVERS

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
        help="corpus name to keep, e.g. state_of_the_union.md (default: all of them)",
    )
    scoring.add_argument(
        "--corpus-dir",
        type=Path,
        default=None,
        help="score a directory of documents plus a gold.jsonl instead of the Chroma "
        "benchmark -- generated fixtures, or your own annotated corpus",
    )
    scoring.add_argument(
        "--k",
        type=int,
        default=None,
        help="retrieval depth; default is per-question, at that question's number "
        "of gold-bearing chunks (the reference's retrieve=-1)",
    )
    scoring.add_argument(
        "--retriever",
        default="bm25",
        choices=list(RETRIEVERS),
        help="bm25 needs nothing; vector and hybrid need --embedder. The retriever is "
        "held FIXED across a chunker comparison -- varying both at once measures neither",
    )
    scoring.add_argument(
        "--embedder",
        default=None,
        help="`hashing` (offline, weak, for exercising the path), `provider` (whatever "
        "DATA_TOOLS_EMBED_MODEL says, defaulting to ollama/nomic-embed-text), or an "
        "explicit model string like ollama/qwen3-embedding",
    )
    scoring.add_argument("--limit", type=int, default=0, help="cap questions per corpus")
    scoring.add_argument(
        "--by-question-type",
        action="store_true",
        help="also rank the strategies separately for each kind of question. A single "
        "ranking is always a ranking against some question mix; this shows how much "
        "that mix decides the answer",
    )
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

    corr = sub.add_parser(
        "correlate",
        help="do the query-free signals predict the query-dependent ranking?",
        description=(
            "A query over accumulated `score --out` rows, not a new pipeline. "
            "Precision Omega is mechanically tied to chunk size, so --control "
            "reports the partial correlation with size removed; a signal that "
            "survives that is telling you something size does not."
        ),
    )
    corr.add_argument("results", type=Path, help="JSONL written by `score --out`")
    corr.add_argument("--against", default="precision_omega", choices=list(TARGETS), dest="target")
    corr.add_argument(
        "--control",
        default="median_length",
        help="signal to partial out, or `none` (default: median_length)",
    )
    corr.set_defaults(run=run_correlate)

    axes = sub.add_parser(
        "axes",
        help="is the chunker the big knob, or the retriever?",
        description=(
            "Measures each axis with the other held fixed and compares the spread. "
            "Needs a results file containing more than one retriever, which means "
            "scoring the same strategies more than once."
        ),
    )
    axes.add_argument("results", type=Path, help="JSONL written by `score --out`")
    axes.add_argument(
        "--metric",
        default="iou",
        choices=["iou", "recall", "precision"],
        help="precision_omega is refused: it is retriever-independent by construction, "
        "so the retriever axis would always show no spread",
    )
    axes.set_defaults(run=run_axes)

    ann = sub.add_parser(
        "annotate",
        help="generate gold spans for your own documents, and report the yield",
        description=(
            "Never asks the model for character offsets -- it asks for the answer "
            "quoted verbatim, locates the quote deterministically, and DISCARDS "
            "anything it cannot find. A weaker model produces less ground truth, "
            "never wrong ground truth, and the shortfall is reported as a yield."
        ),
    )
    ann.add_argument("path", type=Path, help="a document, or a directory of them")
    ann.add_argument("--out", type=Path, required=True, help="directory to write the corpus into")
    ann.add_argument(
        "--per-document", type=int, default=5, help="questions to attempt per document"
    )
    ann.add_argument(
        "--model",
        action="append",
        default=None,
        dest="models",
        help="LiteLLM chat model string. Defaults to DATA_TOOLS_CHAT_MODEL, which "
        "defaults to ollama/llama3.1 -- so local is the ordinary path. Repeatable: "
        "give it more than once to compare models on identical windows, which is how "
        "you find out whether a bigger model is worth its disk space",
    )
    ann.add_argument("--seed", type=int, default=0, help="window sampling seed")
    ann.add_argument("--glob", default="*.md", help="which files to read when path is a directory")
    ann.set_defaults(run=run_annotate)

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
    corpora = corpus_mod.load_dir(args.corpus_dir) if args.corpus_dir else benchmark.load()
    if args.corpora:
        wanted = set(args.corpora)
        corpora = [c for c in corpora if c.name in wanted]
        if not corpora:
            raise ValueError(f"no benchmark corpus matched {sorted(wanted)}")

    embedder = resolve(args.embedder) if args.embedder else None
    if args.retriever != "bm25" and embedder is None:
        raise ValueError(
            f"the {args.retriever!r} retriever needs an encoder. Pass --embedder with a "
            "model string (ollama/nomic-embed-text is the local default), or `hashing` "
            "to exercise the path with an offline stand-in whose numbers mean nothing."
        )

    results = []
    for spec in args.strategies:
        chunker = from_spec(spec)
        for corpus in corpora:
            questions = corpus.questions[: args.limit] if args.limit else None
            results.extend(
                score.run(
                    chunker,
                    corpus,
                    k=args.k,
                    questions=questions,
                    retriever=args.retriever,
                    embedder=embedder,
                )
            )

    summaries = score.summarise(results)
    total_questions = sum(
        len(c.questions[: args.limit] if args.limit else c.questions) for c in corpora
    )
    engine = results[0].retriever if results else args.retriever
    print(
        f"{len(corpora)} corpora, {total_questions} questions, retriever {engine}, "
        f"k={'per-question' if args.k is None else args.k}\n"
    )
    if "hashing" in engine:
        print(
            "WARNING: this ran against the offline hashing embedder, which is a bag of\n"
            "words. It exercises the code path; it is not evidence about vector\n"
            "retrieval. Pass a real encoder, e.g. --embedder ollama/nomic-embed-text.\n"
        )
    print(f"{'strategy':<26}{'P-omega':>9}{'IoU':>8}{'recall':>8}{'prec':>8}{'k':>6}")
    for row in summaries:
        print(
            f"{row.strategy:<26}{row.precision_omega * 100:>9.2f}{row.iou * 100:>8.2f}"
            f"{row.recall * 100:>8.2f}{row.precision * 100:>8.2f}{row.mean_k:>6.1f}"
        )

    if args.by_question_type:
        rows = score.breakdown(results, target="iou")
        kinds = sorted({r.kind for r in rows})
        if kinds == ["unlabelled"]:
            print(
                "\n(this corpus does not label its question types, so there is "
                "nothing to break down)"
            )
        else:
            print(
                "\nrank out of "
                f"{max(r.rank for r in rows)}, by what the question asks for (by IoU):\n"
            )
            width = max(len(k) for k in kinds) + 2
            print(f"{'strategy':<24}" + "".join(f"{k[: width - 2]:>{width}}" for k in kinds))
            order = {r.strategy: r.rank for r in rows if r.kind == kinds[0]}
            for strategy in sorted(order, key=lambda s: order[s]):
                line = f"{strategy:<24}"
                ranks = []
                for kind in kinds:
                    rank = next(r.rank for r in rows if r.kind == kind and r.strategy == strategy)
                    ranks.append(rank)
                    line += f"{rank:>{width}}"
                swing = max(ranks) - min(ranks)
                line += f"   swing {swing}" + ("  <--" if swing >= len(order) // 2 else "")
                print(line)
            print(
                "\nA strategy that swings is one whose value depends on what people ask.\n"
                "There is no single best chunking; there is a best one for a question mix."
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


def run_correlate(args: argparse.Namespace) -> int:
    """Report whether the model-free signals track the measured ranking."""
    points = correlate_mod.load(args.results)
    if not points:
        raise ValueError(f"no result rows in {args.results}")
    control = None if args.control == "none" else args.control
    results = correlate_mod.correlate(points, target=args.target, control=control)
    if not results:
        raise ValueError("not enough strategies per corpus to correlate (need at least 3)")

    corpora = sorted({r.corpus for r in results})
    n = max(r.n for r in results)
    print(
        f"{len(points)} (corpus, strategy) points across {len(corpora)} corpora, vs {args.target}"
    )
    threshold = correlate_mod.critical_rho(n)
    if threshold is not None:
        print(f"* marks |rho| >= {threshold:.2f}, significant at p<0.05 for n={n}")
    if control:
        print(f"partial column removes the effect of {control}")
    print()

    header = f"{'signal':<20}" + "".join(f"{c.replace('.md', '')[:11]:>13}" for c in corpora)
    if control:
        header += f"{'partial(mean)':>15}"
    print(header)

    summary = correlate_mod.summarise(results)
    by_key = {(r.corpus, r.signal): r for r in results}
    for signal in sorted(summary, key=lambda s: -abs(summary[s]["mean_rho"])):
        line = f"{signal:<20}"
        for corpus in corpora:
            r = by_key.get((corpus, signal))
            if r is None:
                cell = "—"
            elif r.constant:
                cell = "const"
            else:
                cell = f"{r.rho:+.2f}{'*' if r.significant else ' '}"
            line += f"{cell:>13}"
        if control:
            if signal == control:
                line += f"{'(control)':>15}"
            elif summary[signal]["constant_everywhere"]:
                line += f"{'—':>15}"
            else:
                line += f"{summary[signal]['mean_partial']:>+15.2f}"
        print(line)

    constant = [s for s in summary if summary[s]["constant_everywhere"]]
    if constant:
        print(
            f"\n`const` = the signal never varies on that corpus, so there is nothing\n"
            f"to correlate. {', '.join(constant)} are UNTESTED here, not shown to be\n"
            f"uninformative -- these corpora contain no Markdown tables or code fences."
        )
    print(
        "\nRead the per-corpus columns, not the average: a signal that changes sign\n"
        "between corpora is telling you something an average would hide."
    )
    return 0


def run_axes(args: argparse.Namespace) -> int:
    """Compare how much each axis moves the numbers, with the other held fixed."""
    points = correlate_mod.load(args.results)
    if not points:
        raise ValueError(f"no result rows in {args.results}")

    retrievers = sorted({p.retriever for p in points})
    strategies = sorted({p.strategy for p in points})
    if len(retrievers) < 2:
        raise ValueError(
            f"{args.results} has only one retriever ({retrievers[0]}), so there is no "
            "retriever axis to measure. Score the same strategies again with "
            "--retriever vector and --retriever hybrid, appending to the same file."
        )

    rows = correlate_mod.spreads(points, metric=args.metric)
    chunker = [r for r in rows if r.axis == "chunker"]
    retriever = [r for r in rows if r.axis == "retriever"]

    print(
        f"{len(strategies)} strategies x {len(retrievers)} retrievers over "
        f"{len({p.corpus for p in points})} corpora, by {args.metric}\n"
    )
    print(f"{'axis':<12}{'held fixed':<34}{'corpus':<22}{'best/worst':>11}")
    for row in sorted(rows, key=lambda r: (r.axis, r.corpus, r.held_fixed)):
        ratio = "inf" if row.ratio == float("inf") else f"{row.ratio:.1f}x"
        print(f"{row.axis:<12}{row.held_fixed[:32]:<34}{row.corpus[:20]:<22}{ratio:>11}")

    def summarise(rows):
        values = sorted(r.ratio for r in rows if r.ratio != float("inf"))
        if not values:
            return None
        at = lambda q: values[min(len(values) - 1, round((len(values) - 1) * q))]  # noqa: E731
        return {
            "n": len(values),
            "min": values[0],
            "median": at(0.5),
            "max": values[-1],
            "over2": sum(1 for v in values if v > 2),
        }

    print(f"\n{'axis':<12}{'n':>4}{'min':>8}{'median':>9}{'max':>8}{'>2x':>10}")
    stats = {}
    for label, rows in (("chunker", chunker), ("retriever", retriever)):
        s = summarise(rows)
        stats[label] = s
        if s:
            share = f"{s['over2']}/{s['n']}"
            print(
                f"{label:<12}{s['n']:>4}{s['min']:>7.1f}x{s['median']:>8.1f}x"
                f"{s['max']:>7.1f}x{share:>10}"
            )

    # A median is a poor summary of a skewed distribution, and these are skewed:
    # one axis can matter almost always while the other matters rarely and hugely.
    # Report how *often* each axis moves things, not just how much on average.
    c, r = stats.get("chunker"), stats.get("retriever")
    if c and r:
        c_rate, r_rate = c["over2"] / c["n"], r["over2"] / r["n"]
        print(
            f"\nthe chunker exceeds 2x in {c['over2']} of {c['n']} cases; "
            f"the retriever in {r['over2']} of {r['n']}."
        )
        if c_rate > r_rate and r["max"] >= c["max"] * 0.7:
            print(
                "So the two axes fail differently, and a median hides it: the chunker\n"
                "matters consistently, while the retriever usually does not matter at all\n"
                f"and occasionally matters as much as the chunker ever does ({r['max']:.1f}x).\n"
                "Read the per-row table above, not the summary."
            )
        elif c_rate > r_rate:
            print("On these corpora the chunker is the more consistent lever.")
        else:
            print("On these corpora the retriever is the more consistent lever.")
    print(
        "\nA spread is only as wide as the options given. Adding a worse chunker or a\n"
        "better retriever moves these numbers, so read them as 'over this range of\n"
        "choices', never as a property of chunking or retrieval in general."
    )
    if any("hashing" in r for r in retrievers):
        print(
            "\nWARNING: one of these retrievers used the offline hashing embedder, which\n"
            "is a bag of words. It understates the retriever axis badly. Re-run with a\n"
            "real encoder before quoting this."
        )
    return 0


def _chat_provider(model: str | None):
    """Resolve a chat model lazily, so `--help` never needs the extra installed."""
    from dataclasses import replace

    from data_tools_core.config import get_settings
    from data_tools_core.llm import get_chat_provider

    settings = get_settings()
    if model:
        settings = replace(settings, chat_model=model)
    return get_chat_provider(settings), settings.chat_model


def _compare_models(args: argparse.Namespace, documents: list[Path], models: list[str]) -> int:
    """Run every model over the *same* windows and report the yields side by side.

    The seed is shared, so each model is asked about identical passages -- the only
    thing varying is the model, which is what makes the comparison mean anything.
    Nothing is written: this answers "which model should I annotate with", and you
    then run the real pass with the winner.
    """
    print(
        f"comparing {len(models)} models over {len(documents)} document(s), "
        f"{args.per_document} attempts each, seed {args.seed}\n"
    )
    rows = []
    for model in models:
        provider, resolved = _chat_provider(model)
        totals = annotate_mod.Yield()
        for document in documents:
            _, produced = annotate_mod.annotate(
                document.name,
                document.read_text(encoding="utf-8"),
                provider,
                count=args.per_document,
                seed=args.seed,
            )
            stages = dict(totals.by_stage)
            for key, value in produced.by_stage.items():
                stages[key] = stages.get(key, 0) + value
            totals = annotate_mod.Yield(
                asked=totals.asked + produced.asked,
                kept=totals.kept + produced.kept,
                call_failed=totals.call_failed + produced.call_failed,
                malformed=totals.malformed + produced.malformed,
                unlocatable=totals.unlocatable + produced.unlocatable,
                by_stage=stages,
            )
        rows.append((resolved, totals))
        print(f"  {resolved:<28} {totals.kept:>3}/{totals.asked:<4} {totals.rate:>6.0%}")

    print(f"\n{'model':<28}{'yield':>7}{'kept':>6}{'paraphrased':>13}{'bad JSON':>10}{'exact':>7}")
    for model, y in sorted(rows, key=lambda r: -r[1].rate):
        print(
            f"{model:<28}{y.rate:>7.0%}{y.kept:>6}{y.unlocatable:>13}"
            f"{y.malformed:>10}{y.by_stage.get('exact', 0):>7}"
        )
    print(
        "\n`paraphrased` is the model rewriting text it was told to copy verbatim --\n"
        "the dominant failure, and the one a larger model is most likely to fix.\n"
        "`exact` counts excerpts found without any whitespace or fuzzy tolerance;\n"
        "a corpus built mostly from fuzzy matches is worth less than its yield suggests."
    )
    return 0


def run_annotate(args: argparse.Namespace) -> int:
    """Manufacture gold spans, keeping only the ones that could be verified."""
    documents = sorted(args.path.glob(args.glob)) if args.path.is_dir() else [args.path]
    if not documents:
        raise ValueError(f"no files matching {args.glob!r} in {args.path}")

    models = args.models or [None]
    if len(models) > 1:
        return _compare_models(args, documents, models)

    provider, model = _chat_provider(models[0])
    print(f"annotating {len(documents)} document(s) with {model}\n")

    corpora, totals = [], annotate_mod.Yield()
    for document in documents:
        corpus, produced = annotate_mod.annotate(
            document.name,
            document.read_text(encoding="utf-8"),
            provider,
            count=args.per_document,
            seed=args.seed,
        )
        corpora.append(corpus)
        stages = dict(totals.by_stage)
        for key, value in produced.by_stage.items():
            stages[key] = stages.get(key, 0) + value
        totals = annotate_mod.Yield(
            asked=totals.asked + produced.asked,
            kept=totals.kept + produced.kept,
            call_failed=totals.call_failed + produced.call_failed,
            malformed=totals.malformed + produced.malformed,
            unlocatable=totals.unlocatable + produced.unlocatable,
            by_stage=stages,
        )
        print(f"  {document.name:<30} {produced.kept}/{produced.asked} usable")

    kept = [c for c in corpora if c.questions]
    if not kept:
        print(
            "\nNo question survived verification, so no corpus was written.\n"
            f"{totals.report()}\n"
            "Every discarded question is one whose quoted answer could not be found "
            "in the document. That is the check working, not a bug -- but a run that "
            "keeps nothing usually means the model is too weak for this task.",
            file=sys.stderr,
        )
        return 1

    gold = corpus_mod.write_dir(kept, args.out)
    print(f"\n{totals.report()}")
    print(f"\nwrote {sum(len(c.questions) for c in kept)} questions to {gold}")
    print(
        "This is now a committed artifact: every comparison from here is "
        "deterministic, offline and free.\n"
        f"  uv run chunking-lab score --corpus-dir {args.out} --strategy recursive:200"
    )
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
