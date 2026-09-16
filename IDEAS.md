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

**Built:** ✅ marks an idea that now lives under `tools/`.
- 🤖 **Agentic** — multi-step, tool-using agent work *is* the tool (not narration bolted on)
- 🏛️ **System** — multi-component platform/product; the "small tool" rule is intentionally waived
- ⚠️ **Deterministic** — core job needs no LLM/RAG; kept for learning value, but AI is optional here
- 🔒 **Data-free** — works from schema, infrastructure, logs and code only; never reads a row value, so it needs no data-residency review and can run in CI

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

### 49. `ingest-ledger` — prove what the pipeline actually read ✅ ⭐⭐⭐ 🧠 💻
Reconcile the units a corpus *declares* (PDF pages, XLSX sheets, DOCX blocks
including footnotes, XML nodes, CSV rows, nested archive members) against what
extraction actually recovered, quarantining anything short instead of indexing
it silently. Delegates PDF page-level silent-drop detection to
[pdfmux](https://github.com/NameetP/pdfmux); contributes the formats nothing
else covers, plus a hostile corpus that asserts each failure is caught.
- **Learn:** reconciliation as a defense against non-deterministic systems,
  subprocess resource isolation, and adversarial fixtures as a product claim.
- **Cost note:** deterministic and model-free end to end.
- **Built:** [`tools/ingest-ledger/`](./tools/ingest-ledger/)

---

## B. MCP-focused tools

> **Status note, 2026-09-08.** These six were written against MCP as it stood in
> early 2025 and have been rewritten against revision **2026-07-28**, which
> removed the `initialize` handshake, protocol-level sessions and
> `resources/subscribe`, and deprecated Roots, Sampling and Logging. Section
> **M** (#198–#217) covers the surface that arrived with it. The decision is
> recorded as D10 in [`docs/001`](docs/001_architecture-and-decisions.md).

### 11. `sqlite-mcp` — safe SQL access as an MCP server ✅ ⭐⭐ 🔌 💻
An MCP server exposing read-only `query`, `schema`, and `sample` tools over a
SQLite/DuckDB file, with row limits and query allow-listing. `query` declares an
`outputSchema`, so a result is a typed record rather than a paragraph; `schema`
returns a `ttlMs` so a client stops re-reading a file that has not changed. **F2**
in [`docs/FINDINGS.md`](docs/FINDINGS.md) argues this is the one in section B
with real value — it touches a system the model cannot reach on its own.
- **Learn:** the canonical MCP pattern — exposing tools and resources safely, and
  how a client discovers them now that there is no handshake: `server/discover`,
  plus capabilities carried in `_meta` on every request.
- **Cost note:** the server is free; pairs with any model as the client.
- **Built:** [`tools/sqlite-mcp/`](./tools/sqlite-mcp/). The read-only guarantee
  is SQLite's own authorizer rather than a check on the SQL, refusals come back
  as typed results rather than errors, and the row cap reports that it fired.
  Design record [`docs/009`](docs/009_sqlite-mcp.md); concepts
  [`docs/010`](docs/010_mcp-concepts.md); the write-up is
  [`let-the-database-say-no.html`](docs/let-the-database-say-no.html).

### 12. `filesystem-rag-mcp` — retrieval as an MCP capability ⭐⭐⭐ 🔌 🧠 💻
Combine #1 with MCP: expose `search_docs` and `get_chunk` tools so *any* MCP
client can do RAG over your files on demand. Worth building once to learn the
shape, but build it knowing the answer — **F2** found that a retrieval server
earns little next to a client that can already read the files itself. That
finding is why section M points at warehouses, orchestrators and catalogs rather
than at folders of documents.
- **Learn:** the difference between baking RAG into a prompt and offering it as a
  *tool* the model calls when needed — and the negative result that follows.
- **Cost note:** retrieval local; generation handled by whatever client connects.

### 13. `http-fetch-mcp` — guarded web fetch/extract tool ⭐⭐ 🔌 💻
MCP server with a `fetch_url` tool that fetches, strips boilerplate, and returns
clean Markdown — with domain allow-lists, size caps, and timeouts. The guards are
the tool. The spec now states plainly that tool descriptions and annotations are
*untrusted* unless the server itself is, so a fetched page carrying instructions
is an injection vector into whatever runs next.
- **Learn:** building *safe* MCP tools (SSRF guards, limits) — the unglamorous
  but essential part; and why a tool's own description can never be a security
  control.
- **Cost note:** pure plumbing, no model cost.

### 14. `cron-pipeline-mcp` — schedule + run pipelines via MCP ⭐⭐⭐ 🔌 💻
Expose `list_jobs` and `run_job` over MCP so an agent can trigger and monitor ETL
jobs conversationally. The `job_status` polling tool this originally proposed is
now the protocol's job: a run returns a durable task handle under the
`io.modelcontextprotocol/tasks` extension and the client polls `tasks/get`.
#199 `run-as-task` is that mechanism studied on its own; this entry is the
orchestrator-specific application of it — Airflow, Dagster or cron behind one
server, with #46 `airflow-state-probe` as the read-only half.
- **Learn:** MCP for *actions and side-effects*, not just retrieval; idempotency,
  confirmation gates, and why a durable handle beats a bespoke status tool.
- **Cost note:** orchestration only; jobs do the real work.

### 15. `secrets-aware-env-mcp` — config/secrets broker for agents ⭐⭐ 🔌 💻
MCP server that exposes the *names* of available config keys and injects their
values into allowed jobs without ever returning a secret to the model. Sessions
are gone from the protocol, so a broker that must remember a grant across calls
mints its own handle and hands it back as an ordinary tool argument — which makes
the grant inspectable and revocable rather than implicit in a connection.
- **Learn:** safe capability design — letting a model *use* a secret without
  *seeing* it; and holding server state explicitly now that the transport will
  not hold it for you.
- **Cost note:** free; a reusable building block for every other tool.

### 16. `mcp-gateway` — multiplex several MCP servers behind one ⭐⭐⭐ 🔌 💻
A façade MCP server that aggregates tools from #11/#13/#15 under one connection,
with namespacing, auth, and per-tool rate limits. Aggregation is more than a name
prefix: the façade merges the capability and extension sets its backends report
from `server/discover`, decides what to advertise when only one backend supports
an extension, fans out `subscriptions/listen` opt-ins, and namespaces task ids so
two backends cannot collide. This is the seam `CONVENTIONS.md` describes — every
installed tool's `data_tools.mcp` factory mounted behind one endpoint.
- **Learn:** MCP client *and* server in one process; tool routing and capability
  composition, which is where the interesting failures live.
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

### 25. `chunking-lab` — compare chunking strategies side by side ✅ ⭐⭐ 🧠 💻
Feed one document; see how fixed-size, recursive, semantic, and structural
chunking affect retrieval quality. Scores at the **character level against gold
spans**, so it can see the failures a chunk-level metric cannot: an answer padded
out with 1,800 irrelevant characters, or severed across two chunks so neither is
usable alone.
- **Learn:** why chunking is *the* RAG decision; build intuition fast.
- **Cost note:** the whole default path is model-free, offline and deterministic —
  no key, no GPU, no network. Semantic chunking (Tier 1) needs an encoder.
- **Boundary with #53:** **#25 varies the chunker with the retriever fixed; #53
  varies the retriever with chunking fixed.** Neither subsumes the other.
- **Built:** [`tools/chunking-lab/`](./tools/chunking-lab/) · design record in
  [`docs/006_chunking-lab.md`](./docs/006_chunking-lab.md) · concepts in
  [`docs/007_chunking-concepts.md`](./docs/007_chunking-concepts.md) · explainer
  [`docs/where-the-cut-falls.html`](./docs/where-the-cut-falls.html)
- **Scope closed.** It measures; it does not recommend. The two threads it left
  open became their own topics rather than being bolted on: **#91
  `context-aug-lab`** (Tier 2 — late chunking and contextual retrieval) and **#92
  `adaptive-chunk`** (reproducing the published per-document recommender).
- **Result:** its Precision Ω reproduces Chroma's published column exactly
  (6.7 / 13.9 / 17.7 / 29.9 over 472 gold-span questions), offline and model-free.
  `make chunking-benchmark`

---

## E. Pipeline-framework tools (generic; useful for metadata-driven platforms)

Plumbing for any config/metadata-driven data pipeline — ingestion, lineage, quality, reference
data, and extracts. Each is generic and standalone; the **Maps to** line names the pipeline need
it serves (handy if you're building a larger platform on top of these).

### 26. `flatfile-parser` — schema-driven extract parser ⭐⭐ 💻 ⚠️
Parse fixed-width / CSV / vendor-XML extracts into typed records using a declared field spec;
nonconforming rows go to a reject file with reasons. The unglamorous front door of legacy ingestion.
- **Learn:** spec-driven parsing, type coercion, and the reject/quarantine pattern.
- **Cost note:** pure code (no model) — fast and free; stream large files line-by-line.
- **Maps to:** legacy/COTS flat-file ingestion.

### 27. `schema-drift-detector` — diff two schema snapshots ⭐⭐ 💻 ⚠️
Compare a captured schema against the previous one; classify each change (add / drop / type-change /
nullability) and emit a drift report with a severity per change.
- **Learn:** schema fingerprinting and modeling "what kind of change is this, and how bad."
- **Cost note:** deterministic diffing; LLM optional, only to narrate a report.
- **Maps to:** per-feed schema-drift policy (auto-evolve / quarantine / fail-fast).

### 28. `load-reconciler` — source↔target reconciliation ⭐⭐ 💻 ⚠️
Compare row counts and control totals (sum/hash of key columns) between a source and its loaded
target, within configurable tolerances; output pass/fail + a delta report.
- **Learn:** control-total reconciliation, the backbone of trustworthy loads.
- **Cost note:** all arithmetic; no model cost.
- **Maps to:** DQ reconciliation / audit logging.

### 29. `config-linter` — validate pipeline config ⭐ 💻 🔌 ⚠️
Validate YAML/JSON pipeline config against a JSON-schema, plus cross-reference checks (does this
feed reference a transform/connector that exists?). Optionally expose as an MCP `lint_config` tool.
- **Learn:** JSON-schema validation + semantic cross-checks; config-as-code guardrails.
- **Cost note:** pure validation; free. A reusable gate for every other tool.
- **Maps to:** config-as-code control plane.

### 30. `sql-lineage` — column-level lineage from SQL ⭐⭐⭐ 💻 ⚠️
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

### 32. `tokenizer` — reversible tokenization vault ⭐⭐ 💻 ⚠️
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

### 36. `scd2-differ` — generate SCD2 merges ⭐⭐ 💻 ⚠️
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

### 39. `cdc-inspector` — make sense of change events ⭐⭐ 💻 ⚠️
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

### 41. `finops-attributor` — cost per feed/domain ⭐⭐ 💻 ⚠️
Join billing/usage data with pipeline run logs to attribute compute/storage cost to each feed or
domain; output a ranked report of where the money goes.
- **Learn:** cost attribution joins and the FinOps "unit economics per pipeline" view.
- **Cost note:** pure aggregation; no model cost.
- **Maps to:** FinOps / cost observability.

### 42. `sql-test-harness` — unit-test your transforms ⭐⭐ 💻 ⚠️
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

### 44. `extract-spec-gen` — scaffold outbound extracts ⭐⭐ 💻 🔌 ⚠️
From a target spec (file/DB/API/SFTP layout) generate an outbound extract config plus a sample
output file so you can validate the shape before wiring the real delivery.
- **Learn:** treating extract generation as the symmetric twin of ingestion config.
- **Cost note:** templating + a dry-run sample; no model cost required.
- **Maps to:** outbound extract engine.

### 45. `watermark-tracker` — high-water-mark state ⭐ 💻 🔌 ⚠️
A tiny service/library to store, advance, reset, and audit the high-water-mark per feed for
incremental/delta loads (last loaded timestamp/id), so reruns are correct and idempotent.
- **Learn:** the state management that makes incremental loads reliable; idempotency.
- **Cost note:** a small key-value store; no model cost. A reusable building block.
- **Maps to:** incremental / delta ingestion.

### 46. `airflow-state-probe` — read-only DAG/run state ⭐⭐ 🔌 💻
Query an orchestrator's state — via the Airflow **stable REST API** (preferred) or read-only against
its metadata tables (`dag_run`, `task_instance`) — to answer "is this DAG running / succeeded /
failed?", when it started/ended, and whether it's **late vs. its schedule**. Expose as MCP tools
(`dag_status`, `last_run`, `is_late`).
- **Learn:** Airflow's run/task data model, REST-API vs. direct-DB tradeoffs, and *strictly
  read-only* access (no triggering/mutation) as a safety boundary.
- **Cost note:** plain queries; no model cost. Cache run state briefly to avoid hammering the API/DB.
- **Maps to:** orchestration / pipeline-state observability. *(Pattern generalizes to any scheduler.)*

### 47. `dag-failure-digest` — explain a failed run ⭐⭐ 💻 ☁️
Given a failed DAG run, find the failing task(s), pull their logs, extract the exception/traceback and
the few lines that actually matter, and produce a crisp failure summary (what broke, where, likely
cause). Deterministic extraction first; LLM only to phrase the gnarly ones.
- **Learn:** navigating task-instance logs, traceback/error extraction, turning noisy logs into a
  one-paragraph diagnosis — keeping the model advisory, not authoritative.
- **Cost note:** log fetch/parse is local; call an API model only for ambiguous failures. Pairs with
  `etl-doctor` (#17) when you want runbook-grounded fixes.
- **Maps to:** pipeline failure triage.

### 48. `pipeline-ops-copilot` — chat with your orchestrator ⭐⭐⭐ 🔌 🧠 ☁️
Compose #46 + #47 (and optionally `etl-doctor` #17 / `runlog-anomaly` #37) behind MCP so an ops user
can ask in plain English: "did the nightly party load finish?", "is feed X late against its SLA?",
"what errored last night and why?" Answers are grounded in **live tool calls**, with an honest
"I don't know / still running" when state is unknown.
- **Learn:** the retrieve-*via-tools* pattern — composing live MCP tools into a grounded conversational
  agent — plus SLA/lateness reasoning and "don't hallucinate state" guardrails.
- **Cost note:** state/log lookups are local tool calls; a small local or API model drives the chat;
  cache status lookups. Off the critical path — read-only, never triggers or mutates DAGs.
- **Maps to:** AIOps / conversational pipeline ops.

## F. Concept labs — the AI/data stack, one measured lab at a time

Sections A–E start from a problem and build a tool. Section F starts from a
**concept** — the 104 concepts in the concept map (`docs/005_concept-coverage.md`)
that recur across AI and data engineering — and builds the smallest thing that
exercises it for real, on a laptop, for roughly nothing.

Three rules hold across the whole section:

1. **Every lab emits an evidence card.** A JSONL record under `evidence/` keyed
   by the concept it covers: what was run, the configuration, the number, the
   baseline it improved on, and what surprised you. That record is what makes a
   lab reproducible later, and it is what a showcase README quotes instead of
   adjectives. `evidence-index` (#90) reads them all back.
2. **Small models, small data, real mechanics.** A 135M-parameter model on CPU
   exercises exactly the same LoRA config, the same KV-cache arithmetic and the
   same catastrophic-forgetting check as a 70B one. Rent a GPU hour only where
   the mechanism genuinely needs it.
3. **The failure is the deliverable.** Each lab has a *break it on purpose*
   step — the skew that sticks at 99%, the async endpoint that collapses under
   load, the quantized model that got quietly worse. Understanding a system
   means having watched it fail in a way you can now explain.

**Legend addition:** 🎓 marks a lab whose primary output is a measurement rather
than a reusable tool. Those are the cheapest to build and the fastest to learn
from; the unmarked ones are tools you will actually reuse.

### 50. `token-ledger` — what a request costs and what got dropped ⭐⭐ 💻 💸
Count tokens per request across prompt / retrieved context / history / output,
price them separately for input and output, and enforce a context budget with a
declared **drop policy** (truncate oldest, summarize history, rank-and-drop
chunks, drop the middle). Emits a per-request ledger row: what fit, what was
evicted, by which rule, and what it cost.
- **Learn:** tokens as a *budget*, not a definition; the overflow decision every
  real system has to make; input vs. output pricing.
- **Cost note:** tokenizers run locally; pricing is a config table. $0.
- **Covers:** §1 Token · §1 Context window · §7 Cost & token economics ·
  §6 Memory & context management (overflow half).

### 51. `decode-lab` — temperature, sampling, and the determinism myth ⭐ 💻 🎓
Sweep temperature / top-p / seed over a fixed prompt set and measure what
actually changes: output variance, JSON parse-failure rate, extraction accuracy,
answer length. Includes the temperature-0 run repeated 50× to show it still
isn't strictly deterministic.
- **Learn:** picking a setting per *component* (near-zero for extraction,
  higher for drafting) instead of leaving a global default.
- **Cost note:** local Ollama, a few hundred short generations. $0.
- **Covers:** §1 Temperature & sampling · §1 Hallucination (variance surface).

### 52. `schema-guard` — structured output that is checked twice ⭐⭐ 💻 🔌
A validation layer for model output: JSON-schema/Pydantic enforcement, a
retry-with-the-error loop, fallback defaults — and then a **second, semantic**
gate of business rules, because schema-valid is not correct. Reports the two
failure classes separately: *didn't parse* vs. *parsed and was wrong*.
- **Learn:** schema compliance ≠ semantic correctness — the distinction that
  bites everyone who parses model output; the same guard in front of tool-call
  arguments.
- **Cost note:** validation is local; only the retry path calls a model.
- **Covers:** §1 Structured output / function calling · §16 Validation at the
  boundary · §6 Tool-argument validation.

### 53. `retrieval-bench` — BM25 vs. vector vs. hybrid vs. reranked ⭐⭐⭐ 🧠 💻
Run the same query set through four retrieval configurations over one corpus and
report recall@k, MRR, context precision, latency and cost for each. Ships a
deliberately hostile query set: exact error codes, part numbers and proper nouns
— the queries where pure vector search fails and hybrid earns its place. Adds a
cross-encoder second stage (retrieve 50 cheap, keep 5 expensive) and reports what
it actually changed.
- **Learn:** why hybrid exists, what fusion weighting does, and what a reranker
  buys — measured, not asserted.
- **Boundary with #25:** **#53 varies the retriever with chunking fixed; #25
  `chunking-lab` varies the chunker with the retriever fixed.** Neither subsumes
  the other, and a benchmark that moves both at once measures neither.
- **Cost note:** local embeddings + a small CPU cross-encoder; reuses
  `embeddings-cache` (#23). $0.
- **Covers:** §2 The RAG pipeline · §2 Hybrid search · §2 Re-ranking ·
  §5 Retrieval metrics (retrieval half).

### 54. `lora-lab` — a fine-tune you can quote the configuration of ⭐⭐⭐ 💻 🎓
QLoRA a small instruct model on a narrow task, recording every number you have
to choose anyway: **rank, alpha, target modules by parameter name**
(`q_proj`, `v_proj`, …), dataset size, epochs, VRAM, wall time. Then the
part most people skip — evaluate on a held-out **general** benchmark alongside
the task metric, to see whether it got worse at everything else.
- **Learn:** what each LoRA knob does; why frozen base weights reduce
  catastrophic-forgetting risk versus a full fine-tune; adapter versioning.
- **Cost note:** 135M–1.1B model, 4-bit, on CPU or one rented GPU hour
  (~$1–3). Keep the adapter, throw away the base.
- **Covers:** §3 LoRA configuration · §3 Catastrophic forgetting ·
  §3 Pre-training vs. fine-tuning vs. inference (demonstrated end to end).

### 55. `synthdata-forge` — generated training data, and what you threw away ⭐⭐ ☁️ 💻
Generate instruction/response pairs with a larger model, then **verify** them
with programmatic checks plus a judge, and record the rejection rate and the
reason for every discard. Builds the held-out test set *before* training, dedups
near-duplicates, and stamps provenance on each example.
- **Learn:** why data quality beats quantity; why the rejection rate is the
  number that proves you verified anything.
- **Cost note:** generate with a cheap API model in one batch; verify locally.
  A few dollars, once.
- **Covers:** §3 Training data preparation & synthetic generation.

### 56. `preference-forge` — preference pairs, a reward model, and DPO ⭐⭐⭐ 💻 🎓
The alignment stack at toy scale: collect preference pairs over your own model's
outputs, have two annotators (you, and a judge model) label them, measure
**inter-annotator agreement**, train a small reward model, then run **DPO** and
compare against the SFT baseline. Documents where PPO's extra machinery would
still be worth it, and watches for reward hacking.
- **Learn:** the three RLHF stages as distinct artifacts; why DPO drops the
  separate reward model; why label quality caps model quality.
- **Cost note:** tiny model, a few hundred pairs, CPU or one GPU hour.
- **Covers:** §4 The three stages · §4 DPO vs. PPO · §4 Preference data
  collection.

### 57. `judge-lab` — is your LLM judge any good? ⭐⭐ 🧠 ☁️
Grade a sample of outputs by hand, then have judge models grade the same sample,
and report the agreement. Probes the known pathologies directly: verbosity bias
(same answer, padded), position bias, and drift when the judge model version
changes. Outputs a sampling plan for ongoing human spot-checks.
- **Learn:** using a judge for scale while keeping it calibrated, and knowing
  which of its scores you are allowed to trust.
- **Cost note:** judge with a local model for CI, an API model weekly. Cents.
- **Covers:** §5 LLM-as-judge · §5 Task metrics vs. vibes (measuring the parts
  that resist hard metrics).

### 58. `agent-governor` — the scar tissue around a ReAct loop ⭐⭐⭐ 🔌 💻
A ReAct runner built entirely out of the controls that separate a demo loop from
one you would leave running: a hard iteration ceiling, a per-session spend cap, a
timeout and a defined failure state, repeated-action detection (same tool, same
arguments, three times), a tool registry with schemas and argument validation
*before* execution, a read/write action split with confirmation gates on the
irreversible ones, session memory with an explicit overflow policy and a
staleness check, and a full audit log of every decision.
- **Learn:** when *not* to use an agent; what a graph gives you that a chain
  doesn't (implement the same task as a fixed pipeline, a plain loop, and a
  LangGraph state machine, and write down the difference).
- **Cost note:** local model for the loop; the caps are the point — every run
  reports its actual token spend.
- **Covers:** §6 Agent vs. pipeline · §6 The ReAct loop · §6 Tool calling & MCP ·
  §6 Memory & context management · §6 Frameworks · §6 Guardrails & HITL.

### 59. `promptops` — prompts as code, with a gate ⭐⭐ 💻 🔌
A prompt registry where every prompt is a versioned, hashed artifact in git:
diffable, reviewable in a PR, deployable per environment, and rollback-able. A
change triggers the golden-set eval and **blocks** on regression; the running
service reports which prompt hash produced any given response.
- **Learn:** the discipline that separates "prompts in a database, edited live"
  from an auditable system.
- **Cost note:** eval runs use a local judge in CI. $0 per change.
- **Covers:** §7 Prompts as versioned artifacts.

### 60. `model-pin` — catching the provider changing under you ⭐⭐ ☁️ 💸
Pin exact dated model versions, then run the golden set on a schedule against
both the pinned version and the floating alias, and diff the behaviour: score
deltas, output-length shifts, format breakages, refusal-rate changes. Produces a
staged-rollout checklist and a rollback switch for version moves.
- **Learn:** the single best LLMOps question — how you *find out* the model
  moved, rather than hearing it from a user.
- **Cost note:** a 60-example golden set, weekly, on a cheap model. Cents.
- **Covers:** §7 Model version pinning & provider drift.

### 61. `llm-trace` — reconstruct exactly what happened yesterday ⭐⭐⭐ 💻 🔌
OpenTelemetry instrumentation for an LLM pipeline: full prompt and response
logged against the prompt hash and model version, token counts, latency broken
out **by stage** (retrieve / rerank / generate / validate), fallback rate and
confidence distribution — plus redaction on the logging path, because the
observability layer is where PII quietly accumulates. Ships a `trace complaint`
command that goes from a user's report to the exact call.
- **Learn:** the tension at the centre of LLM observability — you cannot debug
  what you didn't log, and you cannot log everything if it contains personal
  data.
- **Cost note:** local collector; sampling policy for high-volume stages.
- **Covers:** §7 Observability for LLM systems · §21 PII in traces and logs.

### 62. `serve-bench` — throughput, latency, and the KV cache ⭐⭐⭐ 💻 🎓
Serve one open model two ways — naive `transformers` and a real engine (vLLM, or
llama.cpp where GPU access is scarce) — and measure the numbers that actually
describe a serving setup: **p50 and p95 at stated concurrency**, time-to-first-token
separately, tokens/sec throughput, and the concurrency ceiling. Includes a KV
cache calculator (layers × heads × dim × sequence × batch × precision) showing
why the cache, not the weights, caps concurrent users, and a hosted-vs-self-host
cost-crossover model over volume.
- **Learn:** why serving engines improve throughput far more than single-request
  latency; continuous batching and PagedAttention as mechanisms, not names.
- **Cost note:** llama.cpp locally for free; one rented GPU hour for the vLLM
  comparison.
- **Covers:** §8 KV cache · §8 Serving engines · §8 Throughput vs. latency ·
  §8 Self-host vs. hosted API · §8 Real-time, batch & streaming inference.

### 63. `quant-check` — what quantization actually cost you ⭐⭐ 💻 🎓
Quantize one model at several precisions and methods (GGUF Q8/Q4, bitsandbytes
8-bit/4-bit, AWQ or GPTQ where hardware allows) and run the *same fixed eval set*
before and after, reporting memory saved, throughput gained, and quality lost —
per precision, in a single table.
- **Learn:** that the entire discipline is deciding how much quality you can
  afford; and that without an eval set you cannot have verified any of it.
- **Cost note:** CPU quantization of a small model. $0.
- **Covers:** §8 Quantization.

### 64. `trainer-lab` — a training loop you have watched overfit ⭐⭐⭐ 💻 🎓
Train small models from scratch and fine-tune others in PyTorch, plotting
training vs. validation loss until you can point at the divergence and stop on
it: early stopping, LR schedules, batch size and gradient accumulation. Then run
the same task three ways — encoder-only classifier, decoder-only generator,
encoder-decoder seq2seq — and write down why one fits the problem shape better.
Includes an attention-weight visualisation and a deliberate leakage experiment
that produces a suspiciously excellent score.
- **Learn:** loss, epochs, splits, leakage, and the architecture choice with a
  stated reason rather than a name.
- **Cost note:** tiny datasets on CPU; one GPU hour if you want the seq2seq run
  to finish quickly.
- **Covers:** §9 Training, loss & the training loop · §9 Train/val/test split &
  leakage · §9 Transformers & attention · §9 Encoder, decoder, encoder-decoder ·
  §9 PyTorch vs. TensorFlow (companion note: the same model in both).

### 65. `taxonomy-classifier` — ten thousand labels, long tail ⭐⭐⭐ 💻 🧠
Classification into a large hierarchical label space (a public product taxonomy
or similar), tried four ways: rules baseline, flat classifier, hierarchical
decomposition, and retrieve-then-rank. Reports **per-category** metrics rather
than one aggregate, names the labels it gets wrong most and why, and routes
everything under a confidence threshold to human review.
- **Learn:** why flat classification is awkward at scale; picking precision or
  recall from the cost of each error; where rules genuinely beat a model.
- **Cost note:** small encoder model + local embeddings. $0.
- **Covers:** §9 Large label spaces & hierarchical classification · §9 Rules vs.
  machine learning · §9 Precision, recall & why accuracy lies (applied).

### 66. `tabular-lab` — the ML most business data actually runs on ⭐⭐ 💻 🎓
Gradient boosting done properly on a public tabular dataset: early stopping on a
validation set, `max_depth` and `learning_rate` as the knobs that matter, native
missing-value handling, class imbalance addressed by **threshold tuning** rather
than the default 0.5, Optuna searching against validation and never the test set,
a deliberate temporal-leakage hunt, and SHAP output in two registers — global
importance for the team, a local explanation for the person the decision was
about.
- **Learn:** why boosting beats a single tree and usually beats deep learning on
  tabular data; why tuning gives less than better features.
- **Cost note:** scikit-learn / LightGBM on CPU. $0.
- **Covers:** §10 Gradient boosting · §10 Feature engineering & leakage ·
  §10 Hyperparameter tuning · §10 Class imbalance · §10 Explainability: SHAP.

### 67. `asr-bench` — a WER number you can quote ⭐⭐ 💻 🎓
Transcribe a public speech corpus with Whisper at two model sizes and compute WER
with `jiwer` — baseline and after each intervention: domain-vocabulary biasing,
and denoising on/off, run in both directions **because aggressive suppression can
raise WER**. Breaks the aggregate WER out by speaker group (accent, gender) so
the disparity that an average hides becomes visible.
- **Learn:** how WER is computed and why it can exceed 100%; that the reference
  transcript's provenance is part of the claim; differential accuracy as a
  fairness finding, not just a quality one.
- **Cost note:** `faster-whisper` on CPU over a few hours of audio. $0.
- **Covers:** §11 Word Error Rate · §11 Denoising & the audio front-end ·
  §11 Differential accuracy across speakers.

### 68. `diarize-id` — who spoke when, and who they are ⭐⭐⭐ 💻 🎓
Diarization scored with **DER** (missed speech + false alarm + speaker
confusion), deliberately including overlapping-speech segments and recordings
where the speaker count is unknown in advance. Then speaker *identification* on
top: enrol voice profiles, sweep the similarity threshold, plot false match
against false reject, and make "unknown speaker" a first-class outcome rather
than forcing an assignment.
- **Learn:** why a word-perfect transcript with wrong speaker labels is useless
  in an evidentiary setting; where to set a threshold when a false match is the
  expensive error.
- **Cost note:** `pyannote` community models on CPU. $0.
- **Covers:** §11 Diarization & DER · §11 Speaker identification & enrolment.

### 69. `vision-task-lab` — three tasks, three annotation budgets ⭐⭐ 💻 🎓
The same small image set labelled three ways — image labels, bounding boxes,
pixel masks — with the **annotation time recorded for each**, then a model
trained per task and scored on the right metric (accuracy, mAP, IoU). Second
experiment: a fine-tuned CNN versus a ViT at 200 / 2,000 / 20,000 training images,
producing the data-hunger curve that decides which you should have picked.
- **Learn:** that the fanciest task is rarely the right one, and that annotation
  cost — not model choice — is what a real vision project argues about.
- **Cost note:** small pre-trained backbones, transfer learning, CPU-feasible at
  these sizes. $0.
- **Covers:** §12 Classification, detection, segmentation · §12 CNNs vs. vision
  transformers.

### 70. `doc-vlm-verify` — catching a model describing what isn't there ⭐⭐ ☁️ 🧠
Extract structured fields from document images with a vision-language model, then
**verify every extracted value** against the page — OCR cross-check, regex and
range rules, and a re-ask with the crop. Builds a catalogue of what these models
get wrong: fine detail, dense text-in-image, small numerals, and confidently
described objects that are absent. Reports cost per page.
- **Learn:** that multimodal models hallucinate about images exactly as they do
  about text, and that specific extraction is far weaker than general description.
- **Cost note:** a few hundred pages against a cheap vision model; OCR locally.
- **Covers:** §12 Multimodal vision-language models. *(Also delivers idea #6.)*

### 71. `recsys-lab` — implicit signals and the cold start ⭐⭐ 💻 🎓
Matrix factorization on a public interaction dataset, built on **implicit**
feedback with an explicit decision about negative sampling — what counts as a
non-preference when a non-click might just be a non-view. Adds content-based
signals for new items, a popularity/segment default for new users, and reports
catalogue coverage so the long tail's absence is visible.
- **Learn:** the ambiguity of implicit data; why cold start is the first thing
  that breaks in production and never fully goes away.
- **Cost note:** `implicit` / `lightfm` on CPU. $0.
- **Covers:** §13 Collaborative filtering & matrix factorization · §13 Cold start.

### 72. `ab-lift` — proving the model caused the number ⭐⭐ 💻
The instrument for every percentage anyone claims: design a holdout or A/B test
(power analysis, minimum detectable effect, required duration), analyse the
result with proper significance, and quantify the gap between the offline metric
and the online outcome. Keeps a confounder log — seasonality, marketing, releases
— so "revenue rose during the period" is never mistaken for attribution.
- **Learn:** the single best question to ask of any claimed ML business impact,
  including your own.
- **Cost note:** pure statistics, no model. $0.
- **Covers:** §13 Attribution — proving it worked.

### 73. `kg-hop` — the question vector search cannot answer ⭐⭐⭐ 🧠 💻
Extract entities and relations from a corpus into a small graph, then run a query
set through both graph traversal and vector retrieval, keeping the queries that
**only the graph can answer** — the multi-hop ones ("which cases involve people
connected to this vehicle"). Records the maintenance cost of keeping the graph
current, and a hybrid mode that uses both.
- **Learn:** the concrete motivation for a knowledge graph, and its honest price.
- **Cost note:** local extraction with a small model; SQLite or a local graph
  store. $0.
- **Covers:** §14 Knowledge graphs vs. vector retrieval.

### 74. `sql-safeguard` — text-to-SQL that cannot hurt you ⭐⭐⭐ 🧠 🔌 💻
Everything that sits between a generated query and a database: parse the SQL and
validate **every table and column against the real catalogue** before execution,
retry with the specific error fed back, and restrict generation to a curated
semantic layer of views rather than the raw schema. Then the execution guard —
read-only credentials first, non-`SELECT` blocked, `EXPLAIN`-based cost estimate,
row limits, statement timeouts, per-tenant row scoping. Evaluates whether the SQL
was *correct*, not merely runnable, against known-good answers.
- **Learn:** the two distinct failure modes — hallucinated schema and dangerous
  execution — and that read-only credentials are the answer you give first.
- **Cost note:** DuckDB/SQLite locally; generation with a small model.
- **Covers:** §14 Stopping hallucinated schema · §14 Execution safety.
  *(Pairs with `sqlite-mcp` #11 and `query-copilot` #21.)*

### 75. `runcard` — could you reproduce last year's model? ⭐⭐ 💻 🔌
Experiment tracking with a **reproducibility contract**: a run is only recorded
if it carries parameters *plus* a data version hash *plus* the code commit *plus*
the environment lock. On top of it, a model registry with stages
(staging → production → archived), an approval gate on promotion, a one-command
rollback, and a `what is serving right now` answer that comes from the registry
rather than from memory.
- **Learn:** why logging metrics alone doesn't reproduce anything; that the
  rollback story is the part that proves the registry was real.
- **Cost note:** MLflow locally against SQLite. $0.
- **Covers:** §15 Experiment tracking · §15 Model registry & promotion.

### 76. `drift-sentry` — monitoring a model whose answers arrive late ⭐⭐⭐ 💻 🔌
Separates **data drift** (input distributions moving — detectable immediately)
from **concept drift** (the input→outcome relationship changing — invisible until
outcomes arrive), computes PSI, KL divergence and feature quantiles, and registers
each model's **ground-truth lag** so the dashboard says "accuracy unavailable for
another 78 days" instead of showing a stale number. Because Prometheus stores
numbers and not distributions, it computes the summary upstream and emits a
scalar gauge — with the alert threshold, the runbook and the on-call owner
attached.
- **Learn:** what number you actually send a metrics system to detect drift; what
  a drift alert should make someone *do*.
- **Cost note:** batch job + local Prometheus/Grafana. $0.
- **Covers:** §15 Data drift vs. concept drift · §15 Ground-truth lag ·
  §15 Metrics systems can't store distributions.

### 77. `async-trap` — fast in testing, dead under load ⭐⭐ 💻
A FastAPI service that reproduces the most common serious bug in Python AI
services on demand: a blocking call inside an `async` endpoint, benchmarked
against the same endpoint declared as a plain `def` and against
`run_in_executor`, under rising concurrency. Also measures **memory per worker**
with the model loaded (the Gunicorn multiplication that exhausts a machine),
loads at startup rather than per request, and gates the readiness probe on the
model being loaded.
- **Learn:** why the event loop is shared, where to look when concurrency
  degrades, and why liveness and readiness are not the same probe.
- **Cost note:** a small local model or a stub; the point is the load shape. $0.
- **Covers:** §16 The blocking-call-in-async trap · §16 Loading the model.

### 78. `job-runner` — four-minute requests and dead workers ⭐⭐ 💻 🔌
Long work moved off the request path: a queue, a worker, job status surfaced back
to the caller, and the operational realities — **idempotent tasks** so redelivery
is safe, a visibility timeout, retry with backoff, a dead-letter queue with
alerting and a replay path, and a documented answer to "a worker died halfway
through: what happens to that job?" (which it demonstrates by killing one).
- **Learn:** that queues redeliver, so tasks must be safe to run twice.
- **Cost note:** local Redis or SQLite-backed queue. $0.
- **Covers:** §16 Long-running work & background jobs · §18 Poison messages &
  dead letter queues (the consumer half).

### 79. `spark-clinic` — the job that sticks at 99% ⭐⭐⭐ 💻 🎓
Local Spark against a synthetic dataset with a deliberately poisoned join key (a
null, a placeholder customer ID, one enormous account). Reproduce the stall, read
the stage timings and the DAG from the event log, identify the skew from task
duration distribution, then fix it three ways — **salting**, a broadcast join, and
isolating hot keys — with adaptive query execution on and off, timing each. A
second experiment benchmarks a Python UDF against the built-in equivalent to
measure the serialisation penalty, and a third breaks a broadcast join by
underestimating table size until the driver runs out of memory.
- **Learn:** transformations vs. actions, what triggers a shuffle, how to size
  partitions, and where the time actually went.
- **Cost note:** PySpark in local mode. $0 — no cluster required.
- **Covers:** §17 Execution model & lazy evaluation · §17 Data skew ·
  §17 Shuffle, partitions & broadcast joins · §17 Scala vs. PySpark.

### 80. `delta-keeper` — Parquet, Delta and the maintenance nobody schedules ⭐⭐ 💻
Measure predicate pushdown and column pruning directly (bytes read for the same
query over CSV, row-group-unaware Parquet, and well-sorted Parquet), then run the
Delta operations as distinct jobs with before/after numbers: `OPTIMIZE`
compacting small files, `ZORDER` (and Liquid Clustering) co-locating related
data, and `VACUUM` — with the retention policy reasoned about, because vacuuming
past the window **destroys time travel**. Includes a time-travel recovery drill.
- **Learn:** what Delta gives you that plain Parquet doesn't, as four operations
  with different jobs rather than a feature list.
- **Cost note:** `delta-spark` locally on a few GB. $0.
- **Covers:** §17 Parquet, Delta & maintenance operations.

### 81. `stream-lab` — ordering, lag and a poison message ⭐⭐⭐ 💻 🔌
A local Redpanda/Kafka with a producer, a topic with several partitions and a
consumer group. Demonstrates the fact that surprises everyone: **ordering holds
within a partition, not across a topic** — so the partition key is a design
decision — and that consumers beyond the partition count sit idle. Then the
operational layer: offset management, consumer-lag monitoring, an idempotent
consumer, and a malformed message that kills the consumer repeatedly until it is
routed to a DLQ with an alert and a replay path.
- **Learn:** why "exactly once" needs conditions attached, and why idempotent
  consumers are the practical answer.
- **Cost note:** single-node Redpanda in Docker. $0.
- **Covers:** §18 Kafka: topics, partitions, consumer groups · §18 Poison
  messages & dead letter queues · §18 Batch vs. streaming (companion note).

### 82. `backfill-drill` — three months of bad data ⭐⭐⭐ 💻
CDC events applied with `MERGE`, made **idempotent** on purpose: deterministic
keys, upsert rather than append, partition overwrite, and a processed-batch
marker written in the *same transaction* as the data — then re-run the whole load
twice to prove the row counts don't move. Handles deletes and late-arriving
records, and ships the runbook for the worst case: discovering three months of
bad data and backfilling it without double-counting.
- **Learn:** the distinction between deduplicating afterwards and being safe to
  re-run — the thing that separates operating a pipeline from writing one.
- **Cost note:** DuckDB or local Delta. $0. *(Extends `cdc-inspector` #39.)*
- **Covers:** §18 CDC, MERGE & idempotency.

### 83. `spot-runner` — work that survives being interrupted ⭐⭐ 💻 💸
Run a long batch job as resumable units with checkpointing, then **kill it
mid-flight** (a simulated reclamation notice, then a hard stop) and measure how
much work was lost and how long recovery took. Adds a spot/on-demand blend for
the critical path and quantifies the saving against the actual run rate, not
against a list price.
- **Learn:** the checkpointing story behind most large cloud cost savings, and
  which workloads can never use spot.
- **Cost note:** simulate locally for free; one real spot instance for a few
  hours if you want the reclamation to be genuine (~$1).
- **Covers:** §19 Spot instances & interruption handling · §19 Cost optimisation
  (the mechanisms half, with `finops-attributor` #41).

### 84. `cutover-kit` — proving the data matched ⭐⭐⭐ 💻
A migration rehearsal: replicate a source to a target, run them in **shadow /
dual-write** mode, and reconcile at two levels — row-level checksums and
aggregate comparisons — with a discrepancy report that names the rows. Then the
cutover mechanics: the freeze window, the switch, the verification gate, and a
rollback plan that gets tested rather than written.
- **Learn:** that reconciliation is the answer to "how did you know it worked",
  and that a migration without a rollback plan is a hope.
- **Cost note:** two local databases. $0. *(Builds on `load-reconciler` #28.)*
- **Covers:** §19 Large migrations & cutover.

### 85. `deploy-kit` — infrastructure and a pipeline that blocks ⭐⭐ 💻 🔌
Terraform for one of this collection's tools, done the way it has to be done to
survive a second engineer: **remote state with locking**, modules, environment promotion, a
reviewed `plan` before `apply`, and scheduled drift detection that reports
manual changes. Alongside it, CI that actually **stops** things — failing tests,
a coverage floor, a security scan, secrets sourced outside the repo — plus an
environment promotion path and a rollback command.
- **Learn:** state as the daily pain of Terraform; gates that block versus
  pipelines that only report.
- **Cost note:** `terraform plan` against a local backend or a free-tier
  resource. ~$0.
- **Covers:** §19 Terraform & infrastructure as code · §19 CI/CD.

### 86. `k8s-lab` — operating, not just deploying ⭐⭐⭐ 💻
A `kind` cluster running one of these tools, then every failure that teaches you
something, provoked deliberately: an OOMKill from a memory limit set too
low, a crash loop, a readiness probe that never passes (and the traffic
consequences of confusing it with liveness), a rollout that fails and is rolled
back, and a node pool exhausted by missing resource requests.
- **Learn:** requests vs. limits and what happens without them; the difference
  between running the cluster and running on one — stated honestly either way.
- **Cost note:** `kind` on a laptop. $0.
- **Covers:** §20 Operating vs. deploying onto.

### 87. `fleet-conf` — what breaks at a hundred clusters ⭐⭐⭐ 💻 🔌
Three local clusters, one templated configuration, and the fleet problems that
replace single-cluster mechanics: **configuration drift** detection across
clusters, policy enforced centrally, observability aggregated into one dashboard,
and a cost model showing that fleet-scale telemetry can rival compute. Includes
an alert-discipline exercise — write alerts tied to user-visible failure, then
delete one that wasn't earning its keep, and record why.
- **Learn:** why automation and standardisation are the only answers at fleet
  scale; alert fatigue as a design failure rather than a rota problem.
- **Cost note:** three `kind` clusters + Prometheus locally. $0.
- **Covers:** §20 Multi-cluster & fleet management · §20 Observability & alert
  discipline.

### 88. `jailbreak-range` — what got through ⭐⭐ 🧠 💻
A red-team suite against your own guardrails: prompt injection through retrieved
documents and tool output, instruction override, exfiltration attempts,
off-topic and unsafe use. Scores two rates that must be reported together — the
**bypass rate** and the **false-positive rate on legitimate traffic**, because
over-blocking is also a failure. Ships with a written threat model for the
specific system, and a log of concrete misses and how each was handled.
- **Learn:** that filtering is imperfect, and that "nothing ever got through"
  means nobody looked.
- **Cost note:** local model as the target; the attack corpus is static. $0.
- **Covers:** §21 Guardrails & jailbreak resistance.

### 89. `fairness-audit` — the numbers an aggregate hides ⭐⭐⭐ 💻 🧠
Takes any model in this collection and reports **error rates disaggregated by
group** rather than one headline metric, with confidence intervals and a
minimum-subgroup-size guard. Adds the governance half: human review positioned
as a fairness control with a stated confidence threshold and a review-capacity
budget, a complete audit trail, and an **appeal packet** — what you can actually
show a person who challenges a decision, built from the local explanation
produced by `tabular-lab` (#66).
- **Learn:** that fairness questions answered with access control and encryption
  are answering a different question; that a system assisting a human is a
  different risk posture from one deciding.
- **Cost note:** analysis over existing predictions. $0.
- **Covers:** §21 Bias, fairness & differential performance · §21 Human-in-the-loop
  as a control. *(PII redaction lives in `pii-scanner` #20 and `llm-trace` #61.)*

### 90. `evidence-index` — what has been measured, and what hasn't ⭐⭐ 💻 🔌
The capstone, and the reason every other lab writes an evidence card.
`evidence-index` reads `evidence/*.jsonl` across the whole collection and answers
three questions: which of the 104 concepts have a measured result behind them,
which have only a note, and which have nothing at all. It validates each card
(does the number have a baseline? a stated scale? a reproduction command?),
refuses cards whose claim is an adjective rather than a measurement, and renders
the whole set as a **showcase page** — one line per lab, the number it produced,
and the command that reproduces it — suitable for the repo README or a
spun-out portfolio repo.
- **Learn:** treating your own results the way you would treat a model's — as
  claims that need provenance, a baseline, and a way to re-run them.
- **Cost note:** local; pure aggregation over JSONL. $0.
- **Covers:** the coverage map itself — and the showcase seam described in
  [`docs/005`](docs/005_concept-coverage.md#showcasing-the-work).

---

### 91. `context-aug-lab` — do late chunking and contextual retrieval earn their cost? ⭐⭐⭐ 🧠 ☁️
Tier 2 of the chunking taxonomy, split out of `chunking-lab` (#25) because it is a
different experiment with a different cost model. #25 measures where the *cuts*
go; this measures what happens when the cuts stay put and the **unit changes** —
late chunking (embed the document, then pool per chunk), contextual retrieval (an
LLM writes a 50–100 token blurb onto each chunk before indexing), and the
LLM-boundary chunkers.
- **Why it is separate:** #25's whole default path is model-free and deterministic.
  This one is one LLM call per chunk at index time, so it can never be, and mixing
  the two would forfeit the property that makes #25 runnable anywhere.
- **The question worth answering:** the reported numbers disagree sharply. Anthropic
  reports failed retrievals down 35/49/67%; *Reconstructing Context* (ECIR 2025)
  measured the same family independently at **near-noise margins** (NDCG@5 0.317 vs
  0.312). Somebody should settle which regime each result belongs to.
- **Reuses:** `chunking-lab`'s corpora, gold spans, character-level metrics and
  result schema — `Span` already carries `retrieval_text` and `return_text`
  separately, which is exactly what this family needs.
- **Cost note:** one chat call per chunk at index time. Local models make it free
  and slow; budget a few dollars for a hosted comparison.
- **Covers:** §2 The RAG pipeline (the augmentation half) · §5 Retrieval metrics.

### 92. `adaptive-chunk` — reproduce the published recommender, then check it ⭐⭐⭐ 🧠 💻
A POC of **Adaptive Chunking** (arXiv 2603.25333, LREC 2026), which selects a
chunking method *per document* from five intrinsic metrics with no retrieval run —
References Completeness, Intrachunk Cohesion, Document Contextual Coherence, Block
Integrity, Size Compliance — and reports raising answer correctness to 72% from
62–64%.

This is deliberately **not** `chunking-lab suggest`. Building a recommender of our
own would have been completeness; reproducing a published one and then testing it
is a result either way.
- **The question:** does it reproduce, and does its selection beat the best *fixed*
  strategy on the same corpus? A per-document recommender has to beat "just use
  recursive:200 everywhere" to be worth its complexity, and that baseline is
  rarely the one reported.
- **Why now:** `chunking-lab` (#25) already measured that its own model-free
  intrinsic signals mostly proxy chunk size (F8), and that the structural ones do
  not predict retrieval quality at all (F9). Those are close cousins of Adaptive
  Chunking's five, so there is a specific, falsifiable thing to check.
- **Reuses:** #25's corpora, gold spans, metrics, `correlate` and `axes`.
- **Cost note:** the metrics are cheap; the evaluation is #25's, which is free.
- **Covers:** §2 Chunking · §5 Retrieval metrics · the reproduction habit itself.

### 219. `slopify` — put the tells back in, on purpose ✅ ⭐⭐ 💻
Takes a passage a human wrote and injects the habits #218 looks for, at positions it
records. Deterministic and seeded, so the same input and seed give the same output
every time, and each injection is written out as a label (line, habit, quote) in the
format `tools/ai-sniffer/eval/labels.jsonl` already uses. It's the inverse of the
reviewer, and it exists because every number in #218's eval rests on 165 labels one
person wrote: injection gives ground truth with no labeller's judgement in it.

Transformations, one per habit in #218's catalogue: split a claim into "It isn't Y.
It's X." (antithesis); pad a pair into three (triad); soften a universal to "almost
every" (hedge); prefix "Note that" (reader-instruction); break a clause into a one-line
paragraph (dramatic-beat); append a summarising line to a section (closer); replace a
number or a name with "surprisingly" (generic-detail); insert "exactly" before a verb
(emphasis-word).

- **What it buys the eval:** per-habit recall, which the hand labels can't give — they
  hold 34 antithesis labels and 2 restatement. Run 50 injections per habit and every
  tool and model in the comparison gets a recall figure per habit, with no ambiguity
  about what the right answer was.
- **The limit, to state wherever its numbers appear:** injected habits are what a
  template produces on demand, not what a model produces when left alone. A tool can
  score well here and badly on real drafts, so these numbers stay a diagnostic and the
  hand-labelled held-out numbers stay the headline.
- **Source text matters.** Inject into prose no model wrote: Pavan's own older writing,
  or public-domain text. Injecting into Claude-drafted posts would measure habits on
  top of habits.
- **The demo it makes possible:** one human paragraph, one slopped paragraph, and the
  linter's output under each. No model needed.
- **Where it fits:** built after Pavan's label review is applied and #218's scores are
  final, and before post 3 of the series, whose comparison it strengthens.
- **Covers:** §4 What alignment does to style · §5 Task metrics vs. vibes · building
  ground truth rather than judging it.
- **Built:** [`tools/slopify/`](./tools/slopify/), eleven injectors, stdlib only.
  Design record [`docs/014`](./docs/014_slopify.md). Source prose is three Simon
  Willison posts from 2018 to 2021, downloaded by `corpus/fetch.py` and hash-pinned
  rather than committed, since they carry no reuse licence.
  Two measurements came out of it. **The linter fires 56 times on 4,695 words of
  human technical blogging before anything is injected** — 37 of them one-sentence
  paragraphs, which this author writes deliberately. That is the *break it on
  purpose* step, and the best argument in the repo for having no verdict mode.
  **Per-habit recall over 320 single-habit injections, discounting that baseline:
  129 quoted.** Perfect on the habits that are a closed word list
  (reader-instruction 30/30, emphasis-word 30/30), and at or near zero on every
  habit that is a shape — antithesis, closer, triad and restatement are 3 of 120
  between them. That is the case for the reviewer prompt, per habit, in numbers.
  Three counts differ from the plan above: severity is fixed at `high` rather than
  judged, `--count` is a ceiling because an injector declines where a paragraph
  offers no site, and the corpus is fetched rather than shipped.
  (An earlier run used posts from `pavanrao.github.io` as the human baseline; Pavan
  confirmed they were all model-written to his instructions. docs/014 §2 keeps the
  superseded claim and §5b the superseded numbers.)
- **Prior art, searched after building again.** The method is mutation testing aimed
  at a linter. [CheckList](https://aclanthology.org/2020.acl-main.442.pdf) (ACL 2020)
  already does templated perturbation with per-capability reporting, which is what
  per-habit recall is; [APT-Eval](https://arxiv.org/pdf/2502.15666) already builds
  detector benchmarks by adding AI-ness to human text, using LLM polishing. What is
  left as ours is span-level ground truth: a template gives the line and the exact
  words, so recall can be scored against a reviewer that quotes, which polishing
  cannot do. Reading those two first would not have stopped the build; it would have
  made that the stated reason for it on day one.

### 218. `ai-sniffer` — the tells in your own draft ✅ ⭐⭐ 💻 🔌
Counts the habits that make prose read as machine-written, and refuses to say
whether it was. Sentence-length variance; contraction rate; the recurring
"not X, but Y" pivot; paragraphs that keep landing on a short sentence; hedge
density; and how much concrete detail the text carries at all — digits, dates,
proper nouns, quoted error strings. Findings arrive with positions, so the
output is *line 40, fourth consecutive paragraph ending short* rather than a
score, because locating a habit is reliable where classifying an author is not.
The number is the **overlap** between a pre-2022 human corpus and a generated
one, per signal: how often any threshold would misclassify. That unreliability
is the finding rather than a caveat, and it is why the tool has no verdict mode.
The *break it on purpose* step is pointing it at deliberately idiosyncratic
human writing, counting the false positives, and then pointing it at this
repository's own documentation.
- **Learn:** where the tells come from — post-training, not pretraining, since
  a base model's prose is far more varied; mode collapse as something you can
  *measure in the text* rather than assert; why shape (variance, frame
  repetition, concreteness) is countable while meaning is not; and how register
  confounds all of it, which is what forces located findings over a score.
- **On the one signal that needs a model:** per-token surprisal is the strongest
  published family, and computing it is trivial — a forward pass and a
  log-softmax against a small local model. Start from the **two-model ratio**,
  perplexity under one model over cross-perplexity between two, rather than raw
  perplexity or single-model curvature; it was built against exactly the
  false-positive problem this lab exists to characterise. Expect it to do worse
  here than in its papers, because you will not have the model that produced the
  text and a paraphrase pass defeats the whole family. Check the current state of
  that subfield before committing to a method — it moves.
- **Cost note:** the deterministic core needs no model at all — every signal
  above is arithmetic, a closed word list or a regex. Generating the comparison
  corpus is a few hundred local completions. $0. Surprisal sits behind the `llm`
  extra and records which path ran, per rule 2, so the free signals stay
  measurable on their own.
- **Covers:** §4 What alignment does to style · §5 Task metrics vs. vibes ·
  §5 Calibrated confidence & honest uncertainty.
- **Built:** [`tools/ai-sniffer/`](./tools/ai-sniffer/), as a stdlib linter and a
  review-only prompt that is also a Claude Code agent. The corpus-overlap and
  surprisal parts above weren't built. The eval on 2026-09-15 used 165 hand labels on
  six drafts and 72 model runs. Scored before the labels were reviewed, Sonnet caught
  36 to 43 of 63 held-out habits, Haiku 7 to 10, and the linter alone 10. Design and
  results: [`docs/012`](docs/012_ai-sniffer.md).
- **Series, after the build** (planned 2026-09-15). Four posts, each resting on
  something measured:
  1. *The linter.* What `ai-sniffer check` counts, set against the open-source
     prose linters found on 2026-09-15 (slopless, SlopScore, wsc, sloplint, slop,
     slop-lint, vale-ai-tells) and the Antislop paper. The landscape goes here as
     background, not as a post of its own.
  2. *The reviewer.* The catalogue prompt, why it only quotes, and the eval:
     Haiku, Sonnet and local models (qwen2.5:7b, llama3.1:8b) on recall, false
     alarms, dollars and time per 1,000 words, chunked and unchunked.
  3. *Against the market.* Both tools and the open-source ones on one set of
     drafts. Before this runs, add drafts by other writers and labels from someone
     other than the original labeller, and report each tool on its own categories
     as well as on ours, so the comparison isn't scored on our home ground.
  0. *An overview post* linking the four, written last, so a reader arriving at any one
     of them can find the rest. Pavan's idea, 2026-09-16.
  4. *The revised tool.* Write down what changes and why from posts 2 and 3 before
     rerunning, then run once on fresh held-out drafts, so the improvement isn't
     tuned to the text it's measured on.
     Candidates to test, cheapest first:
     - *Quote checks in code.* Drop any finding whose quote isn't in the draft before
       it's reported; the scorer already locates quotes, so this is a few lines.
     - *A whole-draft pass.* After the section-by-section review, one more request
       over the whole draft only for habits that span sections (closers repeated
       across sections, triads used everywhere), which chunking can't see.
     - *An agentic review.* A tool loop where the model reads sections, runs
       `ai-sniffer check`, and re-checks its own findings against the file. Build it
       only if the eval shows a clear gain over the two cheaper steps: in the 72
       subagent runs, the tool loop re-sent the prompt and draft every turn and cost
       more than a single request would.
     - *Whether to keep our own linter rules at all.* vale-ai-tells caught 18 of 63
       held-out habits to `ai-sniffer check`'s 10, mostly with structural rules. Our
       linter is more precise per finding (13.5 catches per 100 findings against 8.4)
       and it feeds the reviewer, but wrapping Vale's rules, or adopting its structural
       ones, may beat growing our own. Decide this on the post 3 numbers.
     - *Running the agent headless.* Claude Code's print mode (`claude -p`) should
       run the ai-sniffer agent from a script on the Claude Code sign-in, with no API
       key; confirm the flags for choosing an agent before relying on it.

## G. Concept notes (markdown, not code)

Concepts where the honest deliverable is a written position plus a prompt you
can run to demonstrate it — no tool earns its keep. Each note follows the same
shape: **the mechanism**, **the trade-off**, **a prompt or experiment that shows
it**, and **the number from my own lab** (linked to the evidence card). Written
to be readable on their own, so they double as the explanatory half of anything
spun out for showcase.

- **N1 · `notes/llm-foundations.md`** — token, context window, embedding,
  temperature, hallucination, structured output. Prompt experiments: two
  sentences with no shared words that embed close together; the same prompt at
  temperature 0 and 1.2; a JSON schema that parses and is still wrong.
  *Covers §1 in prose; §50–52 supply the numbers.*
- **N2 · `notes/architecture-choices.md`** — the judgment calls, each written as
  "when I would *not*": prompt vs. RAG vs. fine-tune; pre-train vs. fine-tune vs.
  inference; encoder vs. decoder vs. encoder-decoder; rules vs. ML; agent vs.
  pipeline; batch vs. streaming vs. real-time; self-host vs. hosted.
  *Covers §3 decision triangle · §3 pre-train/fine-tune/inference · §6 agent vs.
  pipeline · §8 self-host vs. hosted · §9 rules vs. ML · §18 batch vs. streaming.*
- **N3 · `notes/frameworks.md`** — LangChain vs. LangGraph vs. crewAI vs.
  Pydantic AI (what a graph gives you that a chain doesn't, demonstrated in
  `agent-governor` #58); PyTorch vs. TensorFlow with a stated preference and a
  reason; **MCP framed as standardisation and reuse** — one connector, many
  agents, consistent schemas and auth — with honesty about its immaturity.
  *Covers §6 Frameworks · §6 Tool calling & MCP (the framing half) · §9 PyTorch
  vs. TensorFlow.*
- **N4 · `notes/rlhf-and-alignment.md`** — the three stages as separate
  artifacts, DPO vs. PPO, and what preference data physically looks like.
  Written to accompany `preference-forge` (#56), including the sentence about
  where my own work stops. *Covers §4 in prose.*
- **N5 · `notes/evaluation-discipline.md`** — the golden set (how it was built,
  how big, who adjudicated), faithfulness vs. context precision as different
  failures, thresholds derived from an observed distribution rather than picked.
  *Covers §5 Golden set · §5 Retrieval vs. generation metrics — the reasoning
  half; `eval-harness` (#9) runs them.*

---

## Suggested build order (for learning)

1. **#1 `docs-rag`** — get the whole RAG loop working once, locally and free.
2. **#11 `sqlite-mcp`** — get a clean MCP server working once.
3. **#23 `embeddings-cache`** + **#24 `model-router`** — the economy foundation.
4. **#12 `filesystem-rag-mcp`** — the "aha": RAG *as* an MCP tool.
5. **#9 `eval-harness`** — so every later tweak is measurable.
6. Anything from C — combined pipelines, now that the pieces exist.

### Concept-lab track (sections F–G)

Ordered so the **spine** — the concepts nearly every AI/data tool touches — comes
first, and each lab feeds the next.

1. **N1 + #50 `token-ledger` + #51 `decode-lab` + #52 `schema-guard`** — the
   foundations, with numbers. One weekend.
2. **#9 `eval-harness` + N5 + #57 `judge-lab`** — measurement before anything
   else, so every later change is provable.
3. **#53 `retrieval-bench`** on the corpus `docs-rag` (#1) and `ingest-ledger`
   (#49) already index — RAG depth without a new corpus.
4. **#54 `lora-lab` + #55 `synthdata-forge`** — fine-tuning, done with the
   general-benchmark check that most write-ups skip.
5. **#58 `agent-governor`** + N2/N3 — agentic control flow and the framework
   trade-offs.
6. **#59 `promptops` + #60 `model-pin` + #61 `llm-trace`** — LLMOps: the layer
   that decides whether any of the above survives contact with a second month.
7. **#56 `preference-forge` + N4** — alignment, the least commonly built of the
   spine concepts and the most interesting to read about afterwards.
8. **#88 `jailbreak-range` + #89 `fairness-audit`** + `pii-scanner` (#20) —
   responsible AI, treated as fairness and not only as security.
9. **#62 `serve-bench` + #63 `quant-check`** — serving, worth doing as soon as
   you have any GPU access at all.
10. **#66 `tabular-lab` + #64 `trainer-lab` + #65 `taxonomy-classifier`** —
    classical and deep ML, the model-development half.
11. **Adjacent domains, by what you actually work on** — data and platform first
    (#79, #80, #81, #82, #75, #76, #77, #78), then cloud and Kubernetes
    (#83–#87), then speech, vision, recommenders and graphs (#67–#74).
12. **#90 `evidence-index`** — run it continuously from step 2 onward; it tells
    you which concepts still have no measurement behind them, and renders what
    does.

### MCP track (section M)

The protocol changed shape in revision 2026-07-28, so the order below starts by
seeing what it is now rather than by building on what section B assumed.

1. **#198 `discover-probe`** — point it at the servers you already use. An hour,
   and the rest of the section stops being abstract.
2. **#11 `sqlite-mcp`**, rewritten — one clean server, current spec, against a
   system a model cannot otherwise reach.
3. **#203 `typed-result-lab` + #201 `tool-surface-budget`** — the two things that
   bite first, a result contract and a tool list that will not fit.
4. **#199 `run-as-task` + #200 `approval-gate`** — the async and human-gate pair;
   between them they replace everything #14 originally hand-rolled.
5. **#207 `warehouse-oauth`** — the one that decides whether any of this is
   deployable at work.
6. **Anything from M.2** — by then you can judge which of them you believe.

---

# Enterprise data engineering, where AI is essential

Sections H–J came in from the `stashed_ideas_review_later` branch. They are a
**different axis** from sections F–G above: those map the AI/data *concept* space,
one measured lab per concept; these map *enterprise data-engineering problems* —
legacy onboarding, lineage, contracts, migration — and ask where a language model
is genuinely load-bearing rather than decorative. Every entry carries an **Agentic
core** line saying why, which is the bar for inclusion.

They were renumbered on merge. The branch numbered them #49–123, which collided
with sections F–G; nothing outside the branch referenced them, so they became
#93–167 and their internal cross-references were rewritten to match. References to
#1–#48 were left alone, since those mean the same thing in both.

Three tiers, deliberately: **H** small and sharp (days), **I** bounded agents (one
enterprise job, real multi-step agency), **J** full systems (the "small tool" rule
waived on purpose).

Coverage for these is mapped in [`docs/008_data-engineering-coverage.md`](./docs/008_data-engineering-coverage.md) by the *problem* each solves; where an entry also exercises an AI concept, it is tagged in [`docs/005_concept-coverage.md`](./docs/005_concept-coverage.md) as well.

## H. Small, sharp AI tools — enterprise data engineering (#93–117)

Buildable in days, one job each — but unlike section E's plumbing, **the AI is the whole
point**: each solves a problem that regex/SQL/diffing fundamentally cannot, because it
requires semantic understanding. All target real enterprise data-engineering pain. Each
entry's **Agentic core** line states why an LLM is essential, not decorative.

### 93. `vendor-spec-reader` — file-spec PDF → parser config + DQ rules ⭐⭐ 🧠 ☁️
Feed it a 200-page vendor/reinsurer extract specification PDF; it produces a draft field
spec (names, positions, types, valid values), parser config, and starter DQ rules — each
traced back to the page/section it came from.
- **Agentic core:** reading prose specs ("field 12 is blank when policy status is lapsed")
  and turning them into machine config is pure language understanding; no parser can do it.
- **Learn:** RAG over long structured documents; schema-constrained JSON output; citation discipline.
- **Cost note:** parse/OCR locally; one API pass per spec, cached forever — specs rarely change.
- **Maps to:** legacy/COTS flat-file ingestion onboarding.

### 94. `copybook-decoder` — COBOL copybook → semantics + parser spec ⭐⭐ 🧠 💻
Parse a COBOL copybook (deterministic), then use sample data + field names like
`WS-POL-STS-CD` to produce plain-English field documentation, inferred enumerations, and
a ready-to-use parsing spec.
- **Agentic core:** copybook *syntax* is mechanical; field *meaning* (cryptic 6-char names,
  REDEFINES intent, sentinel conventions) requires semantic inference from names + values.
- **Learn:** combining deterministic parsing with LLM semantic enrichment; EBCDIC/packed-decimal handling.
- **Cost note:** parsing is code; LLM call per field group, cached by copybook hash.
- **Maps to:** mainframe/COTS ingestion.

### 95. `column-semantics-tagger` — decode cryptic legacy column names ⭐⭐ 🧠 💻
Point it at a legacy schema; for each column (`CD_STS_RSN`, `AMT_PRM_ANN`) it infers the
business meaning from the name, sample values, sibling columns, and any glossary — and
proposes a glossary mapping with confidence.
- **Agentic core:** abbreviation expansion + meaning inference from context is exactly what
  LLMs do and string matching doesn't.
- **Learn:** evidence-gathering prompts (values + context), calibrated confidence, human-review output.
- **Cost note:** local model handles most; batch columns per call.
- **Maps to:** catalog enrichment / auto-classification.

### 96. `fixed-width-inferrer` — recover the layout when no spec exists ⭐⭐ 🧠 💻
Given raw fixed-width files with no documentation (the spec retired with its author),
infer field boundaries, types, and likely meanings from character-class transitions plus
semantic plausibility — then emit a draft spec for review.
- **Agentic core:** statistics find *candidate* boundaries; deciding "positions 41–48 is a
  date and 49–57 looks like a premium amount" needs semantic judgment.
- **Learn:** hybrid statistical + LLM inference; expressing uncertainty honestly in output.
- **Cost note:** boundary detection is local stats; LLM only labels the candidate fields.
- **Maps to:** undocumented legacy ingestion.

### 97. `null-semantics-detective` — what do the sentinels mean? ⭐⭐ 🧠 💻
Scan columns across legacy sources for sentinel values (`9999-12-31`, `00000000`, `XX`,
`-1`, blank-vs-NULL) and infer what each one *means* (unknown? not-applicable? open-ended?)
from context — emitting cleansing rules per column.
- **Agentic core:** distinguishing "9999-12-31 means *still active*" from "means *unknown*"
  requires reasoning over column role and co-occurring fields, not frequency counts.
- **Learn:** profiling → hypothesis → LLM adjudication loop; encoding findings as cleansing config.
- **Cost note:** profiling local; LLM sees only value summaries, never raw rows.
- **Maps to:** cleansed-zone standardization rules.

### 98. `units-detective` — find mixed units, currencies, and scales ⭐⭐ 🧠 💻
Detect numeric columns that mix cents with dollars, percentages with basis points, or
thousands with raw amounts — using distribution analysis plus semantic context (column
name, sibling currency-code columns, source system).
- **Agentic core:** a bimodal distribution is a clue; concluding "rows from source B are in
  cents" requires reasoning across metadata, lineage, and domain convention.
- **Learn:** distribution fingerprinting + contextual reasoning; emitting normalization rules.
- **Cost note:** stats local; LLM adjudicates flagged columns only.
- **Maps to:** data-quality / conformance in the cleansed zone.

### 99. `code-set-mapper` — align source codes to canonical reference codes ⭐⭐ 🧠 💻
Given a source system's code set and your canonical reference set, propose value-level
mappings (`M/F/U` ↔ `MALE/FEMALE/UNKNOWN`, state codes, status codes) with confidence and
flags for unmappable or many-to-one cases.
- **Agentic core:** code descriptions are short, inconsistent text; matching `"Lapse-NonPay"`
  to `"LAPSED_NONPAYMENT"` vs `"TERMINATED"` is semantic, not lexical.
- **Learn:** semantic matching over short strings; handling asymmetric/partial mappings; review queues.
- **Cost note:** tiny inputs — a local model is plenty; cache per code-set version.
- **Maps to:** reference-data / cross-reference management.

### 100. `mapping-suggester` — draft source→target column mappings ⭐⭐ 🧠 ☁️
Given a profiled source schema and a target model, propose column-level mappings with
per-mapping confidence, rationale, and a draft transform expression — grounded by RAG over
the glossary and previously approved mappings.
- **Agentic core:** mapping is the single most labor-intensive task in data integration and
  is driven by meaning; prior-mapping retrieval + reasoning is what makes proposals good.
- **Learn:** RAG over structured mapping history; proposal/confidence/review-loop design.
- **Cost note:** one focused API call per entity; everything retrieved is small text.
- **Maps to:** mart-load mapping specs (the human bottleneck in feed onboarding).

### 101. `join-key-suggester` — find how two systems' tables join ⭐⭐ 🧠 💻
Given tables from different systems, find candidate join keys by combining value-overlap
analysis (deterministic) with semantic matching of names and formats — including composite
and transformed keys (`POL_NO` ↔ `policy_id` minus prefix).
- **Agentic core:** value overlap finds candidates; recognizing that one key is the other
  with a check digit stripped — and whether the join *makes business sense* — is reasoning.
- **Learn:** blocking/overlap algorithms + LLM adjudication; precision/recall tradeoffs.
- **Cost note:** overlap math local; LLM sees only candidate-pair summaries.
- **Maps to:** cross-system integration / MDM groundwork.

### 102. `transform-explainer` — legacy SQL → business-rule documentation ⭐⭐ 🧠 💻
Take a gnarly 800-line legacy transform (nested CASEs, magic numbers, layered CTEs) and
produce plain-English business-rule documentation with line citations: what it does, why
each branch exists, what looks suspicious.
- **Agentic core:** translating code intent into business language is comprehension, the
  core LLM competence; sqlglot can parse it but cannot say what it *means*.
- **Learn:** chunking large SQL semantically; citation-grounded explanation; suspicion flagging.
- **Cost note:** local model for most; API pass for the truly gnarly ones.
- **Maps to:** transform documentation / modernization prep.

### 103. `sql-intent-differ` — what changed in business terms? ⭐⭐ 🧠 💻
Diff two versions of a transform and report the *semantic* change ("late-payment grace
period extended from 30 to 45 days; lapsed policies now excluded from the premium sum"),
not the text delta.
- **Agentic core:** mapping an AST diff to business meaning is interpretation; a text diff
  of a refactored query is unreadable noise.
- **Learn:** AST-level diffing (sqlglot) feeding an LLM interpretation layer.
- **Cost note:** diff locally; one small LLM call per change set.
- **Maps to:** change review for transform PRs (pairs with config-as-code CI).

### 104. `metric-definition-extractor` — mine reports for metric definitions ⭐⭐ 🧠 💻
Crawl BI report SQL / dashboard definitions and extract each metric into a reviewable
dictionary entry: name, formula, filters, grain, source columns — the raw material for a
semantic layer.
- **Agentic core:** recognizing that three differently-written queries all compute
  "annualized premium in force" requires semantic normalization of logic.
- **Learn:** extraction over code corpora; canonicalizing equivalent expressions.
- **Cost note:** parse locally; LLM normalizes per metric; cache by query hash.
- **Maps to:** semantic-layer bootstrap / BI governance.

### 105. `glossary-linker` — connect glossary terms to physical columns ⭐⭐ 🧠 💻
Semantically link business-glossary terms to the actual tables/columns that embody them;
surface orphaned terms (defined but unmapped) and undocumented columns (mapped to nothing).
- **Agentic core:** "Annualized Premium" ↔ `ANN_PREM_AMT` across thousands of columns is
  semantic matching at scale; exact/fuzzy string match misses most of it.
- **Learn:** embedding + LLM-verification two-stage matching; stewardship review output.
- **Cost note:** embeddings local; LLM verifies top-k candidates only.
- **Maps to:** catalog/glossary stewardship.

### 106. `contract-from-docs` — extract data contracts from legacy artifacts ⭐⭐ 🧠 ☁️
Given the messy reality — interface Word docs, emails, spec fragments, a sample file —
draft a formal data contract (schema, nullability, keys, SLAs, semantics) with each clause
cited to its source artifact and gaps explicitly listed.
- **Agentic core:** synthesizing a normative contract from contradictory prose sources is
  reading-comprehension + reconciliation; there is no deterministic path.
- **Learn:** multi-document RAG with conflict detection; "what's missing" reporting.
- **Cost note:** one API synthesis pass per contract; sources are small.
- **Maps to:** data contracts / feed onboarding.

### 107. `naming-harmonizer` — propose convention-true names ⭐ 🧠 💻
For new tables/columns, propose names that match the enterprise's *actual* conventions —
learned from the existing catalog rather than a style doc — and flag existing names that
break pattern.
- **Agentic core:** conventions are implicit and inconsistent ("we abbreviate AMOUNT as AMT
  except in claims"); learning them from examples is induction, not lookup.
- **Learn:** few-shot convention induction; catalog-grounded suggestions.
- **Cost note:** local model; the catalog excerpt per call is tiny.
- **Maps to:** model governance / DDL review.

### 108. `doc-drift-detector` — where docs lie about reality ⭐⭐ 🧠 💻
Compare documentation (wiki, README, catalog descriptions) against actual schemas, configs,
and behavior; report semantic disagreements ("doc says daily, schedule says hourly"; "doc
lists 12 statuses, data has 17") and draft corrections.
- **Agentic core:** docs and reality are in different languages (prose vs DDL/config);
  comparing them is meaning-level alignment.
- **Learn:** grounding prose claims against structured facts; targeted patch generation.
- **Cost note:** fact extraction local; LLM compares claim-by-claim.
- **Maps to:** catalog/documentation governance.

### 109. `test-synthesizer` — generate fixtures for SQL transforms ⭐⭐ 🧠 💻
Read a SQL/SparkSQL transform and generate edge-case input fixtures + expected outputs:
boundary dates, null keys, late-arriving rows, duplicate business keys — feeding the
deterministic `sql-test-harness` (#42).
- **Agentic core:** identifying *which* edge cases threaten *this* logic (that COALESCE
  hides a join miss; that the SCD2 close-out breaks on same-day changes) is code reasoning.
- **Learn:** code-comprehension-driven test generation; verifying expected outputs by execution.
- **Cost note:** generation is one call per transform; execution/verification is local DuckDB.
- **Maps to:** transform-engine testing.

### 110. `edge-case-smith` — business-rule-aware test rows ⭐⭐ 🧠 💻
Generate small, schema-valid datasets that respect *inferred* business rules (issue date ≤
claim date; terminated policies have an end date) while deliberately probing edges — the
smart sibling of faker.
- **Agentic core:** faker fills types; inferring cross-column business rules from profile +
  names and then *violating them on purpose, one at a time* requires understanding.
- **Learn:** rule inference from profiles; constrained generation; rule-violation matrices.
- **Cost note:** local model generates rules + a seed set; expansion is code.
- **Maps to:** DQ-rule and pipeline testing.

### 111. `dag-reviewer` — semantic review of orchestration code ⭐⭐ 🧠 💻
Review Airflow DAG/operator code for the anti-patterns that pass linting but burn you at
3am: non-idempotent tasks, catchup/backfill traps, timezone bugs, implicit cross-DAG
dependencies, missing SLAs — with reasoned explanations.
- **Agentic core:** "this task isn't idempotent because the INSERT lacks a delete-first or
  merge" is program reasoning about *behavior*, beyond any linter rule.
- **Learn:** building a domain-specific review rubric; reasoning-with-citations output.
- **Cost note:** local model with a strong rubric prompt covers most; DAG files are small.
- **Maps to:** DAG-factory output review / orchestration quality.

### 112. `change-risk-scorer` — blast radius as a PR comment ⭐⭐ 🧠 🔌 ☁️
For each config/SQL PR, combine lineage (what's downstream), usage (who queries it), and
semantic analysis of the change itself into a risk score and a crisp review comment:
"touches the join feeding `dim_party`; 14 reports downstream; type narrowing may truncate."
- **Agentic core:** fusing lineage facts with *what the diff semantically does* into a risk
  judgment is multi-source reasoning; lineage alone over-warns on everything.
- **Learn:** composing deterministic lineage with LLM diff analysis; CI-bot integration via MCP.
- **Cost note:** lineage local; one LLM call per PR.
- **Maps to:** config-as-code CI gates / change management.

### 113. `freshness-inferrer` — is it late, or is it just Tuesday? ⭐⭐ 🧠 💻
Learn each feed's true arrival rhythm from history (weekday patterns, month-end surges,
holiday gaps, vendor quirks) and answer "should I worry yet?" with reasoning — instead of
naive fixed-deadline alerts that cry wolf.
- **Agentic core:** the *model* of arrival patterns is stats; explaining "late for a
  month-end Friday but the vendor always slips after quarter close" merges learned pattern
  with contextual reasoning.
- **Learn:** seasonality-aware baselining; alert-fatigue reduction; honest uncertainty.
- **Cost note:** stats local; LLM phrases the judgment only when asked.
- **Maps to:** SLA/freshness observability.

### 114. `failure-notifier` — the evidence-backed "your file broke" ticket ⭐ 🧠 💻
When a source extract breaks, draft the email/ticket to the source-system owner with
everything they need: what changed (sample rows, schema diff), which contract clause it
violates, business impact, and what you need from them — in their language, not yours.
- **Agentic core:** selecting the *right* evidence and writing for a non-data-team audience
  is communication work that templates do badly and engineers avoid doing.
- **Learn:** evidence selection + audience-aware generation; the human side of data contracts.
- **Cost note:** local model; inputs are diffs and samples already computed upstream.
- **Maps to:** source-system liaison / contract enforcement.

### 115. `runbook-writer` — turn resolved incidents into runbooks ⭐⭐ 🧠 💻
After an incident is resolved, distill the logs, timeline, and fix into a runbook entry
(symptom → diagnosis path → fix → prevention) — building the corpus that `etl-doctor` (#17)
and every future ops-RAG tool retrieves.
- **Agentic core:** compressing a noisy incident thread into a reusable diagnostic recipe
  is summarization-with-structure; nobody writes these by hand, which is why runbooks rot.
- **Learn:** knowledge distillation into retrievable form; closing the ops-RAG flywheel.
- **Cost note:** one call per incident; incidents are rare relative to queries against the corpus.
- **Maps to:** operational knowledge management.

### 116. `dialect-translator` — SQL dialect migration, verified ⭐⭐ 🧠 💻
Translate queries between dialects (Vertica ↔ SparkSQL ↔ Snowflake), then *prove* the
translation by running both against the same sample data and diffing results; iterate on
mismatches.
- **Agentic core:** transpilers (sqlglot) handle syntax but miss semantic gaps — null
  ordering, date arithmetic, division semantics; the verify-and-repair loop is agentic.
- **Learn:** the generate→execute→verify→repair loop; where transpilers actually fail.
- **Cost note:** sqlglot first, LLM only on failures; verification is local DuckDB/sample runs.
- **Maps to:** future-migration options (Appendix-A portability).

### 117. `sample-redactor` — shareable data samples, structure intact ⭐⭐ 🧠 💻
Produce redacted-but-realistic data samples for vendor/support debugging: PII replaced
with format-consistent fakes, internal codes preserved, cross-row consistency maintained
(same fake person throughout) so the bug still reproduces.
- **Agentic core:** deciding what's identifying *in context* (rare diagnosis + ZIP is PII;
  either alone isn't) and what must survive for the bug to reproduce requires judgment.
- **Learn:** consistency-preserving redaction; quasi-identifier awareness.
- **Cost note:** rules engine does the bulk; LLM adjudicates ambiguous columns once per schema.
- **Maps to:** PII protection / vendor escalation workflows.

---

## I. Ambitious, bounded agents (#118–142)

Still one clear job per tool — but the job is enterprise-grade and the tool is a genuine
**multi-step agent** 🤖: it plans, calls tools, gathers evidence, iterates, and produces a
defensible conclusion. These attack the problems that consume senior data engineers' and
architects' weeks.

### 118. `db-archaeologist` — excavate an undocumented legacy database ⭐⭐⭐ 🤖 🧠 ☁️
Point it at a legacy database nobody understands. It explores agentically — samples tables,
infers keys and relationships from value overlap, reads embedded code/views, names what it
finds — and emits an ERD, inferred FKs, entity descriptions, and a confidence-ranked report.
- **Agentic core:** exploration is iterative and hypothesis-driven (find a candidate key →
  test it → revise); the output is *meaning*, which only semantic inference provides.
- **Learn:** agent loops over a DB-introspection MCP server; hypothesis testing; honest confidence.
- **Cost note:** all queries local; LLM reasons over summaries, never full tables.
- **Maps to:** legacy source onboarding (the "no one knows what's in there" problem).

### 119. `proc-modernizer` — stored procedures → tested SparkSQL ⭐⭐⭐ 🤖 🧠 ☁️
Convert a 5000-line PL/SQL / T-SQL procedure into documented, tested SparkSQL/dbt models:
decompose into steps, translate each, generate fixtures, run both versions on sample data,
and iterate until outputs match — producing a divergence report for what won't translate.
- **Agentic core:** the translate→execute→compare→repair loop *is* the product; one-shot
  translation of real procedures is reliably wrong.
- **Learn:** large-code decomposition; equivalence testing as the agent's stop condition.
- **Cost note:** iteration on sample data locally; API model for translation passes only.
- **Maps to:** transform modernization (every enterprise has hundreds of these).

### 120. `jcl-flow-reconstructor` — mainframe job flows → Airflow DAGs ⭐⭐⭐ 🤖 🧠 ☁️
From JCL libraries and scheduler dumps (CA-7/Control-M), reconstruct the real dependency
graph — including implicit file-based dependencies (job A writes the dataset job B reads) —
and propose equivalent Airflow DAG definitions with the assumptions listed.
- **Agentic core:** dependencies are implicit in dataset names, PROC expansions, and
  conventions; recovering intent from them is inference, not parsing.
- **Learn:** lineage inference from artifacts; generating orchestration config from evidence.
- **Cost note:** parsing local; LLM resolves ambiguous links; one-time migration cost.
- **Maps to:** mainframe decommissioning / orchestration migration.

### 121. `report-reverse-engineer` — the model hiding in your reports ⭐⭐⭐ 🤖 🧠 ☁️
Crawl a legacy BI estate's report SQL; extract every metric and dimension actually in use;
cluster semantically equivalent ones; and emit the *implicit* semantic model — plus a
contradiction list ("'active policy count' has four different definitions").
- **Agentic core:** recognizing semantic equivalence across differently-written SQL and
  judging which definition is canonical requires meaning-level analysis at corpus scale.
- **Learn:** corpus-scale extraction + clustering; from descriptive findings to prescriptive model.
- **Cost note:** parse locally; LLM normalizes per-cluster, cached by query hash.
- **Maps to:** semantic-layer design / BI rationalization groundwork.

### 122. `model-designer` — propose the dimensional model ⭐⭐⭐ 🤖 🧠 ☁️
From profiled sources, the glossary, and stated business questions, propose a Kimball
design: fact tables with explicit grain, dimensions with SCD-type recommendations,
conformance opportunities — as reviewable DDL + mapping spec with rationale per decision.
- **Agentic core:** grain decisions and fact/dim classification encode business judgment
  ("is policy status an SCD2 dimension attribute or a status fact?"); this is design reasoning.
- **Learn:** encoding modeling heuristics into an agent; design-rationale documentation.
- **Cost note:** inputs are profiles + glossary (small); a few API calls per subject area.
- **Maps to:** mart design (Party/Policy model, Phase 1).

### 123. `match-merge-adjudicator` — MDM's gray zone, adjudicated ⭐⭐⭐ 🤖 🧠 ☁️
Deterministic blocking finds candidate party matches; the clear ones auto-resolve by rule;
the gray zone ("J. Smith, same DOB, address one digit off, different SSN format") goes to
an LLM adjudicator that weighs evidence, decides, and writes the rationale — feeding a
human review queue ordered by uncertainty.
- **Agentic core:** gray-zone matching is evidence-weighing under domain knowledge (nickname
  conventions, address typos, household vs individual) — exactly where rules plateau.
- **Learn:** hybrid deterministic/LLM pipelines; rationale capture for audit; review-queue design.
- **Cost note:** LLM sees only the gray zone (a few % of pairs); local model viable.
- **Maps to:** Party MDM match/merge.

### 124. `metric-consistency-auditor` — one KPI, four definitions ⭐⭐⭐ 🤖 🧠 ☁️
Find every place a KPI is computed (reports, dashboards, extracts, SQL), compare the
definitions semantically, quantify how much they disagree on real data, and propose the
canonical definition with a migration list for the deviants.
- **Agentic core:** establishing that two formulas *intend* the same metric but differ in
  edge handling — then arguing which is right — is semantic + domain reasoning.
- **Learn:** definition extraction → empirical divergence measurement → governed proposal.
- **Cost note:** extraction cached; divergence measured by running the SQL locally.
- **Maps to:** semantic-layer governance / "single source of truth" initiatives.

### 125. `recon-investigator` — chase the control-total mismatch ⭐⭐⭐ 🤖 🔌 💻
When source↔target totals disagree, investigate agentically: bisect by partition, then key
range, then transform step, comparing as it goes until the discrepancy is isolated to
specific rows and a specific step — then explain the mechanism (late rows? dup join? filter?).
- **Agentic core:** the bisection *strategy* adapts to what each probe reveals; a fixed
  script can't choose its next query based on findings.
- **Learn:** agentic search over data via MCP query tools; evidence-chain reporting.
- **Cost note:** all probes are local SQL; LLM plans the next probe and writes the conclusion.
- **Maps to:** reconciliation / audit (the hours-long manual chase, automated).

### 126. `rca-investigator` — root cause with an evidence chain ⭐⭐⭐ 🤖 🧠 🔌 ☁️
For a pipeline incident, pull every relevant signal — deploy history, config changes,
upstream data anomalies, infra events, log exceptions — test candidate hypotheses against
the timeline, and produce an RCA doc where every claim links to evidence.
- **Agentic core:** RCA is abductive reasoning across heterogeneous sources; correlation
  rules produce noise, and the synthesis into a coherent causal story is the hard part.
- **Learn:** multi-tool evidence gathering (MCP); hypothesis ranking; auditable conclusions.
- **Cost note:** signals fetched locally; API model for the synthesis pass.
- **Maps to:** AIOps / incident management.

### 127. `backfill-planner` — from incident window to ordered plan ⭐⭐⭐ 🤖 🔌 💻
Given "feed X loaded bad data from the 3rd to the 9th," walk lineage to find every affected
downstream asset, compute the correct reprocessing order, estimate cost/duration per step,
flag side effects (extracts already sent, SCD2 rows to repair) — and emit an executable,
reviewable plan.
- **Agentic core:** the plan depends on *kind* of corruption, each asset's load pattern, and
  consumer exposure — judgment over the lineage graph, not just traversal.
- **Learn:** lineage-driven planning; cost estimation; plan-as-reviewable-artifact.
- **Cost note:** graph work local; LLM reasons over the affected-asset summary.
- **Maps to:** incident remediation (today: a senior engineer's whiteboard afternoon).

### 128. `sla-forecaster` — call the breach before it happens ⭐⭐⭐ 🤖 💻 ☁️
Mid-run, predict tonight's SLA outcomes from current progress vs historical run profiles;
when a breach looms, recommend preemptive actions — scale the cluster, reorder the queue,
notify the consumer — each with expected impact.
- **Agentic core:** the forecast is stats; choosing the *intervention* requires weighing
  cost, downstream criticality, and contention across the whole night's schedule.
- **Learn:** run-profile modeling; decision support with explicit tradeoffs.
- **Cost note:** monitoring local; LLM invoked only when a breach is forecast.
- **Maps to:** SLA management / batch operations.

### 129. `spark-tuner` — performance fixes as validated PRs ⭐⭐⭐ 🤖 💻 ☁️
Read Spark event logs and query plans; diagnose skew, bad partitioning, missed broadcasts,
spill; propose fixes as config/code PRs; validate each by an A/B run on sample data before
the PR is opened — claims backed by measured numbers.
- **Agentic core:** plan-reading and diagnosis is expert pattern recognition over messy
  evidence; the propose→test→measure loop makes it trustworthy.
- **Learn:** Spark internals via event-log analysis; self-validating recommendation agents.
- **Cost note:** A/B runs on samples; LLM reasons over plan summaries.
- **Maps to:** compute FinOps / pipeline performance.

### 130. `quarantine-adjudicator` — triage the reject pile ⭐⭐⭐ 🤖 🧠 💻
Quarantined records accumulate and nobody looks. This agent clusters them by failure cause,
diagnoses each cluster (source bug? rule too strict? genuine bad data?), and proposes the
fix path — rule change, source ticket, or data patch — with rationale and projected impact.
- **Agentic core:** the rule-vs-source-vs-data judgment requires understanding what the rule
  *intends* versus what the data *means* — per cluster, with evidence.
- **Learn:** failure clustering; advisory remediation loops; keeping humans on the approve step.
- **Cost note:** clustering local; LLM diagnoses one representative per cluster.
- **Maps to:** DQ quarantine operations (the pile nobody triages).

### 131. `regression-bisector` — why did it get slow/wrong? ⭐⭐⭐ 🤖 💻
When a pipeline's runtime or output quietly degraded over weeks, bisect across the three
axes that change — code/config versions, data volume/shape, infra — re-running historical
versions against historical data snapshots until the cause is isolated.
- **Agentic core:** three interacting axes make naive git-bisect useless; the agent must
  design experiments that isolate one variable at a time and interpret ambiguous results.
- **Learn:** multi-axis bisection; reproducible historical re-runs (Iceberg time-travel + pinned config).
- **Cost note:** sample-sized re-runs; LLM plans the experiment sequence.
- **Maps to:** performance/result regression ops.

### 132. `env-drift-explainer` — why dev ≠ test ≠ prod ⭐⭐⭐ 🤖 💻
Same feed, different outputs per environment. The agent diffs everything that could matter
— config versions, engine versions, reference data, source snapshots, secrets/connection
targets — runs controlled comparisons, and names the culprit with evidence.
- **Agentic core:** the search space is large and heterogeneous; efficient narrowing
  requires reasoning about which differences *could* produce the observed divergence.
- **Learn:** systematic environment diffing; controlled-comparison methodology.
- **Cost note:** diffs and sample runs local; LLM directs the search.
- **Maps to:** environment management / release confidence.

### 133. `snapshot-debugger` — when did the data go wrong? ⭐⭐⭐ 🤖 💻
"This report was right last month." Bisect Iceberg snapshots through time-travel to find
the exact load where the number diverged, then drill into that load's inputs and transform
version to explain what happened.
- **Agentic core:** temporal bisection is mechanical; knowing *what to compare* at each
  snapshot (which aggregate, which slice) and interpreting the divergence is reasoning.
- **Learn:** time-travel as a debugging instrument; temporal root-cause workflows.
- **Cost note:** snapshot queries local; LLM interprets at each bisection step.
- **Maps to:** point-in-time history / audit investigations.

### 134. `drift-ripple-planner` — schema change, full consequence plan ⭐⭐⭐ 🤖 🔌 ☁️
When drift is detected (or a source announces a change), produce the complete ripple plan:
lake DDL evolution, affected transforms with proposed edits, contract version bumps,
consumer notifications, and the deployment order — as a reviewable change package.
- **Agentic core:** each downstream edit depends on how the change *semantically* interacts
  with that consumer's logic (a widened column is fine here, truncation risk there).
- **Learn:** lineage-guided multi-artifact change generation; change-package discipline.
- **Cost note:** lineage local; LLM reasons per affected artifact; bounded by blast radius.
- **Maps to:** schema-drift policy (the "what now?" after detection).

### 135. `dedup-refactorer` — kill the copy-paste transforms ⭐⭐⭐ 🤖 🧠 💻
Find semantically duplicated transform logic across hundreds of feeds (copy-pasted, then
diverged), determine whether divergences are intentional or drift, and propose shared
templates/macros with per-feed migration diffs.
- **Agentic core:** near-duplicate detection on *logic* (not text) plus the
  intentional-vs-accidental judgment call is semantic analysis rules can't make.
- **Learn:** semantic code clustering; safe consolidation proposals with proof-of-equivalence.
- **Cost note:** AST fingerprinting local; LLM compares cluster representatives.
- **Maps to:** item-store hygiene / shared-template governance.

### 136. `deprecation-planner` — retire the dead weight safely ⭐⭐⭐ 🤖 🔌 💻
Identify unused datasets/columns/extracts from query logs + lineage, distinguish truly-dead
from rarely-but-critically-used (the year-end statutory query!), and generate a staged
deprecation plan: consumer notices, grace periods, removal order, rollback points.
- **Agentic core:** "unused" is a judgment, not a count — seasonal access patterns and
  consumer criticality require interpretation; bad calls here cause outages.
- **Learn:** usage-evidence analysis; staged decommissioning playbooks.
- **Cost note:** log analysis local; LLM adjudicates the borderline assets.
- **Maps to:** storage FinOps / estate hygiene.

### 137. `number-change-detective` — why did this KPI move? ⭐⭐⭐ 🤖 🔌 ☁️
The CFO asks why persistency dropped 2 points. The agent traces the metric back through
the semantic layer, marts, loads, and source deltas; decomposes the change (mix shift?
data correction? late arrivals? logic change?); and answers with an evidence-based
attribution, not a shrug.
- **Agentic core:** change attribution is a multi-hypothesis investigation across lineage
  and time — the question every data team gets weekly and answers manually in days.
- **Learn:** metric decomposition; lineage-walking agents; executive-grade evidence summaries.
- **Cost note:** decomposition queries local; one API synthesis at the end.
- **Maps to:** consumption trust / "explain this number" service.

### 138. `access-explainer` — what can this role actually see? ⭐⭐⭐ 🤖 💻
Compose RBAC grants, ABAC tags, masking policies, and row filters into the *effective*
access per role, explained in plain language; flag toxic combinations, privilege creep,
and grants unused for months — as a continuous review aid.
- **Agentic core:** effective access emerges from interacting policy layers; explaining it
  to a certifier (and spotting "these two roles together re-identify SSNs") is reasoning.
- **Learn:** policy composition analysis; plain-language security explanation.
- **Cost note:** policy graph local; LLM writes the per-role narratives.
- **Maps to:** RBAC+ABAC governance / access certification.

### 139. `reident-tester` — attack your own masking ⭐⭐⭐ 🤖 💻
Adversarially attempt to re-identify masked/tokenized datasets: find quasi-identifier
combinations (ZIP + birth year + rare diagnosis), join against available reference data,
and report concrete leakage paths with affected-row counts and fixes.
- **Agentic core:** an attacker is creative; enumerating *plausible* attack joins and
  judging real-world identifiability requires adversarial reasoning, not k-anonymity math alone.
- **Learn:** privacy attack methodology (defensively); k-anonymity/l-diversity grounding.
- **Cost note:** join experiments local; LLM proposes attack hypotheses.
- **Maps to:** masking/tokenization assurance (test the control, not just deploy it).

### 140. `pia-drafter` — privacy impact assessment from evidence ⭐⭐⭐ 🤖 🧠 ☁️
For a new feed, draft the PIA from what the platform *already knows*: classifications
(what PII enters), lineage (where it flows), access policies (who sees it), retention
(how long it lives) — every assertion cited to platform metadata, gaps flagged for humans.
- **Agentic core:** a PIA is regulatory prose synthesized from technical facts; the agent
  turns metadata into compliance language while distinguishing known from unknown.
- **Learn:** metadata-grounded document generation; compliance-document structure.
- **Cost note:** facts are queries; one API drafting pass per assessment.
- **Maps to:** privacy compliance (GDPR/CCPA) / onboarding gates.

### 141. `audit-evidence-compiler` — the audit binder, assembled ⭐⭐⭐ 🤖 🔌 ☁️
Given an auditor's request list ("evidence of change approval for all prod config changes
in Q3"), interpret each request, gather the artifacts — run logs, PR approvals, lineage,
DQ results — and assemble cited evidence packets per control, noting anything missing.
- **Agentic core:** mapping auditor language to platform artifacts and judging evidence
  *sufficiency* is interpretation; the gathering itself spans many systems.
- **Learn:** requirement→artifact mapping; evidence-chain packaging for SOX/NAIC.
- **Cost note:** retrieval local; LLM interprets requests and writes packet summaries.
- **Maps to:** SOX/NAIC audit support (weeks of analyst time per audit).

### 142. `lineage-narrator` — the story of one number ⭐⭐⭐ 🤖 🧠 ☁️
For a single figure on a statutory report, produce the auditor-grade narrative of its
derivation: source systems → loads → transforms (business rules in plain language) →
aggregation — every step cited to lineage events, run logs, and code versions.
- **Agentic core:** raw lineage is an unreadable graph; the narrative — *what happened to
  the data and why, in order, in English* — is translation only an LLM does.
- **Learn:** graph-to-narrative generation; citation discipline at every claim.
- **Cost note:** lineage walk local; one drafting call per number; cache by report version.
- **Maps to:** statutory/regulatory reporting defense.

---

## J. Full systems (#143–167) 🏛️

Multi-component platforms — the "small tool" rule is **intentionally waived**. Each is a
product an enterprise would fund: several agents, a workflow, state, and a governance
surface. Many compose tools from sections E–G as building blocks. All follow the EDP
guardrails: deterministic core, AI overlay; advisory + severity-gated autonomy; audited;
local-LLM capable.

### 143. `etl-migration-factory` — retire the legacy ETL estate 🏛️ 🤖 ☁️
An agent fleet that converts an Informatica/DataStage estate into framework config + SQL:
inventory and parse every job, translate mappings per job, generate equivalence tests, run
old vs new on production samples, and track the whole migration on a dashboard — humans
approve per-job cutover.
- **Agentic core:** thousands of jobs × translate→test→repair loops; the equivalence
  harness is what makes machine translation trustworthy at estate scale.
- **Learn:** fleet orchestration; proprietary-format parsing; migration-as-pipeline.
- **Maps to:** ETL modernization programs (multi-year consulting engagements, compressed).

### 144. `mainframe-assimilator` — copybooks to governed feeds, end to end 🏛️ 🤖 🧠 ☁️
The legacy-onboarding pipeline as one system: copybook decoding (#94), EBCDIC parsing,
JCL flow reconstruction (#120), semantic field documentation (#95), draft contracts, and
generated feed packages — from tape-era artifacts to running, governed pipelines with a
human review gate at each stage.
- **Agentic core:** every stage needs semantic inference; the system chains them with
  review gates so confidence compounds instead of error.
- **Learn:** staged agent pipelines with human gates; the full legacy-to-modern path.
- **Maps to:** mainframe/COTS source onboarding (the EDP's hardest source class).

### 145. `platform-migration-copilot` — switch engines without faith 🏛️ 🤖 ☁️
Estate-scale warehouse migration (e.g., Vertica → Snowflake, per Appendix A): translate
all DDL/SQL (#116 at scale), plan the migration order from lineage, run dual-write
reconciliation during transition, and report readiness per workload — with rollback points.
- **Agentic core:** translation + verification + sequencing across thousands of objects,
  where each failure needs diagnosis and repair, not a stack trace.
- **Learn:** dual-run reconciliation architecture; migration sequencing from lineage.
- **Maps to:** the documented future-migration options — made executable.

### 146. `ma-data-assimilator` — absorb an acquired company's data 🏛️ 🤖 🧠 ☁️
For M&A: archaeology on the acquired estate (#118), entity matching to your canonical model
(#123 across companies), code-set alignment (#99), gap analysis, and generated integration
pipelines — with a workbench where integration architects review and approve mappings.
- **Agentic core:** two enterprises' models never align by name; the mapping is a thousand
  semantic judgments that today take an integration team a year.
- **Learn:** cross-estate semantic alignment; human-in-the-loop mapping workbenches.
- **Maps to:** M&A integration (insurance consolidates constantly).

### 147. `bi-rationalizer` — collapse 4,000 reports into 400 🏛️ 🤖 🧠 ☁️
Crawl the whole BI estate; extract metrics and audiences per report (#121); cluster
duplicates and near-duplicates; map everything to canonical semantic-layer metrics; and
produce a consolidation plan with usage evidence, owner sign-offs, and a migration tracker.
- **Agentic core:** "are these two reports the same?" is a semantic question times a
  million pairs; usage stats alone can't see that two differently-named reports answer
  the same business question.
- **Learn:** corpus-scale semantic clustering; consolidation governance workflow.
- **Maps to:** BI governance / semantic-layer adoption.

### 148. `estate-knowledge-graph` — the substrate every agent queries 🏛️ 🤖 🧠 🔌 💻
A continuously-updated knowledge graph of the data estate — datasets, columns, owners,
glossary terms, lineage, usage, incidents, contracts — built by extraction agents, queried
via graph-RAG, and exposed over MCP so every other agent (and human) asks it questions:
"who owns what feeds the claims dashboard, and what's changed there this month?"
- **Agentic core:** construction requires semantic extraction (linking terms↔columns,
  docs↔assets); consumption is graph-RAG — both are LLM-native problems.
- **Learn:** knowledge-graph construction agents; graph-RAG; MCP as the universal interface.
- **Maps to:** catalog/lineage/stewardship — unified into one queryable brain.

### 149. `semantic-layer-factory` — generate and *maintain* the semantic layer 🏛️ 🤖 🧠 ☁️
Bootstrap the governed semantic layer from marts + query logs + extracted report metrics
(#104/#121), then keep it alive: detect new query patterns that deserve promotion, flag
metrics drifting from their definition, propose updates as governed PRs.
- **Agentic core:** the bootstrap is semantic synthesis; the *maintenance* loop (watching
  usage, proposing evolution) is what no static tool does and why semantic layers rot.
- **Learn:** living-artifact maintenance agents; governed-PR proposal loops.
- **Maps to:** the EDP's semantic/curated consumption layer.

### 150. `data-product-foundry` — datasets in, data products out 🏛️ 🤖 🧠 ☁️
Turn a curated dataset into a full data product through an agent-assisted assembly line:
draft the contract from observed schema/usage (#106), generate documentation (#102/#43),
define SLAs from measured freshness (#113), create sample queries, register in the catalog
— with product-owner approval gates.
- **Agentic core:** productization is 80% writing (contracts, docs, examples) grounded in
  technical facts — synthesis work that's why teams never finish it manually.
- **Learn:** data-product/mesh operating model; assembly-line agent design.
- **Maps to:** data-product packaging on the consumption layer.

### 151. `contract-lifecycle-system` — contracts that actually live 🏛️ 🤖 🔌 ☁️
Data contracts as a managed lifecycle: drafted from evidence (#106), versioned in git,
enforced as pipeline gates, breach-detected at runtime — and when producers need to change,
an agent analyzes consumer impact, drafts the renegotiation proposal, and routes it to
affected parties.
- **Agentic core:** the negotiation loop — impact analysis, proposal drafting, consumer
  communication — is where contracts die today; it's language + reasoning work.
- **Learn:** contract enforcement architecture; producer/consumer negotiation workflows.
- **Maps to:** data contracts across the EDP's inbound and outbound boundaries.

### 152. `onboarding-concierge` — feed onboarding as a conversation 🏛️ 🤖 🧠 🔌 ☁️
Self-service onboarding, fully realized: the agent interviews the source SME in plain
language, inspects sample data as they talk, drafts the complete feed package (config,
contract, mappings #100, DQ rules #35), runs a sandbox load, walks the SME through the
results, and iterates until green — then submits the package for governed approval.
- **Agentic core:** the interview adapts to answers; drafts are grounded in live data
  inspection; the iterate-to-green loop is agency end to end.
- **Learn:** conversational agents driving real tool pipelines; sandbox-validated generation.
- **Maps to:** R8 self-service onboarding — the flagship EDP AI feature.

### 153. `self-healing-pipelines` — detect → diagnose → fix, governed 🏛️ 🤖 🔌 ☁️
The EDP's runtime-AI vision as a product: failures trigger diagnosis (#126), remediation
proposals are matched against runbooks (#115), low-severity known fixes auto-apply,
everything else becomes a PR for human approval — every action audited, autonomy
severity-gated per the platform's governance model.
- **Agentic core:** diagnosis and fix synthesis are reasoning; the governance wrapper
  (severity gates, audit, advisory-first) is what makes it deployable in an insurer.
- **Learn:** governed-autonomy architecture; the advisory→trusted-automation maturity path.
- **Maps to:** AIOps self-healing (P18/P19 made concrete).

### 154. `incident-war-room` — coordinated incident response 🏛️ 🤖 🔌 ☁️
On a major data incident, a coordinated agent team activates: RCA (#126), blast-radius
assessment via lineage, backfill planning (#127), stakeholder comms drafted per audience
(exec vs engineer vs consumer), and a postmortem draft with timeline — humans command,
agents staff the room.
- **Agentic core:** parallel specialist agents sharing evidence under time pressure;
  audience-specific communication; synthesis into one coherent response.
- **Learn:** multi-agent coordination with shared state; incident-management integration.
- **Maps to:** major-incident management for the data platform.

### 155. `quality-sentinel-network` — DQ that learns the business rhythm 🏛️ 🤖 🧠 💻
Beyond declared rules: per-feed learned expectations (seasonality-aware volumes,
distributions, relationship invariants), anomaly detection that knows month-end from
Monday, and incidents that arrive *triaged* — suspected cause, affected downstream
consumers, suggested response — feeding the steward queue (#163).
- **Agentic core:** learned expectations are stats; the triage (cause hypothesis, consumer
  impact, response) is the reasoning layer that turns alerts into action.
- **Learn:** expectation learning at fleet scale; alert→triaged-incident pipelines.
- **Maps to:** intelligent DQ across all feeds (R12 feature 4, productized).

### 156. `pipeline-portfolio-optimizer` — the whole night, optimized 🏛️ 🤖 💻
Treat the entire batch estate as one optimization problem: dependencies, SLAs, cluster
capacity, cost. Continuously propose schedule/resource changes — reorder queues, shift
non-critical loads, right-size clusters — with predicted SLA/cost impact, applied via
governed config PRs.
- **Agentic core:** the optimizer is OR/heuristics; explaining tradeoffs, handling
  exceptions ("month-end overrides this"), and negotiating SLA changes with owners is the
  agentic layer that makes it adoptable.
- **Learn:** global scheduling optimization; recommendation-with-explanation systems.
- **Maps to:** batch SLA management + compute FinOps, estate-wide.

### 157. `autonomous-finops-governor` — cost control with judgment 🏛️ 🤖 💻 ☁️
Continuous cost watch across EMR/EKS/Vertica/S3: attribute spend per feed/domain (#41 as a
component), detect anomalies and waste (unused assets #136, oversized clusters #129), propose
gated optimizations — storage tiering, schedule shifts, retention enforcement — each with
projected savings and risk, executed only through approval workflows.
- **Agentic core:** attribution is joins; deciding *what's safe to act on* and packaging
  optimizations with risk assessments is judgment over usage semantics.
- **Learn:** FinOps decision loops; savings-vs-risk framing; governed cost actions.
- **Maps to:** platform FinOps (R29), closed-loop.

### 158. `source-watchtower` — see upstream breakage coming 🏛️ 🤖 🧠 ☁️
Monitor everything upstream: vendor release notes and spec updates (RAG over their docs),
sandbox-environment extracts diffed against production expectations, announced COTS
upgrades mapped to your affected feeds — and open preemptive change tickets *before* the
breaking file lands in production.
- **Agentic core:** reading vendor prose and inferring "release 24.2's claim-status rework
  will break our fixed-width parser on field 31" is comprehension + impact reasoning.
- **Learn:** external-signal ingestion; predictive change management.
- **Maps to:** schema-drift policy, moved left of the failure.

### 159. `dsar-orchestrator` — subject rights, fulfilled and proven 🏛️ 🤖 🔌 ☁️
For a data-subject access/erasure request: resolve the person across systems (MDM + fuzzy
identity), find *all* their data via catalog + lineage + content scanning (including the
copies in extracts and archives), generate the access package or erasure plan, respect
legal holds, execute gated, and produce the compliance evidence trail.
- **Agentic core:** "find everything about this person" across a messy estate is iterative
  search + identity reasoning; missing one copy is a regulatory finding.
- **Learn:** estate-wide entity search; erasure vs legal-hold reconciliation; provable completeness.
- **Maps to:** GDPR/CCPA DSAR (today: weeks of manual hunting per request).

### 160. `reg-change-compliance-system` — regulations in, policy changes out 🏛️ 🤖 🧠 ☁️
Watch regulatory sources (NAIC bulletins, state regs, privacy law updates); RAG over new
requirements; map each to affected datasets, policies, and controls via the knowledge graph
(#148); draft the policy-config changes (the EDP's pluggable compliance rules); and track
adoption through to attestation.
- **Agentic core:** reading regulatory text and translating it to "these 14 datasets need
  retention extended to 10 years" is legal-to-technical translation — pure language work.
- **Learn:** regulatory-text RAG; requirement→control mapping; compliance traceability.
- **Maps to:** the extensible compliance policy model (R23), kept current automatically.

### 161. `retention-lifecycle-enforcer` — retention as a managed loop 🏛️ 🤖 💻
Map retention policies to physical assets across lake/warehouse/archives; continuously
detect violations (data past retention, orphaned copies) and conflicts (purge due but legal
hold active); plan gated purges with dependency awareness (don't break the SCD2 chain);
execute with evidence for auditors.
- **Agentic core:** policy-to-physical mapping is semantic (which assets *contain* claims
  data?); conflict resolution and safe purge sequencing require reasoning over lineage.
- **Learn:** policy-driven lifecycle automation; destructive-action governance done right.
- **Maps to:** retention + legal hold (R24), operationalized.

### 162. `access-governance-suite` — continuous access assurance 🏛️ 🤖 💻
Quarterly access reviews replaced by a continuous loop: effective-access explanation (#138)
per role/user, plain-language certification packets for managers, unused-grant cleanup
proposals, toxic-combination and privilege-creep detection, re-identification testing
(#139) on a schedule — findings routed as governed change requests.
- **Agentic core:** certifiers approve what they understand; translating policy math into
  reviewable language at org scale is the unlock that makes reviews real.
- **Learn:** continuous-compliance architecture; certification UX for non-engineers.
- **Maps to:** RBAC+ABAC governance (R22), as a running system.

### 163. `steward-command-center` — one queue, triaged with judgment 🏛️ 🤖 🧠 🔌 ☁️
Every platform event — DQ failures, drift alerts, SLA breaches, quarantine growth, access
findings, contract breaches — lands in one place, where agents deduplicate, correlate
("these five alerts are one upstream incident"), prioritize by business impact, attach
context and a drafted response, and route to the right steward. The inbox that makes
governance staffing scale.
- **Agentic core:** correlation and prioritization across heterogeneous events requires
  understanding what each event *means* for the business — judgment, not routing rules.
- **Learn:** event correlation agents; human-workload-shaped AI (triage, not takeover).
- **Maps to:** stewardship operations across all governance capabilities.

### 164. `analysis-copilot` — business questions, answered with proof 🏛️ 🤖 🧠 🔌 ☁️
Beyond text-to-SQL: decompose a vague business question into an analysis plan; choose
certified datasets (warning about freshness/known issues); generate and *verify* queries
(dry-run, sanity-check magnitudes against history, cross-check via a second path); answer
with caveats and full provenance — over the governed semantic layer, masked data only.
- **Agentic core:** plan→query→verify→caveat is a reasoning loop; naive text-to-SQL
  confidently returns wrong numbers, which is why enterprises don't trust it.
- **Learn:** verified-generation patterns; trust architecture for AI analytics.
- **Maps to:** chat-with-data (R12 feature 5), made trustworthy.

### 165. `data-request-desk` — the ad-hoc request firehose, managed 🏛️ 🤖 🔌 ☁️
Intake every "can you pull me…" request (Slack/email/portal); the agent clarifies intent
conversationally, checks whether a certified asset already answers it (deflecting
duplicates), self-serves governed extracts where policy allows (#164 + outbound engine),
and routes the rest to engineers with requirements already drafted — SLA-tracked.
- **Agentic core:** intent clarification, dedup against existing assets, and
  policy-checked self-service are each language + judgment problems.
- **Learn:** request-intake agents; deflection economics; governed self-service boundaries.
- **Maps to:** the ad-hoc workload that consumes every data team's sprint capacity.

### 166. `synthetic-environment-fabricator` — production-faithful test worlds 🏛️ 🤖 💻
Generate complete PII-free test environments: cross-table referential integrity, realistic
distributions, inferred business rules preserved (#110 at estate scale), temporal
consistency (policy lifecycles that make sense), targeted edge-case injection — refreshed
on demand so dev/test stop using masked production copies.
- **Agentic core:** business-rule inference and cross-entity consistency (a synthetic
  person's policy, claims, and payments must tell one coherent story) require semantic
  modeling of the domain from data.
- **Learn:** constraint-preserving synthesis at scale; test-data-as-a-service.
- **Maps to:** dev/test environments without PII exposure (R21 risk, eliminated).

### 167. `as-built-documentarian` — documentation that can't go stale 🏛️ 🤖 🧠 💻
Continuously regenerate the platform's as-built documentation from its own metadata: data
flows from lineage, model docs from schemas + glossary (#43), operational behavior from
run history, architecture diagrams (Mermaid) from infrastructure config — with a change
feed ("what's different since last quarter") and drift flags where docs were hand-edited.
- **Agentic core:** turning metadata into readable, audience-appropriate documentation is
  generation; *keeping* it true is the continuous loop nobody staffs.
- **Learn:** docs-from-truth architecture; the self-describing platform.
- **Maps to:** architecture/operations documentation, audit-ready by construction.

---

## Suggested build order (for learning)

1. **#1 `docs-rag`** — get the whole RAG loop working once, locally and free.
2. **#11 `sqlite-mcp`** — get a clean MCP server working once.
3. **#23 `embeddings-cache`** + **#24 `model-router`** — the economy foundation.
4. **#12 `filesystem-rag-mcp`** — the "aha": RAG *as* an MCP tool.
5. **#9 `eval-harness`** — so every later tweak is measurable.
6. Anything from C — combined pipelines, now that the pieces exist.

---

## K. Metadata-plane agents — no access to the data itself (#168–183) 🔒

Everything here works from **schema, infrastructure, logs and code**. None of it
reads a row.

That constraint is not an academic exercise; it is what makes these deployable.
A tool that never touches data needs no data-residency review, no PII assessment,
no production access, and can run in CI against a repository and a catalogue
export. Roughly a third of the ideas in sections H–J read row values and cannot
make that claim — `#97 null-semantics-detective` has to see the sentinels,
`#101 join-key-suggester` has to measure value overlap. These cannot and do not.

It is also where the work is genuinely *semantic* rather than statistical. With no
values to profile, everything has to be inferred from naming, structure, config and
intent — which is exactly what a language model is for, and exactly what a linter
is not. Every entry below states what a deterministic tool would already catch, so
the AI's share of the job is explicit rather than assumed.

**The four gaps `docs/008` named as bare are the first four entries.**

### 168. `temporal-linter` — the time bugs that survive every code review ⭐⭐ 🧠 💻 🔒
Reads DDL and transform SQL and flags temporal reasoning that is wrong in ways a
type checker cannot see: an effective-dated table joined as though it were current;
`BETWEEN valid_from AND valid_to` where `valid_to` is exclusive, so boundary rows
count twice; a naive `TIMESTAMP` compared against one with a zone; `+ INTERVAL '24
hours'` where the business means "next day" and a DST boundary makes those
different; calendar-day arithmetic on a column whose name says business days.
- **Agentic core:** the type system is satisfied by all of these. Deciding that
  `party_eff_dt` makes a table effective-dated, and that a join ignoring it is
  therefore a bug, is reading *intent* from naming and shape — no schema states it.
- **Deterministic part:** parsing SQL, matching types, spotting `BETWEEN` on two
  date columns. That is the easy half and it is already free.
- **Learn:** temporal data modelling; where LLM judgement beats static analysis and
  where it does not; writing findings a reviewer will act on rather than mute.
- **Cost note:** local model over DDL and SQL; no data, no cluster. $0.
- **Maps to:** §B in `docs/008` — the bare row. Bitemporal modelling, SCD2 correctness.

### 169. `survivorship-auditor` — which source wins, and who decided ⭐⭐ 🧠 💻 🔒
Golden-record rules are never written down; they live inside `COALESCE` chains,
priority `CASE` expressions and `ROW_NUMBER() OVER (ORDER BY source_rank)`. This
reads the merge code and states, per attribute, which source wins under which
conditions — then flags attributes with **no** rule (silently last-writer-wins),
rules that contradict between two pipelines writing the same target, and rules that
changed in a commit whose message says something else.
- **Agentic core:** recovering a *policy* from an implementation. The rule is
  distributed across joins, window functions and null handling, and stating it in
  business terms is the whole deliverable.
- **Deterministic part:** finding the merge statements and their target columns.
- **Learn:** reading intent out of code; contradiction detection across sources;
  presenting a policy for sign-off rather than a diff.
- **Cost note:** local; SQL only. $0.
- **Maps to:** §C in `docs/008` — the bare row. MDM governance, golden-record policy.

### 170. `collation-conformance` — where two engines will disagree about `'a' = 'A'` ⭐⭐ 🧠 💻 🔒
Reads DDL collations, database and session settings, connector and Spark configs,
and the comparisons in transform code. Reports where a join or `DISTINCT` crosses a
collation boundary, where a sort will order differently on the target engine than
the source, where an implicit charset conversion happens, and where `UPPER()` is
doing the work a case-insensitive collation was supposed to do.
- **Agentic core:** the facts are spread across DDL, platform config and code, in
  different languages, and none of them individually is wrong. The finding is the
  *combination* — which is inference, not lookup.
- **Deterministic part:** extracting declared collations and charsets.
- **Learn:** why a migration changes row counts with no data change; config as a
  correctness surface.
- **Cost note:** local; config and DDL. $0.
- **Maps to:** §B in `docs/008` — the bare row. Migration assurance, cross-engine parity.

### 171. `stream-topology-reviewer` — the state that grows forever ⭐⭐⭐ 🧠 💻 🔒
Reads streaming job code plus its topic, checkpoint and cluster config, and reports
the failures that only appear in week three: a stream-stream join with no watermark
(unbounded state), allowed-lateness longer than the watermark so late data is
dropped after being promised, a parallelism or key change that silently
invalidates checkpointed state on the next deploy, and an ordering assumption the
partitioning does not actually guarantee.
- **Agentic core:** these are *interactions* between code and config, and the
  symptom appears far from the cause. Judging that a particular join will retain
  state indefinitely means understanding what the job is trying to do.
- **Deterministic part:** extracting watermark and window settings.
- **Learn:** streaming state, watermarks and lateness; why streaming failures are
  slow; reading logs for rebalance storms.
- **Cost note:** local; code, config and log summaries. $0.
- **Maps to:** §I in `docs/008` — the bare row. Streaming operations.

### 172. `dependency-truth-checker` — what the DAG says versus what the SQL reads ⭐⭐⭐ 🧠 💻 🔒
Extracts the tables each task actually reads and writes, compares that against the
dependencies the orchestrator declares, and reports both directions: a task reading
a table nobody upstream produces in this run (a race waiting for a slow day), and a
declared dependency nothing justifies (a schedule slower than it needs to be).
- **Agentic core:** the read set is only partly static — dynamic SQL, templated
  table names, config indirection and `EXEC` of generated strings all need a model
  to resolve, and to say honestly when it cannot.
- **Deterministic part:** static SQL parsing, which covers the easy majority.
- **Learn:** lineage from code rather than from a catalogue; expressing "I could not
  resolve this" as a first-class output.
- **Cost note:** local; repository only. $0.
- **Maps to:** §H in `docs/008`. Orchestration correctness, the 3am race condition.

### 173. `idempotency-auditor` — can this safely be re-run? ⭐⭐ 🧠 💻 🔒
Reads a transform and answers the question every on-call engineer asks at 3am.
Flags `INSERT` where `MERGE` was meant, `CURRENT_TIMESTAMP` baked into a stored
value, sequence or identity generation on a retryable path, appends with no natural
key, and external side effects that will fire twice.
- **Agentic core:** idempotency is a property of *intent* — an append is correct for
  an event log and a bug for a dimension. Only reading what the table is for
  separates the two.
- **Deterministic part:** finding non-deterministic function calls.
- **Learn:** exactly-once as a design property rather than a framework promise.
- **Cost note:** local; SQL only. $0.
- **Maps to:** §H/§I in `docs/008`. Backfill safety, incident recovery.

### 174. `partition-advisor` — partition for the queries you actually run ⭐⭐ 🧠 💻 🔒
Reads the **query log** — predicates, join keys, group-bys, and their frequency —
plus current DDL, and recommends partitioning and clustering with the evidence
attached: which queries improve, which get worse, what the skew risk is. Never sees
a value; only which columns are filtered on and how often.
- **Agentic core:** query logs are enormous and repetitive. Clustering thousands of
  statements into a handful of *access patterns*, and naming them, is the work; a
  histogram of column frequencies is not a recommendation.
- **Deterministic part:** parsing predicates out of the log.
- **Learn:** physical design driven by evidence rather than by folklore; stating a
  recommendation with its losers as well as its winners.
- **Cost note:** local; log summaries. $0.
- **Maps to:** §J in `docs/008`. Performance and cost, without a data scan.

### 175. `migration-hazard-reviewer` — will this DDL change take the table offline? ⭐⭐ 🧠 💻 🔒
Given a schema change and the engine it runs on, predicts what actually happens:
a full table rewrite, a blocking lock, a default backfill, an index rebuild — and
separately, which downstream readers break, from code rather than from a catalogue.
Proposes the safe multi-step version where one exists.
- **Agentic core:** the hazard depends on engine, version, table size class and the
  exact change; it is documented in prose across a dozen release notes and encoded
  nowhere machine-readable.
- **Deterministic part:** diffing the DDL.
- **Learn:** online schema change; expand-migrate-contract as a pattern.
- **Cost note:** local; DDL and repository. $0.
- **Maps to:** §H in `docs/008`. Change safety, release confidence.

### 176. `config-archaeologist` — what does this 4,000-line YAML actually do? ⭐⭐ 🧠 💻 🔒
Reads a metadata-driven pipeline's configuration estate and explains it in prose:
what each feed is configured to do, which settings are defaults nobody chose, which
are copy-paste from a feed that no longer exists, which contradict each other, and
which are load-bearing in a way their name does not suggest.
- **Agentic core:** config-as-code estates outgrow anyone's memory. A schema
  validator says the YAML is *valid*; only reading it says the retry policy on this
  feed makes its SLA unachievable.
- **Deterministic part:** schema validation and duplicate detection (`#29
  config-linter` ⚠️ already does this deterministically — this is the layer above).
- **Learn:** summarising a large structured estate without hallucinating specifics;
  citing the file and line for every claim.
- **Cost note:** local; config only. $0.
- **Maps to:** §F in `docs/008`. Config-as-code governance.

### 177. `retry-storm-diagnoser` — one failure or four hundred? ⭐⭐ 🧠 💻 🔒
Reads run logs and separates the originating failure from its amplification: the
retry policy that turned one timeout into a thundering herd, the downstream job
that failed only because its upstream was still retrying, the alert that fired
forty times for one cause. Outputs the causal chain and names the amplifier.
- **Agentic core:** log correlation across systems with no shared trace ID, where
  the same event is described differently by each component. Pattern-matching on
  ERROR lines produces the noise, not the diagnosis.
- **Deterministic part:** parsing timestamps and grouping by job.
- **Learn:** incident forensics from logs; distinguishing cause from consequence.
- **Cost note:** local model over log summaries. $0.
- **Maps to:** §I in `docs/008`. Incident response, alert fatigue.

### 178. `grant-impact-explainer` — what breaks if I revoke this? ⭐⭐ 🧠 💻 🔒
The inverse of `#138 access-explainer`. Given a proposed permission change, reads
IaC, catalogue grants, service-account usage in code, and query logs, and reports
which pipelines, dashboards and service accounts would stop working — separating
"used last week" from "granted in 2019 and never exercised".
- **Agentic core:** entitlement graphs are indirect — role inherits role, view
  masks table, service account is shared between two systems. Resolving the chain
  and judging what is genuinely in use requires reading code and usage together.
- **Deterministic part:** expanding the grant graph.
- **Learn:** least privilege as an achievable state; access certification that does
  not break production.
- **Cost note:** local; IaC, catalogue and log summaries. $0.
- **Maps to:** §K in `docs/008`. Access governance, least-privilege campaigns.

### 179. `schema-historian` — how did this table get this shape? ⭐⭐ 🧠 💻 🔒
Reads the migration history and version-control record for one table and tells its
story: which columns arrived together and therefore belong to one feature, which
are vestigial from a project that was cancelled, which were widened in an incident,
and which have never been referenced by any code since they were added.
- **Agentic core:** a migration log is a sequence of mechanical diffs; the story is
  the *why*, recovered by correlating diffs with commit messages, tickets and the
  code that arrived alongside them.
- **Deterministic part:** replaying the migrations.
- **Learn:** archaeology as a deliverable; separating evidence from inference in a
  narrative output.
- **Cost note:** local; VCS and migration files. $0.
- **Maps to:** §F in `docs/008`. Catalogue enrichment, deprecation groundwork.

### 180. `cost-jump-explainer` — the bill went up on Tuesday ⭐⭐ 🧠 💻 🔒
Correlates a cost or runtime jump against what changed: commits merged, config
edits, cluster resizes, schedule changes, and upstream volume shifts visible in row
*counts* — never row contents. Ranks candidate causes with the evidence for each,
and says plainly when the change is upstream and not yours.
- **Agentic core:** correlation is easy and usually wrong. Judging that a config
  change three days earlier explains a jump today, because of how the schedule
  interacts with it, is reasoning over heterogeneous evidence.
- **Deterministic part:** the time series and the change list.
- **Learn:** attribution under confounding; refusing to name a cause when the
  evidence is thin. Complements `#41 finops-attributor`, which apportions steady
  state rather than explaining a delta.
- **Cost note:** local; billing exports and logs. $0.
- **Maps to:** §J in `docs/008`. FinOps, capacity management.

### 181. `notebook-promotion-reviewer` — is this ready to be a pipeline? ⭐⭐ 🧠 💻 🔒
Reads a notebook and reports what stands between it and production: hidden state
from out-of-order execution, hardcoded paths and credentials, absent error
handling, cells that silently depend on a variable defined three cells up and
deleted since, and non-deterministic ordering that will differ on a cluster.
- **Agentic core:** notebooks encode execution order in a way the file does not.
  Judging that a cell depends on state no longer created means reading the notebook
  as a *narrative*, not as a program.
- **Deterministic part:** import and variable analysis.
- **Learn:** the notebook-to-production gap, stated as a checklist a reviewer can use.
- **Cost note:** local. $0.
- **Maps to:** §H in `docs/008`. Promotion gates, analyst-to-engineer handoff.

### 182. `orphan-asset-finder` — what is nothing reading? ⭐⭐ 🧠 💻 🔒
Combines lineage from code, query logs and job schedules to find tables, columns
and jobs nothing consumes — then, crucially, separates *dead* from *dormant*: the
quarterly regulatory extract that runs four times a year is not orphaned, and the
table read only by a BI tool whose queries never reach the log needs saying so
rather than deleting.
- **Agentic core:** the honest answer is about *unknowns*. Naming the blind spots —
  BI tools, ad-hoc access, external consumers — and refusing to recommend deletion
  where visibility is incomplete is the judgement that makes it usable. Feeds
  `#136 deprecation-planner`, which plans the retirement this finds.
- **Deterministic part:** the reachability graph.
- **Learn:** reasoning about coverage gaps; recommending inaction under uncertainty.
- **Cost note:** local; logs and code. $0.
- **Maps to:** §J in `docs/008`. Estate hygiene, storage cost.

### 183. `schema-contract-differ` — will this change break a consumer? ⭐⭐ 🧠 💻 🔒
Sits in CI on the *producing* side. Given a schema change and the declared contract,
classifies it as compatible, forward-compatible, or breaking — and where breaking,
names which consumer and which line of their code, reading the downstream
repositories rather than guessing from the catalogue.
- **Agentic core:** compatibility is semantic, not structural. Widening a column is
  safe unless a consumer parses it positionally; adding a nullable column is safe
  unless someone does `SELECT *` into a fixed-width extract. Only reading consumer
  code decides.
- **Deterministic part:** the structural diff and the contract check
  (`#19 data-contract-linter` does this).
- **Learn:** compatibility classes; shifting a break left of the merge.
- **Cost note:** local; multi-repository. $0.
- **Maps to:** §G in `docs/008`. Contracts, change management.

---

## L. Agents that must see the data (#184–197) 🤖

Section K deliberately gave up data access. This section takes it back, and pays
for it with a stricter bar: **the loop is the solution.** Every entry here needs
hypothesis → query → revise, where what to look at next is not knowable until you
have looked. A single prompt, however good, does not do these; nor does a script,
however clever.

That bar excludes most of what AI is usually pointed at. Classification,
summarisation, extraction and translation are all one-shot — useful, and not this.
So each entry carries **Why nothing simpler works**, naming the deterministic or
single-prompt approach and saying exactly where it fails. If that line is weak, the
idea does not belong here.

**On data access.** These read real values, so they run where the data already is —
an on-prem or private-cloud model, which is now ordinary. The trade is deliberate:
section K buys deployability by staying in the metadata plane; section L buys
answers that are only visible in the data, and accepts the deployment cost.

**The three gaps `docs/008` named after section K are the first three entries.**

### 184. `boundary-prober` — the window where two systems are never consistent ⭐⭐⭐ 🤖 🧠 ☁️
Two systems are supposed to agree. They do, except in a window nobody has ever
characterised. This probes both empirically — samples the same logical entity on
both sides across the day, finds the disagreements, forms a hypothesis about the
cause (a settlement cut-off, a late-arriving correction, a filter one side applies
and the other does not, a different business definition of "active"), tests it with
targeted queries, and returns the *envelope*: between these hours, for this class
of record, expect divergence of this shape.
- **Why nothing simpler works:** a reconciliation job needs you to already know the
  key, the rule and the expected window. This produces those. `#125
  recon-investigator` chases a mismatch you have already noticed; this finds the
  ones you have normalised as "just how it is".
- **Agentic core:** each probe result changes which entity class is worth sampling
  next. The search space is every combination of time, entity type and status, and
  pruning it is judgement.
- **Learn:** designing an empirical probe; distinguishing a timing artefact from a
  logic difference; writing an envelope a downstream team can code against.
- **Cost note:** local model, targeted queries, no full scans. Cheap.
- **Maps to:** §I in `docs/008` — the bare row. Cross-system consistency.

### 185. `sla-portfolio-auditor` — what you are owed versus what you are getting ⭐⭐⭐ 🤖 🧠 ☁️
Reads vendor contracts, extracts each delivery obligation in prose, then goes and
*finds the evidence* — which requires discovering, per vendor, where "delivered"
is even recorded, because the contract says "by 06:00 business days" and the
platform records an arrival timestamp on a landing table with a different name in
every feed. Measures compliance, quantifies the shortfall, and assembles the
credit or escalation position with citations to both the clause and the data.
- **Why nothing simpler works:** the contract→evidence mapping is different for
  every vendor and exists nowhere. Extraction alone gives you obligations you
  cannot measure; a dashboard alone gives you numbers with no entitlement attached.
- **Agentic core:** for each clause, decide what would constitute evidence, go
  looking, discover the evidence is not where you expected, and adapt.
- **Learn:** obligation → measurement mapping; building a commercial argument from
  operational data; citing both sides.
- **Cost note:** contracts parsed once; measurement is cheap and recurring.
- **Maps to:** §G in `docs/008` — the bare row. Vendor management, service credits.

### 186. `version-coexistence-manager` — run two schema versions until the last consumer moves ⭐⭐⭐ 🤖 🔌 ☁️
`#183` catches a breaking change in CI. This operates the weeks that follow:
maintains both shapes, **proves equivalence on live data** rather than asserting it,
watches query logs to see who is still on the old version, nudges the stragglers
with the specific line they need to change, and closes the window only when the
evidence says nobody is left.
- **Why nothing simpler works:** expand-migrate-contract is a *campaign*, not a
  deployment. The contract step is the one everyone skips, because knowing it is
  safe means knowing who is still reading — which changes daily.
- **Agentic core:** a long-running stateful process with a per-consumer decision at
  each step, and a stopping condition that is itself a judgement.
- **Learn:** online schema evolution as an operated process; equivalence testing on
  production data; when to stop waiting.
- **Cost note:** ongoing but light; log summaries and periodic comparison queries.
- **Maps to:** §H in `docs/008` — the bare row. Change management.

### 187. `grain-detective` — one row per *what*, actually? ⭐⭐⭐ 🤖 🧠 💻
The documentation says one row per policy. Is it? This probes candidate keys, finds
where uniqueness breaks, and then does the part that matters: investigates whether
the duplicates are genuine data errors, a versioning dimension nobody documented, a
join fan-out introduced upstream, or evidence that the grain is actually *policy ×
coverage* and every downstream count has been wrong for years.
- **Why nothing simpler works:** finding duplicate keys is a `GROUP BY HAVING`. The
  answer is worthless without the *diagnosis*, and the diagnosis requires forming a
  theory about what the extra rows represent and testing it against other columns.
- **Agentic core:** hypothesis generation over candidate grains, each tested by a
  query whose result determines the next hypothesis.
- **Learn:** grain as the most consequential and least documented modelling fact;
  investigating rather than reporting.
- **Cost note:** local model, aggregate queries only. Cheap.
- **Maps to:** §B/§E in `docs/008`. Modelling correctness, metric trust.

### 188. `attrition-tracer` — where did the rows go? ⭐⭐⭐ 🤖 🧠 💻
`#49 ingest-ledger` proves what arrived. This covers everything after: walks a
pipeline stage by stage, and at each one decides whether the change in row count
and key set is *expected* — an inner join that was meant to filter, a dedup that was
meant to collapse — or silent loss: a join on a column with trailing whitespace, a
filter written for a source that has since changed, a cast that quietly nulls.
Handles the inverse too, where a fan-out multiplies rows nobody asked for.
- **Why nothing simpler works:** row counts changing between stages is *normal*.
  Only understanding what each stage is for separates the intended reduction from
  the accidental one, and that intent lives in the code and the naming, not the
  numbers.
- **Agentic core:** at each stage, decide whether to accept the delta or investigate
  it, and if investigating, decide what to compare.
- **Learn:** conservation as a pipeline property; the difference between a filter
  and a bug being intent alone.
- **Cost note:** counts and key-set comparisons; no full data movement.
- **Maps to:** §I/§G in `docs/008`. Silent data loss, mid-pipeline integrity.

### 189. `rule-reality-auditor` — the code says it enforces this; the data disagrees ⭐⭐⭐ 🤖 🧠 💻
Reads transform and application code for the rules it *claims* to enforce — a
status transition that should be impossible, a total that should always reconcile,
a field that should never be null when another is set — then goes and checks
whether the data obeys. Where it does not, investigates when it started and what
changed, and reports whether the code is wrong, the rule moved, or the enforcement
has a hole.
- **Why nothing simpler works:** `#35 dq-rule-suggester` infers rules *from data*,
  so it can only find rules the data already follows — it is blind to the exact case
  that matters. This starts from the claim and tests it, which is the opposite
  direction and finds the opposite class of bug.
- **Agentic core:** extracting an enforceable claim from code, translating it into a
  query, and — when it fails — investigating whether the violation is a bug, a
  legitimate exception, or a rule that changed.
- **Learn:** cross-artifact contradiction hunting; testing the claim rather than
  mining the data.
- **Cost note:** local; code plus aggregate queries.
- **Maps to:** §G/§H in `docs/008`. Quality, control assurance.

### 190. `equivalence-adjudicator` — the rewrite gives different answers; does it matter? ⭐⭐⭐ 🤖 🧠 ☁️
Migrations produce diffs. The diff is the easy part. This takes the rows that
differ and adjudicates each class: float accumulation order, a `NULL` sort position
that changed with the engine, a genuine logic bug, or a difference that is
*correct* because the old version was wrong. Returns a verdict per class with the
evidence, so a human signs off on a page rather than a spreadsheet.
- **Why nothing simpler works:** a row-level diff on a migration of any size returns
  thousands of differences and no judgement. Tolerances are the usual answer and are
  how real bugs get waved through.
- **Agentic core:** cluster the differences by suspected cause, form a hypothesis
  for each cluster, test it with a targeted query, and rank by whether a human needs
  to look.
- **Learn:** equivalence as a graded verdict rather than a boolean; making a
  sign-off tractable.
- **Cost note:** the comparison is the expensive part; adjudication is cheap.
- **Maps to:** §D in `docs/008`. Migration assurance. Feeds `#143`, `#145`.

### 191. `hidden-coupling-finder` — these two pipelines are not as independent as you think ⭐⭐⭐ 🤖 🧠 💻
Finds coupling nobody declared: two jobs writing the same staging table under
different names, one silently depending on another's ordering, a shared temp
schema, a config value that means different things to two teams, or two pipelines
that only work because one always finishes first. Confirms each candidate by
looking at what the data actually shows across runs.
- **Why nothing simpler works:** declared lineage shows declared dependencies. The
  dangerous couplings are the undeclared ones, which appear only as a correlation
  between runs — and correlation over a scheduler is mostly coincidence, so
  something has to sort real coupling from shared timing.
- **Agentic core:** generate candidate couplings from code and logs, then design a
  check that would distinguish coupling from coincidence, and run it.
- **Learn:** implicit contracts between teams; distinguishing correlation from
  dependency.
- **Cost note:** logs, code, and light data checks.
- **Maps to:** §H in `docs/008`. Change safety, blast radius.

### 192. `fitness-assessor` — is this dataset fit for *that* purpose? ⭐⭐⭐ 🤖 🧠 ☁️
Someone wants to use a dataset for something. This investigates whether it will
hold: is the grain right for the question, is the population complete for the
segment they care about, is history deep enough, is the freshness compatible with
the decision, are the known quality issues in a column they depend on. Returns a
fitness verdict with the specific caveats, not a quality score.
- **Why nothing simpler works:** a quality score is purpose-free and therefore
  meaningless — the same dataset is excellent for a trend and useless for a
  reconciliation. Fitness only exists relative to a stated use, and checking it
  requires exploring the data along the dimensions that use depends on.
- **Agentic core:** translate a stated purpose into the checks that would falsify
  it, run them, and follow up where a check comes back marginal.
- **Learn:** fitness-for-purpose as the only meaningful quality question;
  falsification as a method.
- **Cost note:** aggregate queries; scales with the number of checks, not data size.
- **Maps to:** §G/§E in `docs/008`. Consumption trust, data-product certification.

### 193. `purpose-limitation-auditor` — is this data being used for what people consented to? ⭐⭐⭐ 🤖 🧠 ☁️
Reads the privacy notice and consent model, then traces actual usage — queries,
extracts, downstream joins, model training sets — and flags where data collected
for one purpose is serving another. Distinguishes a genuine breach from a
compatible secondary use, which is a legal judgement the regulation frames in prose
and nothing encodes.
- **Why nothing simpler works:** classification tells you a column is PII. Nothing
  in the catalogue knows *why* it was collected, and purpose limitation is
  precisely the mismatch between that and how it is used. The answer needs the
  notice, the lineage and the usage together.
- **Agentic core:** for each use found, retrieve the governing purpose, judge
  compatibility, and investigate further where the join makes the purpose ambiguous.
- **Learn:** GDPR purpose limitation as an engineering problem; defensible
  judgement with a citation trail.
- **Cost note:** private-cloud model, given the material. Query logs and lineage.
- **Maps to:** §K in `docs/008`. Privacy compliance beyond PII detection.

### 194. `population-drift-investigator` — the numbers are fine; the population changed ⭐⭐⭐ 🤖 🧠 💻
`#137` asks why a number moved. This asks the harder question underneath: did the
*population* change, and was that us or the world? Distinguishes a genuine business
shift from an upstream filter change, a source that quietly stopped sending a
segment, a join that started dropping a category, and a backfill that reshaped
history. Investigates by segment until it can name the boundary.
- **Why nothing simpler works:** aggregate monitoring cannot see this — totals stay
  plausible while their composition changes underneath. Finding it means slicing by
  dimensions nobody thought to alert on, chosen by what the previous slice showed.
- **Agentic core:** iterative segmentation, where each split is chosen by the result
  of the last.
- **Learn:** composition versus magnitude; monitoring's blind spot.
- **Cost note:** aggregate queries over segments.
- **Maps to:** §E/§G in `docs/008`. Metric trust, silent upstream change.

### 195. `silent-truncation-hunter` — where the pipeline quietly loses precision ⭐⭐ 🤖 🧠 💻
Hunts the losses that never raise an error: a string truncated to a column width, a
decimal rounded by an implicit cast, a timestamp losing sub-second precision at a
boundary, a numeric overflowing to null, a unicode character mangled by an encoding
hop. Reads the code for where a conversion happens, then checks the data at that
point for evidence that it bit.
- **Why nothing simpler works:** type analysis says a conversion is *possible*;
  only the data says whether any value is close enough to the edge for it to
  matter. Reporting every possible narrowing conversion is noise nobody reads.
- **Agentic core:** find candidate conversions in code, design the query that would
  prove harm, run it, and follow the value back to its source when it does.
- **Learn:** lossy conversions as a silent class; evidence over possibility.
- **Cost note:** aggregate queries at candidate points.
- **Maps to:** §B/§I in `docs/008`. Silent corruption, migration parity.

### 196. `reference-data-decay-monitor` — the code set stopped matching reality ⭐⭐ 🤖 🧠 💻
Mappings rot quietly. New codes appear that map to nothing and fall to a default;
mapped codes go extinct without anyone retiring them; a mapping that was right in
2019 now sends a category to the wrong bucket. Watches the join between incoming
codes and the reference set, and for each anomaly investigates whether it is a
genuine new code, a source-side typo, a systematic upstream change, or a mapping
that has quietly gone wrong.
- **Why nothing simpler works:** an unmapped-code alert fires constantly and is
  always muted, because most of them are noise. The value is entirely in triage,
  which needs context about the source and the code's shape.
- **Agentic core:** classify each anomaly by investigating its context, and escalate
  only what a human should decide.
- **Learn:** reference data as a living dependency; alert designs people do not mute.
- **Cost note:** small recurring queries.
- **Maps to:** §B/§G in `docs/008`. Reference data, cleansed-zone conformance.

### 197. `query-intent-consolidator` — four hundred queries, eleven actual questions ⭐⭐⭐ 🤖 🧠 ☁️
Reads the analyst query log and clusters by *intent* rather than by SQL similarity —
two queries that look nothing alike can be the same question, and two near-identical
ones can differ in a `WHERE` clause that changes everything. Names the real
questions, then checks against the data whether a proposed dataset would actually
serve each one, and proposes the handful of marts or products that would retire
most of the log.
- **Why nothing simpler works:** SQL similarity clusters by syntax and gets this
  wrong in both directions. And a proposed mart is only useful if the data supports
  it at the required grain and freshness, which has to be checked, not assumed.
- **Agentic core:** cluster by intent, propose a serving design, test the design
  against the data, and revise when it does not hold.
- **Learn:** demand analysis from logs; designing for the questions rather than the
  queries.
- **Cost note:** log summaries plus verification queries.
- **Maps to:** §E in `docs/008`. Semantic layer, data-product design, `#165` demand.

---

## M. MCP servers for data platforms (#198–#217) 🔌

Sections K and L are about *what an agent reasons over*. This one is about **the
protocol it reasons through**, and it exists because that protocol changed shape.

Revision **2026-07-28** is not an increment on the MCP that section B describes.
The `initialize` handshake is gone and MCP is stateless — every request carries
its own protocol version and capabilities, and a server announces itself through
`server/discover`. Protocol-level sessions are gone; a server that needs state
across calls mints an explicit handle and passes it as an ordinary tool argument.
Server-initiated requests are gone, replaced by **Multi Round-Trip Requests**: the
server returns an `InputRequiredResult` and the client *retries* the original
request carrying `inputResponses`. Long-running work moved into the **Tasks**
extension. `resources/subscribe` became one opt-in `subscriptions/listen` stream.
List results now carry `ttlMs` and `cacheScope`. Roots, Sampling and Logging are
deprecated, and so is the transport half the ecosystem was built on.

**The bar.** The protocol is the subject, not a delivery detail. Every entry names
the mechanism it exercises in a `Protocol surface` line, and has to be materially
worse as a library call or a CLI — if wrapping the same logic in `argparse` loses
nothing, it does not belong here. The second filter comes from **F2** in
[`docs/FINDINGS.md`](docs/FINDINGS.md): a retrieval server earns little next to a
client that can already read files, so the server must reach a system the model
cannot. Every entry below points at a warehouse, an orchestrator, a catalog, a
lakehouse table or a ledger.

**Two tiers.** **M.1** are protocol labs, and section F's rule applies to them —
each ends by writing down a number that did not exist before it ran, and files an
evidence card so #90 `evidence-index` can read it back. **M.2** are servers that
do not exist in the industry today; each states what the current state of the art
does instead, and if that line is weak the idea does not belong.

### M.1 · Protocol labs (#198–#207)

### 198. `discover-probe` — what does this server actually support? ✅ ⭐⭐ 🔌 💻
Points at any MCP server and reports what it really is: which protocol revisions
it accepts, which capabilities and extensions it advertises through
`server/discover`, whether it still expects a handshake, and which deprecated
features it depends on. Then it checks the advertisement against behaviour — a
server claiming an extension it does not implement is common, and nothing in the
protocol catches it.
- **Protocol surface:** `server/discover`; statelessness and per-request
  `io.modelcontextprotocol/protocolVersion` and `clientCapabilities` in `_meta`;
  `UnsupportedProtocolVersionError`; the deprecated-features registry.
- **Learn:** why the handshake was removed and what statelessness costs per call;
  how to negotiate a version without a connection to hang it on; reading a spec
  revision as a diff rather than as a document.
- **Measures:** round-trips and bytes per tool call, handshake versus stateless,
  at one call and at fifty. Plus the fraction of the servers you probe whose
  advertisement does not match what they do.
- **Cost note:** no model needed; it is a client. $0.
- **Maps to:** §6 in `docs/005` — *Tool calling & MCP*.
- **Built:** [`tools/discover-probe/`](./tools/discover-probe/). On 2026-09-14,
  across twelve servers, the SDK's major version decided the era every time: v1
  meant the old handshake only, v2 meant both. None of the six official reference
  servers had migrated; Upstash, MotherDuck and AWS Labs had, Microsoft's
  Playwright and dbt Labs had not. The two v1 SDKs also refuse an unknown method
  with different codes, `-32601` from TypeScript and `-32602` from Python. Design
  record [`docs/011`](docs/011_discover-probe.md), which records two claims this
  entry first made and got wrong; evidence
  [`evidence/discover-probe.jsonl`](evidence/discover-probe.jsonl).

### 199. `run-as-task` — the backfill that outlives the connection ⭐⭐⭐ 🔌 💻
An eight-hour backfill cannot be a blocking tool call, and the workaround
everybody writes — a `run_job` tool plus a `job_status` tool the model has to
remember to poll — is now the protocol's job. This wraps a real Spark or dbt run
as a durable task: `CreateTaskResult` with a `taskId` minted before the response
is sent, `tasks/get` polling at the server's suggested interval, `tasks/cancel`
that the server is free to ignore, and a TTL that says how long the answer
survives.
- **Protocol surface:** the `io.modelcontextprotocol/tasks` extension —
  `CreateTaskResult`, `tasks/get`, `tasks/cancel`, `ttlMs`, `pollIntervalMs`,
  `notifications/tasks`; extension negotiation through `server/discover`.
- **Learn:** durable handles versus open connections; cooperative cancellation and
  why it cannot be guaranteed; designing a status message an agent can act on
  rather than one that only reads well.
- **Measures:** whether the run survives killing and restarting the client
  mid-flight; polling overhead in requests and tokens against
  `notifications/tasks`; the wall-clock point where a blocking call starts losing.
- **Cost note:** local orchestrator, local model. The job costs what the job costs.
- **Maps to:** §6 in `docs/005` — *Async tool execution & long-running work*.

### 200. `approval-gate` — the tool call that stops and asks ⭐⭐⭐ 🔌 💻
A partition overwrite or a DDL apply should not happen because a model was
confident. This is the pause, done properly: the server returns an
`InputRequiredResult` describing exactly what is about to be rewritten, the client
puts it in front of a human, and the *original* request is retried carrying the
answer. The interesting part is `requestState` — the server has no session to
remember what it was doing, so whatever it needs to resume has to survive the
round trip in the open.
- **Protocol surface:** Multi Round-Trip Requests — `InputRequiredResult`,
  `inputRequests`, `inputResponses`, `requestState`, `resultType`; elicitation
  under MRTR; the `input_required` task status for gates inside a long run.
- **Learn:** human-in-the-loop as a protocol feature rather than a prompt
  convention; why a stateless server must externalise its own resume state; what
  a confirmation has to say to be worth reading.
- **Measures:** how far into a multi-step destructive plan the model gets before
  the first gate fires; whether `requestState` survives a client restart between
  the interim result and the retry.
- **Cost note:** local model; a scratch warehouse. $0.
- **Maps to:** §6 in `docs/005` — *Typed tool contracts & server-initiated input*.

### 201. `tool-surface-budget` — four thousand tables will not fit ⭐⭐⭐ 🔌 💻
Every catalog-backed MCP server hits the same wall. One generic `query` tool tells
the model nothing about what exists; one tool per table is unusable long before a
real warehouse runs out of tables. This measures the whole curve — token cost per
turn, prompt-cache hit rate, and tool-selection accuracy as the surface grows —
and tests the three things the protocol offers against it: deterministic
`tools/list` ordering so caches hit, `ttlMs` and `cacheScope` so clients stop
re-listing, and the `completion` utility so a name can be found rather than
listed.
- **Protocol surface:** `tools/list` size and deterministic ordering;
  `CacheableResult` with `ttlMs` and `cacheScope`; pagination; the `completion`
  utility for argument autocomplete.
- **Learn:** what a tool list actually costs in a prompt; why ordering is a
  caching decision; when to stop listing and start completing.
- **Measures:** tokens per turn and prompt-cache hit rate at 10, 100, 1,000 and
  4,000 tools; the size at which the model starts selecting the wrong table, and
  how much of that ordering and completion buy back.
- **Cost note:** the token bill is the experiment. Budget a few dollars, and reuse
  #50 `token-ledger` to account for it.
- **Maps to:** §6 in `docs/005` — *Tool-surface scale, caching & change
  notification*.

### 202. `listen-lab` — telling the agent the partition landed ⭐⭐ 🔌 💻
An agent that asks "is it there yet?" every thirty seconds is paying for the
question. This exposes table freshness as a subscription instead: the client opts
in to specific notification types over one long-lived stream, the server tags what
it sends with a subscription id, and the arrival of a partition is pushed rather
than discovered. It also has to handle what the revision took away —
`resources/subscribe` is gone, per-resource subscription is now an opt-in class,
and the stream can simply break.
- **Protocol surface:** `subscriptions/listen`; the opt-in types
  (`resourcesListChanged`, `resourceSubscriptions`, `toolsListChanged`,
  `promptsListChanged`); `io.modelcontextprotocol/subscriptionId`; the separation
  of request-scoped notifications from the listen stream.
- **Learn:** push versus poll and where the crossover actually sits; why
  request-scoped progress and connection-scoped change notification are different
  channels; designing for a stream that has no resumability.
- **Measures:** notification latency against the polling interval it replaces, and
  the request count each costs over a night; the recovery time after a killed
  stream, and how many events fall in the hole.
- **Cost note:** no model in the loop. $0.
- **Maps to:** §6 in `docs/005` — *Tool-surface scale, caching & change
  notification*.

### 203. `typed-result-lab` — a verdict, not a paragraph ⭐⭐ 🔌 💻
A data-quality tool that returns prose forces the next step to parse English. One
that declares an `outputSchema` and returns `structuredContent` gives the caller a
record — and gives the model a shape to reason about before it calls. This builds
the same DQ check both ways over the same runs and counts what the difference is
worth, including the parts of JSON Schema 2020-12 the revision now permits and
most servers get wrong: `$ref` resolution, and composition keywords with no bound.
- **Protocol surface:** `outputSchema` and `structuredContent`; JSON Schema
  2020-12 keywords, `$ref` resolution requirements, composition-keyword resource
  bounds.
- **Boundary with #52:** `schema-guard` is about constraining what the *model*
  emits. This is about what the *tool* promises to return, which is a contract the
  server owes its callers whether or not a model is involved.
- **Learn:** result contracts as an interface; where schema strictness helps a
  model and where it just fails the call; validating twice, at the server and at
  the client.
- **Measures:** parse-failure rate and downstream re-prompts, prose versus typed,
  over a fixed set of runs; tokens spent per successful extraction.
- **Cost note:** local model, local DuckDB. $0.
- **Maps to:** §6 in `docs/005` — *Typed tool contracts & server-initiated input*.

### 204. `resource-or-tool` — the same catalog, offered three ways ⭐⭐ 🔌 🧠 💻
MCP has three server primitives and almost every data server uses exactly one.
This exposes one catalog as resources, as tools, and as prompts — the pipeline
runbook as a prompt is the case nobody builds — and measures which the model
reaches for, what each costs, and where each is wrong. The answer is not obvious:
resources are context the client chooses to include, tools are what the model
decides to call, and the distinction moves work between the two.
- **Protocol surface:** resources and resource templates; tools; prompts;
  `resources/read` with `ttlMs`; the client-driven versus model-driven split.
- **Learn:** the primitive taxonomy, which is the part of MCP most often skipped;
  who decides what enters the context window; when a prompt is the right answer
  and a tool is not.
- **Measures:** which primitive the model uses for the same twenty questions, at
  what token cost, with what answer accuracy against a fixed key.
- **Cost note:** local model over a small catalog. $0.
- **Maps to:** §6 in `docs/005` — *Tool calling & MCP*.

### 205. `stream-break` — twenty minutes in, the connection drops ⭐⭐ 🔌 💻
The revision removed SSE stream resumability and message redelivery. A broken
response stream now loses the in-flight request outright, and the client must
re-issue it with a new id — which for a warehouse query means paying for it twice.
This measures that honestly across both transports, and finds the duration at
which returning a task handle beats holding the connection open.
- **Protocol surface:** stdio versus Streamable HTTP; the removal of
  `Last-Event-ID` and SSE event ids; the required `Mcp-Method` and `Mcp-Name`
  headers; `x-mcp-header` for custom headers from tool parameters.
- **Learn:** what a transport guarantees and what it does not; why resumability was
  dropped rather than fixed; picking a transport for a workload instead of by
  default.
- **Measures:** wall-clock and dollars lost re-issuing an interrupted query at 1, 5
  and 20 minutes; the crossover duration where #199's task handle wins.
- **Cost note:** a scratch warehouse and a proxy that cuts connections. Cheap.
- **Maps to:** §6 in `docs/005` — *Async tool execution & long-running work*.

### 206. `trace-through` — one id from the agent turn to the Spark stage ⭐⭐⭐ 🔌 💻
"Which of last night's spend was the agent?" is currently unanswerable, because
the trail stops at the MCP boundary. The revision documents OpenTelemetry context
propagation in `_meta`, which closes it: the client's `traceparent` reaches the
server, the server stamps it into the warehouse query tag and the Spark job group,
and one identifier now spans a conversation turn and the compute it caused.
- **Protocol surface:** OpenTelemetry `traceparent`, `tracestate` and `baggage`
  conventions for `_meta` keys; propagation across a stateless request boundary.
  Read `_meta` directly — the SDK's `mcp.server._otel` is private, so depending on
  it would put a private import in the one place D10 says not to.
- **Learn:** distributed tracing across a protocol that deliberately forgets; where
  a span should start and stop when the caller is a model; attributing cost to a
  cause rather than to a service account.
- **Measures:** the fraction of a night's warehouse spend attributable to a single
  agent turn, and how much of the trail survives two hops.
- **Cost note:** local collector, local Spark. $0.
- **Maps to:** §7 in `docs/005` — *Observability for LLM systems*, alongside
  #61 `llm-trace` and #41 `finops-attributor`.

### 207. `warehouse-oauth` — the agent queries as the person ⭐⭐⭐ 🔌 ☁️
Almost every data MCP server in production today holds one service account, which
means row-level security, column masking and audit all see the same principal no
matter who is asking. This is the version that does not: the server is an OAuth
resource server, the human's identity reaches the warehouse, and two users asking
the same question through the same server get different rows. It is the single
biggest thing standing between MCP and an enterprise data platform.
- **Protocol surface:** the authorization resource-server model; Client ID Metadata
  Documents, now preferred over Dynamic Client Registration; the `iss` parameter
  validation requirement; credentials bound to their issuer; enterprise-managed
  authorization.
- **Learn:** token audience, and why a token for one server must not work on
  another; delegated versus service identity, and what each does to an audit log;
  why DCR was deprecated.
- **Measures:** the row-count difference two principals see through one server —
  the check that either passes or the whole design is decorative.
- **Cost note:** a hosted warehouse trial and a local identity provider. Cheap.
- **Maps to:** §6 in `docs/005` — *Capability, identity & egress control*.

### M.2 · Servers that do not exist yet (#208–#217)

### 208. `provenance-mcp` — where did that number come from? ⭐⭐⭐ 🔌 💻
Every tool result carries the collection's `Provenance` in `structuredContent` —
source path, content hash, unit kind, unit id — so any figure an agent quotes can
be walked back to the byte range it came from, by the client, without asking the
server a second question. The `outputSchema` makes provenance mandatory rather
than a courtesy, which means a tool physically cannot return an unsourced number.
- **Why nothing does this today:** data servers return values. Citation is treated
  as a RAG concern and disappears the moment the answer comes from SQL. Nothing
  makes provenance part of the *result contract*, so it stays optional and
  therefore usually absent.
- **Protocol surface:** `outputSchema` and `structuredContent` carrying a required
  provenance object; resource links back to the underlying unit.
- **Learn:** the collection's data seam expressed over its MCP seam; making a
  guarantee structural instead of behavioural.
- **Cost note:** builds on #49 `ingest-ledger`, which already carries the type. $0.
- **Maps to:** §2 in `docs/005` — grounding and citation.

### 209. `freshness-gate-mcp` — the server that declines to answer ⭐⭐ 🔌 💻
Tools that check their own inputs before answering, and refuse when the evidence
is not there: the partition has not landed, the ingest is incomplete, the upstream
feed is two days late. The refusal is not an error — it is a typed result carrying
the ledger evidence for *why*, so the agent can say "I cannot answer this yet, and
here is what is missing" rather than confidently reporting yesterday's number.
- **Why nothing does this today:** every data server answers. Freshness is
  monitored somewhere else, on a dashboard nobody is looking at while the agent is
  talking, so the staleness never reaches the thing making the claim.
- **Protocol surface:** a typed refusal in `structuredContent` rather than a
  JSON-RPC error; `ttlMs` reflecting real data freshness rather than a guess;
  `subscriptions/listen` to withdraw the refusal when the data lands.
- **Learn:** refusal as a feature, which is #49 `ingest-ledger`'s whole thesis,
  moved to where an agent will actually encounter it.
- **Cost note:** reads the ledger; no model needed to decide. $0.
- **Maps to:** §5 in `docs/005` — *Calibrated confidence & honest uncertainty*.

### 210. `surface-synth` — a tool surface shaped like the question ⭐⭐⭐ 🔌 🧠 ☁️
Given a four-thousand-table catalog and a task, this synthesises the twenty tools
that task needs — narrow, well named, with real schemas — advertises exactly those,
and prunes them as the task narrows, telling connected clients through
`toolsListChanged`. The tool list becomes a working set rather than an inventory.
- **Why nothing does this today:** servers pick one of two losing options, a single
  generic `query` tool that carries no information about what exists, or a static
  list too large to put in a prompt. #201 measures how badly both lose; this is the
  third option, and it needs the protocol's dynamic tool list to be possible at
  all.
- **Protocol surface:** dynamic `tools/list` with the `toolsListChanged`
  notification; deterministic ordering and `ttlMs` so a changing list still caches;
  per-request capabilities, since there is no session to hang a working set on.
- **Learn:** tool surfaces as retrieval; what a model needs in a tool name to pick
  correctly; keeping a cache useful when the thing cached is generated.
- **Cost note:** synthesis is a hosted-model job done once per task, then cached.
  Cheap per session.
- **Maps to:** §6 in `docs/005` — *Tool-surface scale, caching & change
  notification*.

### 211. `budget-mcp` — the server tells the agent what it has left ⭐⭐⭐ 🔌 💻
Every result carries what it cost — bytes scanned, slots, dollars — and the running
balance of a per-session budget the server enforces. When a query would exceed it
the server does not simply refuse: it returns what that query would have cost and
what a sampled or narrowed version would cost instead, so the agent can choose.
The model plans against a budget because it can finally see one.
- **Why nothing does this today:** cost governance lives in the warehouse, and the
  only signal reaching the agent is a query that failed. Nothing meters tool calls
  back to the caller, so an agent cannot trade accuracy against spend — it has no
  idea what anything costs.
- **Protocol surface:** cost accounting in `structuredContent` on every result;
  server-minted session handles, now that sessions are not the transport's job; a
  typed over-budget refusal carrying alternatives.
- **Learn:** feedback loops between a model and a resource limit; making a
  constraint legible to something that can reason about it.
- **Cost note:** the point of the tool is that this line stays small. Cheap.
- **Maps to:** §7 in `docs/005` — *Cost & token economics*, alongside
  #50 `token-ledger` and #41 `finops-attributor`.

### 212. `snapshot-mcp` — the session you can replay next quarter ⭐⭐⭐ 🔌 💻
Pins an entire agent session to a lakehouse snapshot minted at the first call and
returned as a server handle the client passes back on every subsequent one. Every
query in that session resolves against the same Iceberg or Delta snapshot, so the
transcript is not a story about what the data said in June — it is a thing you can
run again in September and get the same numbers from.
- **Why nothing does this today:** time travel exists in every lakehouse engine and
  no MCP server exposes it as session scope. Agent transcripts over mutable tables
  are unreproducible by construction, which becomes a problem the moment anyone
  audits a decision. The move to explicit server-minted handles is what makes this
  expressible cleanly.
- **Protocol surface:** server-minted handles as ordinary tool arguments, replacing
  what a session id used to do; snapshot ids echoed in `structuredContent`;
  `cacheScope` set correctly for a pinned read.
- **Learn:** reproducibility over mutable data; why statelessness pushed state into
  the open, and why that turned out to be better.
- **Cost note:** local Iceberg or Delta tables. $0.
- **Maps to:** §7 in `docs/005` — reproducibility, alongside #75 `runcard`.

### 213. `contract-mcp` — the schema in the tool *is* the contract ⭐⭐⭐ 🔌 💻
Generates the server's whole tool surface from the data contracts, so a tool's
`outputSchema` is the contract rather than a copy of it. Change the contract in a
way that breaks a consumer and the tool list changes visibly, `toolsListChanged`
fires, and every connected agent sees it at the next call — a breaking change
becomes something that happens *to callers*, not a line in a review nobody read.
- **Why nothing does this today:** contracts are validated out of band, in CI,
  against artefacts, and the consumer finds out later. Nothing makes a violation
  visible at the point of consumption, because until now a tool surface was a
  static file rather than a projection of anything.
- **Protocol surface:** `outputSchema` generated from the contract;
  `toolsListChanged` as a breaking-change signal; `ttlMs` and `cacheScope` tuned so
  a stale contract cannot be cached past its usefulness.
- **Learn:** contracts as executable interfaces; making a governance artefact
  load-bearing so it cannot rot.
- **Cost note:** deterministic generation, no model. $0.
- **Maps to:** §6 in `docs/005` — *Typed tool contracts & server-initiated input*.
  Complements #19 `data-contract-linter` and #183 `schema-contract-differ`.

### 214. `lineage-app` — the graph you can click, in the conversation ⭐⭐⭐ 🔌 🧠 💻
Column-level lineage, a reconciliation diff, or four hundred proposed
source-to-target mappings, rendered as an interactive view inside the chat rather
than described in prose. Click a node to expand it and the view calls back into the
server for detail; approve a mapping and that decision returns to the model as
context. Approving four hundred mappings by reading them aloud is the status quo,
and it is why nobody does it.
- **Why nothing does this today:** data tooling has not adopted MCP Apps at all.
  The alternative is a separate web app with its own auth, its own state, and no
  connection to the conversation that produced the thing being reviewed.
- **Protocol surface:** the MCP Apps extension — a `ui://` resource referenced from
  the tool's `_meta.ui.resourceUri`, sandboxed iframe rendering, the `ui/` JSON-RPC
  dialect over postMessage, `_meta.ui.csp` for what the view may load.
- **Learn:** where a picture beats a paragraph for an agent's output; bidirectional
  UI as a protocol rather than a framework; the sandbox model and what it forbids.
- **Cost note:** the view is static HTML; the model cost is the lineage work
  itself. Cheap.
- **Maps to:** §6 in `docs/005` — *Interactive tool UI*. Renders #30 `sql-lineage`,
  #38 `lineage-explorer` and #100 `mapping-suggester`.

### 215. `aggregate-only-mcp` — exploration without a residency review ⭐⭐⭐ 🔌 💻
A server that answers only aggregates, enforces a minimum group size and a
k-anonymity floor in the query planner rather than in a policy document, and
refuses anything that would isolate an individual — explaining which constraint it
hit. An agent gets to explore production data; the deployment gets to say, with
evidence, that no row value ever left.
- **Why nothing does this today:** the choice on offer is all or nothing. Section K
  buys deployability by never reading a row; section L buys answers by accepting a
  full data-residency review. The middle — real data, provably non-identifying — is
  where most exploratory work actually sits, and no server occupies it.
- **Protocol surface:** the guarantee expressed as `outputSchema` (aggregates only,
  with a group-size field), a typed refusal naming the violated constraint, and
  tool annotations that describe the limit honestly.
- **Learn:** privacy as an interface property rather than a review outcome;
  k-anonymity and differential-privacy mechanics where they are cheap; writing a
  refusal an analyst can legitimately work around.
- **Cost note:** local DuckDB, no model in the enforcement path. $0.
- **Maps to:** §6 in `docs/005` — *Capability, identity & egress control*.

### 216. `egress-ledger-mcp` — how much data left during that session? ⭐⭐⭐ 🔌 💻
A gateway that accounts, per column and per session, exactly which values crossed
the boundary into a model's context — how many distinct values of which columns,
classified against the catalog's sensitivity tags — and emits the evidence a
privacy review asks for. Not a policy. A ledger.
- **Why nothing does this today:** it is the first question a privacy review asks
  about an AI system and nobody can answer it. Query logs record that a query ran,
  not what a model saw. The accounting has to happen at the protocol boundary,
  which is exactly where a gateway sits.
- **Protocol surface:** a gateway in the shape of #16 `mcp-gateway`, tallying every
  result that passes through it; `cacheScope` respected so a cached read is still
  counted once; per-request client identity from `_meta` rather than from a
  session.
- **Learn:** measuring an exposure rather than asserting a control; what a gateway
  can see that neither endpoint can.
- **Cost note:** counting is deterministic; the classifier can be local. $0.
- **Maps to:** §6 in `docs/005` — *Capability, identity & egress control*. Feeds
  #140 `pia-drafter` and #193 `purpose-limitation-auditor`.

### 217. `mcp-replay` — an agent you can put in CI ⭐⭐ 🔌 💻
Records every MCP exchange of a pipeline-agent run — requests, results, task polls,
interim `input_required` results and the retries that answered them — and replays
them deterministically. The agent becomes testable with no warehouse, no
credentials and no model, which is the collection's own rule about tests applied to
the one thing nobody applies it to.
- **Why nothing does this today:** MCP has inspectors and proxies for watching
  traffic live. It has no fixture format, so agent behaviour is verified by running
  against real systems and hoping, and a regression is noticed in production.
  Replaying MRTR correctly is the hard part, and the reason it has not been done.
- **Protocol surface:** the full request and result envelope including `_meta`;
  `resultType` discrimination between `complete`, `input_required` and `task`;
  `requestState` round-tripping; task polling sequences replayed in order. The SDK
  keeps its in-memory client/server pair in a private module
  (`mcp.client._memory`), and a live connection is not a replayable fixture
  anyway, so building that harness is part of this tool rather than
  something it can borrow.
- **Learn:** determinism at a protocol boundary; recording enough to replay without
  recording secrets; what an agent regression test actually has to assert.
- **Cost note:** replay needs neither model nor warehouse — that is the point. $0.
- **Maps to:** §7 in `docs/005` — *Observability for LLM systems*, alongside
  #61 `llm-trace` and #59 `promptops`.
