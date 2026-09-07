# Tool Ideas

A backlog of small, independent data-pipeline tools to build while learning MCP
and RAG. Pick any one — they don't depend on each other.

**Legend**
- 🧠 **RAG** — exercises retrieval-augmented generation
- 🔌 **MCP** — exercises building or consuming an MCP server/client
- 💻 **Local-first** — runs well on a local LLM (Ollama/llama.cpp)
- ☁️ **API-leaning** — benefits from a hosted model's quality, but stays cheap
- 💸 **Cost note** — how to keep it economical
- 🤖 **Agentic** — multi-step, tool-using agent work *is* the tool (not narration bolted on)
- 🏛️ **System** — multi-component platform/product; the "small tool" rule is intentionally waived
- ⚠️ **Deterministic** — core job needs no LLM/RAG; kept for learning value, but AI is optional here

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

---

## F. Small, sharp AI tools (#49–73)

Buildable in days, one job each — but unlike section E's plumbing, **the AI is the whole
point**: each solves a problem that regex/SQL/diffing fundamentally cannot, because it
requires semantic understanding. All target real enterprise data-engineering pain. Each
entry's **Agentic core** line states why an LLM is essential, not decorative.

### 49. `vendor-spec-reader` — file-spec PDF → parser config + DQ rules ⭐⭐ 🧠 ☁️
Feed it a 200-page vendor/reinsurer extract specification PDF; it produces a draft field
spec (names, positions, types, valid values), parser config, and starter DQ rules — each
traced back to the page/section it came from.
- **Agentic core:** reading prose specs ("field 12 is blank when policy status is lapsed")
  and turning them into machine config is pure language understanding; no parser can do it.
- **Learn:** RAG over long structured documents; schema-constrained JSON output; citation discipline.
- **Cost note:** parse/OCR locally; one API pass per spec, cached forever — specs rarely change.
- **Maps to:** legacy/COTS flat-file ingestion onboarding.

### 50. `copybook-decoder` — COBOL copybook → semantics + parser spec ⭐⭐ 🧠 💻
Parse a COBOL copybook (deterministic), then use sample data + field names like
`WS-POL-STS-CD` to produce plain-English field documentation, inferred enumerations, and
a ready-to-use parsing spec.
- **Agentic core:** copybook *syntax* is mechanical; field *meaning* (cryptic 6-char names,
  REDEFINES intent, sentinel conventions) requires semantic inference from names + values.
- **Learn:** combining deterministic parsing with LLM semantic enrichment; EBCDIC/packed-decimal handling.
- **Cost note:** parsing is code; LLM call per field group, cached by copybook hash.
- **Maps to:** mainframe/COTS ingestion.

### 51. `column-semantics-tagger` — decode cryptic legacy column names ⭐⭐ 🧠 💻
Point it at a legacy schema; for each column (`CD_STS_RSN`, `AMT_PRM_ANN`) it infers the
business meaning from the name, sample values, sibling columns, and any glossary — and
proposes a glossary mapping with confidence.
- **Agentic core:** abbreviation expansion + meaning inference from context is exactly what
  LLMs do and string matching doesn't.
- **Learn:** evidence-gathering prompts (values + context), calibrated confidence, human-review output.
- **Cost note:** local model handles most; batch columns per call.
- **Maps to:** catalog enrichment / auto-classification.

### 52. `fixed-width-inferrer` — recover the layout when no spec exists ⭐⭐ 🧠 💻
Given raw fixed-width files with no documentation (the spec retired with its author),
infer field boundaries, types, and likely meanings from character-class transitions plus
semantic plausibility — then emit a draft spec for review.
- **Agentic core:** statistics find *candidate* boundaries; deciding "positions 41–48 is a
  date and 49–57 looks like a premium amount" needs semantic judgment.
- **Learn:** hybrid statistical + LLM inference; expressing uncertainty honestly in output.
- **Cost note:** boundary detection is local stats; LLM only labels the candidate fields.
- **Maps to:** undocumented legacy ingestion.

### 53. `null-semantics-detective` — what do the sentinels mean? ⭐⭐ 🧠 💻
Scan columns across legacy sources for sentinel values (`9999-12-31`, `00000000`, `XX`,
`-1`, blank-vs-NULL) and infer what each one *means* (unknown? not-applicable? open-ended?)
from context — emitting cleansing rules per column.
- **Agentic core:** distinguishing "9999-12-31 means *still active*" from "means *unknown*"
  requires reasoning over column role and co-occurring fields, not frequency counts.
- **Learn:** profiling → hypothesis → LLM adjudication loop; encoding findings as cleansing config.
- **Cost note:** profiling local; LLM sees only value summaries, never raw rows.
- **Maps to:** cleansed-zone standardization rules.

### 54. `units-detective` — find mixed units, currencies, and scales ⭐⭐ 🧠 💻
Detect numeric columns that mix cents with dollars, percentages with basis points, or
thousands with raw amounts — using distribution analysis plus semantic context (column
name, sibling currency-code columns, source system).
- **Agentic core:** a bimodal distribution is a clue; concluding "rows from source B are in
  cents" requires reasoning across metadata, lineage, and domain convention.
- **Learn:** distribution fingerprinting + contextual reasoning; emitting normalization rules.
- **Cost note:** stats local; LLM adjudicates flagged columns only.
- **Maps to:** data-quality / conformance in the cleansed zone.

### 55. `code-set-mapper` — align source codes to canonical reference codes ⭐⭐ 🧠 💻
Given a source system's code set and your canonical reference set, propose value-level
mappings (`M/F/U` ↔ `MALE/FEMALE/UNKNOWN`, state codes, status codes) with confidence and
flags for unmappable or many-to-one cases.
- **Agentic core:** code descriptions are short, inconsistent text; matching `"Lapse-NonPay"`
  to `"LAPSED_NONPAYMENT"` vs `"TERMINATED"` is semantic, not lexical.
- **Learn:** semantic matching over short strings; handling asymmetric/partial mappings; review queues.
- **Cost note:** tiny inputs — a local model is plenty; cache per code-set version.
- **Maps to:** reference-data / cross-reference management.

### 56. `mapping-suggester` — draft source→target column mappings ⭐⭐ 🧠 ☁️
Given a profiled source schema and a target model, propose column-level mappings with
per-mapping confidence, rationale, and a draft transform expression — grounded by RAG over
the glossary and previously approved mappings.
- **Agentic core:** mapping is the single most labor-intensive task in data integration and
  is driven by meaning; prior-mapping retrieval + reasoning is what makes proposals good.
- **Learn:** RAG over structured mapping history; proposal/confidence/review-loop design.
- **Cost note:** one focused API call per entity; everything retrieved is small text.
- **Maps to:** mart-load mapping specs (the human bottleneck in feed onboarding).

### 57. `join-key-suggester` — find how two systems' tables join ⭐⭐ 🧠 💻
Given tables from different systems, find candidate join keys by combining value-overlap
analysis (deterministic) with semantic matching of names and formats — including composite
and transformed keys (`POL_NO` ↔ `policy_id` minus prefix).
- **Agentic core:** value overlap finds candidates; recognizing that one key is the other
  with a check digit stripped — and whether the join *makes business sense* — is reasoning.
- **Learn:** blocking/overlap algorithms + LLM adjudication; precision/recall tradeoffs.
- **Cost note:** overlap math local; LLM sees only candidate-pair summaries.
- **Maps to:** cross-system integration / MDM groundwork.

### 58. `transform-explainer` — legacy SQL → business-rule documentation ⭐⭐ 🧠 💻
Take a gnarly 800-line legacy transform (nested CASEs, magic numbers, layered CTEs) and
produce plain-English business-rule documentation with line citations: what it does, why
each branch exists, what looks suspicious.
- **Agentic core:** translating code intent into business language is comprehension, the
  core LLM competence; sqlglot can parse it but cannot say what it *means*.
- **Learn:** chunking large SQL semantically; citation-grounded explanation; suspicion flagging.
- **Cost note:** local model for most; API pass for the truly gnarly ones.
- **Maps to:** transform documentation / modernization prep.

### 59. `sql-intent-differ` — what changed in business terms? ⭐⭐ 🧠 💻
Diff two versions of a transform and report the *semantic* change ("late-payment grace
period extended from 30 to 45 days; lapsed policies now excluded from the premium sum"),
not the text delta.
- **Agentic core:** mapping an AST diff to business meaning is interpretation; a text diff
  of a refactored query is unreadable noise.
- **Learn:** AST-level diffing (sqlglot) feeding an LLM interpretation layer.
- **Cost note:** diff locally; one small LLM call per change set.
- **Maps to:** change review for transform PRs (pairs with config-as-code CI).

### 60. `metric-definition-extractor` — mine reports for metric definitions ⭐⭐ 🧠 💻
Crawl BI report SQL / dashboard definitions and extract each metric into a reviewable
dictionary entry: name, formula, filters, grain, source columns — the raw material for a
semantic layer.
- **Agentic core:** recognizing that three differently-written queries all compute
  "annualized premium in force" requires semantic normalization of logic.
- **Learn:** extraction over code corpora; canonicalizing equivalent expressions.
- **Cost note:** parse locally; LLM normalizes per metric; cache by query hash.
- **Maps to:** semantic-layer bootstrap / BI governance.

### 61. `glossary-linker` — connect glossary terms to physical columns ⭐⭐ 🧠 💻
Semantically link business-glossary terms to the actual tables/columns that embody them;
surface orphaned terms (defined but unmapped) and undocumented columns (mapped to nothing).
- **Agentic core:** "Annualized Premium" ↔ `ANN_PREM_AMT` across thousands of columns is
  semantic matching at scale; exact/fuzzy string match misses most of it.
- **Learn:** embedding + LLM-verification two-stage matching; stewardship review output.
- **Cost note:** embeddings local; LLM verifies top-k candidates only.
- **Maps to:** catalog/glossary stewardship.

### 62. `contract-from-docs` — extract data contracts from legacy artifacts ⭐⭐ 🧠 ☁️
Given the messy reality — interface Word docs, emails, spec fragments, a sample file —
draft a formal data contract (schema, nullability, keys, SLAs, semantics) with each clause
cited to its source artifact and gaps explicitly listed.
- **Agentic core:** synthesizing a normative contract from contradictory prose sources is
  reading-comprehension + reconciliation; there is no deterministic path.
- **Learn:** multi-document RAG with conflict detection; "what's missing" reporting.
- **Cost note:** one API synthesis pass per contract; sources are small.
- **Maps to:** data contracts / feed onboarding.

### 63. `naming-harmonizer` — propose convention-true names ⭐ 🧠 💻
For new tables/columns, propose names that match the enterprise's *actual* conventions —
learned from the existing catalog rather than a style doc — and flag existing names that
break pattern.
- **Agentic core:** conventions are implicit and inconsistent ("we abbreviate AMOUNT as AMT
  except in claims"); learning them from examples is induction, not lookup.
- **Learn:** few-shot convention induction; catalog-grounded suggestions.
- **Cost note:** local model; the catalog excerpt per call is tiny.
- **Maps to:** model governance / DDL review.

### 64. `doc-drift-detector` — where docs lie about reality ⭐⭐ 🧠 💻
Compare documentation (wiki, README, catalog descriptions) against actual schemas, configs,
and behavior; report semantic disagreements ("doc says daily, schedule says hourly"; "doc
lists 12 statuses, data has 17") and draft corrections.
- **Agentic core:** docs and reality are in different languages (prose vs DDL/config);
  comparing them is meaning-level alignment.
- **Learn:** grounding prose claims against structured facts; targeted patch generation.
- **Cost note:** fact extraction local; LLM compares claim-by-claim.
- **Maps to:** catalog/documentation governance.

### 65. `test-synthesizer` — generate fixtures for SQL transforms ⭐⭐ 🧠 💻
Read a SQL/SparkSQL transform and generate edge-case input fixtures + expected outputs:
boundary dates, null keys, late-arriving rows, duplicate business keys — feeding the
deterministic `sql-test-harness` (#42).
- **Agentic core:** identifying *which* edge cases threaten *this* logic (that COALESCE
  hides a join miss; that the SCD2 close-out breaks on same-day changes) is code reasoning.
- **Learn:** code-comprehension-driven test generation; verifying expected outputs by execution.
- **Cost note:** generation is one call per transform; execution/verification is local DuckDB.
- **Maps to:** transform-engine testing.

### 66. `edge-case-smith` — business-rule-aware test rows ⭐⭐ 🧠 💻
Generate small, schema-valid datasets that respect *inferred* business rules (issue date ≤
claim date; terminated policies have an end date) while deliberately probing edges — the
smart sibling of faker.
- **Agentic core:** faker fills types; inferring cross-column business rules from profile +
  names and then *violating them on purpose, one at a time* requires understanding.
- **Learn:** rule inference from profiles; constrained generation; rule-violation matrices.
- **Cost note:** local model generates rules + a seed set; expansion is code.
- **Maps to:** DQ-rule and pipeline testing.

### 67. `dag-reviewer` — semantic review of orchestration code ⭐⭐ 🧠 💻
Review Airflow DAG/operator code for the anti-patterns that pass linting but burn you at
3am: non-idempotent tasks, catchup/backfill traps, timezone bugs, implicit cross-DAG
dependencies, missing SLAs — with reasoned explanations.
- **Agentic core:** "this task isn't idempotent because the INSERT lacks a delete-first or
  merge" is program reasoning about *behavior*, beyond any linter rule.
- **Learn:** building a domain-specific review rubric; reasoning-with-citations output.
- **Cost note:** local model with a strong rubric prompt covers most; DAG files are small.
- **Maps to:** DAG-factory output review / orchestration quality.

### 68. `change-risk-scorer` — blast radius as a PR comment ⭐⭐ 🧠 🔌 ☁️
For each config/SQL PR, combine lineage (what's downstream), usage (who queries it), and
semantic analysis of the change itself into a risk score and a crisp review comment:
"touches the join feeding `dim_party`; 14 reports downstream; type narrowing may truncate."
- **Agentic core:** fusing lineage facts with *what the diff semantically does* into a risk
  judgment is multi-source reasoning; lineage alone over-warns on everything.
- **Learn:** composing deterministic lineage with LLM diff analysis; CI-bot integration via MCP.
- **Cost note:** lineage local; one LLM call per PR.
- **Maps to:** config-as-code CI gates / change management.

### 69. `freshness-inferrer` — is it late, or is it just Tuesday? ⭐⭐ 🧠 💻
Learn each feed's true arrival rhythm from history (weekday patterns, month-end surges,
holiday gaps, vendor quirks) and answer "should I worry yet?" with reasoning — instead of
naive fixed-deadline alerts that cry wolf.
- **Agentic core:** the *model* of arrival patterns is stats; explaining "late for a
  month-end Friday but the vendor always slips after quarter close" merges learned pattern
  with contextual reasoning.
- **Learn:** seasonality-aware baselining; alert-fatigue reduction; honest uncertainty.
- **Cost note:** stats local; LLM phrases the judgment only when asked.
- **Maps to:** SLA/freshness observability.

### 70. `failure-notifier` — the evidence-backed "your file broke" ticket ⭐ 🧠 💻
When a source extract breaks, draft the email/ticket to the source-system owner with
everything they need: what changed (sample rows, schema diff), which contract clause it
violates, business impact, and what you need from them — in their language, not yours.
- **Agentic core:** selecting the *right* evidence and writing for a non-data-team audience
  is communication work that templates do badly and engineers avoid doing.
- **Learn:** evidence selection + audience-aware generation; the human side of data contracts.
- **Cost note:** local model; inputs are diffs and samples already computed upstream.
- **Maps to:** source-system liaison / contract enforcement.

### 71. `runbook-writer` — turn resolved incidents into runbooks ⭐⭐ 🧠 💻
After an incident is resolved, distill the logs, timeline, and fix into a runbook entry
(symptom → diagnosis path → fix → prevention) — building the corpus that `etl-doctor` (#17)
and every future ops-RAG tool retrieves.
- **Agentic core:** compressing a noisy incident thread into a reusable diagnostic recipe
  is summarization-with-structure; nobody writes these by hand, which is why runbooks rot.
- **Learn:** knowledge distillation into retrievable form; closing the ops-RAG flywheel.
- **Cost note:** one call per incident; incidents are rare relative to queries against the corpus.
- **Maps to:** operational knowledge management.

### 72. `dialect-translator` — SQL dialect migration, verified ⭐⭐ 🧠 💻
Translate queries between dialects (Vertica ↔ SparkSQL ↔ Snowflake), then *prove* the
translation by running both against the same sample data and diffing results; iterate on
mismatches.
- **Agentic core:** transpilers (sqlglot) handle syntax but miss semantic gaps — null
  ordering, date arithmetic, division semantics; the verify-and-repair loop is agentic.
- **Learn:** the generate→execute→verify→repair loop; where transpilers actually fail.
- **Cost note:** sqlglot first, LLM only on failures; verification is local DuckDB/sample runs.
- **Maps to:** future-migration options (Appendix-A portability).

### 73. `sample-redactor` — shareable data samples, structure intact ⭐⭐ 🧠 💻
Produce redacted-but-realistic data samples for vendor/support debugging: PII replaced
with format-consistent fakes, internal codes preserved, cross-row consistency maintained
(same fake person throughout) so the bug still reproduces.
- **Agentic core:** deciding what's identifying *in context* (rare diagnosis + ZIP is PII;
  either alone isn't) and what must survive for the bug to reproduce requires judgment.
- **Learn:** consistency-preserving redaction; quasi-identifier awareness.
- **Cost note:** rules engine does the bulk; LLM adjudicates ambiguous columns once per schema.
- **Maps to:** PII protection / vendor escalation workflows.

---

## G. Ambitious, bounded agents (#74–98)

Still one clear job per tool — but the job is enterprise-grade and the tool is a genuine
**multi-step agent** 🤖: it plans, calls tools, gathers evidence, iterates, and produces a
defensible conclusion. These attack the problems that consume senior data engineers' and
architects' weeks.

### 74. `db-archaeologist` — excavate an undocumented legacy database ⭐⭐⭐ 🤖 🧠 ☁️
Point it at a legacy database nobody understands. It explores agentically — samples tables,
infers keys and relationships from value overlap, reads embedded code/views, names what it
finds — and emits an ERD, inferred FKs, entity descriptions, and a confidence-ranked report.
- **Agentic core:** exploration is iterative and hypothesis-driven (find a candidate key →
  test it → revise); the output is *meaning*, which only semantic inference provides.
- **Learn:** agent loops over a DB-introspection MCP server; hypothesis testing; honest confidence.
- **Cost note:** all queries local; LLM reasons over summaries, never full tables.
- **Maps to:** legacy source onboarding (the "no one knows what's in there" problem).

### 75. `proc-modernizer` — stored procedures → tested SparkSQL ⭐⭐⭐ 🤖 🧠 ☁️
Convert a 5000-line PL/SQL / T-SQL procedure into documented, tested SparkSQL/dbt models:
decompose into steps, translate each, generate fixtures, run both versions on sample data,
and iterate until outputs match — producing a divergence report for what won't translate.
- **Agentic core:** the translate→execute→compare→repair loop *is* the product; one-shot
  translation of real procedures is reliably wrong.
- **Learn:** large-code decomposition; equivalence testing as the agent's stop condition.
- **Cost note:** iteration on sample data locally; API model for translation passes only.
- **Maps to:** transform modernization (every enterprise has hundreds of these).

### 76. `jcl-flow-reconstructor` — mainframe job flows → Airflow DAGs ⭐⭐⭐ 🤖 🧠 ☁️
From JCL libraries and scheduler dumps (CA-7/Control-M), reconstruct the real dependency
graph — including implicit file-based dependencies (job A writes the dataset job B reads) —
and propose equivalent Airflow DAG definitions with the assumptions listed.
- **Agentic core:** dependencies are implicit in dataset names, PROC expansions, and
  conventions; recovering intent from them is inference, not parsing.
- **Learn:** lineage inference from artifacts; generating orchestration config from evidence.
- **Cost note:** parsing local; LLM resolves ambiguous links; one-time migration cost.
- **Maps to:** mainframe decommissioning / orchestration migration.

### 77. `report-reverse-engineer` — the model hiding in your reports ⭐⭐⭐ 🤖 🧠 ☁️
Crawl a legacy BI estate's report SQL; extract every metric and dimension actually in use;
cluster semantically equivalent ones; and emit the *implicit* semantic model — plus a
contradiction list ("'active policy count' has four different definitions").
- **Agentic core:** recognizing semantic equivalence across differently-written SQL and
  judging which definition is canonical requires meaning-level analysis at corpus scale.
- **Learn:** corpus-scale extraction + clustering; from descriptive findings to prescriptive model.
- **Cost note:** parse locally; LLM normalizes per-cluster, cached by query hash.
- **Maps to:** semantic-layer design / BI rationalization groundwork.

### 78. `model-designer` — propose the dimensional model ⭐⭐⭐ 🤖 🧠 ☁️
From profiled sources, the glossary, and stated business questions, propose a Kimball
design: fact tables with explicit grain, dimensions with SCD-type recommendations,
conformance opportunities — as reviewable DDL + mapping spec with rationale per decision.
- **Agentic core:** grain decisions and fact/dim classification encode business judgment
  ("is policy status an SCD2 dimension attribute or a status fact?"); this is design reasoning.
- **Learn:** encoding modeling heuristics into an agent; design-rationale documentation.
- **Cost note:** inputs are profiles + glossary (small); a few API calls per subject area.
- **Maps to:** mart design (Party/Policy model, Phase 1).

### 79. `match-merge-adjudicator` — MDM's gray zone, adjudicated ⭐⭐⭐ 🤖 🧠 ☁️
Deterministic blocking finds candidate party matches; the clear ones auto-resolve by rule;
the gray zone ("J. Smith, same DOB, address one digit off, different SSN format") goes to
an LLM adjudicator that weighs evidence, decides, and writes the rationale — feeding a
human review queue ordered by uncertainty.
- **Agentic core:** gray-zone matching is evidence-weighing under domain knowledge (nickname
  conventions, address typos, household vs individual) — exactly where rules plateau.
- **Learn:** hybrid deterministic/LLM pipelines; rationale capture for audit; review-queue design.
- **Cost note:** LLM sees only the gray zone (a few % of pairs); local model viable.
- **Maps to:** Party MDM match/merge.

### 80. `metric-consistency-auditor` — one KPI, four definitions ⭐⭐⭐ 🤖 🧠 ☁️
Find every place a KPI is computed (reports, dashboards, extracts, SQL), compare the
definitions semantically, quantify how much they disagree on real data, and propose the
canonical definition with a migration list for the deviants.
- **Agentic core:** establishing that two formulas *intend* the same metric but differ in
  edge handling — then arguing which is right — is semantic + domain reasoning.
- **Learn:** definition extraction → empirical divergence measurement → governed proposal.
- **Cost note:** extraction cached; divergence measured by running the SQL locally.
- **Maps to:** semantic-layer governance / "single source of truth" initiatives.

### 81. `recon-investigator` — chase the control-total mismatch ⭐⭐⭐ 🤖 🔌 💻
When source↔target totals disagree, investigate agentically: bisect by partition, then key
range, then transform step, comparing as it goes until the discrepancy is isolated to
specific rows and a specific step — then explain the mechanism (late rows? dup join? filter?).
- **Agentic core:** the bisection *strategy* adapts to what each probe reveals; a fixed
  script can't choose its next query based on findings.
- **Learn:** agentic search over data via MCP query tools; evidence-chain reporting.
- **Cost note:** all probes are local SQL; LLM plans the next probe and writes the conclusion.
- **Maps to:** reconciliation / audit (the hours-long manual chase, automated).

### 82. `rca-investigator` — root cause with an evidence chain ⭐⭐⭐ 🤖 🧠 🔌 ☁️
For a pipeline incident, pull every relevant signal — deploy history, config changes,
upstream data anomalies, infra events, log exceptions — test candidate hypotheses against
the timeline, and produce an RCA doc where every claim links to evidence.
- **Agentic core:** RCA is abductive reasoning across heterogeneous sources; correlation
  rules produce noise, and the synthesis into a coherent causal story is the hard part.
- **Learn:** multi-tool evidence gathering (MCP); hypothesis ranking; auditable conclusions.
- **Cost note:** signals fetched locally; API model for the synthesis pass.
- **Maps to:** AIOps / incident management.

### 83. `backfill-planner` — from incident window to ordered plan ⭐⭐⭐ 🤖 🔌 💻
Given "feed X loaded bad data from the 3rd to the 9th," walk lineage to find every affected
downstream asset, compute the correct reprocessing order, estimate cost/duration per step,
flag side effects (extracts already sent, SCD2 rows to repair) — and emit an executable,
reviewable plan.
- **Agentic core:** the plan depends on *kind* of corruption, each asset's load pattern, and
  consumer exposure — judgment over the lineage graph, not just traversal.
- **Learn:** lineage-driven planning; cost estimation; plan-as-reviewable-artifact.
- **Cost note:** graph work local; LLM reasons over the affected-asset summary.
- **Maps to:** incident remediation (today: a senior engineer's whiteboard afternoon).

### 84. `sla-forecaster` — call the breach before it happens ⭐⭐⭐ 🤖 💻 ☁️
Mid-run, predict tonight's SLA outcomes from current progress vs historical run profiles;
when a breach looms, recommend preemptive actions — scale the cluster, reorder the queue,
notify the consumer — each with expected impact.
- **Agentic core:** the forecast is stats; choosing the *intervention* requires weighing
  cost, downstream criticality, and contention across the whole night's schedule.
- **Learn:** run-profile modeling; decision support with explicit tradeoffs.
- **Cost note:** monitoring local; LLM invoked only when a breach is forecast.
- **Maps to:** SLA management / batch operations.

### 85. `spark-tuner` — performance fixes as validated PRs ⭐⭐⭐ 🤖 💻 ☁️
Read Spark event logs and query plans; diagnose skew, bad partitioning, missed broadcasts,
spill; propose fixes as config/code PRs; validate each by an A/B run on sample data before
the PR is opened — claims backed by measured numbers.
- **Agentic core:** plan-reading and diagnosis is expert pattern recognition over messy
  evidence; the propose→test→measure loop makes it trustworthy.
- **Learn:** Spark internals via event-log analysis; self-validating recommendation agents.
- **Cost note:** A/B runs on samples; LLM reasons over plan summaries.
- **Maps to:** compute FinOps / pipeline performance.

### 86. `quarantine-adjudicator` — triage the reject pile ⭐⭐⭐ 🤖 🧠 💻
Quarantined records accumulate and nobody looks. This agent clusters them by failure cause,
diagnoses each cluster (source bug? rule too strict? genuine bad data?), and proposes the
fix path — rule change, source ticket, or data patch — with rationale and projected impact.
- **Agentic core:** the rule-vs-source-vs-data judgment requires understanding what the rule
  *intends* versus what the data *means* — per cluster, with evidence.
- **Learn:** failure clustering; advisory remediation loops; keeping humans on the approve step.
- **Cost note:** clustering local; LLM diagnoses one representative per cluster.
- **Maps to:** DQ quarantine operations (the pile nobody triages).

### 87. `regression-bisector` — why did it get slow/wrong? ⭐⭐⭐ 🤖 💻
When a pipeline's runtime or output quietly degraded over weeks, bisect across the three
axes that change — code/config versions, data volume/shape, infra — re-running historical
versions against historical data snapshots until the cause is isolated.
- **Agentic core:** three interacting axes make naive git-bisect useless; the agent must
  design experiments that isolate one variable at a time and interpret ambiguous results.
- **Learn:** multi-axis bisection; reproducible historical re-runs (Iceberg time-travel + pinned config).
- **Cost note:** sample-sized re-runs; LLM plans the experiment sequence.
- **Maps to:** performance/result regression ops.

### 88. `env-drift-explainer` — why dev ≠ test ≠ prod ⭐⭐⭐ 🤖 💻
Same feed, different outputs per environment. The agent diffs everything that could matter
— config versions, engine versions, reference data, source snapshots, secrets/connection
targets — runs controlled comparisons, and names the culprit with evidence.
- **Agentic core:** the search space is large and heterogeneous; efficient narrowing
  requires reasoning about which differences *could* produce the observed divergence.
- **Learn:** systematic environment diffing; controlled-comparison methodology.
- **Cost note:** diffs and sample runs local; LLM directs the search.
- **Maps to:** environment management / release confidence.

### 89. `snapshot-debugger` — when did the data go wrong? ⭐⭐⭐ 🤖 💻
"This report was right last month." Bisect Iceberg snapshots through time-travel to find
the exact load where the number diverged, then drill into that load's inputs and transform
version to explain what happened.
- **Agentic core:** temporal bisection is mechanical; knowing *what to compare* at each
  snapshot (which aggregate, which slice) and interpreting the divergence is reasoning.
- **Learn:** time-travel as a debugging instrument; temporal root-cause workflows.
- **Cost note:** snapshot queries local; LLM interprets at each bisection step.
- **Maps to:** point-in-time history / audit investigations.

### 90. `drift-ripple-planner` — schema change, full consequence plan ⭐⭐⭐ 🤖 🔌 ☁️
When drift is detected (or a source announces a change), produce the complete ripple plan:
lake DDL evolution, affected transforms with proposed edits, contract version bumps,
consumer notifications, and the deployment order — as a reviewable change package.
- **Agentic core:** each downstream edit depends on how the change *semantically* interacts
  with that consumer's logic (a widened column is fine here, truncation risk there).
- **Learn:** lineage-guided multi-artifact change generation; change-package discipline.
- **Cost note:** lineage local; LLM reasons per affected artifact; bounded by blast radius.
- **Maps to:** schema-drift policy (the "what now?" after detection).

### 91. `dedup-refactorer` — kill the copy-paste transforms ⭐⭐⭐ 🤖 🧠 💻
Find semantically duplicated transform logic across hundreds of feeds (copy-pasted, then
diverged), determine whether divergences are intentional or drift, and propose shared
templates/macros with per-feed migration diffs.
- **Agentic core:** near-duplicate detection on *logic* (not text) plus the
  intentional-vs-accidental judgment call is semantic analysis rules can't make.
- **Learn:** semantic code clustering; safe consolidation proposals with proof-of-equivalence.
- **Cost note:** AST fingerprinting local; LLM compares cluster representatives.
- **Maps to:** item-store hygiene / shared-template governance.

### 92. `deprecation-planner` — retire the dead weight safely ⭐⭐⭐ 🤖 🔌 💻
Identify unused datasets/columns/extracts from query logs + lineage, distinguish truly-dead
from rarely-but-critically-used (the year-end statutory query!), and generate a staged
deprecation plan: consumer notices, grace periods, removal order, rollback points.
- **Agentic core:** "unused" is a judgment, not a count — seasonal access patterns and
  consumer criticality require interpretation; bad calls here cause outages.
- **Learn:** usage-evidence analysis; staged decommissioning playbooks.
- **Cost note:** log analysis local; LLM adjudicates the borderline assets.
- **Maps to:** storage FinOps / estate hygiene.

### 93. `number-change-detective` — why did this KPI move? ⭐⭐⭐ 🤖 🔌 ☁️
The CFO asks why persistency dropped 2 points. The agent traces the metric back through
the semantic layer, marts, loads, and source deltas; decomposes the change (mix shift?
data correction? late arrivals? logic change?); and answers with an evidence-based
attribution, not a shrug.
- **Agentic core:** change attribution is a multi-hypothesis investigation across lineage
  and time — the question every data team gets weekly and answers manually in days.
- **Learn:** metric decomposition; lineage-walking agents; executive-grade evidence summaries.
- **Cost note:** decomposition queries local; one API synthesis at the end.
- **Maps to:** consumption trust / "explain this number" service.

### 94. `access-explainer` — what can this role actually see? ⭐⭐⭐ 🤖 💻
Compose RBAC grants, ABAC tags, masking policies, and row filters into the *effective*
access per role, explained in plain language; flag toxic combinations, privilege creep,
and grants unused for months — as a continuous review aid.
- **Agentic core:** effective access emerges from interacting policy layers; explaining it
  to a certifier (and spotting "these two roles together re-identify SSNs") is reasoning.
- **Learn:** policy composition analysis; plain-language security explanation.
- **Cost note:** policy graph local; LLM writes the per-role narratives.
- **Maps to:** RBAC+ABAC governance / access certification.

### 95. `reident-tester` — attack your own masking ⭐⭐⭐ 🤖 💻
Adversarially attempt to re-identify masked/tokenized datasets: find quasi-identifier
combinations (ZIP + birth year + rare diagnosis), join against available reference data,
and report concrete leakage paths with affected-row counts and fixes.
- **Agentic core:** an attacker is creative; enumerating *plausible* attack joins and
  judging real-world identifiability requires adversarial reasoning, not k-anonymity math alone.
- **Learn:** privacy attack methodology (defensively); k-anonymity/l-diversity grounding.
- **Cost note:** join experiments local; LLM proposes attack hypotheses.
- **Maps to:** masking/tokenization assurance (test the control, not just deploy it).

### 96. `pia-drafter` — privacy impact assessment from evidence ⭐⭐⭐ 🤖 🧠 ☁️
For a new feed, draft the PIA from what the platform *already knows*: classifications
(what PII enters), lineage (where it flows), access policies (who sees it), retention
(how long it lives) — every assertion cited to platform metadata, gaps flagged for humans.
- **Agentic core:** a PIA is regulatory prose synthesized from technical facts; the agent
  turns metadata into compliance language while distinguishing known from unknown.
- **Learn:** metadata-grounded document generation; compliance-document structure.
- **Cost note:** facts are queries; one API drafting pass per assessment.
- **Maps to:** privacy compliance (GDPR/CCPA) / onboarding gates.

### 97. `audit-evidence-compiler` — the audit binder, assembled ⭐⭐⭐ 🤖 🔌 ☁️
Given an auditor's request list ("evidence of change approval for all prod config changes
in Q3"), interpret each request, gather the artifacts — run logs, PR approvals, lineage,
DQ results — and assemble cited evidence packets per control, noting anything missing.
- **Agentic core:** mapping auditor language to platform artifacts and judging evidence
  *sufficiency* is interpretation; the gathering itself spans many systems.
- **Learn:** requirement→artifact mapping; evidence-chain packaging for SOX/NAIC.
- **Cost note:** retrieval local; LLM interprets requests and writes packet summaries.
- **Maps to:** SOX/NAIC audit support (weeks of analyst time per audit).

### 98. `lineage-narrator` — the story of one number ⭐⭐⭐ 🤖 🧠 ☁️
For a single figure on a statutory report, produce the auditor-grade narrative of its
derivation: source systems → loads → transforms (business rules in plain language) →
aggregation — every step cited to lineage events, run logs, and code versions.
- **Agentic core:** raw lineage is an unreadable graph; the narrative — *what happened to
  the data and why, in order, in English* — is translation only an LLM does.
- **Learn:** graph-to-narrative generation; citation discipline at every claim.
- **Cost note:** lineage walk local; one drafting call per number; cache by report version.
- **Maps to:** statutory/regulatory reporting defense.

---

## H. Full systems (#99–123) 🏛️

Multi-component platforms — the "small tool" rule is **intentionally waived**. Each is a
product an enterprise would fund: several agents, a workflow, state, and a governance
surface. Many compose tools from sections E–G as building blocks. All follow the EDP
guardrails: deterministic core, AI overlay; advisory + severity-gated autonomy; audited;
local-LLM capable.

### 99. `etl-migration-factory` — retire the legacy ETL estate 🏛️ 🤖 ☁️
An agent fleet that converts an Informatica/DataStage estate into framework config + SQL:
inventory and parse every job, translate mappings per job, generate equivalence tests, run
old vs new on production samples, and track the whole migration on a dashboard — humans
approve per-job cutover.
- **Agentic core:** thousands of jobs × translate→test→repair loops; the equivalence
  harness is what makes machine translation trustworthy at estate scale.
- **Learn:** fleet orchestration; proprietary-format parsing; migration-as-pipeline.
- **Maps to:** ETL modernization programs (multi-year consulting engagements, compressed).

### 100. `mainframe-assimilator` — copybooks to governed feeds, end to end 🏛️ 🤖 🧠 ☁️
The legacy-onboarding pipeline as one system: copybook decoding (#50), EBCDIC parsing,
JCL flow reconstruction (#76), semantic field documentation (#51), draft contracts, and
generated feed packages — from tape-era artifacts to running, governed pipelines with a
human review gate at each stage.
- **Agentic core:** every stage needs semantic inference; the system chains them with
  review gates so confidence compounds instead of error.
- **Learn:** staged agent pipelines with human gates; the full legacy-to-modern path.
- **Maps to:** mainframe/COTS source onboarding (the EDP's hardest source class).

### 101. `platform-migration-copilot` — switch engines without faith 🏛️ 🤖 ☁️
Estate-scale warehouse migration (e.g., Vertica → Snowflake, per Appendix A): translate
all DDL/SQL (#72 at scale), plan the migration order from lineage, run dual-write
reconciliation during transition, and report readiness per workload — with rollback points.
- **Agentic core:** translation + verification + sequencing across thousands of objects,
  where each failure needs diagnosis and repair, not a stack trace.
- **Learn:** dual-run reconciliation architecture; migration sequencing from lineage.
- **Maps to:** the documented future-migration options — made executable.

### 102. `ma-data-assimilator` — absorb an acquired company's data 🏛️ 🤖 🧠 ☁️
For M&A: archaeology on the acquired estate (#74), entity matching to your canonical model
(#79 across companies), code-set alignment (#55), gap analysis, and generated integration
pipelines — with a workbench where integration architects review and approve mappings.
- **Agentic core:** two enterprises' models never align by name; the mapping is a thousand
  semantic judgments that today take an integration team a year.
- **Learn:** cross-estate semantic alignment; human-in-the-loop mapping workbenches.
- **Maps to:** M&A integration (insurance consolidates constantly).

### 103. `bi-rationalizer` — collapse 4,000 reports into 400 🏛️ 🤖 🧠 ☁️
Crawl the whole BI estate; extract metrics and audiences per report (#77); cluster
duplicates and near-duplicates; map everything to canonical semantic-layer metrics; and
produce a consolidation plan with usage evidence, owner sign-offs, and a migration tracker.
- **Agentic core:** "are these two reports the same?" is a semantic question times a
  million pairs; usage stats alone can't see that two differently-named reports answer
  the same business question.
- **Learn:** corpus-scale semantic clustering; consolidation governance workflow.
- **Maps to:** BI governance / semantic-layer adoption.

### 104. `estate-knowledge-graph` — the substrate every agent queries 🏛️ 🤖 🧠 🔌 💻
A continuously-updated knowledge graph of the data estate — datasets, columns, owners,
glossary terms, lineage, usage, incidents, contracts — built by extraction agents, queried
via graph-RAG, and exposed over MCP so every other agent (and human) asks it questions:
"who owns what feeds the claims dashboard, and what's changed there this month?"
- **Agentic core:** construction requires semantic extraction (linking terms↔columns,
  docs↔assets); consumption is graph-RAG — both are LLM-native problems.
- **Learn:** knowledge-graph construction agents; graph-RAG; MCP as the universal interface.
- **Maps to:** catalog/lineage/stewardship — unified into one queryable brain.

### 105. `semantic-layer-factory` — generate and *maintain* the semantic layer 🏛️ 🤖 🧠 ☁️
Bootstrap the governed semantic layer from marts + query logs + extracted report metrics
(#60/#77), then keep it alive: detect new query patterns that deserve promotion, flag
metrics drifting from their definition, propose updates as governed PRs.
- **Agentic core:** the bootstrap is semantic synthesis; the *maintenance* loop (watching
  usage, proposing evolution) is what no static tool does and why semantic layers rot.
- **Learn:** living-artifact maintenance agents; governed-PR proposal loops.
- **Maps to:** the EDP's semantic/curated consumption layer.

### 106. `data-product-foundry` — datasets in, data products out 🏛️ 🤖 🧠 ☁️
Turn a curated dataset into a full data product through an agent-assisted assembly line:
draft the contract from observed schema/usage (#62), generate documentation (#58/#43),
define SLAs from measured freshness (#69), create sample queries, register in the catalog
— with product-owner approval gates.
- **Agentic core:** productization is 80% writing (contracts, docs, examples) grounded in
  technical facts — synthesis work that's why teams never finish it manually.
- **Learn:** data-product/mesh operating model; assembly-line agent design.
- **Maps to:** data-product packaging on the consumption layer.

### 107. `contract-lifecycle-system` — contracts that actually live 🏛️ 🤖 🔌 ☁️
Data contracts as a managed lifecycle: drafted from evidence (#62), versioned in git,
enforced as pipeline gates, breach-detected at runtime — and when producers need to change,
an agent analyzes consumer impact, drafts the renegotiation proposal, and routes it to
affected parties.
- **Agentic core:** the negotiation loop — impact analysis, proposal drafting, consumer
  communication — is where contracts die today; it's language + reasoning work.
- **Learn:** contract enforcement architecture; producer/consumer negotiation workflows.
- **Maps to:** data contracts across the EDP's inbound and outbound boundaries.

### 108. `onboarding-concierge` — feed onboarding as a conversation 🏛️ 🤖 🧠 🔌 ☁️
Self-service onboarding, fully realized: the agent interviews the source SME in plain
language, inspects sample data as they talk, drafts the complete feed package (config,
contract, mappings #56, DQ rules #35), runs a sandbox load, walks the SME through the
results, and iterates until green — then submits the package for governed approval.
- **Agentic core:** the interview adapts to answers; drafts are grounded in live data
  inspection; the iterate-to-green loop is agency end to end.
- **Learn:** conversational agents driving real tool pipelines; sandbox-validated generation.
- **Maps to:** R8 self-service onboarding — the flagship EDP AI feature.

### 109. `self-healing-pipelines` — detect → diagnose → fix, governed 🏛️ 🤖 🔌 ☁️
The EDP's runtime-AI vision as a product: failures trigger diagnosis (#82), remediation
proposals are matched against runbooks (#71), low-severity known fixes auto-apply,
everything else becomes a PR for human approval — every action audited, autonomy
severity-gated per the platform's governance model.
- **Agentic core:** diagnosis and fix synthesis are reasoning; the governance wrapper
  (severity gates, audit, advisory-first) is what makes it deployable in an insurer.
- **Learn:** governed-autonomy architecture; the advisory→trusted-automation maturity path.
- **Maps to:** AIOps self-healing (P18/P19 made concrete).

### 110. `incident-war-room` — coordinated incident response 🏛️ 🤖 🔌 ☁️
On a major data incident, a coordinated agent team activates: RCA (#82), blast-radius
assessment via lineage, backfill planning (#83), stakeholder comms drafted per audience
(exec vs engineer vs consumer), and a postmortem draft with timeline — humans command,
agents staff the room.
- **Agentic core:** parallel specialist agents sharing evidence under time pressure;
  audience-specific communication; synthesis into one coherent response.
- **Learn:** multi-agent coordination with shared state; incident-management integration.
- **Maps to:** major-incident management for the data platform.

### 111. `quality-sentinel-network` — DQ that learns the business rhythm 🏛️ 🤖 🧠 💻
Beyond declared rules: per-feed learned expectations (seasonality-aware volumes,
distributions, relationship invariants), anomaly detection that knows month-end from
Monday, and incidents that arrive *triaged* — suspected cause, affected downstream
consumers, suggested response — feeding the steward queue (#119).
- **Agentic core:** learned expectations are stats; the triage (cause hypothesis, consumer
  impact, response) is the reasoning layer that turns alerts into action.
- **Learn:** expectation learning at fleet scale; alert→triaged-incident pipelines.
- **Maps to:** intelligent DQ across all feeds (R12 feature 4, productized).

### 112. `pipeline-portfolio-optimizer` — the whole night, optimized 🏛️ 🤖 💻
Treat the entire batch estate as one optimization problem: dependencies, SLAs, cluster
capacity, cost. Continuously propose schedule/resource changes — reorder queues, shift
non-critical loads, right-size clusters — with predicted SLA/cost impact, applied via
governed config PRs.
- **Agentic core:** the optimizer is OR/heuristics; explaining tradeoffs, handling
  exceptions ("month-end overrides this"), and negotiating SLA changes with owners is the
  agentic layer that makes it adoptable.
- **Learn:** global scheduling optimization; recommendation-with-explanation systems.
- **Maps to:** batch SLA management + compute FinOps, estate-wide.

### 113. `autonomous-finops-governor` — cost control with judgment 🏛️ 🤖 💻 ☁️
Continuous cost watch across EMR/EKS/Vertica/S3: attribute spend per feed/domain (#41 as a
component), detect anomalies and waste (unused assets #92, oversized clusters #85), propose
gated optimizations — storage tiering, schedule shifts, retention enforcement — each with
projected savings and risk, executed only through approval workflows.
- **Agentic core:** attribution is joins; deciding *what's safe to act on* and packaging
  optimizations with risk assessments is judgment over usage semantics.
- **Learn:** FinOps decision loops; savings-vs-risk framing; governed cost actions.
- **Maps to:** platform FinOps (R29), closed-loop.

### 114. `source-watchtower` — see upstream breakage coming 🏛️ 🤖 🧠 ☁️
Monitor everything upstream: vendor release notes and spec updates (RAG over their docs),
sandbox-environment extracts diffed against production expectations, announced COTS
upgrades mapped to your affected feeds — and open preemptive change tickets *before* the
breaking file lands in production.
- **Agentic core:** reading vendor prose and inferring "release 24.2's claim-status rework
  will break our fixed-width parser on field 31" is comprehension + impact reasoning.
- **Learn:** external-signal ingestion; predictive change management.
- **Maps to:** schema-drift policy, moved left of the failure.

### 115. `dsar-orchestrator` — subject rights, fulfilled and proven 🏛️ 🤖 🔌 ☁️
For a data-subject access/erasure request: resolve the person across systems (MDM + fuzzy
identity), find *all* their data via catalog + lineage + content scanning (including the
copies in extracts and archives), generate the access package or erasure plan, respect
legal holds, execute gated, and produce the compliance evidence trail.
- **Agentic core:** "find everything about this person" across a messy estate is iterative
  search + identity reasoning; missing one copy is a regulatory finding.
- **Learn:** estate-wide entity search; erasure vs legal-hold reconciliation; provable completeness.
- **Maps to:** GDPR/CCPA DSAR (today: weeks of manual hunting per request).

### 116. `reg-change-compliance-system` — regulations in, policy changes out 🏛️ 🤖 🧠 ☁️
Watch regulatory sources (NAIC bulletins, state regs, privacy law updates); RAG over new
requirements; map each to affected datasets, policies, and controls via the knowledge graph
(#104); draft the policy-config changes (the EDP's pluggable compliance rules); and track
adoption through to attestation.
- **Agentic core:** reading regulatory text and translating it to "these 14 datasets need
  retention extended to 10 years" is legal-to-technical translation — pure language work.
- **Learn:** regulatory-text RAG; requirement→control mapping; compliance traceability.
- **Maps to:** the extensible compliance policy model (R23), kept current automatically.

### 117. `retention-lifecycle-enforcer` — retention as a managed loop 🏛️ 🤖 💻
Map retention policies to physical assets across lake/warehouse/archives; continuously
detect violations (data past retention, orphaned copies) and conflicts (purge due but legal
hold active); plan gated purges with dependency awareness (don't break the SCD2 chain);
execute with evidence for auditors.
- **Agentic core:** policy-to-physical mapping is semantic (which assets *contain* claims
  data?); conflict resolution and safe purge sequencing require reasoning over lineage.
- **Learn:** policy-driven lifecycle automation; destructive-action governance done right.
- **Maps to:** retention + legal hold (R24), operationalized.

### 118. `access-governance-suite` — continuous access assurance 🏛️ 🤖 💻
Quarterly access reviews replaced by a continuous loop: effective-access explanation (#94)
per role/user, plain-language certification packets for managers, unused-grant cleanup
proposals, toxic-combination and privilege-creep detection, re-identification testing
(#95) on a schedule — findings routed as governed change requests.
- **Agentic core:** certifiers approve what they understand; translating policy math into
  reviewable language at org scale is the unlock that makes reviews real.
- **Learn:** continuous-compliance architecture; certification UX for non-engineers.
- **Maps to:** RBAC+ABAC governance (R22), as a running system.

### 119. `steward-command-center` — one queue, triaged with judgment 🏛️ 🤖 🧠 🔌 ☁️
Every platform event — DQ failures, drift alerts, SLA breaches, quarantine growth, access
findings, contract breaches — lands in one place, where agents deduplicate, correlate
("these five alerts are one upstream incident"), prioritize by business impact, attach
context and a drafted response, and route to the right steward. The inbox that makes
governance staffing scale.
- **Agentic core:** correlation and prioritization across heterogeneous events requires
  understanding what each event *means* for the business — judgment, not routing rules.
- **Learn:** event correlation agents; human-workload-shaped AI (triage, not takeover).
- **Maps to:** stewardship operations across all governance capabilities.

### 120. `analysis-copilot` — business questions, answered with proof 🏛️ 🤖 🧠 🔌 ☁️
Beyond text-to-SQL: decompose a vague business question into an analysis plan; choose
certified datasets (warning about freshness/known issues); generate and *verify* queries
(dry-run, sanity-check magnitudes against history, cross-check via a second path); answer
with caveats and full provenance — over the governed semantic layer, masked data only.
- **Agentic core:** plan→query→verify→caveat is a reasoning loop; naive text-to-SQL
  confidently returns wrong numbers, which is why enterprises don't trust it.
- **Learn:** verified-generation patterns; trust architecture for AI analytics.
- **Maps to:** chat-with-data (R12 feature 5), made trustworthy.

### 121. `data-request-desk` — the ad-hoc request firehose, managed 🏛️ 🤖 🔌 ☁️
Intake every "can you pull me…" request (Slack/email/portal); the agent clarifies intent
conversationally, checks whether a certified asset already answers it (deflecting
duplicates), self-serves governed extracts where policy allows (#120 + outbound engine),
and routes the rest to engineers with requirements already drafted — SLA-tracked.
- **Agentic core:** intent clarification, dedup against existing assets, and
  policy-checked self-service are each language + judgment problems.
- **Learn:** request-intake agents; deflection economics; governed self-service boundaries.
- **Maps to:** the ad-hoc workload that consumes every data team's sprint capacity.

### 122. `synthetic-environment-fabricator` — production-faithful test worlds 🏛️ 🤖 💻
Generate complete PII-free test environments: cross-table referential integrity, realistic
distributions, inferred business rules preserved (#66 at estate scale), temporal
consistency (policy lifecycles that make sense), targeted edge-case injection — refreshed
on demand so dev/test stop using masked production copies.
- **Agentic core:** business-rule inference and cross-entity consistency (a synthetic
  person's policy, claims, and payments must tell one coherent story) require semantic
  modeling of the domain from data.
- **Learn:** constraint-preserving synthesis at scale; test-data-as-a-service.
- **Maps to:** dev/test environments without PII exposure (R21 risk, eliminated).

### 123. `as-built-documentarian` — documentation that can't go stale 🏛️ 🤖 🧠 💻
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
