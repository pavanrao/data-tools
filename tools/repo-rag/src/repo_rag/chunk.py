"""Code-aware chunking.

Python files are split per top-level function/class using the standard-library
``ast`` module, so each chunk is a meaningful unit with a symbol name and exact
file:line span. Anything else (or unparseable Python) falls back to fixed
line-windows so no content is lost.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".sql", ".sh", ".md", ".txt",
}
IGNORE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".data",
}


@dataclass(frozen=True)
class CodeChunk:
    text: str
    path: str
    start_line: int
    end_line: int
    symbol: str | None
    kind: str  # "function" | "class" | "block"


def chunk_lines(
    source: str, path: str, *, lines_per_chunk: int = 60
) -> list[CodeChunk]:
    """Fallback: fixed line-windows, skipping all-blank windows."""
    lines = source.splitlines()
    chunks: list[CodeChunk] = []
    for i in range(0, len(lines), lines_per_chunk):
        window = lines[i : i + lines_per_chunk]
        if not any(line.strip() for line in window):
            continue
        chunks.append(
            CodeChunk(
                text="\n".join(window),
                path=path,
                start_line=i + 1,
                end_line=i + len(window),
                symbol=None,
                kind="block",
            )
        )
    return chunks


def chunk_python_source(source: str, path: str) -> list[CodeChunk]:
    """One chunk per top-level function/class; line-windows if that yields none."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return chunk_lines(source, path)

    lines = source.splitlines()
    chunks: list[CodeChunk] = []
    for node in tree.body:
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        start = node.lineno
        if node.decorator_list:
            start = min(start, *(d.lineno for d in node.decorator_list))
        end = node.end_lineno or node.lineno
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        chunks.append(
            CodeChunk(
                text="\n".join(lines[start - 1 : end]),
                path=path,
                start_line=start,
                end_line=end,
                symbol=node.name,
                kind=kind,
            )
        )

    return chunks or chunk_lines(source, path)


def chunk_source(source: str, path: str) -> list[CodeChunk]:
    if Path(path).suffix.lower() == ".py":
        return chunk_python_source(source, path)
    return chunk_lines(source, path)


def chunk_repo(root: str | Path) -> list[CodeChunk]:
    """Chunk every code/text file under ``root``, skipping noise directories."""
    chunks: list[CodeChunk] = []
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in CODE_SUFFIXES:
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        chunks.extend(chunk_source(source, str(path)))
    return chunks
