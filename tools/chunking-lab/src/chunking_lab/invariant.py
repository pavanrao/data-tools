"""What every chunker must satisfy, whatever else it does.

This is CONVENTIONS rule 5 turned on the chunkers themselves. The classic bug it
exists to catch is a splitter that silently drops a trailing paragraph: the run
succeeds, the scores look plausible, and a slice of the corpus was never indexed.

The interesting choice here is invariant 4. "Coverage == 1.0" is too strict --
the reference implementation strips whitespace off its boundaries, so a faithful
port leaves small gaps between spans and would fail it. But dropping *content* is
never acceptable. So the rule is the honest one: **no non-whitespace character
may be missing from every span.** That is checkable, it permits the strip, and it
still fails loudly on the dropped paragraph.
"""

from __future__ import annotations

from chunking_lab.spans import Chunking


class InvariantViolation(AssertionError):
    """A chunker produced spans that cannot be scored. Always a bug in the chunker."""


def check(chunking: Chunking, text: str) -> None:
    """Raise ``InvariantViolation`` unless the chunking is well formed.

    Every chunker is run through this in the test suite, so a new strategy cannot
    be added without earning it.
    """
    spans = chunking.spans
    if not spans:
        raise InvariantViolation(f"{chunking.strategy}: produced no spans")

    # 1. in bounds
    for span in spans:
        if span.end > len(text):
            raise InvariantViolation(
                f"{chunking.strategy}: span ({span.start}, {span.end}) runs past "
                f"the document, which is {len(text)} characters"
            )

    # 2. ordered, and 3. overlapping by no more than the strategy declares
    for previous, current in zip(spans, spans[1:], strict=False):
        if current.start < previous.start:
            raise InvariantViolation(
                f"{chunking.strategy}: spans are out of order at offset {current.start}"
            )
        overlap = previous.end - current.start
        if overlap > chunking.declared_overlap:
            raise InvariantViolation(
                f"{chunking.strategy}: spans overlap by {overlap} characters at offset "
                f"{current.start}, but the strategy declares {chunking.declared_overlap}"
            )

    # 4. no non-whitespace character is dropped
    covered = bytearray(len(text))
    for span in spans:
        covered[span.start : span.end] = b"\x01" * span.length
    missing = [i for i, seen in enumerate(covered) if not seen and not text[i].isspace()]
    if missing:
        raise InvariantViolation(
            f"{chunking.strategy}: {len(missing)} non-whitespace characters are in no "
            f"span at all, first at offset {missing[0]} "
            f"({text[missing[0] : missing[0] + 40]!r})"
        )

    # 5. text matches the offsets unless augmentation is declared
    if not chunking.augmented:
        for span in spans:
            if span.return_text != text[span.start : span.end]:
                raise InvariantViolation(
                    f"{chunking.strategy}: return_text at offset {span.start} does not "
                    f"match the document, and the strategy does not declare augmentation"
                )


def coverage(chunking: Chunking, text: str) -> float:
    """Fraction of the document's characters present in at least one span.

    Reported rather than asserted: below 1.0 is not automatically a fault (a
    trimming strategy loses whitespace), but it is always worth seeing. Anything
    that loses *content* is caught by :func:`check`.
    """
    if not text:
        return 1.0
    covered = bytearray(len(text))
    for span in chunking.spans:
        covered[span.start : span.end] = b"\x01" * span.length
    return sum(covered) / len(text)
