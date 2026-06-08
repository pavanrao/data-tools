# docs-rag

Q&A over a local folder of documents (md/txt/pdf), with citations to the source
file. The full local RAG loop (idea #1).

```bash
uv run docs-rag index ./sample_docs
uv run docs-rag ask "what does the guide say about access?"
# or: python -m docs_rag ask "…"
```

Models come from `dt_shared` (Ollama by default; any LiteLLM provider via
`DATA_TOOLS_*` env vars). Design notes: [`docs/003_docs-rag.md`](../../docs/003_docs-rag.md).
