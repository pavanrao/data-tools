"""Turning a quoted answer into exact character offsets.

This is the mechanism behind C9. Gold spans need exact offsets, and language
models are unreliable at emitting them -- so **do not ask for offsets**. Ask for
the answer quoted verbatim, then find that string in the source deterministically,
and discard anything that cannot be found.

That inverts the failure mode. A weaker model does not produce *wrong* ground
truth, it produces *less* of it: 40 usable questions instead of 90. Model quality
becomes a **yield** you can read off, rather than a silent corruption of results.

The cascade below is the reference implementation's, which was read to get it
right: exact match, then a whitespace-tolerant match, then a sentence-level fuzzy
match that must score at least 98. Its one difference from ours is what happens on
failure -- it retries the model until it has enough questions, so a weak model
shows up as a longer run and a larger bill. Reporting the yield instead is the
whole point of the decision.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from chunking_lab.ranges import Range

#: The fuzzy stage must be this close to accept, on a 0-100 scale. Deliberately
#: severe: a near-miss quote is a wrong gold span, and a wrong gold span is worse
#: than a missing one -- it scores every strategy against the wrong answer.
FUZZY_FLOOR = 98

_SENTENCE = re.compile(r"[.!?]\s*|\n")


@dataclass(frozen=True, slots=True)
class Located:
    """Where a quoted answer was found, and which stage of the cascade found it."""

    span: Range
    text: str
    #: "exact", "whitespace" or "fuzzy" -- recorded so a corpus built mostly from
    #: fuzzy matches is visibly less trustworthy than one built from exact ones.
    how: str


def locate(document: str, quote: str) -> Located | None:
    """Find ``quote`` in ``document``. Returns None if it cannot be found.

    None is an ordinary outcome, not an error: the caller discards the question
    and counts it against the yield.
    """
    target = quote.rstrip()
    if target.endswith("."):
        target = target[:-1]
    if not target:
        return None

    start = document.find(target)
    if start != -1:
        return Located((start, start + len(target)), target, "exact")

    loose = _find_ignoring_whitespace(document, target)
    if loose is not None:
        return loose

    return _find_fuzzily(document, target)


def _find_ignoring_whitespace(document: str, target: str) -> Located | None:
    """Match across a line break the model collapsed, or a doubled space."""
    words = re.sub(r"\s+", " ", target).strip().split()
    if not words:
        return None
    pattern = r"\s*".join(re.escape(word) for word in words)
    match = re.search(pattern, document, re.IGNORECASE)
    if match is None:
        return None
    return Located((match.start(), match.end()), match.group(0), "whitespace")


def _find_fuzzily(document: str, target: str) -> Located | None:
    """Last resort: the closest sentence, and only if it is very close indeed."""
    best_text, best_ratio = None, 0.0
    for sentence in (s.strip() for s in _SENTENCE.split(document)):
        if not sentence:
            continue
        ratio = difflib.SequenceMatcher(None, target, sentence).ratio() * 100
        if ratio > best_ratio:
            best_text, best_ratio = sentence, ratio

    if best_text is None or best_ratio < FUZZY_FLOOR:
        return None
    start = document.find(best_text)
    if start == -1:
        return None
    return Located((start, start + len(best_text)), best_text, "fuzzy")


def locate_all(document: str, quotes: list[str]) -> tuple[list[Located], list[str]]:
    """Locate every quote. Returns what was found, and what was not.

    The second list is the yield report: how much ground truth the model failed to
    produce usably, which is the number to publish alongside any corpus built this
    way.
    """
    found, missing = [], []
    for quote in quotes:
        result = locate(document, quote)
        (found.append(result) if result is not None else missing.append(quote))
    return found, missing
