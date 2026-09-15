"""Score saved reviewer runs against labels.json. Deterministic, and never calls a model.

Runs live in ``eval/runs/<setup>/<draft stem>/run-<n>.md`` (a model's reply) or
``run-<n>.json`` (the linter's report). Changing the labels means rerunning this, not
the models.

A finding matches a label in the same draft when their normalised quotes share a run
of at least 20 characters, or one contains the other when the shorter is under 20.
High and medium labels count toward recall; low labels are neutral. An unmatched
finding is a false alarm on a clean draft, and is listed as unlabelled elsewhere,
since some of those will be habits the labels missed.

    uv run python tools/ai-sniffer/eval/score.py
"""

from __future__ import annotations

import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).parent
RUNS = HERE / "runs"
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE))
import build_labels  # noqa: E402

MIN_SHARED = 20
COUNTED = frozenset({"high", "medium"})
ROLES = ("held-out", "development", "clean")
# What each linter signal claims to be, where it names a catalogue habit at all.
LINTER_HABIT = {
    "hedge": "hedge",
    "emphasis-word": "emphasis-word",
    "reader-instruction": "reader-instruction",
    "one-sentence-paragraph": "dramatic-beat",
}


def quotes_match(a: str, b: str) -> bool:
    na, nb = build_labels.normalise(a), build_labels.normalise(b)
    shorter, longer = sorted((na, nb), key=len)
    if not shorter:
        return False
    if len(shorter) < MIN_SHARED:
        return shorter in longer
    m = SequenceMatcher(None, na, nb, autojunk=False).find_longest_match(0, len(na), 0, len(nb))
    return m.size >= MIN_SHARED


def score_run(
    draft: str,
    findings: list[dict],
    labels: list[dict],
    meta: dict,
    drafts_dir: Path,
    hand_only: bool = False,
) -> dict:
    mine = [
        x
        for x in labels
        if x["draft"] == draft and (not hand_only or x.get("source", "hand") == "hand")
    ]
    lines = build_labels.prose_lines(drafts_dir / draft)
    ranges = meta[draft].get("scored_line_ranges")
    clean = meta[draft]["role"] == "clean"

    caught: set[str] = set()
    neutral: set[str] = set()
    agrees: set[str] = set()
    false_alarms, unlabelled, set_aside = [], [], []
    not_in_draft = 0
    for f in findings:
        hits = build_labels.locate(lines, f["quote"])
        if hits:
            line = hits[0]
        else:
            line = f.get("line")
            not_in_draft += 1
        if ranges and not (isinstance(line, int) and any(lo <= line <= hi for lo, hi in ranges)):
            set_aside.append(f)
            continue
        matched = [x for x in mine if quotes_match(f["quote"], x["quote"])]
        if not matched:
            (false_alarms if clean else unlabelled).append({**f, "located_line": line})
            continue
        for x in matched:
            if x["severity"] in COUNTED:
                caught.add(x["id"])
                if f.get("habit") == x["habit"]:
                    agrees.add(x["id"])
            else:
                neutral.add(x["id"])

    order = {x["id"]: i for i, x in enumerate(mine)}
    return {
        "caught": sorted(caught, key=order.get),
        "recall_total": sum(1 for x in mine if x["severity"] in COUNTED),
        "neutral": sorted(neutral, key=order.get),
        "habit_agrees": len(agrees),
        "false_alarms": false_alarms,
        "unlabelled": unlabelled,
        "set_aside": set_aside,
        "quotes_not_in_draft": not_in_draft,
        "findings": len(findings),
    }


def summarise(runs: dict[int, dict[str, dict]], meta: dict) -> dict:
    """Per role: caught and false alarms as the lowest and highest total over runs."""
    out = {}
    for role in ROLES:
        per_run = []
        for results in runs.values():
            drafts = [d for d in results if meta[d]["role"] == role]
            if drafts:
                per_run.append(
                    (
                        sum(len(results[d]["caught"]) for d in drafts),
                        sum(results[d]["recall_total"] for d in drafts),
                        sum(len(results[d]["false_alarms"]) for d in drafts),
                    )
                )
        if per_run:
            out[role] = {
                "caught": {"min": min(r[0] for r in per_run), "max": max(r[0] for r in per_run)},
                "of": per_run[0][1],
                "false_alarms": {
                    "min": min(r[2] for r in per_run),
                    "max": max(r[2] for r in per_run),
                },
                "runs": len(per_run),
            }
    return out


def read_run(path: Path) -> tuple[list[dict], bool]:
    """Findings from a saved run, and whether the run's output could be read at all."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        report = json.loads(text)
        findings = [
            {"line": f["line"], "habit": LINTER_HABIT.get(f["signal"]), "quote": f["quote"]}
            for f in report["findings"]
        ]
        return findings, True
    from ai_sniffer.review import ReplyError, parse_reply

    try:
        findings, _, _ = parse_reply(text)
    except ReplyError:
        return [], False
    return findings, True


def score_all(labels: list[dict], meta: dict, hand_only: bool) -> dict:
    stems = {name.split(".")[0]: name for name in meta}
    setups = {}
    for setup_dir in sorted(p for p in RUNS.iterdir() if p.is_dir()):
        runs: dict[int, dict[str, dict]] = {}
        unreadable = []
        for draft_dir in sorted(p for p in setup_dir.iterdir() if p.is_dir()):
            draft = stems[draft_dir.name]
            for run_file in sorted(draft_dir.glob("run-*.*")):
                n = int(run_file.stem.split("-")[1])
                findings, ok = read_run(run_file)
                if not ok:
                    unreadable.append(str(run_file.relative_to(HERE)))
                runs.setdefault(n, {})[draft] = score_run(
                    draft, findings, labels, meta, build_labels.DRAFTS, hand_only
                )
        setups[setup_dir.name] = {
            "summary": summarise(runs, meta),
            "unreadable_runs": unreadable,
            "runs": runs,
        }
    return setups


def main() -> int:
    data = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))
    meta, labels = data["drafts"], data["labels"]
    RESULTS.mkdir(exist_ok=True)
    for variant, hand_only in (("all-labels", False), ("hand-labels", True)):
        result = score_all(labels, meta, hand_only)
        (RESULTS / f"{variant}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(variant)
        for setup, r in result.items():
            cells = []
            for role, s in r["summary"].items():
                caught, fa = s["caught"], s["false_alarms"]
                cells.append(
                    f"{role} {caught['min']}–{caught['max']}/{s['of']} "
                    f"false alarms {fa['min']}–{fa['max']}"
                )
            bad = f"  unreadable {len(r['unreadable_runs'])}" if r["unreadable_runs"] else ""
            print(f"  {setup:<14} " + " | ".join(cells) + bad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
