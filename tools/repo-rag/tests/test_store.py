from repo_rag.chunk import CodeChunk
from repo_rag.store import CodeStore


def _seed(store):
    chunks = [
        CodeChunk(
            "def authenticate(user):\n    return check(user)",
            "auth.py", 1, 2, "authenticate", "function",
        ),
        CodeChunk(
            "def render_page():\n    return html",
            "views.py", 10, 11, "render_page", "function",
        ),
    ]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    store.add(chunks, embeddings)


def test_vector_search_returns_nearest(tmp_path):
    store = CodeStore(tmp_path / "r.db", dim=3)
    _seed(store)

    hits = store.search_vector([0.9, 0.1, 0.0], k=1)

    assert hits[0].symbol == "authenticate"
    assert hits[0].path == "auth.py"


def test_keyword_search_finds_by_term(tmp_path):
    store = CodeStore(tmp_path / "r.db", dim=3)
    _seed(store)

    hits = store.search_keyword("render", k=5)

    assert [h.symbol for h in hits] == ["render_page"]


def test_hybrid_surfaces_both_vector_and_keyword_matches(tmp_path):
    store = CodeStore(tmp_path / "r.db", dim=3)
    _seed(store)

    # vector points at render_page; keyword points at authenticate
    hits = store.search([0.0, 1.0, 0.0], "authenticate", k=2)

    symbols = {h.symbol for h in hits}
    assert symbols == {"authenticate", "render_page"}


def test_get_chunk_round_trips(tmp_path):
    store = CodeStore(tmp_path / "r.db", dim=3)
    _seed(store)
    hit = store.search_vector([1.0, 0.0, 0.0], k=1)[0]

    got = store.get_chunk(hit.chunk_id)

    assert got.symbol == "authenticate"
    assert got.start_line == 1
    assert "check(user)" in got.text


def test_reopen_reads_dim(tmp_path):
    db = tmp_path / "r.db"
    seeded = CodeStore(db, dim=3)
    _seed(seeded)

    reopened = CodeStore(db)

    assert reopened.dim == 3
    assert reopened.search_vector([1.0, 0.0, 0.0], k=1)[0].symbol == "authenticate"
