#!/usr/bin/env python3
"""Fetch the reference prose: technical blogging written before late 2022.

slopify needs source text no model wrote (see `docs/014` §2). These posts are by
Simon Willison, published 2018 to 2021, and they are the right register for what
ai-sniffer is aimed at: a named engineer arguing a technical case in public.

**Downloaded, never committed.** The posts carry no reuse licence, so the
repository holds this script and the hashes and not the prose. That follows the
precedent in `tools/chunking-lab/benchmarks/fetch.py`, which downloads the Chroma
benchmark for a different reason — size — and pins it the same way.

The hash is taken over the *extracted prose*, not the HTML, because the page
template carries a sponsor block that changes weekly while the article does not.
A changed hash therefore means the post was edited or this extractor broke, and
either way it is a failed check rather than a silently different number.

    uv run python tools/slopify/corpus/fetch.py

Pass --update to print the hashes as they are now, for when a post is genuinely
revised upstream and the new bytes have been looked at.
"""

from __future__ import annotations

import hashlib
import html
import re
import sys
import urllib.request
from pathlib import Path

#: url -> (filename, SHA-256 of the extracted prose). Pinned; never a moving target.
POSTS = {
    "https://simonwillison.net/2018/Nov/19/smaller-python-docker-images/": (
        "willison-2018-docker-images.md",
        "09a58032b7a32e88cf6c7970223b9b30a5c824830f0237f7005722525bf33b0d",
    ),
    "https://simonwillison.net/2018/Oct/4/datasette-ideas/": (
        "willison-2018-datasette-ideas.md",
        "99c65d02891209428e7d7ba93c35c0112e8379044e9f4bdc2cc7b3959ab44ada",
    ),
    "https://simonwillison.net/2021/Jul/17/standing-out/": (
        "willison-2021-standing-out.md",
        "ac6b7eeb668d535986e00469a62cf5dc481aa893b899ff967ba97251a3047d1f",
    ),
}

DATA = Path(__file__).parent / "reference"
BODY = re.compile(r'<div data-permalink-context="[^"]*">(.*?)<div class="entryFooter"', re.S)
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


def extract(page: str) -> str:
    """The article as Markdown: prose as paragraphs, everything else fenced or listed.

    Code and lists are deliberately kept in a shape slopify's parser treats as
    verbatim, so nothing is ever injected into them.
    """
    body = BODY.search(page)
    if not body:
        raise SystemExit("could not find the article body; the site template changed")
    out: list[str] = []
    for tag, inner in BLOCK.findall(body[1]):
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
    return "\n\n".join(out) + "\n"


def get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "data-tools slopify corpus"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def main(update: bool) -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    failures = []
    for url, (name, expected) in POSTS.items():
        prose = extract(get(url))
        digest = hashlib.sha256(prose.encode("utf-8")).hexdigest()
        if update:
            print(f'    "{url}": (\n        "{name}",\n        "{digest}",\n    ),')
            (DATA / name).write_text(prose, encoding="utf-8")
            continue
        if expected and digest != expected:
            failures.append(f"{name}: expected {expected[:12]}…, got {digest[:12]}…")
            continue
        (DATA / name).write_text(prose, encoding="utf-8")
        print(f"{name}  {len(prose.split()):>5} words  {digest[:12]}…")
    if failures:
        lines = ["the prose changed upstream, or this extractor broke:", *failures]
        print("\n".join(lines), file=sys.stderr)
        return 1
    if not update:
        print(f"\n-> {DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--update" in sys.argv))
