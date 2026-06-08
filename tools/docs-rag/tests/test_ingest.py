from docs_rag.ingest import Chunk, chunk_text, ingest_folder, load_file


def test_chunk_text_short_text_is_one_chunk():
    assert chunk_text("hello world", chunk_size=800) == ["hello world"]


def test_chunk_text_empty_is_no_chunks():
    assert chunk_text("   ", chunk_size=800) == []


def test_chunk_text_splits_long_text_with_overlap():
    text = "".join(str(i % 10) for i in range(2000))  # 2000 chars

    chunks = chunk_text(text, chunk_size=800, overlap=100)

    assert len(chunks) == 3
    assert all(len(c) <= 800 for c in chunks)
    # tail of one chunk overlaps the head of the next
    assert chunks[0][-100:] == chunks[1][:100]


def test_load_file_reads_text(tmp_path):
    p = tmp_path / "note.md"
    p.write_text("# Title\n\nsome body text", encoding="utf-8")

    assert "some body text" in load_file(p)


def test_ingest_folder_yields_chunks_tagged_with_source(tmp_path):
    (tmp_path / "a.txt").write_text("alpha content", encoding="utf-8")
    (tmp_path / "b.md").write_text("beta content", encoding="utf-8")
    (tmp_path / "ignore.bin").write_text("nope", encoding="utf-8")

    chunks = ingest_folder(tmp_path)

    assert all(isinstance(c, Chunk) for c in chunks)
    sources = {c.source for c in chunks}
    assert any(s.endswith("a.txt") for s in sources)
    assert any(s.endswith("b.md") for s in sources)
    assert not any(s.endswith("ignore.bin") for s in sources)
