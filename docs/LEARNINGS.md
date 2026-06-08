# Learnings (running log)

Reusable, transferable **craft** — technical and process know-how that applies
beyond any single tool. Append a new `## Iteration N` section at the **top** each
sprint; keep entries concrete.

> For project verdicts and direction calls, see [FINDINGS.md](./FINDINGS.md).
> For per-feature design + decision records, see the numbered docs (`001_…`).

---

## Iteration 1 — 2026-06-08 — workspace scaffold + docs-rag + repo-rag

### uv / packaging
- A **uv workspace** gives one lockfile / one `uv sync`, while each member stays a
  real, independently-importable package. The umbrella root can be a code-less
  metapackage via hatchling `bypass-selection = true`.
- **Spin-out seam:** a member declares a normal dep *plus* a dev-only
  `[tool.uv.sources] X = { workspace = true }`. uv sources are stripped from built
  wheels, so deleting that one line is the entire "decouple from the workspace" step.
- `uv run --directory <abs-path> <tool> …` runs a workspace tool from anywhere —
  used to launch the MCP server regardless of the client's cwd.

### pytest in a multi-package workspace
- Several `test_smoke.py` files with the same basename **collide** under the default
  import mode ("import file mismatch"). Fix: `addopts = "--import-mode=importlib"`,
  which lets each member keep a conventional `tests/` layout without `__init__.py`.

### sqlite-vec
- KNN needs its limit **on the vec0 scan itself**: `WHERE embedding MATCH ? AND k = ?`.
  A `LIMIT` on an outer JOIN raises *"A LIMIT or 'k = ?' constraint is required"* —
  do the match in a subquery, then JOIN the metadata.
- Persist the embedding `dim` in a `meta` table so a store can be **reopened** for
  querying without re-specifying it.

### Hybrid retrieval
- Fuse sqlite-vec (semantic) + FTS5 (keyword/BM25) with **Reciprocal Rank Fusion**
  (k=60). RRF needs no score calibration across the two very different scales.
- FTS5 **external-content** table (`content='chunks', content_rowid='id'`) keeps a
  single source of truth for text.
- **Gotcha (open):** building the FTS `MATCH` as an OR of *all* query tokens pulls in
  stopwords (`what OR data OR in OR use`), so common words dominate BM25 and pollute
  results. Drop stopwords / weight identifiers.

### Code chunking
- stdlib `ast` yields clean per-function/class chunks with exact line spans; include
  decorators by taking `min(decorator linenos)`. Fall back to fixed line-windows on
  `SyntaxError` or when a file has no top-level defs, so nothing is lost.

### Model-pluggability
- Keeping our own `EmbeddingProvider`/`ChatProvider` protocols in front of **LiteLLM**
  means a provider swap is a model-string/env change and tools never import a vendor.
  Tests **mock `litellm`** → fast, hermetic, no live model needed (41 tests).

### MCP
- `FastMCP` + `@server.tool()`. Keep tool logic in plain `*_impl` functions so it's
  testable without a transport; assert registration via `await server.list_tools()`.
- Connect to Claude Code via a project `.mcp.json` (`command`/`args`); absolute
  `--directory`/`--db` avoid launch-cwd ambiguity.

### RAG question shapes
- Top-k retrieval serves **"needle"** questions ("where is X") but not
  **"survey/aggregate"** ones ("what tests exist"). With k=5 over 131 chunks the model
  simply can't enumerate 56 tests — that's a *recall* failure, not generation. Different
  question classes need different mechanisms (high recall, or structured listing).
