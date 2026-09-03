# Findings (running log)

Project **verdicts, conclusions, and direction decisions** — what's useful, what
we're building or parking, and why. Append a new `## Iteration N` section at the
**top** each sprint.

> For reusable craft, see [LEARNINGS.md](./LEARNINGS.md).

---

## Iteration 2 — 2026-09-03

### F4 — The collection now has three tools and one set of conventions
`docs-rag` (#1) and `repo-rag` (#2) were merged onto main and adapted to the
`ingest-ledger` conventions: distributions renamed `data-tools-<tool>`, the
shared model layer moved from `dt_shared` to `data_tools_core.llm` as an
optional extra, entry-point discovery added, workspace unified on Python 3.13.
Rationale in [`001`](001_architecture-and-decisions.md) (D1a, D2a, D9); the
current shape in [`000`](000_project-organization.md).

### F5 — The two branches agreed on principles and differed only on mechanics
Independently, both lines of work arrived at: tools never import each other,
each tool independently installable, SQLite as the substrate, MCP as a seam, and
a deterministic core testable without a model. That convergence is why the merge
was a reconciliation rather than a rewrite — and why those five rules are the
ones to defend hardest.

Where they differed (umbrella root vs. non-package root; `dt_shared` vs.
`data_tools_core`; extras policy) the `ingest-ledger` position won on every
point, because in each case it took "a tool must run alone" more literally.

### F6 — The model layer became optional, not merely mockable
`CONVENTIONS.md` rule 3 has always said a tool that cannot run without a model
cannot be tested. Iteration 1 satisfied that by *mocking* litellm; the shared
library still depended on it. It is now genuinely optional: `data-tools-core`
carries no base dependencies, `litellm` is imported inside the call and ships as
the `llm` extra. The stronger form is worth the small cost — it makes the rule
checkable rather than aspirational, and `test_llm.py` now asserts it directly.

### Owed — upgrade `repo-rag` to the MCP SDK 2.x
`mcp` is pinned `<2`. Version 2.x renames `FastMCP` to `MCPServer` and changes
tool registration. The pin is deliberate and CONVENTIONS-sanctioned (r4: pin the
integration, confine it to one adapter module), and the confinement held — the
blast radius is exactly `tools/repo-rag/src/repo_rag/mcp_server.py`. But it is a
deferral, not a resolution. Do it when `repo-rag` is next picked up.

### Carried forward, unchanged
The Iteration 1 verdicts still stand and still direct the work:
- **F2** — a RAG-as-MCP tool's value depends on the consumer. `ingest-ledger`
  is the constructive answer: it does what a capable model with file access
  cannot do for itself, namely prove what it *failed to read*.
- **repo-rag stays parked.** It was merged to preserve the exercise and its
  design record, not because the F2 verdict changed. Its real home remains a
  no-filesystem consumer.
- **docs-rag is the more defensible RAG tool** — and is now better understood as
  a *downstream* of `ingest-ledger` (grounded generation over an already
  reconciled index) than as a standalone folder-Q&A tool. `CONVENTIONS.md`
  anticipates exactly this in the data seam.
- The Tier-1 retrieval fixes (stopword-aware keyword search, excluding docs from
  the index, larger/diverse k) remain valid if `repo-rag` is resurrected.

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
