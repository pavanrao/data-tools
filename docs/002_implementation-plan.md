# 002 — Implementation Plan

The build plan that produced the workspace scaffold and the first two tools.
Rationale for the choices here lives in [001](001_architecture-and-decisions.md).

## Workspace layout

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

## Packaging mechanics

- **Root** declares `[tool.uv.workspace] members = ["shared", "tools/*"]` and
  depends on `docs-rag` + `repo-rag`. `bypass-selection = true` lets the umbrella
  be a code-less metapackage.
- **Each tool** defines `[project.scripts]` (e.g. `docs-rag = "docs_rag.cli:main"`)
  **and** a `__main__.py` (`python -m docs_rag`), and carries the dev-only
  `[tool.uv.sources] data-tools-shared = { workspace = true }` spin-out seam.
- **Imports:** `from docs_rag.query import answer`, `from dt_shared import get_chat_provider`.

## Shared model layer (`dt_shared`)

```python
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
class ChatProvider(Protocol):
    def complete(self, prompt: str, **opts) -> str: ...
```

`config.Settings` reads `DATA_TOOLS_CHAT_MODEL` (default `ollama/llama3.1`),
`DATA_TOOLS_EMBED_MODEL` (default `ollama/nomic-embed-text`), optional
`DATA_TOOLS_API_BASE` / `DATA_TOOLS_API_KEY`. `get_chat_provider()` /
`get_embedding_provider()` build LiteLLM-backed implementations from settings.

## Build sequence (test-first)

1. Scaffold workspace; `uv sync` green; smoke tests pass.
2. `dt_shared`: config + providers + factory (litellm mocked).
3. `docs-rag`: ingest → sqlite-vec store → grounded query → CLI.
4. `repo-rag`: AST chunk → hybrid store (vec + FTS5, RRF) → query → MCP server → CLI.
5. README + `docs/001`–`004`.

## Verification

- `uv run pytest` — 41 tests, no live model needed.
- Live smoke (local, $0): `ollama pull nomic-embed-text && ollama pull llama3.1`,
  then index/ask each tool (see tool docs).
- Provider swap: set `DATA_TOOLS_CHAT_MODEL` to any LiteLLM model string and
  confirm tools work unchanged.
- Both invocation paths verified: console scripts (`docs-rag`, `repo-rag`) and
  `python -m docs_rag` / `python -m repo_rag`.
