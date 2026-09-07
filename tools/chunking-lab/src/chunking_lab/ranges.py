"""Character-range arithmetic. Every metric in this tool is built from these.

Ranges are half-open ``(start, end)`` pairs over the normalized document. Three
operations do all the work, and the reference implementation's versions are
reproduced here because the published numbers came from them.

Kept separate from the metrics so the arithmetic can be tested on its own. When a
score looks wrong, this is the layer you want to have already ruled out.
"""

from __future__ import annotations

type Range = tuple[int, int]


def total(ranges: list[Range]) -> int:
    """Summed width. Note: *summed*, so overlapping ranges are counted twice.

    That is not an oversight -- see :func:`chunking_lab.extrinsic.score`, where one
    metric wants the sum and another wants the union of the very same ranges.
    """
    return sum(end - start for start, end in ranges)


def union(ranges: list[Range]) -> list[Range]:
    """Merge overlapping and touching ranges, so every character counts once."""
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def intersect(left: Range, right: Range) -> Range | None:
    """The overlap of two ranges, or None if they do not touch."""
    start = max(left[0], right[0])
    end = min(left[1], right[1])
    return (start, end) if start <= end else None


def difference(ranges: list[Range], target: Range) -> list[Range]:
    """Remove ``target`` from every range in ``ranges``, splitting where it lands inside."""
    result: list[Range] = []
    target_start, target_end = target
    for start, end in ranges:
        if end < target_start or start > target_end:
            result.append((start, end))
        elif start < target_start and end > target_end:
            result.append((start, target_start))
            result.append((target_end, end))
        elif start < target_start:
            result.append((start, target_start))
        elif end > target_end:
            result.append((target_end, end))
        # otherwise the range is entirely consumed
    return result
