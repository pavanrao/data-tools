# 003 — docs-rag

**Idea #1.** Q&A over a local folder of documents, with citations to the source
file. The full RAG loop, runnable locally for free.

## Pipeline

```
folder ─▶ ingest ─▶ chunks ─▶ embed ─▶ sqlite-vec store
                                              │
question ─▶ embed ─▶ search(top-k) ─▶ grounded prompt ─▶ ChatProvider ─▶ answer + sources
```

## Modules (`tools/docs-rag/src/docs_rag/`)

- **`ingest.py`** — `load_file` (md/txt/pdf; PDF via `pypdf`, imported lazily
  so it can ship as the `pdf` extra), `chunk_text`
  (overlapping char windows, default 800/100), `ingest_folder` → `list[Chunk]`
  where `Chunk(text, source, ordinal)`. Pure and model-free.
- **`store.py`** — `VectorStore` over SQLite + sqlite-vec. Chunk text/metadata in
  a `chunks` table; embeddings in a `vec0` virtual table joined by rowid. The
  embedding `dim` is persisted in a `meta` table so a store reopens for querying
  without re-specifying it. KNN uses the `k = ?` constraint sqlite-vec requires.
- **`query.py`** — `build_prompt` (numbered context blocks tagged with source) and
  `answer(...)`, which embeds the question, retrieves top-k, prompts the chat
  provider to cite `[n]` and to say "I don't know" when unsupported. Providers
  are injected (testable without a model).
- **`cli.py`** — `docs-rag index <folder>` and `docs-rag ask "<q>"`; also
  `python -m docs_rag`. Default index at `.data/docs-rag.db`; re-index is fresh.

## Design notes

- The LLM **only ever sees retrieved context** and is asked to ground + cite.
  Determinism (chunking, storage, retrieval) is in code; only narration is the model.
- Tests use a deterministic fake embedder, so retrieval ordering is asserted
  exactly without any model.

## Try it (local, $0)

```bash
ollama pull nomic-embed-text && ollama pull llama3.1
uv run docs-rag index ./sample_docs
uv run docs-rag ask "what does the onboarding guide say about access?"
```

## Possible next steps

- Reranking; API generation mode for hard questions; embeddings cache (#23) keyed
  by content hash; richer PDF/section citations.
