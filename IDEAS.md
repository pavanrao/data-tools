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

## F. Field-guide labs (evidence for the STG concept map)

Section F exists for one reason: to turn the concepts in the *Technical Field
Guide* into things you have **actually run**, so that every answer you give
carries a number you produced yourself — a LoRA rank, a WER delta, a p95 under
load, a PSI score, a cost per run.

Three rules hold across the whole section:

1. **Every lab emits an evidence card.** A JSONL record under `evidence/`
   keyed by the guide card it covers: what you ran, the number you got, the
   baseline, and what surprised you. `viva` (#90) reads them back.
2. **Small models, small data, real mechanics.** A 135M-parameter model on CPU
   exercises exactly the same LoRA config, the same KV-cache arithmetic and the
   same catastrophic-forgetting check as a 70B one. Rent a GPU hour only where
   the mechanism genuinely needs it.
3. **The failure is the deliverable.** Each lab has a *break it on purpose*
   step — the skew that sticks at 99%, the async endpoint that collapses under
   load, the quantized model that got quietly worse. Those are the stories the
   guide says cannot be fabricated.

**Legend addition:** 🎓 marks a lab whose primary output is an evidence card
rather than a reusable tool.

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
- **Learn:** the difference the guide calls the tell — schema compliance ≠
  semantic correctness; the same guard in front of tool-call arguments.
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
- **Cost note:** local embeddings + a small CPU cross-encoder; reuses
  `embeddings-cache` (#23). $0.
- **Covers:** §2 The RAG pipeline · §2 Hybrid search · §2 Re-ranking ·
  §5 Retrieval metrics (retrieval half).

### 54. `lora-lab` — a fine-tune you can quote the configuration of ⭐⭐⭐ 💻 🎓
QLoRA a small instruct model on a narrow task, recording every number the guide
says practitioners produce instantly: **rank, alpha, target modules by parameter
name** (`q_proj`, `v_proj`, …), dataset size, epochs, VRAM, wall time. Then the
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
- **Learn:** using a judge for scale while keeping it calibrated — and knowing
  the caveats before someone asks for them.
- **Cost note:** judge with a local model for CI, an API model weekly. Cents.
- **Covers:** §5 LLM-as-judge · §5 Task metrics vs. vibes (measuring the parts
  that resist hard metrics).

### 58. `agent-governor` — the scar tissue around a ReAct loop ⭐⭐⭐ 🔌 💻
A ReAct runner built entirely out of the controls the guide treats as evidence of
production experience: a hard iteration ceiling, a per-session spend cap, a
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
- **Learn:** the tension the guide flags — you cannot debug what you didn't log,
  and you cannot log everything if it contains personal data.
- **Cost note:** local collector; sampling policy for high-volume stages.
- **Covers:** §7 Observability for LLM systems · §21 PII in traces and logs.

### 62. `serve-bench` — throughput, latency, and the KV cache ⭐⭐⭐ 💻 🎓
Serve one open model two ways — naive `transformers` and a real engine (vLLM, or
llama.cpp where GPU access is scarce) — and measure the things the guide says
practitioners quote: **p50 and p95 at stated concurrency**, time-to-first-token
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

### 66. `tabular-lab` — the ML that is actually on most résumés ⭐⭐ 💻 🎓
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
records, and ships the runbook for the interview question: discovering three
months of bad data and backfilling it without double-counting.
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
Terraform for one of this collection's tools, done the way the guide's tell
demands: **remote state with locking**, modules, environment promotion, a
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
A `kind` cluster running one of these tools, then every failure the guide expects
scar tissue from, provoked deliberately: an OOMKill from a memory limit set too
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

### 90. `viva` — answer with your own numbers ⭐⭐ 💻 🔌
The capstone, and the reason every other lab writes an evidence card. `viva`
reads `evidence/*.jsonl` across the collection and drills you on the field
guide's own follow-up questions, but grades against **what you actually
measured**: it will not accept "we tuned it" where the card holds a rank, a WER,
a p95, or a rejection rate. Reports coverage across all 104 concept cards, flags
every concept where you hold no evidence, and drafts the one-line, defensible
phrasing the guide's "writing it up" section describes.
- **Learn:** the method half of the guide — the depth ladder, the tells, the
  floor questions, the red flags — from the answering side.
- **Cost note:** local; questions are static, grading is a local model. $0.
- **Covers:** Method: reading depth · The calibration bar · Reading by role level ·
  Floor questions · Universal red flags · Writing it up.

---

## G. Concept notes (markdown, not code)

Cards where the honest deliverable is a written position plus a prompt you can
run to demonstrate it — no tool earns its keep. Each note follows the same
shape: **the mechanism**, **the trade-off**, **a prompt or experiment that shows
it**, and **the number from my own lab** (linked to the evidence card).

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
- **N6 · `notes/interview-method.md`** — the guide read from the candidate's
  side: the depth ladder, why failure stories are the fairest question, the
  calibration bar, what relaxes at Specialist Programmer versus Senior
  Technologist, the floor questions answered in one line each, and the red flags
  audited against my own résumé bullets.
  *Covers the method sections; `viva` (#90) drills them.*

---

## Suggested build order (for learning)

1. **#1 `docs-rag`** — get the whole RAG loop working once, locally and free.
2. **#11 `sqlite-mcp`** — get a clean MCP server working once.
3. **#23 `embeddings-cache`** + **#24 `model-router`** — the economy foundation.
4. **#12 `filesystem-rag-mcp`** — the "aha": RAG *as* an MCP tool.
5. **#9 `eval-harness`** — so every later tweak is measurable.
6. Anything from C — combined pipelines, now that the pieces exist.

### Field-guide track (sections F–G)

Ordered so that the **CORE** sections of the guide — the ones the req actually
requires — are covered first, and each lab feeds the next.

1. **N1 + #50 `token-ledger` + #51 `decode-lab` + #52 `schema-guard`** — the
   foundations, with numbers. One weekend.
2. **#9 `eval-harness` + N5 + #57 `judge-lab`** — measurement before anything
   else, so every later change is provable.
3. **#53 `retrieval-bench`** on the corpus `docs-rag` (#1) and `ingest-ledger`
   (#49) already index — RAG depth without a new corpus.
4. **#54 `lora-lab` + #55 `synthdata-forge`** — the strongest single probe in
   the guide; do not skip the general-benchmark check.
5. **#58 `agent-governor`** + N2/N3 — agentic AI and the framework opinions.
6. **#59 `promptops` + #60 `model-pin` + #61 `llm-trace`** — LLMOps, the section
   where an operator profile is built.
7. **#56 `preference-forge` + N4** — alignment, the rarest CORE claim.
8. **#88 `jailbreak-range` + #89 `fairness-audit`** + `pii-scanner` (#20) —
   the responsible-AI requirement, answered as fairness rather than as security.
9. **#62 `serve-bench` + #63 `quant-check`** — serving, the best differentiator
   available if you have any GPU access at all.
10. **#66 `tabular-lab` + #64 `trainer-lab` + #65 `taxonomy-classifier`** —
    classical and deep ML, the JD's model-development half.
11. **BREADTH, by résumé relevance** — data/platform first (#79, #80, #81, #82,
    #75, #76, #77, #78), then cloud and Kubernetes (#83–#87), then the adjacent
    domains you may never be asked about (#67–#74).
12. **#90 `viva`** — run it continuously from step 2 onward; it tells you which
    cards still have no evidence behind them.
