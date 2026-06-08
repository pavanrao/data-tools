# 001 — Architecture & Decisions

Decision log (ADR-style) for how `data-tools` is structured. Written when the
first two tools were built. Every later feature/tool adds the next-numbered doc.

## Context

`data-tools` builds the 48 tool ideas in [`IDEAS.md`](../IDEAS.md) as a way to
learn MCP and RAG. Before writing code we had to settle how the repo is
organized so that:

1. **UV** manages all Python.
2. It releases as **one thing**, yet each tool is **importable and invokable
   independently**.
3. Tools are **model-pluggable** — start on Ollama, switch to any provider by
   config, not code.
4. A tool that grows or gets popular can be **spun out into its own repo** with
   minimal friction and with its history intact.

## Decisions

### D1 — uv **workspace**, not a single src-layout package

**Options weighed:** (a) one package with a subpackage per tool + extras; (b) a
uv *workspace* where each tool is its own package, plus a shared library and an
umbrella root.

**Chosen: (b) workspace.** It honors the repo's "independent, no-monolith"
principle (each tool is a real package with its own `pyproject.toml`, `src/`,
`tests/`, and entry point) and is the cleanest base for spin-out (D4). The
umbrella root metapackage (`data-tools`) depends on the members, so `uv sync`
installs everything and a single `pip install data-tools` would too — giving the
"one releasable thing" property without forcing a monolith.

**Trade-off accepted:** slightly more packaging ceremony than a single package;
"one package" is really "one workspace / umbrella."

### D2 — Model-pluggability via narrow interfaces backed by **LiteLLM**

Tools depend only on `dt_shared`'s `EmbeddingProvider` / `ChatProvider`
protocols — never on LiteLLM or any vendor directly. The concrete
implementations wrap LiteLLM, so switching providers is a model-string change
(`ollama/llama3.1` → `anthropic/claude-3-5-sonnet`) set via `DATA_TOOLS_*` env
vars. Defaults run fully locally on Ollama (≈$0). This is the seed of the
`model-router` idea (#24).

**Why LiteLLM over a homegrown provider per backend:** one dependency speaks
Ollama, Anthropic, OpenAI, etc.; we keep our *own* interface in front so tools
stay decoupled and a different backend could replace LiteLLM later without
touching any tool.

### D3 — Storage: **sqlite-vec** (+ FTS5 for repo-rag), official **mcp** SDK

SQLite keeps everything file-based and dependency-light. `sqlite-vec` provides
vector KNN; FTS5 (built into SQLite) provides keyword search for repo-rag's
hybrid retrieval. MCP servers use the official `mcp` Python SDK (`FastMCP`).

### D4 — Spin-out seam via `[tool.uv.sources]`

Each tool declares a normal dependency `data-tools-shared>=0.1` and a **dev-only**
override `[tool.uv.sources] data-tools-shared = { workspace = true }`. In
development uv resolves it from the local `shared/` package; deleting that one
line makes it resolve from a published wheel. Rules kept from day one so this
stays a non-event:

- Tools import only `dt_shared`, **never each other**.
- Everything a tool needs lives under its own directory.
- `dt_shared` is versioned like a real library.

Spin-out recipe: `git subtree split -P tools/<name>` → push to a new repo → drop
the `[tool.uv.sources]` line → depend on the published `data-tools-shared`.

### D5 — TDD throughout, **litellm mocked**

Red→green→refactor for every unit. The test suite never needs a live model:
`dt_shared` tests mock `litellm`; each tool's tests inject a deterministic fake
`EmbeddingProvider`/`ChatProvider`. Result: 41 fast, hermetic tests.

### D6 — Tools built first: `docs-rag` (#1) and `repo-rag` (#2)

The literal first two ideas. docs-rag exercises the full local RAG loop;
repo-rag adds AST-aware chunking, hybrid retrieval, and an MCP server — together
covering both axes (RAG + MCP) the repo exists to teach.

## Other defaults

- Python **3.13**; CLIs use stdlib **argparse**; pytest in `--import-mode=importlib`.
- repo-rag AST chunking starts **Python-only** (`ast`); tree-sitter multi-language
  is a deliberate later iteration.
- Shared dist name **`data-tools-shared`**, import package **`dt_shared`**.

See [002 — Implementation Plan](002_implementation-plan.md) for the build itself.
