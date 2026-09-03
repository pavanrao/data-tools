"""Chunking and indexing: quarantined content must never reach the index."""

from __future__ import annotations

from pathlib import Path

import pytest
from data_tools_core.provenance import UnitKind
from ingest_ledger.chunk import chunks_for, split
from ingest_ledger.embed import HashingEmbedder, cosine
from ingest_ledger.index import describe_gap
from ingest_ledger.manifest import ManifestEntry
from ingest_ledger.models import Declared, Extracted
from ingest_ledger.reconcile import reconcile


def row(status_units: int, declared: int, text: str, missing=()):
    entry = ManifestEntry(Path("f.xlsx"), "abc", (), Declared(declared, UnitKind.SHEET), "xlsx")
    return reconcile(entry, Extracted(status_units, text=text, missing=tuple(missing)))


def test_complete_file_is_chunked():
    chunks = chunks_for(row(2, 2, "alpha beta\n\ngamma delta"))
    assert chunks
    assert all(chunk.provenance.sha256 == "abc" for chunk in chunks)


def test_quarantined_file_is_never_chunked():
    """A partial file with real text is the dangerous case: it looks indexable."""
    assert chunks_for(row(1, 2, "alpha beta gamma", missing=("Rates",))) == []


def test_chunks_carry_a_resolvable_locator():
    chunk = chunks_for(row(1, 1, "alpha"))[0]
    assert chunk.locator.startswith("f.xlsx#sheet=") or "f.xlsx" in chunk.locator
    assert chunk.locator.endswith("@0")


def test_split_respects_the_budget_even_for_one_long_paragraph():
    chunks = split("x" * 5000, max_chars=1000, overlap=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_embedder_is_deterministic_and_normalised():
    embedder = HashingEmbedder()
    first, second = embedder.encode("payment schedule"), embedder.encode("payment schedule")
    assert first == second
    assert cosine(first, second) == pytest.approx(1.0)


def test_related_text_scores_above_unrelated_text():
    embedder = HashingEmbedder()
    query = embedder.encode("intellectual property indemnity")
    near = embedder.encode("intellectual property created under this agreement")
    far = embedder.encode("the vendor shall provide two senior engineers on site")
    assert cosine(query, embedder.encode(" ".join(["x"]))) == 0.0
    assert cosine(query, near) > cosine(query, far)


def test_gap_descriptor_keeps_the_words_a_question_would_use():
    """You cannot search an unread file's contents -- but its sheet names,
    filename and failure reason are exactly what a question tends to name."""
    descriptor = describe_gap(row(2, 3, "cover", missing=("Payment Schedule",)))
    assert "Payment Schedule" in descriptor
    assert "f.xlsx" in descriptor
