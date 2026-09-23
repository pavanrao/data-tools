"""Every technique, on every engine that is available.

The contract a technique signs by existing: its correct.sql returns exactly the
ground truth the seed computed in Python, and its naive.sql does not. A
technique whose naive query happens to agree with the truth demonstrates
nothing, so that fails too.
"""

from __future__ import annotations

import pytest
from kimball_lab import runner

TECHNIQUES = runner.techniques()


def _check(engine, technique, truth):
    d = runner.demo(engine, technique, truth)
    if d.skipped:
        pytest.skip(d.skipped)
    assert d.correct_matches_truth, (
        f"{technique.number} correct.sql disagrees with ground truth: {d.correct} vs {d.truth}"
    )
    assert d.naive_differs, f"{technique.number} naive.sql agrees with ground truth"
    assert set(d.naive) & set(d.truth), f"{technique.number} naive.sql shares no keys with truth"


@pytest.mark.parametrize("technique", TECHNIQUES, ids=[t.number for t in TECHNIQUES])
def test_on_duckdb(warehouse, technique, truth):
    _check(warehouse, technique, truth)


@pytest.mark.parametrize("technique", TECHNIQUES, ids=[t.number for t in TECHNIQUES])
def test_on_ducklake(lake, technique, truth):
    _check(lake, technique, truth)


def test_every_technique_has_its_files():
    for t in TECHNIQUES:
        for name in ("naive.sql", "correct.sql", "NOTES.md"):
            assert (t.path / name).exists(), f"{t.path.name} is missing {name}"
