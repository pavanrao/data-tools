"""Retrieve relevant chunks and ask the model to answer, grounded with citations.

The model only ever sees retrieved context; it is instructed to cite sources by
bracket number and to admit when the answer isn't present. Providers are passed
in (dependency injection) so this is testable without a live model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .store import SearchResult


@dataclass
class Answer:
    text: str
    sources: list[str]


class _Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class _Chat(Protocol):
    def complete(self, prompt: str, **opts: object) -> str: ...


class _Store(Protocol):
    def search(
        self, query_embedding: Sequence[float], k: int = 5
    ) -> list[SearchResult]: ...


_INSTRUCTIONS = (
    "Answer the question using ONLY the context below. "
    "Cite the sources you use with their bracket numbers like [1]. "
    "If the answer is not in the context, say you don't know.\n\n"
)


def build_prompt(question: str, results: Sequence[SearchResult]) -> str:
    blocks = [
        f"[{i}] (source: {r.source})\n{r.text}" for i, r in enumerate(results, 1)
    ]
    context = "\n\n".join(blocks)
    return f"{_INSTRUCTIONS}Context:\n{context}\n\nQuestion: {question}\nAnswer:"


def answer(
    question: str,
    *,
    store: _Store,
    embedder: _Embedder,
    chat: _Chat,
    k: int = 5,
) -> Answer:
    query_embedding = embedder.embed([question])[0]
    results = store.search(query_embedding, k=k)
    prompt = build_prompt(question, results)
    text = chat.complete(prompt)
    sources = list(dict.fromkeys(r.source for r in results))
    return Answer(text=text, sources=sources)
