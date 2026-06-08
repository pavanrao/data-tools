# Findings (running log)

Project **verdicts, conclusions, and direction decisions** — what's useful, what
we're building or parking, and why. Append a new `## Iteration N` section at the
**top** each sprint.

> For reusable craft, see [LEARNINGS.md](./LEARNINGS.md).

---

## Iteration 1 — 2026-06-08

### F1 — Agentic consumption >> single-shot retrieval
Driving repo-rag's MCP from Claude (looping `search_code` / `get_chunk`) clearly
beat the single-shot `ask` CLI: the client iterates and a strong model synthesizes.
The weakness in `ask` was retrieval breadth + an 8B local synthesizer — not "RAG."

### F2 — A RAG-as-MCP tool's value depends on the *consumer*, not the retriever
In **Claude Code** (which already has Grep/Glob/Read), `search_code`/`get_chunk` are
largely **redundant** — Claude itself said it would answer better by reading files
directly. The tool earns its keep only for:
- **semantic "by meaning"** queries grep can't phrase (e.g. "retries" when the code
  says "backoff"), and
- **consumers with no filesystem** (Claude Desktop, hosted agents, custom apps),
  where it *is* the retrieval layer.

### F3 — Enumeration needs structured tools, not fuzzy search
"What tests are in my project?" can't be answered reliably by top-k semantic search
at any k. It needs deterministic `list_files` / `list_symbols`.

### Decision — park `repo-rag`, move on
repo-rag was a high-value **exercise** (AST chunking, hybrid retrieval, MCP serving,
agentic consumption, and the meta-lesson in F2) but is structurally **redundant for
our primary client, Claude Code**. We are **not investing further in repo-rag** now.
Next effort goes to tools that are non-redundant precisely because the host can't do
them itself:
- **`docs-rag`** — semantic Q&A over PDFs/arbitrary docs with citations (the host
  can't read your documents and ground an answer). The more defensible RAG tool.
- a **system-access MCP** such as `sqlite-mcp` (#11) — touches a system Claude can't
  reach, so it never competes with built-in file tools.

### Carried forward
- If repo-rag is ever revisited, its real home is a **no-filesystem consumer** — test
  it in Claude Desktop, where it stops competing with grep.
- The Tier-1 retrieval fixes (stopword-aware keyword search, exclude docs from the
  index, larger/diverse k) remain valid *if* repo-rag is resurrected — but are not
  worth doing for the Claude Code use case.
