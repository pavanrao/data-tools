# 001 — Architecture & Decisions

Decision log (ADR-style) for how `data-tools` is structured. Originally written
when the first two RAG tools were built, on the `build-docs-rag-repo-rag`
branch, before `ingest-ledger` existed.

**This document is append-only.** Decisions later overturned are annotated in
place with a *Status* line and a pointer to what replaced them — never deleted.
The reasoning is the point: a decision you can no longer reconstruct is one you
will make badly a second time.

For the current shape of the project, read
[`000_project-organization.md`](000_project-organization.md). This file is why
it is that shape.

## Context

`data-tools` builds the 49 tool ideas in [`IDEAS.md`](../IDEAS.md) as a way to
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

> **Status: current.**

**Options weighed:** (a) one package with a subpackage per tool + extras; (b) a
uv *workspace* where each tool is its own package, plus a shared library and an
umbrella root.

**Chosen: (b) workspace.** It honors the repo's "independent, no-monolith"
principle (each tool is a real package with its own `pyproject.toml`, `src/`,
`tests/`, and entry point) and is the cleanest base for spin-out (D4).

**Trade-off accepted:** slightly more packaging ceremony than a single package.

### D1a — The root as an umbrella metapackage

> **Status: superseded** (2026-09, when `ingest-ledger` merged). The workspace
> root is now explicitly **not a package**.

**Original reasoning, preserved.** The umbrella root metapackage (`data-tools`)
depended on every member, so `uv sync` installed everything and a single
`pip install data-tools` would too — giving the "one releasable thing" property
of requirement 2 without forcing a monolith. It was a code-less package via
hatchling's `bypass-selection = true`.

**Why it was replaced.** The `ingest-ledger` line of work took requirement 2 in
the other direction: the strongest form of "each tool is independent" is that
*nothing at the root is needed to run one*. A root that is installable invites
exactly the coupling the workspace exists to prevent, and "install the whole
collection" is served well enough by `uv sync` for developers and by per-tool
`uvx --from git+…#subdirectory=tools/<name>` for users.

**What was given up:** there is no longer a single `pip install data-tools` that
pulls in every tool. That was judged a fair price for a root that cannot become
a dependency.

### D2 — Model-pluggability via narrow interfaces backed by **LiteLLM**

> **Status: current**, with one amendment — the model layer is now **optional**
> and lives at `data_tools_core.llm` rather than in a separate `dt_shared`
> distribution. See D2a.

Tools depend only on the `EmbeddingProvider` / `ChatProvider` protocols — never
on LiteLLM or any vendor directly. The concrete implementations wrap LiteLLM, so
switching providers is a model-string change (`ollama/llama3.1` →
`anthropic/claude-sonnet-4-5`) set via `DATA_TOOLS_*` env vars. Defaults run
fully locally on Ollama (≈$0). This is the seed of the `model-router` idea (#24).

**Why LiteLLM over a homegrown provider per backend:** one dependency speaks
Ollama, Anthropic, OpenAI, etc.; we keep our *own* interface in front so tools
stay decoupled and a different backend could replace LiteLLM later without
touching any tool.

### D2a — The model layer is optional, and lazily imported

> **Status: current.** Added 2026-09 when the layer moved into
> `data-tools-core`.

`CONVENTIONS.md` rule 3 requires that a tool's deterministic core run — and be
tested — with no model stack installed, on the grounds that "a tool that cannot
run without a model is a tool that cannot be tested." D2 as originally built
made `litellm` a hard dependency of the shared library, which would have
violated that the moment the two libraries merged.

**Resolution:** the protocols and factories live in `data_tools_core.llm`, but
`litellm` is imported *inside the call*, and ships as the `llm` extra. Importing
the module never pulls a model stack. `config.py` was rewritten stdlib-only for
the same reason — `data-tools-core` keeps `dependencies = []`.

This strengthened D5: the model is no longer merely *mockable*, it is *absent*.

### D3 — Storage: **sqlite-vec** (+ FTS5 for repo-rag), official **mcp** SDK

> **Status: current.**

SQLite keeps everything file-based and dependency-light. `sqlite-vec` provides
vector KNN; FTS5 (built into SQLite) provides keyword search for repo-rag's
hybrid retrieval. MCP servers use the official `mcp` Python SDK.

**Amendment (2026-09), resolved:** the SDK was briefly pinned `<2` after 2.x
renamed `FastMCP` to `MCPServer`. **Now upgraded to `mcp>=2.1.1,<3`.** Rule 4
held exactly as intended — the rename itself cost three lines in the one adapter
module. What it did *not* contain was a behavioural change: 2.x dispatches tool
calls on a **worker thread**, which broke `CodeStore`'s thread-affine SQLite
connection and made every tool call over the wire fail. That fix landed in
`store.py`, not the adapter.

**The lesson recorded against rule 4:** confining an integration bounds the
*API surface* you must edit, not the *runtime assumptions* the dependency makes
about your code. See F7 in [`FINDINGS.md`](FINDINGS.md). The constraint is now
bounded below 3.0 rather than pinned exactly, because a major bound is the part
that prevents this class of break; patch/minor float so security fixes are not
gated on a manual bump.

### D4 — Spin-out seam via `[tool.uv.sources]`

> **Status: current.** Now applied to every tool; see
> [`000` §5](000_project-organization.md#5-the-spin-out-seam).

Each tool declares a normal dependency on the shared library and a **dev-only**
override `[tool.uv.sources] data-tools-core = { workspace = true }`. In
development uv resolves it from the local workspace; deleting that one block
makes it resolve from a published wheel, because uv strips `[tool.uv.sources]`
from built wheels. Rules kept from day one so this stays a non-event:

- Tools import only the shared library, **never each other**.
- Everything a tool needs lives under its own directory.
- The shared library is versioned like a real library.

Spin-out recipe: `git subtree split -P tools/<name>` → push to a new repo → drop
the `[tool.uv.sources]` block → depend on the published `data-tools-core`.

### D5 — TDD throughout, model backend mocked

> **Status: current**, strengthened by D2a.

Red→green→refactor for every unit. The test suite never needs a live model:
the shared layer's tests patch its single lazy backend accessor; each tool's
tests inject a deterministic fake `EmbeddingProvider`/`ChatProvider`.

### D6 — Tools built first: `docs-rag` (#1) and `repo-rag` (#2)

> **Status: historical.** Both were built. See
> [`FINDINGS.md`](FINDINGS.md) for the verdicts, including the decision to park
> `repo-rag`.

The literal first two ideas. docs-rag exercises the full local RAG loop;
repo-rag adds AST-aware chunking, hybrid retrieval, and an MCP server — together
covering both axes (RAG + MCP) the repo exists to teach.

### D7 — Three seams: CLI, data, MCP

> **Status: current.** Introduced with `ingest-ledger`; see `CONVENTIONS.md`.

Tools never import each other, and compose only as installable commands, as
exchanged artifacts, or as MCP servers. This arrived independently of D4 but
enforces the same rule, from a different motivation: D4 wanted spin-out to be
cheap, D7 wants a single tool to run with nothing else installed.

### D8 — `Provenance` on every record that crosses a tool boundary

> **Status: current.** Introduced with `ingest-ledger`.

A value without provenance is a value you cannot audit. Source path, content
hash, unit kind, unit id — and a `locator` that reads like
`rfp.zip!appendix.xlsx#sheet=4`.

### D9 — Python **3.13** across the workspace

> **Status: current.** Adopted 2026-09.

The RAG tools were written for 3.13; `ingest-ledger` targeted 3.11. Unified on
3.13 on the owner's call: 3.11 is in security-fix-only maintenance, and the
codebase already leans on `StrEnum`, `slots=True` dataclasses, and PEP 604
unions throughout.

## Other defaults

- CLIs use stdlib **argparse**; pytest runs in `--import-mode=importlib`
  (three tools ship a `test_cli.py`).
- repo-rag AST chunking is **Python-only** (`ast`); tree-sitter multi-language
  is a deliberate later iteration.
- Shared distribution is **`data-tools-core`**, import package
  **`data_tools_core`**. (Originally `data-tools-shared` / `dt_shared`, on the
  RAG branch; renamed on merge.)

See [002 — Implementation Plan](002_implementation-plan.md) for the original
build, and [000 — Project Organization](000_project-organization.md) for how to
add the next tool.
