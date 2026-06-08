from repo_rag.chunk import CodeChunk, chunk_lines, chunk_python_source, chunk_source

PY_SAMPLE = '''\
import os


def foo(x):
    return x + 1


class Bar:
    def method(self):
        return 2
'''


def test_chunk_python_extracts_top_level_function():
    chunks = chunk_python_source(PY_SAMPLE, "m.py")

    foo = next(c for c in chunks if c.symbol == "foo")
    assert foo.kind == "function"
    assert foo.path == "m.py"
    assert foo.start_line == 4
    assert foo.end_line == 5
    assert "return x + 1" in foo.text


def test_chunk_python_extracts_top_level_class():
    chunks = chunk_python_source(PY_SAMPLE, "m.py")

    bar = next(c for c in chunks if c.symbol == "Bar")
    assert bar.kind == "class"
    assert bar.start_line == 8
    assert "def method" in bar.text


def test_chunk_python_includes_decorators_in_span():
    src = "@deco\ndef wrapped():\n    return 1\n"

    chunk = chunk_python_source(src, "d.py")[0]

    assert chunk.symbol == "wrapped"
    assert chunk.start_line == 1  # decorator line, not the def line
    assert "@deco" in chunk.text


def test_chunk_python_falls_back_to_lines_when_no_defs():
    chunks = chunk_python_source("x = 1\ny = 2\n", "c.py")

    assert chunks
    assert all(c.symbol is None and c.kind == "block" for c in chunks)


def test_chunk_lines_windows_with_line_numbers():
    chunks = chunk_lines("line1\nline2\nline3\n", "notes.txt", lines_per_chunk=2)

    assert len(chunks) == 2
    assert chunks[0].start_line == 1 and chunks[0].end_line == 2
    assert chunks[1].start_line == 3 and chunks[1].end_line == 3
    assert chunks[0].kind == "block"


def test_chunk_source_dispatches_on_suffix():
    assert chunk_source("def f():\n    pass\n", "a.py")[0].kind == "function"
    assert chunk_source("hello world\n", "a.md")[0].kind == "block"


def test_chunk_python_invalid_syntax_falls_back_to_lines():
    chunks = chunk_source("def broken(\n", "bad.py")

    assert isinstance(chunks[0], CodeChunk)
    assert chunks[0].kind == "block"
