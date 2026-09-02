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

**Built so far:** [`ingest-ledger`](./tools/ingest-ledger/) — reconciles what a
document pipeline was *given* against what it actually *read*, so partial
extraction stops being silent, and refuses to answer a question whose evidence
never made it into the index.

**New here?** [`docs/getting-started.md`](./docs/getting-started.md) is a
five-minute walkthrough that ends with the tool refusing to answer a question —
no prior RAG knowledge needed.

See [`IDEAS.md`](./IDEAS.md) for the running backlog of **49** tool ideas. Pick
one, move it into a `tools/<name>/` directory, and build. [`CONVENTIONS.md`](./CONVENTIONS.md)
describes the shape every tool follows.

Sections **A–D** are RAG/MCP-focused tools and infrastructure. Section **E**
(*Pipeline-framework tools*) adds generic data-pipeline plumbing — ingestion,
lineage, data quality, reference data, and extracts — that any metadata-driven
platform can reuse.

## Repo layout

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) of
independent packages. The root is not a package — it exists so `uv sync` gives
you a dev environment spanning every tool.

```
data-tools/
├── IDEAS.md                  # backlog of tool ideas
├── CONVENTIONS.md            # the shape every tool follows
├── pyproject.toml            # workspace root; shared lint/test config
├── shared/
│   └── data-tools-core/      # provenance, ledger schema, the `dt` meta-CLI
└── tools/
    └── ingest-ledger/        # one installable distribution per tool
```

## Using the collection — whole or in parts

Tools never import each other. They compose along three seams, so any one of
them is useful alone and all of them are useful together.

| Seam | In parts | As a whole |
| --- | --- | --- |
| **CLI** | `uvx --from "git+https://github.com/pavanrao/data-tools#subdirectory=tools/ingest-ledger" ingest-ledger` | `dt ls` discovers every installed tool via the `data_tools.tools` entry-point group |
| **Data** | each tool reads and writes plain files | a shared SQLite ledger and JSONL records carrying a common `Provenance` type |
| **MCP** | a tool may expose `<package>.mcp:server` | `mcp-gateway` (#16) mounts every installed one behind a single endpoint |

```bash
make sync    # dev environment for the whole collection
make test    # every tool's tests
make demo    # build the hostile corpus and reconcile it
```
