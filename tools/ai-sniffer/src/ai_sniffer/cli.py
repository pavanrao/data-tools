"""Find the habits that make prose read as machine-written, and quote each one.

    ai-sniffer check FILE [--json] [--strict]
    ai-sniffer review FILE [--json] [--model MODEL] [--no-linter]

Exit codes:

    0   done (findings or not)
    1   check --strict, and there was at least one finding
    2   the file couldn't be read, or review has no model to run
    3   review: the model's reply had no usable JSON

A finding is a place to look, not a verdict about who wrote the text.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import review
from .document import read
from .signals import Report, check


def render(path: Path, report: Report) -> str:
    m = report.metrics
    rhythm, detail = m["sentence_length"], m["detail"]
    lines = [
        str(path),
        f"  {m['words']} words, {m['sentences']} sentences, {m['paragraphs']} paragraphs",
        f"  contractions  {m['contractions_per_100_words']} per 100 words",
        f"  sentences     mean {rhythm['mean']} words, variation {rhythm['cv']}",
        f"  detail        {detail['per_100_words']} per 100 words "
        f"({detail['numbers']} numbers, {detail['dates']} dates, "
        f"{detail['quoted']} quoted, {detail['code']} code)",
        "",
    ]
    if report.findings:
        width = max(len(str(f.line)) for f in report.findings)
        lines.append(f"findings ({len(report.findings)})")
        lines += [f"  {f.line:>{width}}  {f.signal}  {f.quote}" for f in report.findings]
    else:
        lines.append("findings: none")
    if report.closers:
        lines += ["", "section closers, for a reader to judge"]
        lines += [f"  {c.line}  {c.text}" for c in report.closers]
    return "\n".join(lines)


def _check(args: argparse.Namespace) -> int:
    try:
        doc = read(args.file)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ai-sniffer: can't check {args.file}: {exc}", file=sys.stderr)
        return 2
    report = check(doc)
    if args.json:
        payload = {"path": str(args.file), "format": doc.format, **report.to_dict()}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render(args.file, report))
    return 1 if args.strict and report.findings else 0


def render_review(result: dict) -> str:
    lines = [result["path"], f"  model {result['model']}", ""]
    findings = result["findings"]
    if findings:
        width = max(len(str(f["line"])) for f in findings)
        lines.append(f"findings ({len(findings)})")
        lines += [
            f"  {f['line']:>{width}}  {f['severity']}  {f['habit']}  {f['quote']}" for f in findings
        ]
    else:
        lines.append("findings: none")
    if result["invalid"]:
        lines.append(f"  ({len(result['invalid'])} entries in the reply were missing fields)")
    if result["summary"]:
        lines += ["", result["summary"]]
    return "\n".join(lines)


def _review(args: argparse.Namespace) -> int:
    model = review.resolve_model(args.model)
    if model is None:
        print(f"ai-sniffer: {review.NO_MODEL}", file=sys.stderr)
        return 2
    try:
        doc = read(args.file)  # an unreadable or unsupported file fails before any model call
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ai-sniffer: can't review {args.file}: {exc}", file=sys.stderr)
        return 2
    report = None if args.no_linter else check(doc).to_dict()
    try:
        result = review.run(args.file, model, report)
    except review.ReplyError as exc:
        start = getattr(exc, "reply", "")[:500]
        print(f"ai-sniffer: {exc}. The reply started:\n{start}", file=sys.stderr)
        return 3
    except review.Unavailable as exc:
        print(f"ai-sniffer: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_review(result))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Find the habits that make prose read as machine-written, and quote each one."""
    parser = argparse.ArgumentParser(prog="ai-sniffer", description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    check_cmd = commands.add_parser("check", help="count the habits a pattern can find")
    check_cmd.add_argument("file", type=Path, help="a .md or .html draft")
    check_cmd.add_argument("--json", action="store_true", help="print JSON")
    check_cmd.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    check_cmd.set_defaults(run=_check)

    review_cmd = commands.add_parser("review", help="run the reviewer prompt through a model")
    review_cmd.add_argument("file", type=Path, help="a .md or .html draft")
    review_cmd.add_argument("--json", action="store_true", help="print JSON")
    review_cmd.add_argument("--model", help="LiteLLM model string; else DATA_TOOLS_CHAT_MODEL")
    review_cmd.add_argument(
        "--no-linter", action="store_true", help="don't send the linter's report to the model"
    )
    review_cmd.set_defaults(run=_review)

    args = parser.parse_args(argv)
    return args.run(args)
