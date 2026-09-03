# 004 — repo-rag

**Idea #2.** "Ask your codebase." Index a repo with code-aware chunking, answer
questions like *"where is auth handled?"* with **file:line** citations, and
expose retrieval as an **MCP server** so any MCP client can query the codebase.

## Pipeline

```
repo ─▶ AST chunk ─▶ embed ─▶ hybrid store (sqlite-vec + FTS5)
                                       │
question ─▶ embed ─▶ hybrid search (RRF) ─▶ grounded prompt ─▶ ChatProvider ─▶ answer + file:line cites
                                       │
                              MCP: search_code / get_chunk
```

## Modules (`tools/repo-rag/src/repo_rag/`)

- **`chunk.py`** — `chunk_python_source` uses the stdlib `ast` module to emit one
  `CodeChunk` per top-level function/class, with the exact `start_line`/`end_line`
  (decorators included) and the `symbol` name. Non-Python files (or unparseable
  Python) fall back to fixed line-windows so nothing is lost. `chunk_repo` walks a
  tree, skipping `.git`/`.venv`/`node_modules`/etc.
- **`store.py`** — `CodeStore` does **hybrid** retrieval: `sqlite-vec` for semantic
  search and an FTS5 index for keyword/BM25 (great for exact identifiers). `search`
  fuses the two ranked lists with **Reciprocal Rank Fusion** (RRF, k=60), which
  needs no score calibration across the two scales. `get_chunk(id)` fetches a full
  chunk for the MCP tool.
- **`query.py`** — `answer(...)` runs hybrid search and prompts the model to cite
  `file:line`; returns `Answer(text, citations)`.
- **`mcp_server.py`** — `FastMCP` server exposing **read-only** `search_code`
  (ranked snippets with `chunk_id` + file:line) and `get_chunk` (full text by id).
  Logic is in plain `*_impl` functions so it's tested without a transport. No
  mutation tools — read-only is the safety boundary.
- **`cli.py`** — `repo-rag index <repo>`, `repo-rag ask "<q>"`, `repo-rag serve`
  (MCP over stdio); also `python -m repo_rag`.

## Design notes

- **Hybrid > vector-only** for code: identifiers (`authenticate`) are matched
  precisely by FTS5 even when embeddings are fuzzy; semantics are caught by vectors.
- AST chunking is **Python-only for now** (D-ref: 001/§Other defaults). tree-sitter
  multi-language support is the planned next iteration; the line-window fallback
  already covers other files acceptably.
- All tests are model-free (fake embedder; MCP tool registration checked via
  `list_tools()`).
- The `mcp` SDK is pinned `<2`: 2.x renames `FastMCP` to `MCPServer` and changes
  tool registration. The pin is confined to this one adapter module by design
  (CONVENTIONS r4); the upgrade is still owed. See FINDINGS.

## Try it

```bash
uv run repo-rag index .
uv run repo-rag ask "where is hybrid search implemented?"
uv run repo-rag serve     # then connect an MCP client / inspector
```

MCP client config (stdio) example:

```json
{ "mcpServers": { "repo-rag": { "command": "uv", "args": ["run", "repo-rag", "serve"] } } }
```

## Possible next steps

- tree-sitter for multi-language AST chunking; incremental re-index by file hash
  (#23 cache); a `get_file` tool; impact-style queries (toward #38 lineage-explorer).
