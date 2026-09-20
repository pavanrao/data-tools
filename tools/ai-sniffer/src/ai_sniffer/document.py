"""Turn a Markdown or HTML draft into sections, paragraphs and sentences.

Only prose survives: front matter, code, tables and markup are dropped, and inline
code becomes the placeholder word ``CODE`` so a dotted name can't end a sentence.
Every sentence keeps the source line it starts on, because a finding is only
useful if the author can find it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal

CODE = "CODE"
Kind = Literal["prose", "item", "block"]  # block: HTML text outside <p> and <li>


@dataclass(frozen=True, slots=True)
class Sentence:
    line: int
    text: str


@dataclass(slots=True)
class Paragraph:
    line: int
    kind: Kind
    text: str
    sentences: list[Sentence]


@dataclass(slots=True)
class Section:
    heading: str
    line: int
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass(slots=True)
class Document:
    format: Literal["markdown", "html"]
    sections: list[Section]
    code_spans: int = 0

    def paragraphs(self) -> list[Paragraph]:
        return [p for s in self.sections for p in s.paragraphs]

    def sentences(self) -> list[Sentence]:
        return [s for p in self.paragraphs() for s in p.sentences]


# ---- sentences ----------------------------------------------------------------------------

_BOUNDARY = re.compile(r"([.!?]+)([\"”’')\]]*)(\s+)(?=[\"“‘(\[]?[A-Z0-9])")
_ABBREVIATIONS = frozenset(
    [
        "e.g.",
        "i.e.",
        "etc.",
        "vs.",
        "cf.",
        "approx.",
        "fig.",
        "no.",
        "dr.",
        "mr.",
        "mrs.",
        "ms.",
        "st.",
        "al.",
    ]
)


def split_sentences(text: str) -> list[tuple[int, str]]:
    """(offset, sentence) pairs. Splits at terminal punctuation before a capital or digit."""
    out: list[tuple[int, str]] = []
    start = 0
    for m in _BOUNDARY.finditer(text):
        before = text[start : m.end(1)].rsplit(None, 1)[-1].lower()
        if m.group(1) == "." and (before in _ABBREVIATIONS or re.fullmatch(r"[a-z]\.", before)):
            continue
        out.append((start, text[start : m.end(2)]))
        start = m.end(3)
    if text[start:].strip():
        out.append((start, text[start:].rstrip()))
    return out


class _Block:
    """Characters with the source line of each, so offsets map back to lines."""

    def __init__(self) -> None:
        self.chars: list[str] = []
        self.lines: list[int] = []

    def add(self, text: str, line: int) -> None:
        for ch in text:
            self.chars.append(ch)
            self.lines.append(line)
            if ch == "\n":
                line += 1

    def finish(self) -> tuple[str, list[int]]:
        text: list[str] = []
        lines: list[int] = []
        pending_space = False
        for ch, line in zip(self.chars, self.lines, strict=True):
            if ch.isspace():
                pending_space = bool(text)
                continue
            if pending_space:
                text.append(" ")
                lines.append(line)
                pending_space = False
            text.append(ch)
            lines.append(line)
        self.chars, self.lines = [], []
        return "".join(text), lines


def _paragraph(block: _Block, kind: Kind) -> Paragraph | None:
    text, lines = block.finish()
    if not text:
        return None
    sentences = [Sentence(lines[offset], s) for offset, s in split_sentences(text)]
    return Paragraph(lines[0], kind, text, sentences)


class _Builder:
    def __init__(self, fmt: Literal["markdown", "html"]) -> None:
        self.doc = Document(fmt, [Section("", 1)])

    def add(self, paragraph: Paragraph | None) -> None:
        if paragraph is not None:
            self.doc.sections[-1].paragraphs.append(paragraph)

    def heading(self, text: str, line: int) -> None:
        self.doc.sections.append(Section(text, line))

    def result(self) -> Document:
        first = self.doc.sections[0]
        if not first.paragraphs and len(self.doc.sections) > 1:
            self.doc.sections.pop(0)
        return self.doc


# ---- markdown -----------------------------------------------------------------------------

_MD_CODE = re.compile(r"`+[^`]*`+")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_SHORTCODE = re.compile(r"\{\{[<%].*?[%>]\}\}")
_MD_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def _md_inline(text: str, doc: Document) -> str:
    def code(_: re.Match[str]) -> str:
        doc.code_spans += 1
        return CODE

    text = _MD_CODE.sub(code, text)
    text = _MD_SHORTCODE.sub("", text)
    text = _MD_IMAGE.sub("", text)
    text = _MD_LINK.sub(r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("**", "").replace("*", "")


def parse_markdown(source: str) -> Document:
    build = _Builder("markdown")
    block, kind = _Block(), "prose"
    lines = source.split("\n")
    fence: str | None = None
    front_matter = lines[0].strip() in {"---", "+++"} if lines else False
    in_comment = False

    def flush() -> None:
        build.add(_paragraph(block, kind))

    for number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if front_matter:
            if number > 1 and stripped in {"---", "+++"}:
                front_matter = False
            continue
        if fence:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(("```", "~~~")):
            flush()
            fence = stripped[:3]
            continue
        if in_comment or stripped.startswith("<!--"):
            in_comment = "-->" not in stripped
            continue
        if not stripped or stripped.startswith("|"):
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            build.heading(_md_inline(stripped.lstrip("#").strip(), build.doc), number)
            continue
        if _MD_ITEM.match(raw):
            flush()
            kind = "item"
            raw = _MD_ITEM.sub("", raw)
        elif kind == "item" and not raw[:1].isspace():
            flush()
            kind = "prose"
        if not block.chars and kind != "item":
            kind = "prose"
        block.add(_md_inline(raw.lstrip("> ").strip(), build.doc) + "\n", number)
    flush()
    return build.result()


# ---- html ---------------------------------------------------------------------------------

_SKIP = frozenset(
    [
        "head",
        "title",
        "style",
        "script",
        "svg",
        "pre",
        "table",
        "noscript",
        "nav",
        "template",
        "math",
        "button",
        "select",
        "textarea",
        "form",
    ]
)
_BLOCKS = frozenset(
    [
        "p",
        "div",
        "li",
        "ul",
        "ol",
        "dl",
        "dd",
        "dt",
        "blockquote",
        "section",
        "article",
        "header",
        "footer",
        "main",
        "aside",
        "figure",
        "figcaption",
        "details",
        "summary",
        "body",
        "html",
        "hr",
    ]
)
_HEADINGS = frozenset(["h1", "h2", "h3", "h4", "h5", "h6"])


class _HTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.build = _Builder("html")
        self.block = _Block()
        self.kind: Kind = "block"
        self.skip = 0
        self.code = 0
        self.heading_line: int | None = None

    def flush(self) -> None:
        if self.heading_line is not None:
            text, _ = self.block.finish()
            if text:
                self.build.heading(text, self.heading_line)
            self.heading_line = None
        else:
            self.build.add(_paragraph(self.block, self.kind))
        self.kind = "block"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip or tag in _SKIP:
            self.skip += tag in _SKIP
            return
        if tag in _BLOCKS or tag in _HEADINGS:
            self.flush()
            if tag in {"p", "blockquote"}:
                self.kind = "prose"
            elif tag in {"li", "dd", "dt"}:
                self.kind = "item"
            if tag in _HEADINGS:
                self.heading_line = self.getpos()[0]
        elif tag == "code":
            if not self.code:
                self.build.doc.code_spans += 1
                self.block.add(CODE, self.getpos()[0])
            self.code += 1
        elif tag == "br":
            self.block.add(" ", self.getpos()[0])

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP and self.skip:
            self.skip -= 1
            return
        if self.skip:
            return
        if tag in _BLOCKS or tag in _HEADINGS:
            self.flush()
        elif tag == "code" and self.code:
            self.code -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip and not self.code:
            self.block.add(data, self.getpos()[0])


def parse_html(source: str) -> Document:
    parser = _HTML()
    parser.feed(source)
    parser.close()
    parser.flush()
    return parser.build.result()


def read(path: Path) -> Document:
    """Parse a draft, choosing the format by extension. Raises OSError or ValueError."""
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return parse_markdown(path.read_text(encoding="utf-8"))
    if suffix in {".html", ".htm"}:
        return parse_html(path.read_text(encoding="utf-8"))
    raise ValueError(f"unsupported file type {suffix or '(none)'}: use .md or .html")
