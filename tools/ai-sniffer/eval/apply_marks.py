"""Apply marks from the label review page to labels.jsonl.

The page keeps marks in its artifact database. Claude saves them with ``read_db`` and
an output directory, which gives ``decisions/<label id>.json`` and
``missed/<doc id>.json``. Then:

    uv run python tools/ai-sniffer/eval/apply_marks.py MARKS_DIR [--dry-run]

keep     the label is marked reviewed
change   new habit or severity; the first values stay under ``was``
drop     the label stays in the file with status ``dropped``
no mark  left alone, and counts as keep
missed   a new label with the next id for its draft, once its quote is found

Applying the same export again changes nothing, so it's safe to rerun after more
marks. Nothing is written unless the result still builds.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_labels  # noqa: E402
import render_labels  # noqa: E402


@dataclass
class Result:
    labels: list[dict]
    summary: dict[str, int] = field(
        default_factory=lambda: {
            "keep": 0,
            "change": 0,
            "drop": 0,
            "note": 0,
            "added": 0,
            "accepted": 0,
            "rejected": 0,
        }
    )
    skipped: list[str] = field(default_factory=list)


def read_marks(directory: Path) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    def collection(name: str) -> dict[str, dict]:
        folder = directory / name
        if not folder.is_dir():
            return {}
        files = sorted(folder.glob("*.json"))
        return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in files}

    return collection("decisions"), collection("missed"), collection("candidates")


def _review(verdict: str, at: str, note: str) -> dict:
    review = {"verdict": verdict, "at": at} if verdict else {"at": at}
    if note:
        review["note"] = note
    return review


def apply(
    labels: list[dict],
    decisions: dict[str, dict],
    missed: dict[str, dict],
    meta: dict,
    drafts_dir: Path,
    candidates: dict[str, dict] | None = None,
) -> Result:
    result = Result(copy.deepcopy(labels))
    index = {x["id"]: x for x in result.labels}

    unknown = sorted(set(decisions) - set(index))
    if unknown:
        raise SystemExit(
            "marks for labels that don't exist (have ids moved?): " + ", ".join(unknown)
        )

    for lid, mark in sorted(decisions.items()):
        label = index[lid]
        verdict, note, at = mark.get("verdict", ""), mark.get("note", ""), mark.get("updatedAt", "")
        if not verdict and not note:
            continue
        if verdict not in {"", "keep", "change", "drop"}:
            raise SystemExit(f"{lid}: unknown verdict {verdict!r}")
        if verdict == "change":
            habit, severity = (
                mark.get("habit", label["habit"]),
                mark.get("severity", label["severity"]),
            )
            if habit not in build_labels.HABITS or severity not in build_labels.SEVERITIES:
                raise SystemExit(
                    f"{lid}: change to unknown habit {habit!r} or severity {severity!r}"
                )
            if (habit, severity) != (label["habit"], label["severity"]) and "was" not in label:
                label["was"] = {"habit": label["habit"], "severity": label["severity"]}
            label["habit"], label["severity"] = habit, severity
        if verdict == "drop":
            label["status"] = "dropped"
        else:
            label.pop("status", None)
        label["review"] = _review(verdict, at, note)
        result.summary[verdict or "note"] += 1

    lines = {name: build_labels.prose_lines(drafts_dir / name) for name in meta}
    from_missed = {x["missed_id"]: x for x in result.labels if "missed_id" in x}
    for doc_id, item in sorted(missed.items(), key=lambda kv: (kv[1].get("createdAt", ""), kv[0])):
        if doc_id in from_missed:
            continue
        where = f"missed habit {item.get('quote', '')[:60]!r} on {item.get('draft')}"
        if item.get("draft") not in meta:
            result.skipped.append(f"{where}: draft isn't in drafts.json")
            continue
        if item.get("habit") not in build_labels.HABITS:
            result.skipped.append(
                f"{where}: habit {item.get('habit')!r} needs a catalogue name "
                f"(note: {item.get('note') or 'none'})"
            )
            continue
        hits = build_labels.locate(lines[item["draft"]], item["quote"])
        if len(hits) != 1:
            result.skipped.append(
                f"{where}: {len(hits)} matches in the draft; paste the exact text"
            )
            continue
        new = {
            "id": build_labels.next_id(result.labels, item["draft"]),
            "draft": item["draft"],
            "habit": item["habit"],
            "severity": item["severity"],
            "quote": item["quote"],
            "source": "hand",
            "missed_id": doc_id,
            "review": _review("added", item.get("createdAt", ""), item.get("note", "")),
        }
        result.labels.append(new)
        result.summary["added"] += 1

    by_candidate = {x["candidate_id"]: x for x in result.labels if "candidate_id" in x}
    for cid, mark in sorted((candidates or {}).items()):
        verdict, at, note = mark.get("verdict"), mark.get("updatedAt", ""), mark.get("note", "")
        existing = by_candidate.get(cid)
        if verdict == "reject":
            if existing is not None:
                existing["status"] = "dropped"
                existing["review"] = _review("rejected", at, note)
            result.summary["rejected"] += 1
            continue
        if verdict != "accept":
            continue
        if mark.get("habit") not in build_labels.HABITS:
            result.skipped.append(
                f"candidate {cid}: habit {mark.get('habit')!r} isn't a catalogue name"
            )
            continue
        if existing is None:
            hits = build_labels.locate(lines[mark["draft"]], mark["quote"])
            if len(hits) != 1:
                result.skipped.append(f"candidate {cid}: {len(hits)} matches in {mark['draft']}")
                continue
            existing = {
                "id": build_labels.next_id(result.labels, mark["draft"]),
                "draft": mark["draft"],
                "habit": mark["habit"],
                "severity": mark["severity"],
                "quote": mark["quote"],
                "source": "model",
                "candidate_id": cid,
            }
            result.labels.append(existing)
            by_candidate[cid] = existing
        existing.pop("status", None)
        existing["habit"], existing["severity"] = mark["habit"], mark["severity"]
        existing["review"] = _review("accepted", at, note)
        result.summary["accepted"] += 1

    for doc_id, label in from_missed.items():
        if doc_id not in missed:
            result.skipped.append(
                f"{label['id']} came from a missed habit that's no longer on the page; "
                "drop it on the page or remove it by hand"
            )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("marks", type=Path, help="directory saved by read_db")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args(argv)

    meta = build_labels.load_meta()
    decisions, missed, candidates = read_marks(args.marks)
    result = apply(
        build_labels.load_labels(build_labels.LABELS_FILE),
        decisions,
        missed,
        meta,
        build_labels.DRAFTS,
        candidates,
    )
    build_labels.build(meta, result.labels, build_labels.DRAFTS)  # refuses to write a broken file

    s = result.summary
    print(
        f"{len(decisions)} marks, {len(missed)} missed habits: keep {s['keep']}, "
        f"change {s['change']}, drop {s['drop']}, note only {s['note']}, added {s['added']}, "
        f"candidates accepted {s['accepted']}, rejected {s['rejected']}"
    )
    for line in result.skipped:
        print(f"  skipped: {line}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    build_labels.save_labels(build_labels.LABELS_FILE, result.labels)
    build_labels.main()
    render_labels.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
