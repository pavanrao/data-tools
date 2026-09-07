#!/usr/bin/env python3
"""Fetch the Chroma chunking benchmark, and verify it byte for byte.

Five corpora and 472 gold-span questions from `brandonstarxel/chunking_evaluation`
(MIT, Brandon Smith), pinned to one upstream commit and checked against recorded
SHA-256 hashes. This is what `precision_omega` is validated against -- see
README C17 and `SOURCE.md` next to this file.

Downloaded rather than committed, following this repo's precedent: 1.6MB of text
would triple the pack size of a collection whose entire history is 260KB. The
pinned commit and the hashes are what make it reproducible anyway -- a changed
byte upstream is a failed check here, not a silently different number.

    uv run python tools/chunking-lab/benchmarks/fetch.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

#: Pinned. Never follow a branch: the whole point is that the bytes cannot move.
COMMIT = "e708410d1c61cb76a85cd9d433630ef89b9c6b85"
BASE = (
    f"https://raw.githubusercontent.com/brandonstarxel/chunking_evaluation/{COMMIT}"
    "/chunking_evaluation/evaluation_framework/general_evaluation_data"
)

#: relative path -> SHA-256 of the file as published at COMMIT.
FILES = {
    "corpora/chatlogs.md": "543a98f82b2a6a492349fd7f8c9d6c3e78d1a4af81d13c79a7fd513c3f65bda6",
    "corpora/finance.md": "1c48d0156820abc88e46e5c992fa0cd2708b07ae59a3771b2b18234b7208561f",
    "corpora/pubmed.md": "0fd9242ffb253695e5d0f0215cb79a66a2a8f1236591e764c60d370747684ced",
    "corpora/state_of_the_union.md": (
        "6fc21d560d31eb2421e337596feea0f83f1fa9ca02c6c4e47bc26959d7531b37"
    ),
    "corpora/wikitexts.md": "74cafcdb771185ecb9f22cc41b73e2e44477e0636ecf9cf1f96fd6ee0f4b86c0",
    "questions_df.csv": "3ab3901889b8900f43775537bf12d36bd6614255fc59124faca31bede1dda7a3",
}

DATA = Path(__file__).parent / "chroma"


def verified(path: Path, expected: str) -> bool:
    return path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected


def fetch(force: bool = False) -> int:
    for name, expected in FILES.items():
        target = DATA / name
        if not force and verified(target, expected):
            print(f"  ok       {name}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"  fetching {name} ...", end=" ", flush=True)
        with urllib.request.urlopen(f"{BASE}/{name}") as response:  # noqa: S310
            body = response.read()
        digest = hashlib.sha256(body).hexdigest()
        if digest != expected:
            print("FAILED")
            print(
                f"\n{name} does not match the recorded hash.\n"
                f"  expected {expected}\n  got      {digest}\n"
                "The upstream bytes have changed, or the download was corrupted. "
                "Do not use this data for the reproduction until that is explained.",
                file=sys.stderr,
            )
            return 1
        target.write_bytes(body)
        print("ok")
    print(f"\nBenchmark ready in {DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(fetch(force="--force" in sys.argv))
