"""Build the label review page from labels.json and the pinned drafts.

Each label is shown inside the paragraph it came from, with the quote highlighted,
so it can be judged without opening the draft. The page stores marks by label id in
the artifact's database, which is why ids must never move (see build_labels.py).

    uv run python tools/ai-sniffer/eval/review/build_page.py

writes review/label-proof.html, which is republished to the same artifact URL.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
EVAL = HERE.parent
TEMPLATE = HERE / "template.html"
OUTPUT = HERE / "label-proof.html"

sys.path.insert(0, str(EVAL))
from build_labels import HABITS  # noqa: E402

_BLOCK = re.compile(
    r"<(p|li|h1|h2|h3|h4|blockquote|figcaption|td|th|dd|dt|summary|caption)\b[^>]*>(.*?)</\1>",
    re.S | re.I,
)
_SKIP = re.compile(r"<(style|pre|script|svg)\b.*?</\1>", re.S | re.I)
_FOLD = {"‘": "'", "’": "'", "“": '"', "”": '"', "—": "-", "–": "-"}


def _clean(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").replace("**", "")
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _blocks_html(raw: str) -> list[dict]:
    raw = _SKIP.sub(lambda m: "\n" * m.group(0).count("\n"), raw)
    out = []
    for m in _BLOCK.finditer(raw):
        start = raw.count("\n", 0, m.start()) + 1
        text = _clean(m.group(2))
        if text:
            out.append(
                {
                    "start": start,
                    "end": start + m.group(0).count("\n"),
                    "text": text,
                    "heading": m.group(1).lower() in {"h2", "h3"},
                }
            )
    return out


def _blocks_md(raw: str) -> list[dict]:
    out: list[dict] = []
    buf: list[str] = []
    buf_start, fence, front_matter = 0, False, 0 if raw.startswith("---") else 2

    def flush(end: int) -> None:
        if buf:
            joined = " ".join(buf)
            heading = joined.startswith("#")
            body = joined.lstrip("#").strip() if heading else re.sub(r"^\s*[-*]\s+", "", joined)
            if text := _clean(body):
                out.append({"start": buf_start, "end": end, "text": text, "heading": heading})
            buf.clear()

    for n, line in enumerate(raw.split("\n"), 1):
        s = line.strip()
        if front_matter < 2:
            front_matter += s == "---"
            continue
        if s.startswith("```"):
            flush(n - 1)
            fence = not fence
            continue
        if fence or s.startswith("|"):
            flush(n - 1)
            continue
        if not s or s.startswith("#") or re.match(r"^[-*]\s", s):
            flush(n - 1)
            if not s:
                continue
        if not buf:
            buf_start = n
        buf.append(s)
        if s.startswith("#"):
            flush(n)
    flush(n)
    return out


def _find_span(text: str, quote: str) -> tuple[int, int] | None:
    """Match ignoring whitespace, case, curly quotes and dash style; offsets are into text."""

    def fold(ch: str) -> str:
        return _FOLD.get(ch, ch).lower()

    keep = [(i, fold(c)) for i, c in enumerate(text) if not c.isspace() and c not in "`*"]
    hay = "".join(c for _, c in keep)
    bare = html.unescape(re.sub(r"<[^>]+>", "", quote))
    needle = "".join(fold(c) for c in bare if not c.isspace() and c not in "`*")
    at = hay.find(needle) if needle else -1
    if at == -1:
        return None
    return keep[at][0], keep[at + len(needle) - 1][0] + 1


def _locate(
    raw: str, blocks: list[dict], line: int, quote: str
) -> tuple[str, tuple[int, int]] | None:
    body = [b for b in blocks if not b["heading"]]
    idx = next((i for i, b in enumerate(body) if b["start"] <= line <= b["end"]), None)
    if idx is None and body:
        idx = min(range(len(body)), key=lambda i: abs(body[i]["start"] - line))
    if idx is not None:
        windows = [body[idx : idx + w] for w in (1, 2, 3)] + [body[max(0, idx - 1) : idx + 2]]
        for window in windows:
            text = " ".join(b["text"] for b in window)
            if span := _find_span(text, quote):
                return text, span
    # Headings are labelled too, and text in a bare <div> isn't a block above.
    for b in blocks:
        if (
            b["heading"]
            and b["start"] <= line <= b["end"]
            and (span := _find_span(b["text"], quote))
        ):
            return b["text"], span
    lines = raw.split("\n")
    window = "\n".join(lines[max(0, line - 4) : line + 8])
    window = re.sub(r"</?(div|ul|ol|li|p)\b[^>]*>", "\n\n", window)
    for part in re.split(r"\n\s*\n", window):
        text = _clean(part)
        if span := _find_span(text, quote):
            return text, span
    return None


def _title(raw: str, name: str) -> str:
    m = re.search(r"<title>([^<]*)</title>", raw) or re.search(
        r'^title:\s*"?([^"\n]*)"?', raw, re.M
    )
    return html.unescape(m.group(1).strip()) if m else name


def with_context(data: dict, drafts_dir: Path) -> dict:
    """The page payload: drafts with titles, and labels with heading, before, match and after."""
    drafts, labels, misses = {}, [], []
    for name, meta in data["drafts"].items():
        raw = (drafts_dir / name).read_text(encoding="utf-8")
        blocks = _blocks_html(raw) if name.endswith((".html", ".htm")) else _blocks_md(raw)
        drafts[name] = {**meta, "title": _title(raw, name)}
        for x in (x for x in data["labels"] if x["draft"] == name):
            found = _locate(raw, blocks, x["line"], x["quote"])
            if found is None:
                misses.append(x["id"])
                continue
            text, (a, b) = found
            heading = next(
                (h["text"] for h in reversed(blocks) if h["heading"] and h["start"] <= x["line"]),
                "",
            )
            labels.append(
                {**x, "heading": heading, "before": text[:a], "match": text[a:b], "after": text[b:]}
            )
    if misses:
        raise SystemExit("couldn't highlight these quotes in their drafts: " + ", ".join(misses))
    return {"drafts": drafts, "habits": sorted(HABITS), "labels": labels}


def render(template: str, payload: dict, commit: str) -> str:
    # "</" inside a script block would end it early; "<\/" is the same string to JSON.
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    head, tail = template.replace("__COMMIT__", commit).split("__DATA__", 1)
    return head + data + tail


def labels_commit() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", "labels.jsonl"],
        cwd=EVAL,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "uncommitted"


def main() -> None:
    data = json.loads((EVAL / "labels.json").read_text(encoding="utf-8"))
    payload = with_context(data, EVAL / "drafts")
    OUTPUT.write_text(
        render(TEMPLATE.read_text(encoding="utf-8"), payload, labels_commit()), encoding="utf-8"
    )
    print(
        f"wrote {OUTPUT} with {len(payload['labels'])} labels from {len(payload['drafts'])} drafts"
    )


if __name__ == "__main__":
    main()
