from docs_rag.ingest import Chunk
from docs_rag.store import VectorStore


def _seed(store):
    chunks = [
        Chunk("apples are red", "fruit.txt", 0),
        Chunk("the sky is blue", "sky.txt", 0),
    ]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    store.add(chunks, embeddings)


def test_add_and_search_returns_nearest_first(tmp_path):
    store = VectorStore(tmp_path / "t.db", dim=3)
    _seed(store)

    results = store.search([0.9, 0.1, 0.0], k=2)

    assert len(results) == 2
    assert results[0].text == "apples are red"
    assert results[0].source == "fruit.txt"


def test_search_respects_k(tmp_path):
    store = VectorStore(tmp_path / "t.db", dim=3)
    _seed(store)

    assert len(store.search([0.9, 0.1, 0.0], k=1)) == 1


def test_reopened_store_knows_its_dim_and_keeps_data(tmp_path):
    db = tmp_path / "t.db"
    VectorStore(db, dim=3).add([Chunk("apples are red", "fruit.txt", 0)], [[1.0, 0.0, 0.0]])

    reopened = VectorStore(db)  # dim not supplied — must be read back

    assert reopened.dim == 3
    assert reopened.search([1.0, 0.0, 0.0], k=1)[0].source == "fruit.txt"
