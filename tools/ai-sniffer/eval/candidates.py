"""Group model findings that match no label into candidate labels for the review page.

A candidate is every unmatched finding on one draft whose quotes match each other,
across runs and setups. Its quote is the one the runs used most often. A candidate a
person accepts becomes a label with ``"source": "model"``, and recall is reported with
and without those labels, since a label that came from a model's finding flatters it.

Linter findings aren't candidates: the linter's lists are fixed, so its misses are
known without a review. Candidate ids come from the draft and the normalised quote, so
apply marks before regenerating candidates from new runs.

    uv run python tools/ai-sniffer/eval/candidates.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_labels  # noqa: E402
import score  # noqa: E402

NOT_CANDIDATES = frozenset({"linter"})


def _id(draft: str, quote: str) -> str:
    digest = hashlib.sha1(build_labels.normalise(quote).encode("utf-8")).hexdigest()[:6]
    return f"{build_labels.prefix_of(draft)}-c{digest}"


def gather(results: dict, meta: dict, drafts_dir: Path) -> list[dict]:
    lines = {name: build_labels.prose_lines(drafts_dir / name) for name in meta}
    groups: list[dict] = []
    for setup, result in results.items():
        if setup in NOT_CANDIDATES:
            continue
        for run, per_draft in result["runs"].items():
            for draft, scored in per_draft.items():
                for f in scored.get("unlabelled", []) + scored.get("false_alarms", []):
                    hits = build_labels.locate(lines[draft], f["quote"])
                    if len(hits) != 1:
                        continue
                    group = next(
                        (
                            g
                            for g in groups
                            if g["draft"] == draft
                            and any(score.quotes_match(f["quote"], q) for q in g["quotes"])
                        ),
                        None,
                    )
                    if group is None:
                        group = {"draft": draft, "quotes": Counter(), "habits": Counter(),
                                 "severities": Counter(), "lines": {}, "runs": set()}  # fmt: skip
                        groups.append(group)
                    group["quotes"][f["quote"]] += 1
                    group["lines"].setdefault(f["quote"], hits[0])
                    group["habits"][f.get("habit")] += 1
                    group["severities"][f.get("severity")] += 1
                    group["runs"].add((setup, run))

    out = []
    for g in groups:
        # Most-used quote; ties go to the one seen first.
        quote = max(g["quotes"], key=lambda q: (g["quotes"][q], -list(g["quotes"]).index(q)))
        raised_by = Counter(setup for setup, _ in g["runs"])
        out.append(
            {
                "id": _id(g["draft"], quote),
                "draft": g["draft"],
                "line": g["lines"][quote],
                "quote": quote,
                "habits": dict(g["habits"].most_common()),
                "severities": dict(g["severities"].most_common()),
                "raised_by": dict(sorted(raised_by.items())),
                "runs": len(g["runs"]),
            }
        )
    out.sort(key=lambda c: (-c["runs"], c["draft"], c["line"]))
    return out


def main() -> int:
    results = json.loads((score.RESULTS / "all-labels.json").read_text(encoding="utf-8"))
    meta = build_labels.load_meta()
    found = gather(results, meta, build_labels.DRAFTS)
    (HERE / "candidates.json").write_text(
        json.dumps(found, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    by_draft = Counter(c["draft"] for c in found)
    print(f"{len(found)} candidates")
    for draft in meta:
        print(f"  {draft:<36} {by_draft.get(draft, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
