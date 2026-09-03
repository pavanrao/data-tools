from docs_rag import cli


class _FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class _FakeChat:
    def complete(self, prompt, **opts):
        return "Apples are red."


def test_parser_parses_index_and_ask():
    parser = cli.build_parser()

    a = parser.parse_args(["index", "somedir", "--chunk-size", "500"])
    assert a.command == "index"
    assert a.folder == "somedir"
    assert a.chunk_size == 500

    b = parser.parse_args(["--db", "x.db", "ask", "hi there", "-k", "3"])
    assert b.command == "ask"
    assert b.question == "hi there"
    assert b.k == 3
    assert b.db == "x.db"


def test_index_then_ask_roundtrip(tmp_path, capsys):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("apples are red", encoding="utf-8")
    db = tmp_path / "idx.db"

    index_args = cli.build_parser().parse_args(["--db", str(db), "index", str(folder)])
    cli.run_index(index_args, embedder=_FakeEmbedder())
    assert db.exists()

    ask_args = cli.build_parser().parse_args(["--db", str(db), "ask", "what colour?"])
    cli.run_ask(ask_args, embedder=_FakeEmbedder(), chat=_FakeChat())

    out = capsys.readouterr().out
    assert "Apples are red." in out
    assert "a.txt" in out  # source is cited
