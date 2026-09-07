"""Corpora, their gold spans, and the builder that makes those spans exact."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from chunking_lab.corpus import DocumentBuilder, load_dir, write_dir


def _load_generator():
    """Load the structured-corpus generator by path, under a unique name.

    Never `sys.path.insert` plus a bare import: `ingest-ledger` ships a
    `corpus/generate.py` too, and putting either directory on `sys.path` hijacks
    the other tool's import for the whole session (CONVENTIONS rule 1, which is
    about test code as much as source).
    """
    path = Path(__file__).resolve().parents[1] / "corpus" / "generate_docs.py"
    spec = importlib.util.spec_from_file_location("chunking_lab_generate_docs", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_generator = _load_generator()


# ------------------------------------------------------------------- builder


def test_the_builder_records_the_span_it_wrote():
    """The property that makes generated ground truth free."""
    d = DocumentBuilder("notes.md")
    d.add("Some preamble. ")
    d.answer("The threshold is four hours.", question="What is the threshold?")
    d.add(" And a trailing sentence.")

    corpus = d.build()
    (start, end) = corpus.questions[0].gold[0]
    assert corpus.text[start:end] == "The threshold is four hours."


def test_several_answers_in_one_document_each_get_their_own_span():
    d = DocumentBuilder("notes.md")
    for i in range(5):
        d.add(f"Section {i}. ").answer(f"Answer number {i}.", question=f"What is answer {i}?")
        d.add(" filler ")

    corpus = d.build()
    assert len(corpus.questions) == 5
    for i, question in enumerate(corpus.questions):
        start, end = question.gold[0]
        assert corpus.text[start:end] == f"Answer number {i}."


def test_question_ids_are_stable_and_namespaced_by_document():
    d = DocumentBuilder("api.md").answer("x", question="q")
    assert d.build().questions[0].question_id == "api.md:000"


# -------------------------------------------------------------------- round trip


def test_a_corpus_round_trips_through_a_directory(tmp_path):
    d = DocumentBuilder("notes.md")
    d.add("Before. ").answer("The answer.", question="What?", about="a note")
    written = [d.build()]
    write_dir(written, tmp_path)

    (loaded,) = load_dir(tmp_path)
    assert loaded.name == "notes.md"
    assert loaded.text == written[0].text
    assert loaded.questions[0].gold == written[0].questions[0].gold
    assert loaded.questions[0].about == "a note"
    assert loaded.provenance.sha256 == written[0].provenance.sha256


def test_a_gold_span_outside_its_document_is_refused(tmp_path):
    """A wrong gold span scores every strategy against the wrong text.

    Worse than having no corpus, and silent unless something checks.
    """
    (tmp_path / "notes.md").write_text("short")
    (tmp_path / "gold.jsonl").write_text(
        json.dumps({"question_id": "q0", "question": "?", "corpus": "notes.md", "gold": [[0, 999]]})
        + "\n"
    )
    with pytest.raises(ValueError, match="is outside notes.md"):
        load_dir(tmp_path)


def test_a_gold_file_referencing_a_missing_document_is_refused(tmp_path):
    (tmp_path / "gold.jsonl").write_text(
        json.dumps({"question_id": "q0", "question": "?", "corpus": "gone.md", "gold": [[0, 1]]})
        + "\n"
    )
    with pytest.raises(FileNotFoundError, match="which is not in"):
        load_dir(tmp_path)


def test_a_directory_without_a_gold_file_is_refused(tmp_path):
    with pytest.raises(FileNotFoundError, match="no gold.jsonl"):
        load_dir(tmp_path)


# --------------------------------------------------- the structured corpus


def test_the_structured_corpus_has_the_structure_it_exists_for():
    """Its whole purpose is to exercise the two signals the Chroma corpora cannot.

    All five Chroma corpora contain zero Markdown tables and zero code fences, so
    `mid_table_rate` and `split_fence_rate` are constant there -- untested rather
    than uninformative. If this corpus ever loses its structure, that gap silently
    reopens.
    """
    corpora = _generator.build()
    assert len(corpora) == 5

    table_rows = sum(
        1 for c in corpora for line in c.text.splitlines() if line.strip().startswith("|")
    )
    fences = sum(c.text.count("```") for c in corpora)
    assert table_rows > 80, "the corpus has lost its tables"
    assert fences > 20, "the corpus has lost its code fences"
    assert fences % 2 == 0, "an unbalanced fence would be a defect in the fixture, not the chunker"


def test_every_generated_gold_span_matches_its_document():
    """Exactness is the only thing a generated corpus has going for it."""
    for corpus in _generator.build():
        assert corpus.questions, f"{corpus.name} has no questions"
        for question in corpus.questions:
            for start, end in question.gold:
                assert 0 <= start < end <= len(corpus.text)
                assert corpus.text[start:end].strip(), "a gold span is entirely whitespace"


def test_the_corpus_is_large_enough_for_chunk_size_to_matter():
    """A 2KB document gives an 800-character chunker two chunks and nothing to rank."""
    for corpus in _generator.build():
        assert len(corpus.text) > 2500, f"{corpus.name} is too small to vary"


def test_regenerating_produces_identical_documents():
    """Deterministic, or the corpus is not a fixture."""
    first, second = _generator.build(), _generator.build()
    assert [c.text for c in first] == [c.text for c in second]
    assert [q.gold for c in first for q in c.questions] == [
        q.gold for c in second for q in c.questions
    ]
