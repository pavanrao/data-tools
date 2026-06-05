# data-tools

A growing collection of **small, independent data-pipeline tools** built to learn
**MCP (Model Context Protocol)** and **RAG (Retrieval-Augmented Generation)** in
practice.

## Principles

Every tool in this repo aims to be:

- **Independent** — each lives in its own directory, runs on its own, and shares
  nothing but conventions. No monolith.
- **Small** — one job, done well. If a tool needs a second job, it becomes a
  second tool.
- **Practical** — solves a real data-pipeline annoyance, not a toy.
- **Architecturally clean** — clear boundaries between ingestion, retrieval,
  LLM calls, and output. Swappable components.
- **Economical** — favors local LLMs (Ollama, llama.cpp) where quality allows,
  uses paid API keys only where they earn their cost, and caches aggressively.
- **Model-pluggable** — a single LLM/embeddings interface so any tool can run
  against a local model *or* a hosted API by changing config, not code.

## Learning goals

- Build and consume **MCP servers** (exposing tools, resources, and prompts).
- Build **RAG pipelines** end to end: chunking, embeddings, vector stores,
  retrieval strategies, reranking, and grounded generation.
- Understand the **cost/quality/latency** tradeoffs of local vs. hosted models.

## Where to start

See [`IDEAS.md`](./IDEAS.md) for the running backlog of **45** tool ideas. Pick one,
move it into a `tools/<name>/` directory, and build.

Sections **A–D** are RAG/MCP-focused tools and infrastructure. Section **E**
(*Pipeline-framework tools*) adds generic data-pipeline plumbing — ingestion,
lineage, data quality, reference data, and extracts — that any metadata-driven
platform can reuse.

## Repo layout (planned)

```
data-tools/
├── IDEAS.md              # backlog of tool ideas
├── README.md
├── shared/               # shared LLM/embeddings/MCP helpers (added as needed)
└── tools/
    └── <tool-name>/      # one self-contained tool per directory
```
