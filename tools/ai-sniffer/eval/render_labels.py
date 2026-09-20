"""Render labels.json as LABELS.md, for a person to review."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent

ROLE_NOTE = {
    "development": (
        "The catalogue's examples are quoted from here, so recall on this draft is optimistic."
    ),
    "held-out": (
        "Never quoted in the prompt. Labelled before any model saw it. "
        "This is the recall that counts."
    ),
    "clean": (
        "Habits the rewrite left behind or introduced. "
        "Flags on anything *not* labelled here are false alarms."
    ),
}
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def main() -> None:
    data = json.loads((HERE / "labels.json").read_text())
    labels = data["labels"]
    roles = ["held-out", "development", "clean"]
    ORDER = sorted(data["drafts"], key=lambda name: roles.index(data["drafts"][name]["role"]))
    out = [
        "# ai-sniffer eval labels",
        "",
        "Generated from `labels.json` by `render_labels.py`; edit `labels.jsonl`, not this file.",
        "",
        "**How severity is scored.** `high` and `medium` count toward recall, so a reviewer that "
        "misses one loses a point. `low` is neutral: a defensible use either way, so flagging it "
        "neither earns nor costs anything.",
        "",
        "**Reviewing.** Disagree with a label by its id: wrong habit, wrong severity, not a habit "
        "at all, or a habit that isn't labelled.",
        "",
        "| Draft | Role | High | Medium | Low |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in ORDER:
        counts = {
            s: sum(1 for x in labels if x["draft"] == name and x["severity"] == s)
            for s in SEVERITY_RANK
        }
        role = data["drafts"][name]["role"]
        out.append(
            f"| `{name}` | {role} | {counts['high']} | {counts['medium']} | {counts['low']} |"
        )
    totals = {s: sum(1 for x in labels if x["severity"] == s) for s in SEVERITY_RANK}
    out.append(f"| **total** | | {totals['high']} | {totals['medium']} | {totals['low']} |")

    for name in ORDER:
        meta = data["drafts"][name]
        rows = sorted((x for x in labels if x["draft"] == name), key=lambda x: x["line"])
        out += [
            "",
            f"## `{name}`",
            "",
            f"**{meta['role']}** · {meta['source']}. {ROLE_NOTE[meta['role']]}",
        ]
        if "scored_line_ranges" in meta:
            spans = ", ".join(f"{a}–{b}" for a, b in meta["scored_line_ranges"])
            out += [
                "",
                f"Only lines {spans} are labelled and scored (sections 1, 4, 7, 10 and 13).",
            ]
        out += ["", "| Id | Line | Severity | Habit | Quote |", "| --- | --- | --- | --- | --- |"]
        for x in rows:
            quote = x["quote"].replace("|", "\\|")
            out.append(f"| `{x['id']}` | {x['line']} | {x['severity']} | {x['habit']} | {quote} |")

    (HERE / "LABELS.md").write_text("\n".join(out) + "\n")
    print(f"wrote LABELS.md with {len(labels)} labels")


if __name__ == "__main__":
    main()
