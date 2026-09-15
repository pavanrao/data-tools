"""Build and verify eval/labels.json from eval/labels.jsonl and eval/drafts.json.

Every quote must occur exactly once in its draft after normalisation, or the build
fails. Line numbers are computed from the draft rather than typed, so they can't
drift from the text they point at.

Ids are stored with each label and never derived from its position. A new label takes
the next unused number for its draft, and a dropped label's id is retired, so a mark
made on the review page stays on the quote it was made on.

Severity decides how a label is scored:
  high, medium  counted in recall; a reviewer that misses one loses a point
  low           neutral; flagging it neither earns nor costs anything

Held-out labels were written before any model had been shown either held-out post.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DRAFTS = HERE / "drafts"
LABELS_FILE = HERE / "labels.jsonl"
META_FILE = HERE / "drafts.json"

HABITS = frozenset(
    {
        "antithesis",
        "fragment",
        "triad",
        "dramatic-beat",
        "closer",
        "restatement",
        "cliche-emphasis",
        "generic-detail",
        "reader-instruction",
        "hedge",
        "emphasis-word",
    }
)
SEVERITIES = frozenset({"high", "medium", "low"})
ROLES = frozenset({"development", "held-out", "clean"})
STATUSES = frozenset({"active", "dropped"})
SOURCES = frozenset({"hand", "model"})
_ID = re.compile(r"(?P<prefix>.+)-(?P<number>\d{2,})")


def load_meta(path: Path = META_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_labels(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def save_labels(path: Path, labels: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in labels), encoding="utf-8"
    )


def prefix_of(draft: str) -> str:
    return draft.split(".")[0]


def next_id(labels: list[dict], draft: str) -> str:
    """One past the highest number ever used for this draft, dropped labels included."""
    prefix = prefix_of(draft)
    used = [
        int(m["number"]) for x in labels if (m := _ID.fullmatch(x["id"])) and m["prefix"] == prefix
    ]
    return f"{prefix}-{max(used, default=0) + 1:02d}"


def normalise(text: str) -> str:
    """The comparison form shared by labels, drafts and reviewer findings."""
    text = html.unescape(text)
    # Inline tags vanish without leaving a space, so "<code>x</code>." stays "x.".
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links
    text = text.replace("`", "").replace("*", "")
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"\s*[—–]\s*", " - ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip().lower()


def prose_lines(path: Path) -> list[tuple[int, str]]:
    """(line number, normalised text) for prose lines, skipping code, style and svg."""
    out: list[tuple[int, str]] = []
    in_block = False
    front_matter = 0
    for number, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if path.suffix == ".md":
            if raw.strip() == "---" and front_matter < 2:
                front_matter += 1
                continue
            if front_matter < 2:
                continue
            if raw.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                continue
        else:
            if re.search(r"<(style|pre|script|svg)\b", raw):
                in_block = True
            if in_block:
                if re.search(r"</(style|pre|script|svg)>", raw):
                    in_block = False
                continue
        text = normalise(raw)
        if text:
            out.append((number, text))
    return out


def locate(lines: list[tuple[int, str]], quote: str) -> list[int]:
    """Every line on which the normalised quote begins."""
    joined, starts = "", []
    for number, text in lines:
        starts.append((len(joined), number))
        joined += text + " "
    needle = normalise(quote)
    hits, i = [], joined.find(needle)
    while i != -1:
        hits.append(max(n for offset, n in starts if offset <= i))
        i = joined.find(needle, i + 1)
    return hits


def build(meta: dict, source: list[dict], drafts_dir: Path) -> dict:
    problems = []
    for name, info in meta.items():
        if info.get("role") not in ROLES:
            problems.append(f"{name} has role {info.get('role')!r}; use one of {sorted(ROLES)}")
    cache = {name: prose_lines(drafts_dir / name) for name in meta if (drafts_dir / name).exists()}
    seen: set[str] = set()
    labels, dropped = [], []
    for x in source:
        lid, draft = x["id"], x["draft"]
        if lid in seen:
            problems.append(f"{lid} is used twice")
        seen.add(lid)
        m = _ID.fullmatch(lid)
        if not m:
            problems.append(f"{lid} isn't <draft>-<number>")
        elif m["prefix"] != prefix_of(draft):
            problems.append(f"{lid} doesn't start with {prefix_of(draft)}-")
        if x["habit"] not in HABITS:
            problems.append(f"{lid}: unknown habit {x['habit']!r}")
        if x["severity"] not in SEVERITIES:
            problems.append(f"{lid}: unknown severity {x['severity']!r}")
        status = x.get("status", "active")
        if status not in STATUSES:
            problems.append(f"{lid}: unknown status {status!r}")
        if x.get("source", "hand") not in SOURCES:
            problems.append(f"{lid}: unknown source {x.get('source')!r}")
        if draft not in meta:
            problems.append(f"{lid}: {draft} isn't in drafts.json")
            continue
        if draft not in cache:
            problems.append(f"{lid}: {draft} isn't in {drafts_dir}")
            continue
        hits = locate(cache[draft], x["quote"])
        if len(hits) != 1:
            problems.append(f"{lid}: {len(hits)} matches for {x['quote']!r}")
            continue
        line = hits[0]
        ranges = meta[draft].get("scored_line_ranges")
        if ranges and not any(lo <= line <= hi for lo, hi in ranges):
            problems.append(f"{lid}: line {line} is outside the scored sections")
        entry = {"id": lid, "draft": draft, "line": line}
        entry |= {k: v for k, v in x.items() if k not in {"id", "draft", "status"}}
        (dropped if status == "dropped" else labels).append(entry)
    if problems:
        raise SystemExit("label problems:\n  " + "\n  ".join(problems))
    return {
        "drafts": meta,
        "scoring": {
            "match": "same draft; normalised quotes share a run of at least 20 characters, "
            "or one contains the other when a quote is shorter than 20",
            "recall_counts": ["high", "medium"],
            "neutral": ["low"],
        },
        "labels": labels,
        "dropped": dropped,
    }


def main() -> None:
    data = build(load_meta(), load_labels(LABELS_FILE), DRAFTS)
    (HERE / "labels.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    by_draft = {name: {"high": 0, "medium": 0, "low": 0} for name in data["drafts"]}
    for x in data["labels"]:
        by_draft[x["draft"]][x["severity"]] += 1
    print(
        f"{len(data['labels'])} labels, {len(data['dropped'])} dropped, "
        "every quote found exactly once"
    )
    for draft, c in by_draft.items():
        print(f"  {draft:<36} high {c['high']:>2}  medium {c['medium']:>2}  low {c['low']:>2}")


if __name__ == "__main__":
    main()
