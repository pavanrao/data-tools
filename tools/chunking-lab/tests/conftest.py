"""Shared fixtures.

Note the import mode: the suite runs under ``--import-mode=importlib``, so a bare
``from conftest import ...`` will not resolve. Constants are passed as fixtures.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from data_tools_core.provenance import Provenance, UnitKind

#: Prose with the structure the strategies actually disagree about: paragraphs of
#: uneven length, a heading, a short line, and a sentence that runs past any
#: reasonable chunk boundary.
PROSE = """# Quarterly Notes

The pipeline read every file it was given. That is not the same as reading every
byte of every file, and the difference is where the interesting failures live.

A short line.

Reconciliation compares what a pipeline was handed against what it actually
extracted, unit by unit, so that a silent drop becomes a number rather than a
surprise six weeks later when somebody asks why the report is wrong and nobody
can say which stage lost the rows.
"""


@pytest.fixture
def prose() -> str:
    return PROSE


@pytest.fixture
def provenance() -> Provenance:
    return Provenance(
        source=Path("notes.md"),
        sha256=hashlib.sha256(PROSE.encode()).hexdigest(),
        unit_kind=UnitKind.DOCUMENT,
    )


@pytest.fixture
def specs() -> list[str]:
    """Every spec the invariant is enforced against, across both built tiers."""
    return [
        "fixed:120",
        "fixed:120/30",
        "fixed:40",
        "recursive:120",
        "recursive:120/30",
        "recursive:40",
        "recursive:10000",
        "sentence:1",
        "sentence:3",
        "sentence:3/1",
        "structural",
        "structural:200",
        "sentence-window:0",
        "sentence-window:2",
        "parent-document:60/240",
        # Tier 1. These construct with the offline hashing embedder, so the
        # invariant is enforced on them with nothing optional installed.
        "semantic:90",
        "semantic:50/200",
        "cluster-semantic:200",
        "cluster-semantic:200/60",
    ]
