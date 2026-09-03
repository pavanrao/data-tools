# 002 — Implementation Plan (historical)

> **Status: historical record.** This is the plan that produced the workspace
> scaffold and the first two RAG tools on the `build-docs-rag-repo-rag` branch.
> It is preserved because the sequence and the verification steps are worth
> reusing, but parts of it describe a layout that has since been replaced.
>
> For the current layout and the checklist for adding a tool, read
> [`000_project-organization.md`](000_project-organization.md). For what changed
> and why, see D1a and D2a in
> [`001_architecture-and-decisions.md`](001_architecture-and-decisions.md).

## Workspace layout *(as planned; see note below)*

```
data-tools/
├── pyproject.toml            # umbrella metapackage + [tool.uv.workspace]
├── uv.lock                   # ONE lock for the whole workspace
├── .python-version           # 3.13
├── docs/                     # 001_, 002_, … sequential plans + decision logs
├── shared/                   # data-tools-shared  (import: dt_shared)
│   └── src/dt_shared/
│       ├── config.py         # env-driven Settings (pydantic-settings)
│       └── llm.py            # EmbeddingProvider/ChatProvider + LiteLLM impls + factory
└── tools/
    ├── docs-rag/             # see 003_docs-rag.md
    └── repo-rag/             # see 004_repo-rag.md
```

**Three things here are now different:**

| Planned | Actual today | Why |
|---|---|---|
| Umbrella metapackage at the root | Root is **not** a package | 001 / D1a |
| `shared/` → `data-tools-shared` / `dt_shared` | `shared/data-tools-core/` → `data_tools_core` | merged on consolidation |
| `config.py` on pydantic-settings | stdlib-only | core keeps `dependencies = []` — 001 / D2a |

`uv.lock` is also no longer committed; it is gitignored.

## Packaging mechanics

- **Each tool** defines `[project.scripts]` (e.g. `docs-rag = "docs_rag.cli:main"`)
  **and** a `__main__.py` (`python -m docs_rag`), and carries the dev-only
  `[tool.uv.sources]` spin-out seam.
- **Imports:** `from docs_rag.query import answer`,
  `from data_tools_core.llm import get_chat_provider`.

Since consolidation, each tool also registers in the `data_tools.tools`
entry-point group so `dt ls` finds it, and distributions are named
`data-tools-<tool-name>`.

## Shared model layer

```python
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class ChatProvider(Protocol):
    def complete(self, prompt: str, **opts) -> str: ...
```

`config.get_settings()` reads `DATA_TOOLS_CHAT_MODEL` (default `ollama/llama3.1`),
`DATA_TOOLS_EMBED_MODEL` (default `ollama/nomic-embed-text`), optional
`DATA_TOOLS_API_BASE` / `DATA_TOOLS_API_KEY`. `get_chat_provider()` /
`get_embedding_provider()` build LiteLLM-backed implementations from settings.

## Build sequence (test-first)

The sequence itself generalizes — it is the one to reuse for the next tool:

1. Scaffold the package; `uv sync` green; smoke test passes.
2. Shared contracts first, with the backend mocked.
3. Deterministic core: ingest → store → retrieve, no model in the loop.
4. Model-facing layer: grounded prompt → provider → cited answer.
5. Interfaces last: CLI, then MCP server.
6. README + the numbered design doc.

## Verification

- `uv run pytest` — no live model needed.
- Live smoke (local, $0): `ollama pull nomic-embed-text && ollama pull llama3.1`,
  then index/ask each tool (see the per-tool docs).
- Provider swap: set `DATA_TOOLS_CHAT_MODEL` to any LiteLLM model string and
  confirm tools work unchanged.
- Both invocation paths: console scripts (`docs-rag`, `repo-rag`) **and**
  `python -m docs_rag` / `python -m repo_rag`.
- Discovery: `dt ls` lists the tool with its one-line summary.
