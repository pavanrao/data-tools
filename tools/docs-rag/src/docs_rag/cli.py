"""Command-line entry point: ``docs-rag index <folder>`` and ``docs-rag ask "<q>"``.

Providers default to the workspace's configured LLM/embeddings (Ollama out of
the box) but can be injected for testing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .ingest import ingest_folder
from .query import answer
from .store import VectorStore

DEFAULT_DB = ".data/docs-rag.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docs-rag", description="Q&A over a local document folder, with citations."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to the index database.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Index a folder of documents.")
    p_index.add_argument("folder", help="Folder of .md/.txt/.pdf files.")
    p_index.add_argument("--chunk-size", type=int, default=800)
    p_index.add_argument("--overlap", type=int, default=100)

    p_ask = sub.add_parser("ask", help="Ask a question against the index.")
    p_ask.add_argument("question")
    p_ask.add_argument("-k", type=int, default=5, help="Number of chunks to retrieve.")

    return parser


def run_index(args: argparse.Namespace, *, embedder=None) -> None:
    if embedder is None:
        from dt_shared import get_embedding_provider

        embedder = get_embedding_provider()

    chunks = ingest_folder(
        args.folder, chunk_size=args.chunk_size, overlap=args.overlap
    )
    if not chunks:
        print(f"No supported documents (.md/.txt/.pdf) found in {args.folder}")
        return

    embeddings = embedder.embed([c.text for c in chunks])

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)  # fresh index each run

    store = VectorStore(db_path, dim=len(embeddings[0]))
    store.add(chunks, embeddings)
    store.close()
    print(f"Indexed {len(chunks)} chunks from {args.folder} -> {args.db}")


def run_ask(args: argparse.Namespace, *, embedder=None, chat=None) -> None:
    if embedder is None:
        from dt_shared import get_embedding_provider

        embedder = get_embedding_provider()
    if chat is None:
        from dt_shared import get_chat_provider

        chat = get_chat_provider()

    store = VectorStore(args.db)
    result = answer(args.question, store=store, embedder=embedder, chat=chat, k=args.k)
    store.close()

    print(result.text)
    if result.sources:
        print("\nSources:")
        for source in result.sources:
            print(f"  - {source}")


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "index":
        run_index(args)
    elif args.command == "ask":
        run_ask(args)


if __name__ == "__main__":
    main()
