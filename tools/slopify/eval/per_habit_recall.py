"""Per-habit recall for a detector, against injected ground truth.

Reproduces the table in docs/014 section 5. One habit is injected at a time, so a
finding can only be credited to the habit that was put there.

    uv run python tools/slopify/eval/per_habit_recall.py DRAFT [DRAFT ...]

Ideally the drafts are prose no model wrote (docs/014 section 2). Where that is not
available, every finding the detector already makes on the untouched draft is
recorded first and subtracted, so a habit that was there before the injection
cannot be credited to it. That makes the result honest on contaminated source; it
does not make the source clean, because an injection landing on top of an existing
habit is still a site the detector had two reasons to flag.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEEDS = range(1, 11)
FINDING = re.compile(r"\s+(\d+)\s+([a-z-]+)\s+(.*)")


def flat(text: str) -> str:
    return " ".join(text.lower().split())


def run(*args: str) -> str:
    return subprocess.run(
        ["uv", "run", *args], cwd=REPO, capture_output=True, text=True, check=False
    ).stdout


def habits() -> list[str]:
    return [line.split()[0] for line in run("slopify", "habits").splitlines() if line.strip()]


def findings(path: Path) -> list[tuple[int, str, str]]:
    out = []
    for line in run("ai-sniffer", "check", str(path)).splitlines():
        match = FINDING.match(line)
        if match:
            out.append((int(match[1]), match[2], match[3]))
    return out


def baseline(path: Path) -> Counter[tuple[str, str]]:
    """What the detector says about the draft before anything is injected.

    Counted, not just collected, and matched on habit and text rather than line,
    because an injection above a pre-existing finding moves it down the file. The
    count matters: the human sources already contain the word "exactly", so
    injecting another one has to show up as a second instance and not be cancelled
    by the first.
    """
    return Counter((habit, flat(text)) for _, habit, text in findings(path))


def added(found: list[tuple[int, str, str]], already: Counter[tuple[str, str]]):
    """The findings this injection is responsible for, one instance at a time."""
    remaining = already.copy()
    new = []
    for line, habit, text in found:
        key = (habit, flat(text))
        if remaining[key]:
            remaining[key] -= 1
        else:
            new.append((line, habit, text))
    return new


def main(sources: list[Path]) -> int:
    injected: defaultdict[str, int] = defaultdict(int)
    quoted: defaultdict[str, int] = defaultdict(int)
    on_line: defaultdict[str, int] = defaultdict(int)
    workspace = Path(tempfile.mkdtemp())

    for source in sources:
        already = baseline(source)
        for habit in habits():
            for seed in SEEDS:
                draft, labels = workspace / "slopped.md", workspace / "labels.jsonl"
                labels.unlink(missing_ok=True)
                run(
                    "slopify",
                    "inject",
                    str(source),
                    "--seed",
                    str(seed),
                    "--count",
                    "1",
                    "--habit",
                    habit,
                    "--out",
                    str(draft),
                    "--labels",
                    str(labels),
                )
                records = (
                    [json.loads(x) for x in labels.read_text().splitlines() if x.strip()]
                    if labels.exists()
                    else []
                )
                if not records:
                    continue  # no site for this habit in this draft
                label = records[0]
                injected[habit] += 1
                # Only what the injection added: a finding the detector already
                # made on the untouched draft is not evidence about this habit.
                found = added(findings(draft), already)
                quote = flat(label["quote"])
                if any(flat(t) and (flat(t) in quote or quote in flat(t)) for _, _, t in found):
                    quoted[habit] += 1
                if any(abs(line - label["line"]) <= 1 for line, _, _ in found):
                    on_line[habit] += 1

    print(f"{'habit':<20}{'injected':>9}{'quoted':>8}{'on line':>9}")
    for habit in sorted(injected):
        print(f"{habit:<20}{injected[habit]:>9}{quoted[habit]:>8}{on_line[habit]:>9}")
    print(
        f"{'total':<20}{sum(injected.values()):>9}{sum(quoted.values()):>8}{sum(on_line.values()):>9}"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main([Path(a) for a in sys.argv[1:]]))
