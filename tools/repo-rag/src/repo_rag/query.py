"""Answer codebase questions, grounded in hybrid-retrieved chunks with file:line cites."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .store import CodeHit


@dataclass
class Answer:
    text: str
    citations: list[str]


class _Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class _Chat(Protocol):
    def complete(self, prompt: str, **opts: object) -> str: ...


class _Store(Protocol):
    def search(
        self, query_embedding: Sequence[float], query_text: str, k: int = 5
    ) -> list[CodeHit]: ...


_INSTRUCTIONS = (
    "You are answering questions about a codebase using ONLY the snippets below. "
    "Cite the code you rely on as file:line (e.g. auth.py:1-5). "
    "If the answer is not in the snippets, say you don't know.\n\n"
)


def _cite(hit: CodeHit) -> str:
    return f"{hit.path}:{hit.start_line}-{hit.end_line}"


def build_prompt(question: str, hits: Sequence[CodeHit]) -> str:
    blocks = []
    for i, hit in enumerate(hits, 1):
        header = f"[{i}] {_cite(hit)}"
        if hit.symbol:
            header += f" ({hit.kind} {hit.symbol})"
        blocks.append(f"{header}\n{hit.text}")
    snippets = "\n\n".join(blocks)
    return f"{_INSTRUCTIONS}Snippets:\n{snippets}\n\nQuestion: {question}\nAnswer:"


def answer(
    question: str,
    *,
    store: _Store,
    embedder: _Embedder,
    chat: _Chat,
    k: int = 5,
) -> Answer:
    query_embedding = embedder.embed([question])[0]
    hits = store.search(query_embedding, question, k=k)
    text = chat.complete(build_prompt(question, hits))
    citations = list(dict.fromkeys(_cite(h) for h in hits))
    return Answer(text=text, citations=citations)
