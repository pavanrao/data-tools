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

See [`IDEAS.md`](./IDEAS.md) for the running backlog of **48** tool ideas.
Sections **A–D** are RAG/MCP-focused tools and infrastructure; section **E**
(*Pipeline-framework tools*) adds generic data-pipeline plumbing.

Architecture decisions and per-tool design notes live in [`docs/`](./docs),
numbered sequentially (`001_…`, `002_…`). Start with
[`docs/001_architecture-and-decisions.md`](./docs/001_architecture-and-decisions.md).

Built so far: [`docs-rag`](./tools/docs-rag) (#1) and
[`repo-rag`](./tools/repo-rag) (#2).

## Repo layout

This is a **uv workspace**: one lockfile, one `uv sync`, but every tool is a
real, independently-importable package.

```
data-tools/
├── pyproject.toml        # umbrella metapackage + [tool.uv.workspace]
├── uv.lock               # one lock for the whole workspace
├── docs/                 # 001_, 002_, … plans + decision logs
├── shared/               # data-tools-shared  (import: dt_shared)
│   └── src/dt_shared/    #   model-pluggable LLM/embeddings layer (LiteLLM-backed)
└── tools/
    ├── docs-rag/         # one self-contained tool per directory
    └── repo-rag/
```

## Usage

```bash
uv sync                       # install the whole workspace + dev deps
uv run pytest                 # 41 tests, no live model needed (litellm mocked)

# Each tool runs on its own — as a console script or a module:
uv run docs-rag index ./docs && uv run docs-rag ask "…"
uv run python -m repo_rag serve
```

### Choosing a model

Tools depend only on `dt_shared`'s `EmbeddingProvider`/`ChatProvider` interfaces,
so you switch providers by config, not code. Defaults run locally on Ollama:

```bash
export DATA_TOOLS_CHAT_MODEL=ollama/llama3.1            # or anthropic/claude-…, openai/…
export DATA_TOOLS_EMBED_MODEL=ollama/nomic-embed-text
# export DATA_TOOLS_API_BASE / DATA_TOOLS_API_KEY as needed
```

Any [LiteLLM](https://docs.litellm.ai/) model string works.

## Spinning a tool out

Each tool is already a standalone package. To move one to its own repo:
`git subtree split -P tools/<name>` (keeps history) → push to a new repo → delete
the tool's one-line `[tool.uv.sources]` override → depend on the published
`data-tools-shared`. See [`docs/001`](./docs/001_architecture-and-decisions.md) (D4).
