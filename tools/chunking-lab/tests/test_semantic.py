"""Tier 1: semantic chunking, tested with no model installed.

Every test here injects a fake embedder. That is CONVENTIONS rule 6 -- the suite
needs no network and no model stack -- but it is also the only way to test these
chunkers *as algorithms*: with a controlled embedding, "where should this cut?"
has a right answer, and a real encoder would turn every assertion into a
judgement call about the encoder.
"""

from __future__ import annotations

import pytest
from chunking_lab import check, from_spec
from chunking_lab.chunkers.semantic import (
    ClusterSemanticChunker,
    PercentileSemanticChunker,
    _percentile,
)
from chunking_lab.embeddings import HashingEmbedder, ProviderEmbedder, cosine, resolve


class TopicEmbedder:
    """Maps a sentence to a one-hot vector by the topic word it contains.

    Sentences on the same topic are identical (distance 0); sentences on different
    topics are orthogonal (distance 1). So the correct cut is unambiguous and any
    assertion below is about the chunker, not about an encoder's opinion.
    """

    TOPICS = ("alpha", "beta", "gamma")

    @property
    def id(self) -> str:
        return "fake-topic-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * len(self.TOPICS)
            for i, topic in enumerate(self.TOPICS):
                if topic in text.lower():
                    vector[i] = 1.0
            vectors.append(vector or [0.0] * len(self.TOPICS))
        return vectors


TWO_TOPICS = (
    "Alpha one here. Alpha two here. Alpha three here. "
    "Beta one here. Beta two here. Beta three here."
)


def test_the_percentile_chunker_cuts_at_the_topic_change(provenance):
    chunker = PercentileSemanticChunker(percentile=90, buffer=0, embedder=TopicEmbedder())
    chunking = chunker.chunk(TWO_TOPICS, provenance)
    check(chunking, TWO_TOPICS)

    assert len(chunking) == 2
    assert chunking.spans[0].retrieval_text == "Alpha one here. Alpha two here. Alpha three here."
    assert chunking.spans[1].retrieval_text == "Beta one here. Beta two here. Beta three here."


def test_a_lower_percentile_cuts_more_often(prose, provenance):
    """The threshold is a percentile of the document's own distances, so it scales.

    Uses the hashing embedder rather than the one-hot fake: this needs *graded*
    distances to say anything, and one-hot only ever produces 0 or 1.
    """
    coarse = PercentileSemanticChunker(percentile=90, buffer=0, embedder=HashingEmbedder())
    fine = PercentileSemanticChunker(percentile=10, buffer=0, embedder=HashingEmbedder())
    assert len(fine.chunk(prose, provenance)) > len(coarse.chunk(prose, provenance))


def test_a_uniform_passage_is_not_shredded(provenance):
    """The regression behind the strict `>`: identical sentences have identical
    distances, so a `>=` threshold cuts between every pair of them."""
    text = " ".join(f"Alpha sentence number {i}." for i in range(30))
    chunker = PercentileSemanticChunker(percentile=99, buffer=0, embedder=TopicEmbedder())
    assert len(chunker.chunk(text, provenance)) == 1


def test_the_max_size_cap_overrides_a_run_of_similar_sentences(provenance):
    """Without a cap, a long uniform passage becomes one enormous chunk."""
    text = " ".join(f"Alpha sentence number {i}." for i in range(30))
    uncapped = PercentileSemanticChunker(percentile=99, buffer=0, embedder=TopicEmbedder())
    capped = PercentileSemanticChunker(
        percentile=99, max_size=120, buffer=0, embedder=TopicEmbedder()
    )
    assert len(uncapped.chunk(text, provenance)) == 1
    capped_chunking = capped.chunk(text, provenance)
    assert len(capped_chunking) > 1
    assert all(span.length <= 120 for span in capped_chunking.spans)


def test_the_buffer_widens_only_the_embedding_input_not_the_span(provenance):
    """A lone sentence often has too little signal; its neighbours disambiguate it."""
    seen: list[str] = []

    class Recording(TopicEmbedder):
        def embed(self, texts):
            seen.extend(texts)
            return super().embed(texts)

    chunker = PercentileSemanticChunker(percentile=90, buffer=1, embedder=Recording())
    chunking = chunker.chunk(TWO_TOPICS, provenance)
    check(chunking, TWO_TOPICS)

    # The embedded text for the middle sentence spans three sentences ...
    assert any(text.count(".") == 3 for text in seen)
    # ... but every span still addresses exactly the document.
    for span in chunking.spans:
        assert TWO_TOPICS[span.start : span.end] == span.retrieval_text


def test_the_cluster_chunker_partitions_by_topic(provenance):
    chunker = ClusterSemanticChunker(max_size=60, piece=40, embedder=TopicEmbedder())
    chunking = chunker.chunk(TWO_TOPICS, provenance)
    check(chunking, TWO_TOPICS)

    for span in chunking.spans:
        body = span.retrieval_text.lower()
        assert not ("alpha" in body and "beta" in body), (
            f"a chunk straddles the topic boundary: {span.retrieval_text!r}"
        )


def test_the_cluster_chunker_respects_its_max_size(provenance):
    text = " ".join(f"Alpha sentence number {i}." for i in range(20))
    chunking = ClusterSemanticChunker(max_size=100, piece=30, embedder=TopicEmbedder()).chunk(
        text, provenance
    )
    assert all(span.length <= 100 for span in chunking.spans)


def test_a_globally_optimal_partition_can_beat_the_greedy_one(provenance):
    """Why the dynamic program exists at all, rather than another threshold."""
    text = "Alpha one. Beta one. Beta two. Beta three. Beta four. Alpha two."
    clustered = ClusterSemanticChunker(max_size=60, piece=30, embedder=TopicEmbedder()).chunk(
        text, provenance
    )
    check(clustered, text)
    # The four beta sentences belong together; a purely local rule would have to
    # decide each gap without seeing the run.
    assert any(span.retrieval_text.lower().count("beta") >= 2 for span in clustered.spans)


def test_every_tier_1_result_records_which_embedder_produced_it(provenance):
    """Rule 2: never silently substitute, always record the path that ran."""
    fake = PercentileSemanticChunker(percentile=90, embedder=TopicEmbedder())
    offline = PercentileSemanticChunker(percentile=90, embedder=HashingEmbedder())

    assert fake.chunk(TWO_TOPICS, provenance).code_path == "tier-1/embeddings:fake-topic-v1"
    assert "hashing-bow-v1" in offline.chunk(TWO_TOPICS, provenance).code_path


def test_a_tier_0_result_is_marked_model_free(prose, provenance):
    assert from_spec("recursive:200").chunk(prose, provenance).code_path == "tier-0/model-free"


def test_constructing_a_provider_embedder_does_not_need_the_extra():
    """Resolution is lazy, so `from_spec` stays total on a machine with no backend."""
    embedder = ProviderEmbedder(model="openai/text-embedding-3-small")
    assert "text-embedding-3-small" in embedder.id
    assert embedder._provider is None


def test_an_unknown_embedder_is_refused_with_a_usable_example():
    """`magic` is not a LiteLLM model string, and guessing what was meant is worse
    than saying so -- the error names the shape a model string actually has."""
    with pytest.raises(ValueError, match="ollama/nomic-embed-text"):
        resolve("magic")


def test_the_hashing_embedder_is_deterministic():
    """It is weak, but it must not be random -- a run has to be reproducible."""
    first = HashingEmbedder().embed(["the pipeline read every file"])
    second = HashingEmbedder().embed(["the pipeline read every file"])
    assert first == second
    assert cosine(first[0], first[0]) == pytest.approx(1.0)


def test_semantic_specs_round_trip_and_validate():
    assert from_spec("semantic:95").name == "semantic:95"
    assert from_spec("semantic:95/2000").name == "semantic:95/2000"
    assert from_spec("cluster-semantic:400").name == "cluster-semantic:400"
    assert from_spec("cluster-semantic:400/50").name == "cluster-semantic:400/50"

    with pytest.raises(ValueError, match="percentile must be in"):
        from_spec("semantic:100")
    with pytest.raises(ValueError, match="needs a percentile"):
        from_spec("semantic")
    with pytest.raises(ValueError, match="needs a max size"):
        from_spec("cluster-semantic")


def test_percentile_interpolates_rather_than_degenerating_on_short_documents():
    assert _percentile([], 50) == 0.0
    assert _percentile([0.4], 95) == 0.4
    assert _percentile([0.0, 1.0], 50) == pytest.approx(0.5)


def test_a_document_with_one_sentence_still_produces_a_span(provenance):
    text = "Only one sentence here."
    for spec in ("semantic:95", "cluster-semantic:400"):
        chunking = from_spec(spec).chunk(text, provenance)
        check(chunking, text)
        assert len(chunking) == 1
