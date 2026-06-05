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

## E. Pipeline-framework tools (generic; useful for metadata-driven platforms)

Plumbing for any config/metadata-driven data pipeline — ingestion, lineage, quality, reference
data, and extracts. Each is generic and standalone; the **Maps to** line names the pipeline need
it serves (handy if you're building a larger platform on top of these).

### 26. `flatfile-parser` — schema-driven extract parser ⭐⭐ 💻
Parse fixed-width / CSV / vendor-XML extracts into typed records using a declared field spec;
nonconforming rows go to a reject file with reasons. The unglamorous front door of legacy ingestion.
- **Learn:** spec-driven parsing, type coercion, and the reject/quarantine pattern.
- **Cost note:** pure code (no model) — fast and free; stream large files line-by-line.
- **Maps to:** legacy/COTS flat-file ingestion.

### 27. `schema-drift-detector` — diff two schema snapshots ⭐⭐ 💻
Compare a captured schema against the previous one; classify each change (add / drop / type-change /
nullability) and emit a drift report with a severity per change.
- **Learn:** schema fingerprinting and modeling "what kind of change is this, and how bad."
- **Cost note:** deterministic diffing; LLM optional, only to narrate a report.
- **Maps to:** per-feed schema-drift policy (auto-evolve / quarantine / fail-fast).

### 28. `load-reconciler` — source↔target reconciliation ⭐⭐ 💻
Compare row counts and control totals (sum/hash of key columns) between a source and its loaded
target, within configurable tolerances; output pass/fail + a delta report.
- **Learn:** control-total reconciliation, the backbone of trustworthy loads.
- **Cost note:** all arithmetic; no model cost.
- **Maps to:** DQ reconciliation / audit logging.

### 29. `config-linter` — validate pipeline config ⭐ 💻 🔌
Validate YAML/JSON pipeline config against a JSON-schema, plus cross-reference checks (does this
feed reference a transform/connector that exists?). Optionally expose as an MCP `lint_config` tool.
- **Learn:** JSON-schema validation + semantic cross-checks; config-as-code guardrails.
- **Cost note:** pure validation; free. A reusable gate for every other tool.
- **Maps to:** config-as-code control plane.

### 30. `sql-lineage` — column-level lineage from SQL ⭐⭐⭐ 💻
Parse SQL/SparkSQL and build a column-level lineage graph (which source columns feed which target
columns), handling joins, CTEs, and subqueries.
- **Learn:** SQL parsing (sqlglot), graph construction — the hard, high-value part of lineage.
- **Cost note:** static analysis, no model needed; cache by query hash.
- **Maps to:** OpenLineage / column-level lineage.

### 31. `iceberg-inspector` — table metadata as an MCP server ⭐⭐ 🔌 💻
MCP server exposing `snapshots`, `partitions`, `schema_history`, and `files` tools over an
Iceberg/Parquet table so an agent can inspect table state and time-travel without bespoke scripts.
- **Learn:** exposing read-only introspection safely as MCP; table-format internals.
- **Cost note:** metadata reads only; no scan cost, no model cost.
- **Maps to:** lake manager / time-travel.

### 32. `tokenizer` — reversible tokenization vault ⭐⭐ 💻
Deterministic, format-preserving tokenization for sensitive fields (same input → same token), with
a local vault for detokenization under access control. The companion to a PII *scanner*.
- **Learn:** format-preserving tokenization vs. hashing vs. encryption; key/vault separation.
- **Cost note:** pure crypto/lookup; free. Keep the vault local and access-gated.
- **Maps to:** PII tokenization (e.g. SSN).

### 33. `refdata-manager` — code sets + cross-references ⭐⭐ 💻 🔌
Manage code/lookup sets and source↔master cross-reference (xref) tables, versioned with effective
dates and history; expose `lookup` / `resolve_xref` as MCP tools.
- **Learn:** reference-data lifecycle and stable cross-keys across systems.
- **Cost note:** a small DB + API; no model cost.
- **Maps to:** reference-data / cross-reference management.

### 34. `catalog-search-rag` — semantic dataset/column finder ⭐⭐ 🧠 💻
Embed a data catalog (table/column names, descriptions, glossary terms) and answer "which dataset
has policyholder addresses?" with the matching tables/columns and their definitions.
- **Learn:** RAG over *metadata* (short, structured text) rather than prose; hybrid name+vector match.
- **Cost note:** tiny corpus → local embeddings; re-embed only on catalog change.
- **Maps to:** data-catalog / glossary discovery.

### 35. `dq-rule-suggester` — propose data-quality rules ⭐⭐ 🧠 💻
Profile a dataset (types, ranges, nulls, uniqueness, enums) and suggest Great Expectations/Soda
rules, each with a plain-English rationale; you review and accept. The model suggests, never enforces.
- **Learn:** profiling → rule synthesis; keeping the LLM advisory, not authoritative.
- **Cost note:** profiling is pandas/polars; local model drafts the rationale.
- **Maps to:** data-quality rule authoring.

### 36. `scd2-differ` — generate SCD2 merges ⭐⭐ 💻
Given before/after snapshots and a business key, produce the SCD Type-2 change set (close old row,
open new row with effective dates + current flag). Deterministic, testable historization.
- **Learn:** slowly-changing-dimension mechanics end to end.
- **Cost note:** set arithmetic; no model cost.
- **Maps to:** SCD2 historization in marts.

### 37. `runlog-anomaly` — spot weird pipeline runs ⭐⭐ 💻 ☁️
Ingest pipeline run history (durations, row counts, statuses) and flag anomalies — a load 10× slower
than usual, a row count that halved — with a short explanation.
- **Learn:** simple statistical baselining (z-score/IQR) before reaching for ML.
- **Cost note:** stats are local; API model only to phrase the alert.
- **Maps to:** pipeline observability / AIOps.

### 38. `lineage-explorer` — query a lineage graph via MCP ⭐⭐⭐ 🔌 🧠
Load OpenLineage events into a graph and expose MCP tools (`upstream`, `downstream`,
`impact_of_change`) so an agent can answer "what feeds `dim_party`?" or "what breaks if I drop this column?"
- **Learn:** turning lineage data into agent-callable graph queries; impact analysis.
- **Cost note:** graph queries local; generation handled by whatever client connects.
- **Maps to:** AIOps lineage / impact analysis.

### 39. `cdc-inspector` — make sense of change events ⭐⭐ 💻
Parse Debezium/DMS-style change events, summarize per-table insert/update/delete counts, diff a
record's before↔after, and replay a time window for debugging.
- **Learn:** CDC event shapes and the before/after semantics that trip people up.
- **Cost note:** parsing only; no model cost.
- **Maps to:** CDC ingestion.

### 40. `feed-scaffolder` — generate a new feed package ⭐⭐ 💻 🔌
From a sample file + a few prompts, generate a self-contained feed package (config + a starter
SQL transform + DQ rules + a test) following a template. Expose as MCP for agentic onboarding.
- **Learn:** scaffolding/codegen from a template; the self-service onboarding pattern.
- **Cost note:** templating is free; optional local LLM to draft starter SQL/DQ.
- **Maps to:** self-service feed onboarding.

### 41. `finops-attributor` — cost per feed/domain ⭐⭐ 💻
Join billing/usage data with pipeline run logs to attribute compute/storage cost to each feed or
domain; output a ranked report of where the money goes.
- **Learn:** cost attribution joins and the FinOps "unit economics per pipeline" view.
- **Cost note:** pure aggregation; no model cost.
- **Maps to:** FinOps / cost observability.

### 42. `sql-test-harness` — unit-test your transforms ⭐⭐ 💻
Golden-file testing for SQL/SparkSQL: provide input fixtures + expected output, run the transform
against a local engine (DuckDB/SQLite/Spark), and diff results. Red/green for data transforms.
- **Learn:** fixture-based testing of SQL; making transforms safe to change.
- **Cost note:** local engines; no model cost. Pairs naturally with `eval-harness` (#9).
- **Maps to:** transform-engine testing.

### 43. `data-dictionary-gen` — auto-document datasets ⭐⭐ 🧠 💻
RAG over schema + sample values + any glossary to generate human-readable dataset/column
documentation (what each column means, example values, caveats), with the source facts cited.
- **Learn:** grounded generation over derived/structured facts; keeping docs traceable.
- **Cost note:** profiling local; local model drafts the prose.
- **Maps to:** catalog / glossary documentation.

### 44. `extract-spec-gen` — scaffold outbound extracts ⭐⭐ 💻 🔌
From a target spec (file/DB/API/SFTP layout) generate an outbound extract config plus a sample
output file so you can validate the shape before wiring the real delivery.
- **Learn:** treating extract generation as the symmetric twin of ingestion config.
- **Cost note:** templating + a dry-run sample; no model cost required.
- **Maps to:** outbound extract engine.

### 45. `watermark-tracker` — high-water-mark state ⭐ 💻 🔌
A tiny service/library to store, advance, reset, and audit the high-water-mark per feed for
incremental/delta loads (last loaded timestamp/id), so reruns are correct and idempotent.
- **Learn:** the state management that makes incremental loads reliable; idempotency.
- **Cost note:** a small key-value store; no model cost. A reusable building block.
- **Maps to:** incremental / delta ingestion.

---

## Suggested build order (for learning)

1. **#1 `docs-rag`** — get the whole RAG loop working once, locally and free.
2. **#11 `sqlite-mcp`** — get a clean MCP server working once.
3. **#23 `embeddings-cache`** + **#24 `model-router`** — the economy foundation.
4. **#12 `filesystem-rag-mcp`** — the "aha": RAG *as* an MCP tool.
5. **#9 `eval-harness`** — so every later tweak is measurable.
6. Anything from C — combined pipelines, now that the pieces exist.
