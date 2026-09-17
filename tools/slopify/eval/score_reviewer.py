#!/usr/bin/env python3
"""Score a model reviewer's findings against slopify's injected labels.

The reviewer quotes; slopify knows what it put there and where. A habit counts as
caught when the reviewer's quote and the injected quote share the same stretch of
text, which is the same matching rule ai-sniffer's own eval uses — a 20-character
shared run, or containment either way once the quote is long enough to be specific.

Findings the reviewer already made on the *untouched* draft are discounted first,
counted rather than merely collected, so a second instance of a habit the prose
already had is still credited to the injection that added it.

    uv run python tools/slopify/eval/score_reviewer.py RUN_DIR [TOOL]

With TOOL, it reads NAME.TOOL.findings.json and SOURCE.TOOL.findings.json instead,
which is what `run_linters.py --drafts-dir` writes for the other linters. Those tools
report their own rule names rather than catalogue habits, so the `named` column is
zero for them by construction and only `caught` is comparable.

RUN_DIR holds, per draft: NAME.labels.jsonl (from slopify) and NAME.findings.json
(from the reviewer), plus baseline-SOURCE.findings.json for each untouched source.

**Tell the reviewer not to run the linter.** In the first run one agent reported that
it had run `ai-sniffer check --json` over its drafts "as a hint" before reviewing
them, which makes the two detectors dependent and the comparison meaningless. The
prompt had not forbidden it. Measured by dropping those drafts, the effect was not
detectable at that sample size, but that is luck rather than method — see docs/014
section 5d.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

MIN_SHARED = 20
MIN_CONTAINED = 4


def flat(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    for bad, good in (("’", "'"), ("“", '"'), ("”", '"'), ("—", "-")):
        text = text.replace(bad, good)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text.lower()).split())


def matches(a: str, b: str) -> bool:
    """Same rule as ai-sniffer's scorer: a shared run, or containment."""
    a, b = flat(a), flat(b)
    if not a or not b:
        return False
    if len(a) >= MIN_CONTAINED and a in b:
        return True
    if len(b) >= MIN_CONTAINED and b in a:
        return True
    shortest, longest = sorted((a, b), key=len)
    return any(
        shortest[i : i + MIN_SHARED] in longest
        for i in range(0, max(1, len(shortest) - MIN_SHARED + 1))
    )


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    text = re.sub(r"^```(?:json)?\n|\n```$", "", text)  # a fenced reply, sometimes
    data = json.loads(text)
    return data if isinstance(data, list) else data.get("findings", [])


def discount(found: list[dict], already: list[dict]) -> list[dict]:
    """Drop findings the reviewer also made on the untouched draft, one for one."""
    remaining = Counter((f.get("habit", ""), flat(f.get("quote", ""))) for f in already)
    kept = []
    for finding in found:
        key = (finding.get("habit", ""), flat(finding.get("quote", "")))
        if remaining[key]:
            remaining[key] -= 1
        else:
            kept.append(finding)
    return kept


def main(run: Path, tool: str = "") -> int:
    suffix = f".{tool}" if tool else ""
    injected: Counter[str] = Counter()
    caught: Counter[str] = Counter()
    named: Counter[str] = Counter()  # caught *and* called the right habit
    drafts = sorted(run.glob("*.labels.jsonl"))
    if not drafts:
        print(f"no *.labels.jsonl under {run}", file=sys.stderr)
        return 2

    per_source: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for labels_path in drafts:
        stem = labels_path.name[: -len(".labels.jsonl")]
        labels = load(labels_path)
        found = load(run / f"{stem}{suffix}.findings.json")
        source = stem.rsplit("--", 1)[0]
        baseline = f"{source}{suffix}.findings.json" if tool else f"baseline-{source}.findings.json"
        found = discount(found, load(run / baseline))
        for label in labels:
            injected[label["habit"]] += 1
            per_source[source][0] += 1
            hit = [f for f in found if matches(f.get("quote", ""), label["quote"])]
            if hit:
                caught[label["habit"]] += 1
                per_source[source][1] += 1
                if any(f.get("habit") == label["habit"] for f in hit):
                    named[label["habit"]] += 1

    print(f"{'habit':<20}{'injected':>9}{'caught':>8}{'named':>7}")
    for habit in sorted(injected):
        print(f"{habit:<20}{injected[habit]:>9}{caught[habit]:>8}{named[habit]:>7}")
    print(
        f"{'total':<20}{sum(injected.values()):>9}{sum(caught.values()):>8}{sum(named.values()):>7}"
    )
    print(f"\n{'source':<36}{'injected':>9}{'caught':>8}")
    for source, (n, hit) in sorted(per_source.items()):
        print(f"{source:<36}{n:>9}{hit:>8}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) == 3 else ""))
