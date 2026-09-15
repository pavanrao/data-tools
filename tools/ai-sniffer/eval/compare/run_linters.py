"""Run other open-source prose linters on the eval drafts and score them like ai-sniffer.

Every tool gets the same input: Markdown drafts as they are, and HTML drafts as a
Markdown view that keeps each paragraph on its source line, with inline code kept as
text. `ai-sniffer check` runs on the same views, so no tool is judged on markup
another tool never saw.

Each tool's output is reduced to findings (line, quote, rule) and written to
runs/<tool>/<draft>/run-1.md in the shape score.py reads. A quote is the text the
tool matched, never the surrounding line, because a whole line would overlap a label
on that line and count as a catch the tool didn't make. A lone character such as an
em dash stays a finding but can't match a label (score.MIN_CONTAINED).

The tools are installed outside the repo; see eval/README.md:

    uv run python tools/ai-sniffer/eval/compare/run_linters.py --tools-dir DIR
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
EVAL = HERE.parent
sys.path.insert(0, str(EVAL))
sys.path.insert(0, str(EVAL / "review"))
import build_labels  # noqa: E402
from build_page import _blocks_html  # noqa: E402

VERSIONS = {
    "slopless": "npm slopless@0.2.38",
    "wsc": "npm wsc-lint@1.3.0",
    "slop": "github bheijden/slop@9a6864e0d061",
    "vale": "vale 3.21.0 with vale-ai-tells v1.37.0",
    "slopscore": "pip slopscore-lint==0.14.0 (lean core)",
    "slop-lint": "npm slop-lint@0.8.0",
    "sloplint": "gem sloplint 0.7.0 on Homebrew Ruby 4.0.7",
}


def markdown_view(path: Path) -> str:
    """Markdown as is; HTML as its prose blocks, each on the line it starts on."""
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        return raw
    lines = [""] * (raw.count("\n") + 1)
    for block in _blocks_html(raw):
        text = ("## " + block["text"]) if block["heading"] else block["text"]
        i = block["start"] - 1
        lines[i] = f"{lines[i]} {text}".strip()
    return "\n".join(lines)


def _line_of(source: str, quote: str, fallback: int = 1) -> int:
    needle = quote.strip()
    at = source.find(needle) if needle else -1
    return source.count("\n", 0, at) + 1 if at >= 0 else fallback


def _slopless(output: str, source: str) -> list[dict]:
    found = []
    for file in json.loads(output):
        for m in file["messages"]:
            a, b = m["range"]
            found.append({"line": m["line"], "quote": source[a:b], "rule": m["ruleId"]})
    return found


def _wsc(output: str, source: str) -> list[dict]:
    found = []
    for file in json.loads(output):
        for category, issues in file["issues"].items():
            for issue in issues:
                # Each category names its text differently; long sentences arrive truncated.
                stored = next(
                    issue[k] for k in ("text", "word", "phrase", "sentence") if k in issue
                )
                a, n = issue.get("index"), issue.get("length")
                sliced = source[a : a + n] if a is not None and n else ""
                prefix = stored.rstrip(".").rstrip()[:8]
                quote = sliced if sliced and sliced.startswith(prefix) else stored
                line = source.count("\n", 0, a) + 1 if sliced == quote else _line_of(source, quote)
                found.append({"line": line, "quote": quote, "rule": category})
    return found


def _slop(output: str, source: str) -> list[dict]:
    found = []
    for file in json.loads(output)["files"]:
        for f in file["findings"]:
            quote = f.get("match") or ""
            found.append({"line": f.get("line") or _line_of(source, quote), "quote": quote,
                          "rule": f["rule"]})  # fmt: skip
    return found


def _vale(output: str, source: str) -> list[dict]:
    return [
        {"line": alert["Line"], "quote": alert["Match"], "rule": alert["Check"]}
        for alerts in json.loads(output or "{}").values()
        for alert in alerts
    ]


def _slopscore(output: str, source: str) -> list[dict]:
    # Character offsets are counted after slopscore strips markup, so place by text.
    return [
        {"line": _line_of(source, e["span"]), "quote": e["span"], "rule": e["rule_id"]}
        for e in json.loads(output).get("evidence", [])
    ]


_SLOP_LINT_LINE = re.compile(r"^\s+(\d+): (\S+) (.*)$")


def _slop_lint(output: str, source: str) -> list[dict]:
    found = []
    for line in output.splitlines():
        m = _SLOP_LINT_LINE.match(line)
        if not m:
            continue
        number, rest = int(m[1]), m[3]
        if rest.startswith("em-dash"):
            quote = "—"
        else:
            quoted = re.search(r'"([^"]+)"', rest)
            quote = quoted[1] if quoted else rest
        rule = "em-dash" if quote == "—" else (rest.split('"')[0].strip() or "construction")
        found.append({"line": number, "quote": quote, "rule": rule})
    return found


def _sloplint(output: str, source: str) -> list[dict]:
    notes = json.loads(output or "[]")
    if isinstance(notes, dict):  # an object keyed by path when several files are scanned
        notes = [n for per_path in notes.values() for n in per_path]
    return [{"line": n["line"], "quote": n["excerpt"], "rule": n["rule"]} for n in notes]


ADAPTERS = {
    "slopless": _slopless,
    "wsc": _wsc,
    "slop": _slop,
    "vale": _vale,
    "slopscore": _slopscore,
    "slop-lint": _slop_lint,
    "sloplint": _sloplint,
}


def commands(tools: Path, file: Path) -> dict[str, list[str]]:
    bins = tools / "node_modules" / ".bin"
    return {
        "slopless": [str(bins / "slopless"), str(file)],
        "wsc": [str(bins / "wsc"), "check", str(file), "--format", "json"],
        "slop": [str(bins / "slop"), "check", "--format", "json", str(file)],
        "vale": [
            str(tools / "bin" / "vale"),
            "--config",
            str(tools / ".vale.ini"),
            "--output=JSON",
            str(file),
        ],  # fmt: skip
        "slopscore": [
            "uvx",
            "--from",
            "slopscore-lint==0.14.0",
            "slopscore-lint",
            "scan",
            str(file),
            "--format",
            "json",
        ],  # fmt: skip
        "slop-lint": [
            "node",
            str(tools / "node_modules" / "slop-lint" / "slop-lint.mjs"),
            str(file),
        ],
        "sloplint": ["env", f"GEM_HOME={tools / 'gems'}", "/opt/homebrew/opt/ruby/bin/ruby",
                     str(tools / "gems" / "bin" / "sloplint"), "-o", "json", "check",
                     "--markdown", str(file)],  # fmt: skip
    }


def write_run(path: Path, findings: list[dict]) -> None:
    entries = [
        {
            "line": f["line"],
            "habit": None,
            "severity": "n/a",
            "quote": f["quote"],
            "rule": f["rule"],
            "why": "",
        }  # fmt: skip
        for f in findings
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"findings": entries}, ensure_ascii=False, indent=1)
    path.write_text(f"```json\n{body}\n```\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tools-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    from ai_sniffer.document import read
    from ai_sniffer.signals import check

    meta = build_labels.load_meta()
    with tempfile.TemporaryDirectory() as tmp:
        for draft in meta:
            view = markdown_view(build_labels.DRAFTS / draft)
            stem = draft.split(".")[0]
            file = Path(tmp) / f"{stem}.md"
            file.write_text(view, encoding="utf-8")
            report = check(read(file))
            ours = [{"line": f.line, "quote": f.quote, "rule": f.signal} for f in report.findings]
            write_run(EVAL / "runs" / "ai-sniffer-check-md" / stem / "run-1.md", ours)
            counts = {"ai-sniffer-check-md": len(ours)}
            for tool, cmd in commands(args.tools_dir, file).items():
                done = subprocess.run(cmd, capture_output=True, text=True, cwd=args.tools_dir)
                try:
                    found = ADAPTERS[tool](done.stdout, view)
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    print(
                        f"  {tool} on {draft}: output unreadable ({exc}); "
                        f"stderr: {done.stderr[:200]}"
                    )
                    continue
                write_run(EVAL / "runs" / tool / stem / "run-1.md", found)
                counts[tool] = len(found)
            print(draft, counts, flush=True)
    versions = {**VERSIONS, "ai-sniffer-check-md": "this repo, on the same Markdown views"}
    (EVAL / "runs" / "compare-manifest.json").write_text(
        json.dumps({"date": "2026-09-15", "tools": versions}, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
