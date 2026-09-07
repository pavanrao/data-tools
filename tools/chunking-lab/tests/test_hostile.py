"""The hostile corpus: documents built so specific strategies provably fail.

Marked `hostile`, per `docs/000` section 8 — a strategy that *stops* failing one
of these is a product regression, not a win, because it means the fixture has
drifted and is no longer testing anything.

Gold spans are known by construction: the generator wrote the answer text, so it
knows exactly which characters it occupies. No annotation, no model, no fuzzy
matching (README C11).

Building these turned up something the design record had merged into one idea.
There are **two** distinct failure modes, and they need different fixtures and
different assertions:

* **Severing** — the answer is cut across chunks, so no single chunk holds it.
* **Orphaning** — the chunk holding the answer is perfectly intact, and still
  unusable, because the thing that makes it meaningful (a heading, a table's
  header row, the noun a pronoun refers to) is in a different chunk.

The second is the interesting one. No boundary placement fixes it — the boundary
is already correct — which is precisely why the context-augmenting strategies
exist, and why `Span` carries `retrieval_text` and `return_text` separately.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest
from chunking_lab import check, from_spec
from chunking_lab.extrinsic import gold_bearing_chunks
from data_tools_core.provenance import Provenance, UnitKind


def _load_generator():
    """Load the corpus generator by path, under a name nothing else can collide with.

    Not ``sys.path.insert`` plus ``import generate``: `ingest-ledger` ships a
    ``corpus/generate.py`` too, and putting either directory on ``sys.path``
    silently hijacks the other tool's import for the whole session. That is
    CONVENTIONS rule 1 -- tools do not reach into each other -- broken by a test
    helper rather than by a dependency, which is exactly how it happens.
    """
    path = Path(__file__).resolve().parents[1] / "corpus" / "generate.py"
    spec = importlib.util.spec_from_file_location("chunking_lab_corpus_generate", path)
    module = importlib.util.module_from_spec(spec)
    # Registered before exec because @dataclass resolves its own module through
    # sys.modules while the class body is being processed, and fails with a bare
    # AttributeError if it is not there yet. The name is unique, so nothing collides.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_generator = _load_generator()
build, write = _generator.build, _generator.write

pytestmark = pytest.mark.hostile

DOCUMENTS = {doc.name: doc for doc in build()}


def _chunk(name: str, spec: str):
    doc = DOCUMENTS[name]
    provenance = Provenance(
        source=Path(name),
        sha256=hashlib.sha256(doc.text.encode()).hexdigest(),
        unit_kind=UnitKind.DOCUMENT,
    )
    chunking = from_spec(spec).chunk(doc.text, provenance)
    check(chunking, doc.text)
    return doc, chunking


def _holders(doc, chunking):
    """The chunks holding any part of the answer."""
    return [
        span
        for span in chunking.spans
        if any(span.start < end and span.end > start for start, end in doc.gold)
    ]


# --------------------------------------------------------------- construction


def test_every_gold_span_is_exactly_the_answer_text():
    """The property that makes this ground truth free: the generator wrote it."""
    for doc in build():
        assert doc.gold, f"{doc.name} has no marked answer"
        for start, end in doc.gold:
            assert 0 <= start < end <= len(doc.text)
        assert doc.question, f"{doc.name} has no question"


def test_the_corpus_writes_documents_and_gold_spans(tmp_path):
    gold_path = write(tmp_path)
    lines = gold_path.read_text().strip().splitlines()
    assert len(lines) == len(DOCUMENTS)
    for doc in DOCUMENTS.values():
        assert (tmp_path / doc.name).exists()


# ------------------------------------------------------------------ severing


def test_a_recursive_splitter_severs_an_answer_that_straddles_a_paragraph_break():
    """A blank line is the *first* place a recursive splitter cuts. Put the answer
    across one and it is guaranteed to be split."""
    doc, chunking = _chunk("straddle.md", "recursive:120")
    assert gold_bearing_chunks(chunking, list(doc.gold)) > 1

    _, intact = _chunk("straddle.md", "structural")
    assert gold_bearing_chunks(intact, list(doc.gold)) == 1


def test_size_based_splitting_cuts_a_code_example_into_unrunnable_fragments():
    doc, chunking = _chunk("code_fence.md", "fixed:120")
    assert gold_bearing_chunks(chunking, list(doc.gold)) > 1
    holders = _holders(doc, chunking)
    # Every fragment is half a fence, which is worse than useless: it looks like code.
    assert any(span.retrieval_text.count("```") == 1 for span in holders)

    _, intact = _chunk("code_fence.md", "structural")
    assert gold_bearing_chunks(intact, list(doc.gold)) == 1


# ----------------------------------------------------------------- orphaning


@pytest.mark.parametrize("spec", ["fixed:200", "recursive:200"])
def test_a_size_based_cut_orphans_a_fact_from_its_heading(spec):
    """The chunk holds the filing date and never says which region it is for."""
    doc, chunking = _chunk("heading_subject.md", spec)
    holders = _holders(doc, chunking)

    assert gold_bearing_chunks(chunking, list(doc.gold)) == 1, "not severed -- just orphaned"
    assert not any("Northeast" in span.retrieval_text for span in holders)


def test_a_structural_splitter_keeps_the_heading_with_its_section():
    doc, chunking = _chunk("heading_subject.md", "structural")
    assert any("Northeast" in span.retrieval_text for span in _holders(doc, chunking))


def test_context_augmentation_recovers_the_subject_in_what_it_returns():
    """The family-6 payoff, and the clearest argument for `Span` carrying both fields.

    Sentence-window still *indexes* a chunk with no subject in it -- so retrieval is
    no easier -- but what reaches the model does contain it. Score the wrong field
    and this strategy looks either better or worse than it is.
    """
    doc, chunking = _chunk("heading_subject.md", "sentence-window:1")
    holders = _holders(doc, chunking)

    assert not any("Northeast" in span.retrieval_text for span in holders)
    assert any("Northeast" in span.return_text for span in holders)


def test_a_table_row_is_orphaned_from_its_header():
    """Four numbers with no column names. Nothing about the chunk looks wrong."""
    doc, chunking = _chunk("rate_table.md", "fixed:200")
    holders = _holders(doc, chunking)
    assert not any("| Region" in span.retrieval_text for span in holders)

    _, intact = _chunk("rate_table.md", "structural")
    assert any("| Region" in span.retrieval_text for span in _holders(doc, intact))


def test_a_back_reference_defeats_boundary_placement_entirely():
    """No cut fixes this one: the chunk is correct and still cannot stand alone.

    A one-sentence window is not enough either -- the subject is two sentences back.
    Only widening what is returned far enough recovers it, which is the whole
    argument for parent-document retrieval.
    """
    doc, chunking = _chunk("back_reference.md", "recursive:200")
    holders = _holders(doc, chunking)
    assert gold_bearing_chunks(chunking, list(doc.gold)) == 1
    assert not any("audit log" in span.retrieval_text for span in holders)

    _, narrow = _chunk("back_reference.md", "sentence-window:1")
    assert not any("audit log" in span.return_text for span in _holders(doc, narrow))

    _, wide = _chunk("back_reference.md", "parent-document:120/600")
    assert any("audit log" in span.return_text for span in _holders(doc, wide))


def test_the_orphan_metric_sees_the_back_reference():
    """The query-free signal that catches this with no questions at all."""
    from chunking_lab import measure

    doc, chunking = _chunk("back_reference.md", "sentence:1")
    assert measure(chunking, doc.text).orphan_rate > 0
