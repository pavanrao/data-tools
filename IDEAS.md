# Tool Ideas

A backlog of small, independent data-pipeline tools to build while learning MCP
and RAG. Pick any one — they don't depend on each other.

**Legend**
- 🧠 **RAG** — exercises retrieval-augmented generation
- 🔌 **MCP** — exercises building or consuming an MCP server/client
- 💻 **Local-first** — runs well on a local LLM (Ollama/llama.cpp)
- ☁️ **API-leaning** — benefits from a hosted model's quality, but stays cheap
- 💸 **Cost note** — how to keep it economical

Difficulty: ⭐ starter · ⭐⭐ intermediate · ⭐⭐⭐ involved

---

## A. RAG-focused tools

### 1. `docs-rag` — Q&A over a local document folder ⭐ 🧠 💻
Point it at a folder of PDFs/Markdown/txt; it chunks, embeds, and answers
questions with citations to the source file + page/section.
- **Learn:** the full RAG loop — loaders, chunking, embeddings, a vector store
  (start with SQLite + `sqlite-vec` or Chroma), retrieval, grounded prompting.
- **Cost note:** local embeddings (`nomic-embed-text`/`bge-small`) + local
  generation = $0. Add an API generation mode for hard questions only.

### 2. `repo-rag` — "ask your codebase" ⭐⭐ 🧠 🔌 💻
Index a Git repo (AST-aware chunking per function/class) and answer questions
like "where is auth handled?" with file:line citations. Expose it as an **MCP
server** so editors/agents can query the codebase.
- **Learn:** code-aware chunking, hybrid (keyword + vector) retrieval, and
  shipping retrieval *as an MCP tool*.
- **Cost note:** embeddings are one-time per commit; cache by file hash.

### 3. `changelog-rag` — release-note generator from commits + diffs ⭐⭐ 🧠 ☁️
Retrieves commits/PRs in a range, clusters them by theme, and drafts a
human-readable changelog grouped into Features/Fixes/Breaking.
- **Learn:** map-reduce summarization, retrieval over structured records.
- **Cost note:** summarize per-cluster (not per-commit) to cut token counts.

### 4. `support-triage-rag` — answer drafting over a knowledge base ⭐⭐ 🧠 ☁️
Given an incoming support ticket, retrieves relevant KB articles/past tickets
and drafts a grounded reply with linked sources and a confidence score.
- **Learn:** retrieval quality metrics, "I don't know" guardrails, reranking.
- **Cost note:** cheap local model for retrieval/draft; escalate low-confidence
  drafts to an API model.

### 5. `semantic-log-search` — natural-language search over logs ⭐⭐ 🧠 💻
Embed log lines/traces and let users ask "show errors related to payment
timeouts last Tuesday." Hybrid filter (time/level) + semantic match.
- **Learn:** combining metadata filtering with vector search; streaming ingest.
- **Cost note:** embed only WARN/ERROR by default; sample INFO.

### 6. `pdf-table-extractor-rag` — structured extraction from messy PDFs ⭐⭐ 🧠 ☁️
Extract tables/figures from reports into clean CSV/JSON, using retrieval to pull
the surrounding text as context for ambiguous cells.
- **Learn:** layout-aware parsing, schema-constrained (JSON) output.
- **Cost note:** OCR/parse locally; only call an LLM for ambiguous regions.

### 7. `csv-profiler-rag` — "interview your dataset" ⭐ 🧠 💻
Profiles a CSV/Parquet (types, nulls, distributions, outliers) and lets you ask
plain-English questions; retrieves the relevant profile facts before answering.
- **Learn:** RAG over *structured/derived* facts rather than prose.
- **Cost note:** profiling is pure pandas/polars; LLM only narrates.

### 8. `web-clip-rag` — personal read-it-later knowledge base ⭐⭐ 🧠 💻
Save URLs; it fetches, cleans, chunks, embeds, and lets you ask questions across
everything you've saved, with source links and dates.
- **Learn:** HTML extraction, dedup/near-dup detection, incremental indexing.
- **Cost note:** fully local stack; embeddings cached by URL+content hash.

### 9. `eval-harness` — RAG quality/regression tester ⭐⭐⭐ 🧠 ☁️
Define Q/expected-source pairs; it measures retrieval recall@k, faithfulness,
and answer relevance, then tracks scores over time as you tweak the pipeline.
- **Learn:** how to *measure* RAG (the skill that makes the rest trustworthy),
  LLM-as-judge with a rubric.
- **Cost note:** run cheap local judges for CI; sample with an API judge weekly.

### 10. `meeting-notes-rag` — searchable transcript memory ⭐⭐ 🧠 💻
Ingest transcripts (VTT/SRT/txt), speaker-aware chunking, then answer "what did
we decide about pricing?" with quotes + timestamps.
- **Learn:** speaker/diarization-aware chunking, temporal retrieval.
- **Cost note:** local Whisper for transcription if you add audio ingest.

---

## B. MCP-focused tools

### 11. `sqlite-mcp` — safe SQL access as an MCP server ⭐⭐ 🔌 💻
An MCP server exposing read-only `query`, `schema`, and `sample` tools over a
SQLite/DuckDB file, with row limits and query allow-listing.
- **Learn:** the canonical MCP pattern — exposing tools + resources safely; how
  an LLM client discovers and calls them.
- **Cost note:** the server is free; pairs with any model as the client.

### 12. `filesystem-rag-mcp` — retrieval as an MCP capability ⭐⭐⭐ 🔌 🧠 💻
Combine #1 with MCP: expose `search_docs` and `get_chunk` tools so *any* MCP
client (Claude Desktop, an agent) can do RAG over your files on demand.
- **Learn:** the difference between baking RAG into a prompt vs. offering it as a
  *tool* the model calls when needed.
- **Cost note:** retrieval local; generation handled by whatever client connects.

### 13. `http-fetch-mcp` — guarded web fetch/extract tool ⭐⭐ 🔌 💻
MCP server with a `fetch_url` tool that fetches, strips boilerplate, and returns
clean Markdown — with domain allow-lists, size caps, and timeouts.
- **Learn:** building *safe* MCP tools (SSRF guards, limits) — the unglamorous
  but essential part.
- **Cost note:** pure plumbing, no model cost.

### 14. `cron-pipeline-mcp` — schedule + run pipelines via MCP ⭐⭐⭐ 🔌 💻
Expose `list_jobs`, `run_job`, `job_status` over MCP so an LLM agent can trigger
and monitor your ETL jobs conversationally.
- **Learn:** MCP for *actions/side-effects* (not just retrieval); idempotency,
  confirmations, and progress reporting.
- **Cost note:** orchestration only; jobs do the real work.

### 15. `secrets-aware-env-mcp` — config/secrets broker for agents ⭐⭐ 🔌 💻
MCP server that exposes *names* of available config/keys and injects them into
allowed jobs without ever returning secret values to the model.
- **Learn:** safe capability design — letting an LLM *use* a secret without
  *seeing* it.
- **Cost note:** free; a reusable building block for every other tool.

### 16. `mcp-gateway` — multiplex several MCP servers behind one ⭐⭐⭐ 🔌 💻
A façade MCP server that aggregates tools from #11/#13/#15 under one connection,
with namespacing, auth, and per-tool rate limits.
- **Learn:** MCP client *and* server in one process; tool routing/composition.
- **Cost note:** infrastructure; no model cost.

---

## C. RAG + MCP combined pipelines

### 17. `etl-doctor` — diagnose failed pipeline runs ⭐⭐⭐ 🧠 🔌 ☁️
RAG over runbooks + past incidents, exposed via MCP, so an agent handed a stack
trace retrieves the likely cause and suggested fix with citations.
- **Learn:** retrieval over operational knowledge + serving it agentically.
- **Cost note:** local retrieval; API model only for the final diagnosis.

### 18. `schema-migration-advisor` — safe DDL change reviewer ⭐⭐⭐ 🧠 🔌 ☁️
Given a proposed schema change, retrieves current schema (via #11), prior
migrations, and downstream usage, then flags breaking changes.
- **Learn:** grounding generation in *live* tool-fetched context, not a static
  index.
- **Cost note:** retrieval/diffing local; one focused API call to reason.

### 19. `data-contract-linter` — validate datasets against contracts ⭐⭐ 🧠 💻
Checks incoming data against a declared contract (types, ranges, enums) and uses
RAG over past violations to explain failures in plain language + suggest fixes.
- **Learn:** combining deterministic validation with LLM explanation (LLM never
  decides pass/fail — it only narrates).
- **Cost note:** validation is code; LLM only explains failures. Local is plenty.

### 20. `pii-scanner` — find + explain sensitive data ⭐⭐ 🧠 💻
Scans datasets/files for PII with regex + NER, then uses an LLM to classify
ambiguous cases and write a redaction report with rationale.
- **Learn:** LLM-assisted classification with cheap deterministic pre-filtering.
- **Cost note:** regex/NER catch 90% locally; LLM adjudicates only the gray area.

### 21. `query-copilot` — natural language → SQL with grounding ⭐⭐⭐ 🧠 🔌 ☁️
Retrieves schema + example queries (via #11's MCP server), generates SQL,
dry-runs/explains it, and shows the plan before you run it.
- **Learn:** schema-grounded generation, the retrieve→generate→verify loop,
  guardrails against destructive SQL.
- **Cost note:** read-only by default; small API model handles most NL→SQL.

### 22. `release-notes-bot` — changelog from issues + PRs over MCP ⭐⭐ 🧠 🔌 ☁️
Like #3 but pulls live data through a Git/issue-tracker MCP server, then drafts
notes — fully agentic from "give me notes for v2.1."
- **Learn:** composing an MCP data source with a RAG summarizer.
- **Cost note:** cluster-then-summarize to bound tokens.

---

## D. Stretch / infrastructure

### 23. `embeddings-cache` — content-addressed embedding store ⭐⭐ 💻 💸
A tiny shared library/service that caches embeddings by content hash so every
other tool stops re-embedding unchanged text.
- **Learn:** the single biggest RAG cost lever — caching.
- **Cost note:** *this is the cost note* — pays for itself across all tools.

### 24. `model-router` — route requests to local vs. API by policy ⭐⭐⭐ 💻 ☁️ 💸
A shared interface that sends easy/bulk calls to a local model and hard/critical
ones to an API, based on a configurable policy + token budget.
- **Learn:** the local-vs-hosted tradeoff made concrete and measurable.
- **Cost note:** the framework that keeps every other tool economical.

### 25. `chunking-lab` — compare chunking strategies side by side ⭐⭐ 🧠 💻
Feed one document; see how fixed-size, recursive, semantic, and structural
chunking affect retrieval quality (paired with #9's metrics).
- **Learn:** why chunking is *the* RAG decision; build intuition fast.
- **Cost note:** local embeddings; pure experimentation, no API needed.

---

## Suggested build order (for learning)

1. **#1 `docs-rag`** — get the whole RAG loop working once, locally and free.
2. **#11 `sqlite-mcp`** — get a clean MCP server working once.
3. **#23 `embeddings-cache`** + **#24 `model-router`** — the economy foundation.
4. **#12 `filesystem-rag-mcp`** — the "aha": RAG *as* an MCP tool.
5. **#9 `eval-harness`** — so every later tweak is measurable.
6. Anything from C — combined pipelines, now that the pieces exist.
