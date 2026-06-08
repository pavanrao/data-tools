from repo_rag import cli


class _FakeEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


class _FakeChat:
    def complete(self, prompt, **opts):
        return "It lives in auth.py."


def test_parser_handles_index_ask_and_serve():
    parser = cli.build_parser()

    assert parser.parse_args(["index", "myrepo"]).command == "index"

    ask = parser.parse_args(["--db", "x.db", "ask", "where is auth?", "-k", "8"])
    assert ask.command == "ask"
    assert ask.question == "where is auth?"
    assert ask.k == 8

    assert parser.parse_args(["serve"]).command == "serve"


def test_index_then_ask_roundtrip(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "auth.py").write_text(
        "def authenticate(user):\n    return check(user)\n", encoding="utf-8"
    )
    db = tmp_path / "idx.db"

    index_args = cli.build_parser().parse_args(["--db", str(db), "index", str(repo)])
    cli.run_index(index_args, embedder=_FakeEmbedder())
    assert db.exists()

    ask_args = cli.build_parser().parse_args(["--db", str(db), "ask", "where is auth?"])
    cli.run_ask(ask_args, embedder=_FakeEmbedder(), chat=_FakeChat())

    out = capsys.readouterr().out
    assert "It lives in auth.py." in out
    assert "auth.py:1-2" in out  # file:line citation printed
