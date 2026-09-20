"""Check the reviewer prompt against the eval drafts.

The prompt's examples must come from development drafts, and no phrase the prompt quotes
may appear in a held-out or clean draft. Otherwise a reviewer could score on those
drafts by recognising text it was shown, and the held-out number would mean nothing.

    uv run python tools/ai-sniffer/eval/check_prompt.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
AGENT = HERE.parent / "agent" / "ai-sniffer.md"
sys.path.insert(0, str(HERE))
import build_labels  # noqa: E402

_ENTRY = re.compile(r"^### (\S+)\s*$", re.M)
_EXAMPLE = re.compile(r'^\s*(?:[-*]\s*)?Example: "(.+)"\s*$', re.M)
# A single quoted word is vocabulary ("exactly" is in every draft); a phrase is text.
_QUOTED = re.compile(r'"([^"]+)"')
_PHRASE = re.compile(r"\S\s+\S")


def catalogue_habits(prompt: str) -> set[str]:
    return set(_ENTRY.findall(prompt))


def problems(
    prompt: str,
    meta: dict | None = None,
    drafts_dir: Path = build_labels.DRAFTS,
    habits: set[str] | frozenset[str] = build_labels.HABITS,
) -> list[str]:
    meta = build_labels.load_meta() if meta is None else meta
    found: list[str] = []

    entries = catalogue_habits(prompt)
    if missing := sorted(set(habits) - entries):
        found.append("catalogue has no entry for: " + ", ".join(missing))
    if extra := sorted(entries - set(habits)):
        found.append("catalogue entry isn't a label habit: " + ", ".join(extra))

    text = {
        name: " ".join(t for _, t in build_labels.prose_lines(drafts_dir / name)) for name in meta
    }
    development = [name for name in meta if meta[name]["role"] == "development"]
    scored_on = [name for name in meta if meta[name]["role"] != "development"]

    for example in _EXAMPLE.findall(prompt):
        needle = build_labels.normalise(example)
        if not any(needle in text[name] for name in development):
            found.append(f"example isn't in any development draft: {example!r}")
    # A quote can wrap onto the next line, so quotes are paired over the whole prompt.
    spans = (" ".join(q.split()) for q in _QUOTED.findall(prompt))
    for quoted in (q for q in spans if _PHRASE.search(q)):
        needle = build_labels.normalise(quoted)
        for name in scored_on:
            if needle in text[name]:
                found.append(f"quoted text appears in {name}: {quoted!r}")
    return found


def main() -> int:
    found = problems(AGENT.read_text(encoding="utf-8"))
    for line in found:
        print(line)
    print("prompt check passed" if not found else f"{len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
