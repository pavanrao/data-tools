"""Split a Markdown draft into prose paragraphs and everything else.

Everything else is carried through byte for byte: front matter, fences, tables,
HTML, lists, headings and block quotes. Only ``prose`` blocks are eligible for
injection, because a habit injected into a code fence would be a habit no reader
ever sees.

``render`` writes the document back out and, as it goes, updates each block's
``line`` to where it landed — so a label's line number refers to the file the
reader will actually be given.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Kind = Literal["prose", "blank", "verbatim"]

_FENCE = re.compile(r"^\s{0,3}(```+|~~~+)")
_HEADING = re.compile(r"^\s{0,3}(#{1,6}\s|={3,}\s*$|-{3,}\s*$)")
_LIST = re.compile(r"^\s*([-*+]\s|\d+[.)]\s)")
_QUOTE = re.compile(r"^\s*>")
_TABLE = re.compile(r"^\s*\|")
_HTML = re.compile(r"^\s{0,3}<")
_INDENTED = re.compile(r"^(\t| {4,})\S")

DEFAULT_WIDTH = 88


@dataclass(slots=True)
class Block:
    kind: Kind
    text: str
    line: int
    lines: list[str]
    #: the text as parsed, so render can tell a changed paragraph from an untouched one
    original: str = ""

    def changed(self) -> bool:
        return self.kind == "prose" and self.text != self.original


def _is_verbatim(line: str) -> bool:
    return bool(
        _HEADING.match(line)
        or _LIST.match(line)
        or _QUOTE.match(line)
        or _TABLE.match(line)
        or _HTML.match(line)
        or _INDENTED.match(line)
    )


def parse(text: str) -> list[Block]:
    """Blocks in source order. Joining every block's ``lines`` reproduces ``text``."""
    lines = text.split("\n")
    if lines and lines[-1] == "":  # the file's final newline; render puts it back
        lines = lines[:-1]

    blocks: list[Block] = []
    i, n = 0, len(lines)

    # Front matter, only when the very first line opens it.
    if n and lines[0].rstrip() == "---":
        for j in range(1, n):
            if lines[j].rstrip() in ("---", "..."):
                blocks.append(Block("verbatim", "", 1, lines[0 : j + 1]))
                i = j + 1
                break

    while i < n:
        line = lines[i]
        start = i + 1

        if not line.strip():
            blocks.append(Block("blank", "", start, [line]))
            i += 1
            continue

        fence = _FENCE.match(line)
        if fence:
            marker = fence[1][0] * 3
            run = [line]
            i += 1
            while i < n:
                run.append(lines[i])
                closed = lines[i].lstrip().startswith(marker)
                i += 1
                if closed:
                    break
            blocks.append(Block("verbatim", "", start, run))
            continue

        if _is_verbatim(line):
            run = []
            while i < n and lines[i].strip() and not _FENCE.match(lines[i]):
                run.append(lines[i])
                i += 1
            blocks.append(Block("verbatim", "", start, run))
            continue

        # A prose paragraph: consecutive lines until a blank, a fence or a
        # verbatim opener.
        run = []
        while i < n and lines[i].strip():
            if _FENCE.match(lines[i]) or _is_verbatim(lines[i]):
                break
            run.append(lines[i])
            i += 1
        joined = " ".join(x.strip() for x in run)
        blocks.append(Block("prose", joined, start, run, original=joined))

    return blocks


def wrap(text: str, width: int = DEFAULT_WIDTH) -> list[str]:
    """Greedy wrap, matching how the drafts in this repo are written."""
    out: list[str] = []
    for para_line in text.split("\n"):
        line = ""
        for word in para_line.split():
            if line and len(line) + len(word) + 1 > width:
                out.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        out.append(line)
    return out


def render(blocks: list[Block], width: int = DEFAULT_WIDTH) -> str:
    """Write the document back out, updating each block's ``line`` as it lands."""
    out: list[str] = []
    for block in blocks:
        block.line = len(out) + 1
        if block.kind == "prose" and block.changed():
            out.extend(wrap(block.text, width))
        else:
            out.extend(block.lines)
    return "\n".join(out) + "\n"
