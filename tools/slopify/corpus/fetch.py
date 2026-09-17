#!/usr/bin/env python3
"""Fetch the reference prose: technical writing by named humans, mostly pre-2022.

slopify needs source text no model wrote (see `docs/014` §2). These are posts by
working engineers and researchers arguing a technical case in public, which is the
register ai-sniffer is aimed at.

**Downloaded, never committed.** None of these carries a reuse licence, so the
repository holds this script and the hashes and not the prose. That follows the
precedent in `tools/chunking-lab/benchmarks/fetch.py`, which downloads the Chroma
benchmark for a different reason — size — and pins it the same way.

The hash is taken over the *extracted prose*, not the HTML, because page templates
carry navigation and sponsor blocks that change while the article does not. A
changed hash therefore means the post was edited or an extractor broke, and either
way it is a failed check rather than a silently different number.

    uv run python tools/slopify/corpus/fetch.py
    uv run python tools/slopify/corpus/fetch.py --update   # reprint the hashes

Each source names its own start and end markers. A site redesign breaks one entry
loudly instead of quietly returning a page of navigation as though it were prose.
"""

from __future__ import annotations

import hashlib
import html
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Source:
    url: str
    name: str
    published: str
    start: str  #: regex marking where the article body begins
    end: str  #: regex marking where it ends
    sha256: str = ""
    #: set when the date alone does not establish that no model was involved
    caveat: str = ""


WILLISON_START = r'<div data-permalink-context="[^"]*">'
WILLISON_END = r'<div class="entryFooter"'

SOURCES: list[Source] = [
    Source(
        "https://simonwillison.net/2018/Nov/19/smaller-python-docker-images/",
        "willison-2018-docker-images.md",
        "2018-11-19",
        WILLISON_START,
        WILLISON_END,
        "09a58032b7a32e88cf6c7970223b9b30a5c824830f0237f7005722525bf33b0d",
    ),
    Source(
        "https://simonwillison.net/2018/Oct/4/datasette-ideas/",
        "willison-2018-datasette-ideas.md",
        "2018-10-04",
        WILLISON_START,
        WILLISON_END,
        "99c65d02891209428e7d7ba93c35c0112e8379044e9f4bdc2cc7b3959ab44ada",
    ),
    Source(
        "https://simonwillison.net/2021/Jul/17/standing-out/",
        "willison-2021-standing-out.md",
        "2021-07-17",
        WILLISON_START,
        WILLISON_END,
        "ac6b7eeb668d535986e00469a62cf5dc481aa893b899ff967ba97251a3047d1f",
    ),
    Source(
        "https://hakibenita.com/postgresql-hash-index",
        "benita-2021-hash-indexes.md",
        "2021-01-11",
        r'<article class="article__content"',
        r"</article>",
        "aa5dd44eff54ed3ace9bfd55cf69fcf591427adee34966a7febbbb1d8248c2fd",
    ),
    Source(
        "https://www.starburst.io/blog/data-mesh-data-warehouse/",
        "starburst-2021-data-mesh.md",
        "2021-03-25",
        r'class="prose-sb-full blog-content',
        r"</article>|<footer",
        "7bc54e4bc6090ca7ab12ca5757c85124d5e03364d7e5a66302c05a17173b7fa3",
    ),
    Source(
        "https://www.cs.cmu.edu/~pavlo/blog/2022/12/2022-databases-retrospective.html",
        "pavlo-2022-databases-review.md",
        "2022-12-31",
        r'<article class="blogpost">',
        r"</article>",
        "53085c361d3d37957ef98f7ca61c1ce507fb903c79765511b44d9654f31c471b",
        caveat=(
            "dated one month after ChatGPT's release, so the date alone does not place "
            "it before model-drafted prose the way the others do. Included on Pavan's "
            "judgement that the models of December 2022 were not capable of it"
        ),
    ),
]

DATA = Path(__file__).parent / "reference"
BLOCK = re.compile(r"<(h[1-6]|p|pre|ul|ol|blockquote)\b[^>]*>(.*?)</\1>", re.S)


def _inline(text: str) -> str:
    def code(match: re.Match[str]) -> str:
        return "`" + re.sub(r"<[^>]+>", "", match[1]) + "`"

    text = re.sub(r"<code>(.*?)</code>", code, text, flags=re.S)
    text = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", text, flags=re.S)
    text = re.sub(r"<(i|em)>(.*?)</\1>", r"*\2*", text, flags=re.S)
    text = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(html.unescape(text).split())


def extract(page: str, source: Source) -> str:
    """The article as Markdown: prose as paragraphs, everything else fenced or listed.

    Code and lists are deliberately kept in a shape slopify's parser treats as
    verbatim, so nothing is ever injected into them.
    """
    opening = re.search(source.start, page)
    if not opening:
        raise SystemExit(f"{source.name}: start marker not found; the site template changed")
    rest = page[opening.end() :]
    closing = re.search(source.end, rest)
    body = rest[: closing.start()] if closing else rest

    out: list[str] = []
    for tag, inner in BLOCK.findall(body):
        if tag == "pre":
            code = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip("\n")
            out.append("```text\n" + code + "\n```")
        elif tag in ("ul", "ol"):
            mark = "- " if tag == "ul" else "1. "
            items = re.findall(r"<li\b[^>]*>(.*?)</li>", inner, re.S)
            out.append("\n".join(mark + _inline(x) for x in items))
        elif tag == "blockquote":
            out.append("\n".join("> " + line for line in _inline(inner).split("\n")))
        elif tag.startswith("h"):
            out.append("#" * int(tag[1]) + " " + _inline(inner))
        else:
            text = _inline(inner)
            if text:
                out.append(text)
    if not out:
        raise SystemExit(f"{source.name}: markers matched but no prose came out")
    return "\n\n".join(out) + "\n"


def get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "data-tools slopify corpus"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def main(update: bool) -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for source in SOURCES:
        prose = extract(get(source.url), source)
        digest = hashlib.sha256(prose.encode("utf-8")).hexdigest()
        if not update and source.sha256 and digest != source.sha256:
            failures.append(f"{source.name}: expected {source.sha256[:12]}…, got {digest[:12]}…")
            continue
        (DATA / source.name).write_text(prose, encoding="utf-8")
        if update:
            print(f'        "{digest}",  # {source.name}')
        else:
            flag = "  (see caveat)" if source.caveat else ""
            print(f"{source.name:<34}{source.published}  {len(prose.split()):>5} words{flag}")
    if failures:
        lines = ["the prose changed upstream, or an extractor broke:", *failures]
        print("\n".join(lines), file=sys.stderr)
        return 1
    if not update:
        print(f"\n-> {DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--update" in sys.argv))
