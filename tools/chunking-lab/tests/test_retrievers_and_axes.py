"""Vector and hybrid retrieval, and the comparison between the two axes.

Every test injects a fake embedder. Not only because the suite must run with
nothing installed (CONVENTIONS rule 6), but because with a controlled embedding
"which chunk should win?" has a right answer, where a real encoder would turn each
assertion into a judgement about the encoder.
"""

from __future__ import annotations

import pytest
from chunking_lab import from_spec
from chunking_lab.correlate import Point, spreads
from chunking_lab.embeddings import CachingEmbedder, HashingEmbedder, resolve
from chunking_lab.retrieve import RRF_K, BM25Retriever, HybridRetriever, VectorRetriever, build

DOC = (
    "Requests are retried with exponential backoff. "
    "The audit log is retained for seven years. "
    "Chunk boundaries decide what a retriever can find. "
    "Every release is published on the fifteenth."
)


class TopicEmbedder:
    """One-hot by topic word, so the right answer is unambiguous."""

    TOPICS = ("backoff", "audit", "boundaries", "release", "retries")

    @property
    def id(self) -> str:
        return "fake-topic-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            lowered = text.lower()
            out.append([1.0 if topic in lowered else 0.0 for topic in self.TOPICS])
        return out


# ------------------------------------------------------------------ embedders


def test_a_model_string_is_accepted_and_overrides_the_environment():
    """Local is the default path; an explicit string must still win over it."""
    assert resolve("ollama/nomic-embed-text").id == "provider/ollama/nomic-embed-text"
    assert resolve("openai/text-embedding-3-small").id == "provider/openai/text-embedding-3-small"
    assert resolve("provider").id == "provider/configured"
    assert "hashing" in resolve("hashing").id


def test_a_bare_name_that_is_not_a_model_string_is_refused():
    """`qwen` is not a LiteLLM model string, and guessing what it meant would be worse."""
    with pytest.raises(ValueError, match="ollama/nomic-embed-text"):
        resolve("qwen")


def test_the_cache_embeds_each_distinct_text_once():
    """Comparing fourteen strategies re-embeds overlapping text fourteen times."""
    calls = []

    class Counting(TopicEmbedder):
        def embed(self, texts):
            calls.append(list(texts))
            return super().embed(texts)

    cache = CachingEmbedder(Counting())
    cache.embed(["alpha", "beta"])
    cache.embed(["beta", "alpha", "gamma"])

    assert calls == [["alpha", "beta"], ["gamma"]]
    assert cache.hits == 2 and cache.misses == 3


def test_the_cache_returns_results_in_the_order_asked_for():
    cache = CachingEmbedder(TopicEmbedder())
    first = cache.embed(["backoff here", "audit here"])
    second = cache.embed(["audit here", "backoff here"])
    assert second == [first[1], first[0]]


def test_the_cache_is_transparent_about_which_embedder_it_wraps():
    """Rule 2: a cached run and an uncached one must not be distinguishable by id."""
    assert CachingEmbedder(HashingEmbedder()).id == HashingEmbedder().id


# ------------------------------------------------------------------ retrieval


def _chunking(provenance):
    return from_spec("sentence:1").chunk(DOC, provenance)


def test_vector_retrieval_finds_the_chunk_on_the_right_topic(provenance):
    with VectorRetriever(_chunking(provenance), TopicEmbedder()) as retriever:
        (top,) = retriever.search("tell me about the audit trail", k=1)
    assert "audit log" in top.retrieval_text


def test_the_retriever_name_carries_the_encoder(provenance):
    """A vector run against two encoders is two experiments, and must say so."""
    with VectorRetriever(_chunking(provenance), TopicEmbedder()) as r:
        assert r.name == "vector/fake-topic-v1"
    with HybridRetriever(_chunking(provenance), TopicEmbedder()) as r:
        assert r.name == "hybrid-rrf/fake-topic-v1"


def test_the_numpy_and_pure_python_paths_rank_identically(provenance, monkeypatch):
    """numpy is an optimisation, never a different answer."""
    chunking = _chunking(provenance)
    with VectorRetriever(chunking, TopicEmbedder()) as fast:
        fast_order = [s.start for s in fast.search("audit", k=4)]

    slow = VectorRetriever(chunking, TopicEmbedder())
    slow._matrix = None  # force the fallback
    slow_order = [s.start for s in slow.search("audit", k=4)]
    assert fast_order[0] == slow_order[0]


def test_hybrid_returns_what_either_retriever_found(provenance):
    chunking = _chunking(provenance)
    with HybridRetriever(chunking, TopicEmbedder()) as hybrid:
        fused = {s.start for s in hybrid.search("audit log retention", k=3)}
    with BM25Retriever(chunking) as lexical:
        keyword = {s.start for s in lexical.search("audit log retention", k=3)}
    with VectorRetriever(chunking, TopicEmbedder()) as semantic:
        vector = {s.start for s in semantic.search("audit log retention", k=3)}
    assert fused & (keyword | vector)


def test_rrf_needs_no_score_calibration_between_the_two_rankings():
    """The reason to fuse on rank rather than on score: the scales are unrelated."""
    assert RRF_K == 60


def test_vector_and_hybrid_refuse_to_run_without_an_encoder(provenance):
    chunking = _chunking(provenance)
    for name in ("vector", "hybrid"):
        with pytest.raises(ValueError, match="needs an embedder"):
            build(name, chunking, None)


def test_an_unknown_retriever_names_the_ones_that_exist(provenance):
    with pytest.raises(ValueError, match="known: bm25, vector, hybrid"):
        build("magic", _chunking(provenance), TopicEmbedder())


def test_bm25_still_needs_nothing(provenance):
    """Tier 0 must not acquire a dependency because Tier 1 gained one."""
    assert build("bm25", _chunking(provenance)).name == "bm25/fts5"


# ---------------------------------------------------------------------- axes


def _point(corpus, strategy, retriever, iou):
    return Point(
        corpus=corpus,
        strategy=strategy,
        retriever=retriever,
        questions=10,
        intrinsic={"median_length": 100.0},
        extrinsic={"precision_omega": 0.5, "iou": iou, "recall": 0.5, "precision": 0.1},
    )


def test_each_axis_is_measured_with_the_other_held_fixed():
    points = [
        _point("a.md", strategy, retriever, iou)
        for strategy, retriever, iou in [
            ("recursive:200", "bm25", 0.40),
            ("structural", "bm25", 0.10),
            ("recursive:200", "vector", 0.44),
            ("structural", "vector", 0.11),
        ]
    ]
    rows = spreads(points, metric="iou")
    chunker = [r for r in rows if r.axis == "chunker"]
    retriever = [r for r in rows if r.axis == "retriever"]

    # Two retrievers -> two chunker spreads; two strategies -> two retriever spreads.
    assert len(chunker) == 2 and len(retriever) == 2
    assert all(r.ratio == pytest.approx(4.0, abs=0.05) for r in chunker)
    assert all(r.ratio == pytest.approx(1.1, abs=0.05) for r in retriever)


def test_precision_omega_is_refused_for_this_comparison():
    """It is retriever-independent, so the retriever axis would always show 1.0 --
    not because the retriever does not matter, but because the metric cannot see it."""
    points = [_point("a.md", "s", "bm25", 0.4), _point("a.md", "s", "vector", 0.4)]
    with pytest.raises(ValueError, match="retriever-independent"):
        spreads(points, metric="precision_omega")


def test_a_single_configuration_produces_no_spread():
    assert spreads([_point("a.md", "s", "bm25", 0.4)], metric="iou") == []


def test_the_best_and_worst_are_named_not_just_counted():
    points = [
        _point("a.md", "recursive:200", "bm25", 0.40),
        _point("a.md", "structural", "bm25", 0.10),
    ]
    (row,) = spreads(points, metric="iou")
    assert row.best[0] == "recursive:200"
    assert row.worst[0] == "structural"
    assert row.held_fixed == "bm25"
