"""Place habits across a draft and write down where each one went.

The order is fixed by the seed, and injections are spread one per paragraph
before any paragraph gets a second, so a small count doesn't pile every habit
into the first paragraph that happened to accept one.

Line numbers are taken after rendering, because injecting into an early
paragraph moves every line below it. A label whose line came from the input
would point at the wrong place in the file the detector is given.

A quote is checked against the rendered draft with whitespace normalised, since
wrapping can put a line break inside it — and it is checked *after* every
injection, because a later one can rewrite the sentence an earlier one landed in.
A label that can no longer be found is dropped rather than shipped, since the eval
would score every detector at zero against it.
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import dataclass, replace

from slopify.document import DEFAULT_WIDTH, Block, parse, render
from slopify.habits import INJECTORS

#: Injected labels are all one severity. A template instance is the strong form of
#: its habit by construction, and calling some of them "low" would be a judgement —
#: the thing injection exists to avoid. ai-sniffer's scorer counts high and medium
#: towards recall, so this keeps every injected habit countable.
SEVERITY = "high"

#: More than this in one paragraph and the prose stops resembling a draft anyone
#: would write, which makes it a bad test of a detector aimed at drafts.
MAX_PER_PARAGRAPH = 3


@dataclass(frozen=True, slots=True)
class Label:
    habit: str
    quote: str
    line: int
    paragraph: int
    seed: int
    index: int = 1

    def as_json(self, draft: str) -> str:
        stem = draft.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return json.dumps(
            {
                "id": f"{stem}-{self.index:02d}",
                "draft": draft,
                "habit": self.habit,
                "severity": SEVERITY,
                "quote": self.quote,
                "source": "injected",
                "seed": self.seed,
                "line": self.line,
            }
        )


def flatten(text: str) -> str:
    """Whitespace as a reader sees it: one space, so a wrapped quote still matches."""
    return re.sub(r"\s+", " ", text).strip()


def _prose_indices(blocks: list[Block]) -> list[int]:
    return [i for i, b in enumerate(blocks) if b.kind == "prose" and b.text.strip()]


def slop(
    text: str,
    seed: int,
    count: int,
    habits: list[str] | None = None,
    width: int = DEFAULT_WIDTH,
) -> tuple[str, list[Label]]:
    """Inject up to ``count`` habits. Returns the new draft and one label each."""
    rng = random.Random(seed)
    blocks = parse(text)
    names = sorted(habits) if habits else sorted(INJECTORS)
    unknown = [n for n in names if n not in INJECTORS]
    if unknown:
        raise ValueError(f"no injector for {', '.join(unknown)}")

    targets = _prose_indices(blocks)
    if not targets or count <= 0:
        return render(blocks, width), []

    order = list(targets)
    rng.shuffle(order)
    per_paragraph: Counter[int] = Counter()
    placed: list[tuple[int, str, str]] = []

    while len(placed) < count:
        progress = False
        for index in order:
            if len(placed) >= count:
                break
            if per_paragraph[index] >= MAX_PER_PARAGRAPH:
                continue
            for name in rng.sample(names, len(names)):
                result = INJECTORS[name](blocks[index].text, rng)
                if result is None:
                    continue
                blocks[index].text = result.text
                placed.append((index, name, result.quote))
                per_paragraph[index] += 1
                progress = True
                break
        if not progress:
            break

    rendered = render(blocks, width)
    flat = flatten(rendered)
    lines = rendered.split("\n")

    labels: list[Label] = []
    for index, name, quote in placed:
        if flatten(quote) not in flat:
            continue  # a later injection rewrote the sentence this one landed in
        labels.append(Label(name, quote, _find_line(lines, blocks[index], quote), index, seed))
    return rendered, [replace(label, index=n) for n, label in enumerate(labels, start=1)]


def _find_line(lines: list[str], block: Block, quote: str) -> int:
    """The 1-based line the quote starts on, searched from the block it went into."""
    head = " ".join(flatten(quote).split()[:4])
    for offset in range(max(block.line - 1, 0), len(lines)):
        if head in flatten(" ".join(lines[offset : offset + 3])):
            return offset + 1
    return block.line
