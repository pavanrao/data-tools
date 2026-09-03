"""Command-line entry point for repo-rag.

repo-rag index <repo>      build the hybrid index
repo-rag ask "<question>"  answer a question with file:line citations
repo-rag serve             run the read-only MCP server over stdio
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .chunk import chunk_repo
from .query import answer
from .store import CodeStore

DEFAULT_DB = ".data/repo-rag.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-rag",
        description="Ask-your-codebase RAG with AST chunking and an MCP server.",
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to the index database.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Index a code repository.")
    p_index.add_argument("repo", help="Path to the repository root.")

    p_ask = sub.add_parser("ask", help="Ask a question about the codebase.")
    p_ask.add_argument("question")
    p_ask.add_argument("-k", type=int, default=5, help="Number of chunks to retrieve.")

    sub.add_parser("serve", help="Run the read-only MCP server (stdio).")

    return parser


def run_index(args: argparse.Namespace, *, embedder=None) -> None:
    if embedder is None:
        from data_tools_core.llm import get_embedding_provider

        embedder = get_embedding_provider()

    chunks = chunk_repo(args.repo)
    if not chunks:
        print(f"No code/text files found under {args.repo}")
        return

    embeddings = embedder.embed([c.text for c in chunks])

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)  # fresh index each run

    store = CodeStore(db_path, dim=len(embeddings[0]))
    store.add(chunks, embeddings)
    store.close()
    print(f"Indexed {len(chunks)} chunks from {args.repo} -> {args.db}")


def run_ask(args: argparse.Namespace, *, embedder=None, chat=None) -> None:
    if embedder is None:
        from data_tools_core.llm import get_embedding_provider

        embedder = get_embedding_provider()
    if chat is None:
        from data_tools_core.llm import get_chat_provider

        chat = get_chat_provider()

    store = CodeStore(args.db)
    result = answer(args.question, store=store, embedder=embedder, chat=chat, k=args.k)
    store.close()

    print(result.text)
    if result.citations:
        print("\nCitations:")
        for citation in result.citations:
            print(f"  - {citation}")


def run_serve(args: argparse.Namespace, *, embedder=None) -> None:
    if embedder is None:
        from data_tools_core.llm import get_embedding_provider

        embedder = get_embedding_provider()

    from .mcp_server import build_server

    store = CodeStore(args.db)
    build_server(store, embedder).run()


def main(argv: list[str] | None = None) -> None:
    """Ask your codebase: AST-aware retrieval with file:line citations."""
    args = build_parser().parse_args(argv)
    if args.command == "index":
        run_index(args)
    elif args.command == "ask":
        run_ask(args)
    elif args.command == "serve":
        run_serve(args)


if __name__ == "__main__":
    main()
