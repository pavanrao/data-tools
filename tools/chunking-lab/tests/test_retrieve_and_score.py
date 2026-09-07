"""The fixed retriever, and the result rows the whole tool exists to produce."""

from __future__ import annotations

import json

import pytest
from chunking_lab import from_spec
from chunking_lab.benchmark import Corpus, Question
from chunking_lab.retrieve import STOPWORDS, BM25Retriever
from chunking_lab.score import breakdown as score_breakdown
from chunking_lab.score import run, summarise, write_jsonl

DOC = (
    "The pipeline read every file it was given. "
    "Reconciliation compares what a pipeline was handed against what it extracted. "
    "Chunking decides what a retriever is able to find at all. "
    "A table split across a boundary is unusable by either. "
    "The ledger records both counts so a silent drop becomes a number."
)


@pytest.fixture
def corpus(provenance):
    text = DOC
    return Corpus(
        name="notes.md",
        text=text,
        provenance=provenance,
        questions=(
            Question(
                question_id="q0",
                text="what does reconciliation compare?",
                corpus="notes.md",
                gold=((text.index("Reconciliation"), text.index("Chunking decides") - 1),),
            ),
            Question(
                question_id="q1",
                text="what happens to a split table?",
                corpus="notes.md",
                gold=((text.index("A table"), text.index("The ledger") - 1),),
            ),
        ),
    )


# ------------------------------------------------------------------ retriever


def test_stopwords_are_dropped_from_the_query():
    """The gotcha logged against repo-rag in docs/LEARNINGS.md."""
    assert BM25Retriever.to_match("What are the payment schedule milestones?") == (
        '"payment" OR "schedule" OR "milestones"'
    )
    assert "the" in STOPWORDS and "payment" not in STOPWORDS


def test_an_all_stopword_question_still_retrieves_something():
    """A degenerate ranking beats scoring that question zero for every strategy."""
    assert BM25Retriever.to_match("what is it") != ""


def test_the_retriever_finds_the_chunk_holding_the_answer(corpus):
    chunking = from_spec("sentence:1").chunk(corpus.text, corpus.provenance)
    with BM25Retriever(chunking) as retriever:
        top = retriever.search("what does reconciliation compare?", k=1)
    assert top and "Reconciliation compares" in top[0].retrieval_text


def test_the_retriever_indexes_what_is_retrieved_not_what_is_returned(corpus):
    """Family 6 again: BM25 must see `retrieval_text`, or the strategy is misscored."""
    chunking = from_spec("sentence-window:1").chunk(corpus.text, corpus.provenance)
    with BM25Retriever(chunking) as retriever:
        top = retriever.search("what happens to a split table?", k=1)
    assert top
    assert top[0].retrieval_text == "A table split across a boundary is unusable by either."
    assert len(top[0].return_text) > len(top[0].retrieval_text)


# --------------------------------------------------------------------- rows


def test_a_result_row_carries_intrinsic_and_extrinsic_together(corpus):
    """Open question 4: the correlation experiment must be a group-by, not a script."""
    rows = list(run(from_spec("sentence:2"), corpus))
    assert len(rows) == 2

    row = rows[0].as_row()
    assert set(row) == {
        "strategy",
        "corpus",
        "question_id",
        "question_kind",
        "code_path",
        "retriever",
        "source_sha256",
        "locator",
        "intrinsic",
        "extrinsic",
    }
    assert "boundary_fidelity" in row["intrinsic"]
    assert "precision_omega" in row["extrinsic"]


def test_a_row_is_interpretable_without_the_run_that_produced_it(corpus):
    row = next(iter(run(from_spec("recursive:100"), corpus))).as_row()
    assert row["strategy"] == "recursive:100"
    assert row["retriever"] == "bm25/fts5"
    assert row["code_path"] == "tier-0/model-free"
    assert row["source_sha256"] == corpus.provenance.sha256
    assert row["extrinsic"]["k"] >= 1


def test_the_question_kind_travels_onto_every_row(corpus):
    """C13: a ranking that hides its question mix has a thumb on the scale.

    The kind has to be on the row, not just in the corpus, or the breakdown would
    need the corpus back to interpret results months later.
    """
    rows = list(run(from_spec("sentence:2"), corpus))
    assert {r.question_kind for r in rows} == {"unlabelled"}
    assert all(r.as_row()["question_kind"] for r in rows)


def test_a_breakdown_ranks_each_kind_of_question_separately(provenance):
    """The demonstration that there is no single best chunking.

    Same document, same cuts: a strategy's rank depends on what is being asked.
    """
    from chunking_lab.benchmark import Corpus, Question

    text = (
        "| region | limit |\n|--------|-------|\n| north  | 12/s  |\n"
        "The northern region is limited because its upstream is shared.\n"
    )
    row_start = text.index("| north")
    prose_start = text.index("The northern")
    labelled = Corpus(
        name="rates.md",
        text=text,
        provenance=provenance,
        questions=(
            Question(
                "q0",
                "what is the limit for north?",
                "rates.md",
                ((row_start, row_start + 21),),
                kind="table-row",
            ),
            Question(
                "q1",
                "why is north limited?",
                "rates.md",
                ((prose_start, len(text) - 1),),
                kind="prose",
            ),
        ),
    )

    results = []
    for spec in ("sentence:1", "fixed:400"):
        results.extend(run(from_spec(spec), labelled))

    rows = score_breakdown(results)
    assert {r.kind for r in rows} == {"table-row", "prose"}
    # Every strategy is ranked within every kind, so a swing is computable.
    for kind in ("table-row", "prose"):
        assert sorted(r.rank for r in rows if r.kind == kind) == [1, 2]


def test_an_unlabelled_corpus_breaks_down_into_one_bucket(corpus):
    """Chroma's questions carry no kind, and that must not be a crash."""
    rows = score_breakdown(list(run(from_spec("sentence:2"), corpus)))
    assert {r.kind for r in rows} == {"unlabelled"}


def test_an_explicit_k_reaches_every_row(corpus):
    rows = list(run(from_spec("sentence:1"), corpus, k=3))
    assert all(row.extrinsic.k == 3 for row in rows)


def test_summaries_rank_by_precision_omega(corpus):
    rows = []
    for spec in ("sentence:1", "recursive:400"):
        rows.extend(run(from_spec(spec), corpus))
    summaries = summarise(rows)

    assert [s.strategy for s in summaries] == sorted(
        [s.strategy for s in summaries],
        key=lambda name: -next(s.precision_omega for s in summaries if s.strategy == name),
    )
    # Tight chunks impose a higher ceiling than one chunk holding the document.
    assert summaries[0].strategy == "sentence:1"


def test_rows_round_trip_through_jsonl(corpus, tmp_path):
    path = tmp_path / "results.jsonl"
    written = write_jsonl(run(from_spec("sentence:2"), corpus), path)
    assert written == 2

    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["intrinsic"]["chunks"] > 0

    # Appending, not truncating: results accumulate across runs so the
    # correlation experiment can query them together.
    write_jsonl(run(from_spec("recursive:100"), corpus), path)
    assert len(path.read_text().splitlines()) == 4
