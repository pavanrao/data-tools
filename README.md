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

**Built so far:**

- [`ingest-ledger`](./tools/ingest-ledger/) — reconciles what a document
  pipeline was *given* against what it actually *read*, so partial extraction
  stops being silent, and refuses to answer a question whose evidence never made
  it into the index. **Actively developed.**
- [`docs-rag`](./tools/docs-rag/) (#1) — Q&A over a local folder of documents
  with citations to the source file. *Parked.*
- [`repo-rag`](./tools/repo-rag/) (#2) — ask-your-codebase RAG with AST-aware
  chunking, hybrid retrieval, and a read-only MCP server. *Parked.*
- [`sqlite-mcp`](./tools/sqlite-mcp/) (#11) — read-only SQL over a SQLite file,
  as a CLI and an MCP server, with the limits enforced by the database rather
  than by reading the SQL. The first server written against protocol revision
  2026-07-28. **Actively developed.**

Parked means built and installed, but not under active development;
[`docs/FINDINGS.md`](./docs/FINDINGS.md) records why.

**New here?** [`tools/ingest-ledger/GETTING-STARTED.md`](./tools/ingest-ledger/GETTING-STARTED.md) is a
five-minute walkthrough that ends with the tool refusing to answer a question —
no prior RAG knowledge needed.

See [`IDEAS.md`](./IDEAS.md) for the running backlog of **217** tool ideas. Pick
one, move it into a `tools/<name>/` directory, and build.

**Before adding a tool**, read
[`docs/000_project-organization.md`](./docs/000_project-organization.md) — how
the project is shaped, why, and the checklist for adding the next one.
[`CONVENTIONS.md`](./CONVENTIONS.md) is the short normative version;
[`docs/`](./docs/) holds the decision log, the design records, and the running
learnings/findings.

Sections **A–D** are RAG/MCP-focused tools and infrastructure. Section **E**
(*Pipeline-framework tools*) adds generic data-pipeline plumbing — ingestion,
lineage, data quality, reference data, and extracts — that any metadata-driven
platform can reuse. Sections **F–G** (*Concept labs* and *Concept
notes*) work the other way round: they start from a concept that recurs across
AI and data engineering and build the smallest thing that exercises it for real,
ending in a measured number rather than a description.
[`docs/005_concept-coverage.md`](./docs/005_concept-coverage.md) maps all 103
concepts to what covers each, and sets out what makes a tool ready to show
someone.

Sections **H–J** come at it from a third direction: *enterprise data-engineering
problems* — legacy onboarding, lineage, contracts, migration — where a language
model is genuinely load-bearing rather than decorative. Every entry states its
**agentic core**, which is the bar for being in there at all. Three tiers by
ambition: **H** small and sharp, **I** bounded agents doing one enterprise job,
**J** full systems, where the "small tool" rule is waived on purpose.

Section **K** is a class of its own: 🔒 **metadata-plane** agents that work from
schema, infrastructure, logs and code and **never read a row**. That is a
deployment property — no data-residency review, no PII assessment, no production
data access — so they can run in CI against a repository and a catalogue export.

Section **L** takes data access back, and pays for it with a stricter bar: the
loop *is* the solution — hypothesis, query, revise, where what to look at next is
not knowable until you have looked. Single-prompt work does not qualify, so every
entry names the simpler approach and says where it fails. These run where the data
already is, on an on-prem or private-cloud model.

Section **M** turns the lens on the plumbing. It is the only section where the
*protocol* is the subject rather than the delivery mechanism, and it exists
because MCP changed shape in revision **2026-07-28** — no handshake, no sessions,
long-running work moved to an extension, Roots and Sampling deprecated. Every
entry names the mechanism it exercises and has to be materially worse as a plain
CLI. Two tiers: ten **protocol labs** that each end in a measured number, and ten
**servers that do not exist in the industry today**. Section **B** is the
original six, rewritten against the same revision, and now reads as the starter
set that leads into M.

## Repo layout

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) of
independent packages. The root is not a package — it exists so `uv sync` gives
you a dev environment spanning every tool.

```
data-tools/
├── IDEAS.md                  # backlog of tool ideas
├── CONVENTIONS.md            # the shape every tool follows
├── pyproject.toml            # workspace root; shared lint/test config
├── docs/                     # decisions, design records, learnings, findings
├── shared/
│   └── data-tools-core/      # provenance, ledger schema, `dt` CLI, optional model layer
└── tools/
    ├── ingest-ledger/        # one installable distribution per tool
    ├── docs-rag/
    └── repo-rag/
```

## Using the collection — whole or in parts

Tools never import each other. They compose along three seams, so any one of
them is useful alone and all of them are useful together.

| Seam | In parts | As a whole |
| --- | --- | --- |
| **CLI** | `uvx --from "git+https://github.com/pavanrao/data-tools#subdirectory=tools/ingest-ledger" ingest-ledger` | `dt ls` discovers every installed tool via the `data_tools.tools` entry-point group |
| **Data** | each tool reads and writes plain files | a shared SQLite ledger and JSONL records carrying a common `Provenance` type |
| **MCP** | a tool may expose a server factory, as `repo-rag` does | `mcp-gateway` (#16) mounts every installed one behind a single endpoint via the `data_tools.mcp` entry-point group |

```bash
make sync    # dev environment for the whole collection
make lint    # ruff check + format --check
make test    # every tool's tests
make demo    # build the hostile corpus and reconcile it
```

### Choosing a model

The model layer is **optional**: every tool's deterministic core runs and is
tested with no model stack installed. Install one with `uv sync --extra llm`,
then point the tools at any [LiteLLM](https://docs.litellm.ai/) model string —
config, not code. Defaults run locally on Ollama:

```bash
export DATA_TOOLS_CHAT_MODEL=ollama/llama3.1            # or anthropic/…, openai/…
export DATA_TOOLS_EMBED_MODEL=ollama/nomic-embed-text
# export DATA_TOOLS_API_BASE / DATA_TOOLS_API_KEY as needed
```

### Spinning a tool out

Each tool is already a standalone distribution. To move one to its own repo:
`git subtree split -P tools/<name>` (keeps history) → push → delete that tool's
one `[tool.uv.sources]` block → depend on the published `data-tools-core`. See
[`docs/000` §5](./docs/000_project-organization.md#5-the-spin-out-seam).
