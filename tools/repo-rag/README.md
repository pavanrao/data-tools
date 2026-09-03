# repo-rag

Ask-your-codebase RAG (idea #2): AST-aware chunking, hybrid (vector + keyword)
retrieval, answers with **file:line** citations, and a read-only **MCP server**.

```bash
uv run repo-rag index .
uv run repo-rag ask "where is hybrid search implemented?"
uv run repo-rag serve        # MCP server over stdio
# or: python -m repo_rag …
```

MCP client (stdio):

```json
{ "mcpServers": { "repo-rag": { "command": "uv", "args": ["run", "repo-rag", "serve"] } } }
```

Install a model backend with `uv sync --extra llm`; chunking, indexing and
retrieval are testable without one.

Models come from `data_tools_core.llm` (Ollama by default; any LiteLLM
provider via `DATA_TOOLS_*` env vars). Design notes: [`docs/004_repo-rag.md`](../../docs/004_repo-rag.md).
