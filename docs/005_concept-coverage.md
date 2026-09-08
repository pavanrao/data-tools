# 005 — Concept coverage: what to build to learn the AI/data stack

**Status:** plan · **Date:** 2026-09-04

A working map of the concepts that recur across AI and data engineering — 98 of
them, in 21 groups — and, for each one, the smallest thing in this collection
that exercises it for real. It exists so that learning this stack is a build
queue rather than a reading list.

## The verdict

Every concept on the map can be covered, and most of them by something that runs
on a laptop for free. The split is roughly:

| Track | What it is | Concepts |
| --- | --- | --- |
| **F · Labs** (#50–#90, 41 new tools) | small tools that produce a measured number | 84 |
| **G · Notes** (N1–N5, markdown + prompts) | positions and trade-offs where no tool earns its keep | 14 |
| **Existing backlog** (#1–#49) | ideas already in `IDEAS.md`, some already built | 24 (shared) |

Concepts are counted where their *primary* coverage sits; many are touched twice
(a note states the trade-off, a lab produces the number). Nothing is skipped —
the matrix below lists all 98.

## Why this shape

Most of these concepts have a detail that only appears once you have run
something: the rank you had to pick, the WER before and after, the p95 at a
stated concurrency, the fraction of generated data that failed verification,
`salting`, `q_proj`, the alert you deleted. Reading produces the vocabulary;
running produces the detail. So:

> **Every lab in section F ends by writing down a number that didn't exist
> before it ran.**

Hence the **evidence card** — a JSONL record under `evidence/`, keyed by the
concept, carrying: what was run, the configuration, the number, the baseline it
improved on, and what surprised you. It reuses the collection's existing data
seam (`Provenance` in `data-tools-core`), so `evidence-index` (#90) can read the
whole set back, report which concepts still have no measurement behind them, and
render the ones that do.

The three practical constraints, stated honestly:

1. **GPU-dependent concepts** — LoRA (#54), DPO (#56), vLLM (#62), quantization
   (#63). All are real at 135M–1.1B parameters on CPU, and the mechanics —
   rank, alpha, target module names, continuous batching, KV cache arithmetic —
   are identical at that scale. Budget one or two rented GPU hours (~$3) for the
   runs where a comparison needs to be honest.
2. **Infrastructure concepts** — Spark (#79–80), Kafka (#81), Kubernetes
   (#86–87), Terraform (#85). All run locally: PySpark in local mode, single-node
   Redpanda, `kind`, a local Terraform backend. The failure modes worth learning
   (skew, poison messages, OOMKill, state locking) reproduce faithfully at laptop
   scale — they are properties of the model, not of the cluster size.
3. **Concepts that are really a claim about scale** — operating a hundred
   clusters, a petabyte migration, real annotator panels. `fleet-conf` (#87) and
   `cutover-kit` (#84) give you the mechanism and the vocabulary; they do not
   give you the scale. Every evidence card records the scale its number was
   produced at, so the write-up can be exact about what was demonstrated.

## Showcasing the work

Not every lab deserves an audience. A lab is **showcase-grade** when all five
hold — and `evidence-index` (#90) checks the first four mechanically:

1. **A number with a baseline.** "38% WER → 21% WER on 4 hours of noisy audio",
   not "improved transcription quality".
2. **One command reproduces it.** `make demo` or a single `uv run …`, on a
   machine with nothing special installed.
3. **A README that leads with the result** and states the scale it was measured
   at, then explains the mechanism.
4. **Tests that run with nothing optional installed** (`CONVENTIONS.md` rule 6).
5. **A failure it can show you**, not just a success — the skew that stalls, the
   endpoint that collapses under load, the quantized model that got worse.

Two ways to show it, and they compose:

- **In place.** `evidence-index` renders the showcase page from the evidence
  cards; the repo README links it. Cheapest, and it stays current because it is
  generated from the runs rather than written by hand.
- **Spun out.** Each tool is already a standalone distribution, so
  `git subtree split -P tools/<name>` (history intact) → push → delete the one
  `[tool.uv.sources]` block gives a polished single-purpose repo with its own
  README and CI. See [`000` §5](000_project-organization.md#5-the-spin-out-seam).
  Good first picks, each self-contained and showing something in under a
  minute: `retrieval-bench` (#53), `spark-clinic`
  (#79), `async-trap` (#77), `sql-safeguard` (#74), `drift-sentry` (#76) — plus
  `ingest-ledger`, which is already built and already ends its demo by refusing
  to answer.

## The other axis

This map answers *which AI concepts do I have a measured tool for*. Sections **H–J**
of `IDEAS.md` are written along a second axis — *which enterprise data-engineering
problems do I have a tool for* — and are mapped in
[`008_data-engineering-coverage.md`](008_data-engineering-coverage.md).

Ideas from H–J appear in **both**, against different cards: `#93 vendor-spec-reader`
is *§2 The RAG pipeline* here and *§A Source onboarding* there. Each H–J entry
carries a `Learn:` line (the AI concept, mapped here) and a `Maps to:` line (the
data problem, mapped there). In sections A–G the two collapse into one, which is
why this map alone was enough until those sections arrived.

## Coverage matrix

`§` numbers group the concept map. **Spine** marks the groups almost any tool in
this collection ends up touching; **Adjacent** marks the domains worth picking up
when a specific piece of work needs them. Neither is a difficulty rating.

### §1 · LLM foundations — Spine

| Card | Covered by |
| --- | --- |
| Token | #50 `token-ledger` · N1 · #25 `chunking-lab` ✅ (token vs character, and why its metrics count characters) |
| Context window | #50 `token-ledger` (drop policies) · N1 |
| Embedding | #53 `retrieval-bench` · #23 `embeddings-cache` · N1 · #25 `chunking-lab` ✅ (semantic chunking; embeddings placing boundaries rather than retrieving) |
| Temperature & sampling | #51 `decode-lab` · N1 |
| Hallucination | #51 `decode-lab` · #49 `ingest-ledger` (refusal path) · N1 |
| Structured output / function calling | #52 `schema-guard` · N1 · #93 `vendor-spec-reader`, #106 `contract-from-docs` (schema-constrained JSON as the *deliverable*, not a convenience) |
| **Deterministic core, optional model** | #49 `ingest-ledger` ✅ · #25 `chunking-lab` ✅ (Tier 0 runs with nothing installed) · #94 `copybook-decoder`, #96 `fixed-width-inferrer` (deterministic parse, LLM only for the semantics it cannot reach) — *where the model is **not** the answer, and what you gain by keeping it optional* · **all of section K** 🔒 — every entry states what a deterministic tool already catches, so the model's share is explicit |

### §2 · RAG & grounding — Spine

*`chunking-lab` (#25) is closed. Its two open threads are tagged below as
**#91 `context-aug-lab`** (Tier 2 — late chunking and contextual retrieval, which
cannot share #25's model-free default) and **#92 `adaptive-chunk`** (reproduce the
published per-document recommender, then check it beats a fixed strategy).*

| Card | Covered by |
| --- | --- |
| The RAG pipeline | #1 `docs-rag` ✅ · #2 `repo-rag` ✅ · #53 `retrieval-bench` · #91 `context-aug-lab` (the augmentation half — what changes when the cuts stay put and the *unit* changes) · #93 `vendor-spec-reader` (RAG over a 200-page spec, answers traced to the page they came from) |
| Chunking | #25 `chunking-lab` ✅ (six families, character-level scoring, Precision Ω reproduced against a published table) · #2 `repo-rag` (AST-aware) ✅ · #92 `adaptive-chunk` (per-document strategy selection, reproduced from LREC 2026 and tested against a fixed baseline) · #91 `context-aug-lab` (family 6, which moves no boundaries at all) |
| Hybrid search | #53 `retrieval-bench` (exact-code query set) · #2 `repo-rag` ✅ · #25 `chunking-lab` ✅ (BM25 vs vector vs RRF hybrid, and *how much* the retriever axis moves things against the chunker axis) |
| Re-ranking | #53 `retrieval-bench` (two-stage, cost/benefit measured) · #91 `context-aug-lab` (contextual retrieval vs late chunking, where the vendor and independent numbers disagree) |
| Grounding, citations & the empty case | #49 `ingest-ledger` ✅ (refuses when evidence is absent) · #1 `docs-rag` ✅ · #126 `rca-investigator`, #142 `lineage-narrator` (an evidence chain is the product, not a footnote) |

### §3 · Fine-tuning — Spine

| Card | Covered by |
| --- | --- |
| Decision triangle: prompt vs. RAG vs. fine-tune | N2 (written as "when I would not") |
| LoRA configuration — rank, alpha, target modules | #54 `lora-lab` |
| Catastrophic forgetting | #54 `lora-lab` (general held-out benchmark) |
| Training data prep & synthetic generation | #55 `synthdata-forge` (rejection rate) |
| Pre-training vs. fine-tuning vs. inference | #54 `lora-lab` · #64 `trainer-lab` (a small model genuinely trained from scratch) · N2 |

### §4 · RLHF & alignment — Spine

| Card | Covered by |
| --- | --- |
| The three stages | #56 `preference-forge` · N4 |
| DPO vs. PPO | #56 `preference-forge` (DPO run; PPO argued) · N4 |
| Preference data collection | #56 `preference-forge` (agreement measured) · N4 |

### §5 · Evaluation — Spine (measure first)

| Card | Covered by |
| --- | --- |
| Golden set / eval set | #9 `eval-harness` · N5 · #25 `chunking-lab` ✅ (gold *spans*; quote-then-locate, and yield as the honest failure mode) |
| Retrieval metrics vs. generation metrics | #9 `eval-harness` (faithfulness vs. context precision) · #53 `retrieval-bench` · N5 · #25 `chunking-lab` ✅ (chunk-level vs character-level; why recall alone scores a useless chunker 100%) · #91 `context-aug-lab` · #92 `adaptive-chunk` (both reuse #25's corpora, gold spans and metrics rather than inventing their own) |
| LLM-as-judge | #57 `judge-lab` (calibrated against human labels) |
| Task metrics vs. vibes | #57 `judge-lab` · #66 `tabular-lab` (hard metrics where they exist) |
| **Calibrated confidence & honest uncertainty** | #95 `column-semantics-tagger`, #97 `null-semantics-detective`, #118 `db-archaeologist` (confidence-ranked output routed to human review) · #25 `chunking-lab` ✅ (the *yield* a weak model produces, reported rather than hidden) — *saying how sure you are, in a way a reader can act on* · #172 `dependency-truth-checker`, #182 `orphan-asset-finder` (naming the blind spot, and declining to recommend deletion into it) |

### §6 · Agentic AI — Spine

| Card | Covered by |
| --- | --- |
| Agent vs. pipeline | #58 `agent-governor` (same task three ways) · N2 |
| The ReAct loop | #58 `agent-governor` (iteration ceiling, spend cap, cost per run) · #118 `db-archaeologist` (hypothesis → test → revise, over a database nobody understands) |
| Tool calling & MCP | #58 `agent-governor` (arg validation) · #16 `mcp-gateway` · #2 `repo-rag` ✅ · N3 (MCP as standardisation) · #148 `estate-knowledge-graph` (the substrate every other agent queries) |
| Memory & context management | #58 `agent-governor` (overflow + staleness) · #50 `token-ledger` |
| Frameworks: LangChain / LangGraph / crewAI / Pydantic AI | #58 `agent-governor` (chain vs. graph, built both) · N3 |
| Guardrails & human-in-the-loop | #58 `agent-governor` (read/write split, confirmation gates, audit log) · #123 `match-merge-adjudicator`, #130 `quarantine-adjudicator`, #163 `steward-command-center` (the gray zone routed to a human, with the evidence attached) |

### §7 · LLMOps — Spine

| Card | Covered by |
| --- | --- |
| Model version pinning & provider drift | #60 `model-pin` |
| Prompts as versioned artifacts | #59 `promptops` (eval gate blocks the merge) |
| Cost & token economics | #50 `token-ledger` · #24 `model-router` · #41 `finops-attributor` |
| Observability for LLM systems | #61 `llm-trace` (trace a complaint to the call) |
| Failure handling & degradation | #24 `model-router`, extended: timeouts, backoff, circuit breaking, shedding, degraded-but-useful fallback |

### §8 · LLM serving & inference — Adjacent

| Card | Covered by |
| --- | --- |
| KV cache | #62 `serve-bench` (cache-size calculator; concurrency ceiling) |
| Serving engines: vLLM, TGI, TensorRT-LLM | #62 `serve-bench` (continuous batching, PagedAttention, measured against naive) |
| Throughput vs. latency | #62 `serve-bench` (p50/p95/TTFT at stated concurrency) |
| Quantization | #63 `quant-check` (method, precision, quality delta) |
| Self-host vs. hosted API | #62 `serve-bench` (cost crossover) · N2 |
| Real-time, batch & streaming inference | #62 `serve-bench` (three modes) · #78 `job-runner` · N2 |

### §9 · ML & deep learning — Spine

| Card | Covered by |
| --- | --- |
| Training, loss & the training loop | #64 `trainer-lab` (loss curves, early stopping) |
| Train / validation / test split & leakage | #64 `trainer-lab` · #66 `tabular-lab` (deliberate leakage experiment) |
| Precision, recall & why accuracy lies | #66 `tabular-lab` · #65 `taxonomy-classifier` (per-category) |
| Large label spaces & hierarchical classification | #65 `taxonomy-classifier` (four architectures compared) |
| Transformers & attention | #64 `trainer-lab` (attention visualisation, RNN contrast) |
| Encoder, decoder, encoder-decoder | #64 `trainer-lab` (one task, three architectures) |
| PyTorch vs. TensorFlow | #64 `trainer-lab` · N3 (same model in both, preference with a reason) |
| Rules vs. machine learning | #65 `taxonomy-classifier` (rules baseline) · #35 `dq-rule-suggester` · N2 |

### §10 · Classical & tabular ML — Spine

| Card | Covered by |
| --- | --- |
| Gradient boosting: XGBoost, LightGBM | #66 `tabular-lab` |
| Feature engineering & leakage | #66 `tabular-lab` (temporal leakage hunt) |
| Hyperparameter tuning | #66 `tabular-lab` (Optuna on validation; measured against feature work) |
| Class imbalance | #66 `tabular-lab` (threshold tuning as the lever) |
| Explainability: SHAP & feature importance | #66 `tabular-lab` (global vs. local) · #89 `fairness-audit` (appeal packet) |

### §11 · Speech & audio — Adjacent

| Card | Covered by |
| --- | --- |
| Word Error Rate (WER) | #67 `asr-bench` (baseline and after, per intervention) |
| Diarization & DER | #68 `diarize-id` (overlap, unknown speaker count) |
| Denoising & the audio front-end | #67 `asr-bench` (measured both ways — including where it hurt) |
| Speaker identification & enrolment | #68 `diarize-id` (false match vs. false reject curve) |
| Differential accuracy across speakers | #67 `asr-bench` (WER by group) · #89 `fairness-audit` |

### §12 · Computer vision — Adjacent

| Card | Covered by |
| --- | --- |
| Classification, detection, segmentation | #69 `vision-task-lab` (annotation time recorded per task) |
| CNNs vs. vision transformers | #69 `vision-task-lab` (data-hunger curve) |
| Multimodal vision-language models | #70 `doc-vlm-verify` (verification step; failure catalogue) |

### §13 · Recommenders & ranking — Adjacent

| Card | Covered by |
| --- | --- |
| Collaborative filtering & matrix factorization | #71 `recsys-lab` (implicit vs. explicit; negative sampling) |
| Cold start | #71 `recsys-lab` (fallbacks; long-tail coverage) |
| Attribution — proving it worked | #72 `ab-lift` (holdout design, power, offline↔online gap) |

### §14 · Knowledge graphs & text-to-SQL — Adjacent

| Card | Covered by |
| --- | --- |
| Knowledge graphs vs. vector retrieval | #73 `kg-hop` (the multi-hop query vectors can't answer) · #38 `lineage-explorer` |
| Stopping hallucinated schema | #74 `sql-safeguard` (catalogue validation, retry with the error, semantic layer) |
| Execution safety | #74 `sql-safeguard` (read-only first, EXPLAIN gate, limits, tenancy) · #11 `sqlite-mcp` |

### §15 · ML platform & serving — Spine

| Card | Covered by |
| --- | --- |
| Experiment tracking (MLflow, W&B) | #75 `runcard` (reproducibility contract) |
| Model registry & promotion | #75 `runcard` (approval gate, rollback drill) |
| Data drift vs. concept drift | #76 `drift-sentry` (PSI, KL, quantiles) |
| Ground-truth lag | #76 `drift-sentry` (lag registry; proxy monitoring) |
| Metrics systems can't store distributions | #76 `drift-sentry` (the scalar it emits, and why) |

### §16 · Python service layer — Spine

| Card | Covered by |
| --- | --- |
| The blocking-call-in-async trap | #77 `async-trap` (reproduced under rising concurrency) |
| Loading the model | #77 `async-trap` (memory × workers; readiness gated on load) |
| Validation at the boundary (Pydantic) | #52 `schema-guard` (schema-valid vs. semantically valid) |
| Long-running work & background jobs | #78 `job-runner` (idempotency; worker killed mid-task) |

### §17 · Spark & Databricks — Spine

| Card | Covered by |
| --- | --- |
| Execution model & lazy evaluation | #79 `spark-clinic` (stage timings from the event log) |
| Data skew | #79 `spark-clinic` (poisoned key; salting, broadcast, hot-key isolation, AQE) |
| Shuffle, partitions & broadcast joins | #79 `spark-clinic` (including a broadcast that OOMs the driver) |
| Parquet, Delta & maintenance operations | #80 `delta-keeper` (pushdown measured; OPTIMIZE/ZORDER/VACUUM; time-travel drill) |
| Scala vs. PySpark | #79 `spark-clinic` (UDF serialisation benchmark) |

### §18 · Pipelines & streaming — Spine

| Card | Covered by |
| --- | --- |
| Batch vs. streaming | #81 `stream-lab` · N2 (the case for choosing batch) |
| Kafka: topics, partitions, consumer groups | #81 `stream-lab` (ordering within a partition; idle consumers) |
| Poison messages & dead letter queues | #81 `stream-lab` · #78 `job-runner` (DLQ, alerting, replay) |
| CDC, MERGE & idempotency | #82 `backfill-drill` (atomic marker; re-run proves stable counts) · #39 `cdc-inspector` |
| Data quality & schema evolution | #19 `data-contract-linter` · #27 `schema-drift-detector` · #35 `dq-rule-suggester` — extended with hard gates that stop the pipeline and a reject table carrying reasons |

### §19 · Cloud & migration — Adjacent

| Card | Covered by |
| --- | --- |
| Spot instances & interruption handling | #83 `spot-runner` (reclamation; work lost; recovery time) |
| Large migrations & cutover | #84 `cutover-kit` (dual-write, reconciliation, tested rollback) · #28 `load-reconciler` |
| Cost optimisation — the real levers | #83 `spot-runner` · #41 `finops-attributor` (levers named, baseline stated, one-off vs. recurring) |
| Terraform & infrastructure as code | #85 `deploy-kit` (remote state, locking, drift detection) |
| CI/CD | #85 `deploy-kit` (gates that block a merge) |

### §20 · Kubernetes at scale — Adjacent

| Card | Covered by |
| --- | --- |
| Operating vs. deploying onto | #86 `k8s-lab` (OOMKill, crash loop, probes, rollback — provoked) |
| Multi-cluster & fleet management | #87 `fleet-conf` (config drift, central policy, cost per cluster) |
| Observability & alert discipline | #87 `fleet-conf` (SLO alerts; the one you deleted) · #61 `llm-trace` |

### §21 · AI security & compliance — Spine

| Card | Covered by |
| --- | --- |
| PII detection & redaction | #20 `pii-scanner` — extended to redact **before the model call and before logging** · #61 `llm-trace` · #117 `sample-redactor`, #139 `reident-tester` (attack your own masking), #166 `synthetic-environment-fabricator` |
| Guardrails & jailbreak resistance | #88 `jailbreak-range` (bypass rate *and* false-positive rate) |
| Bias, fairness & differential performance | #89 `fairness-audit` (disaggregated metrics) · #67 `asr-bench` |
| Human-in-the-loop as a control | #89 `fairness-audit` (threshold, review capacity, audit trail) · #58 `agent-governor` · #140 `pia-drafter`, #141 `audit-evidence-compiler` (evidence assembled for a human to sign) |

## What this is not

- **Not a substitute for scale.** Running `lora-lab` at 135M parameters teaches
  you rank, alpha, `q_proj`/`v_proj`, and what a narrow fine-tune breaks. It does
  not teach you what a 70B run costs to schedule, and the evidence card records
  the scale so nothing has to be implied.
- **Not sequential.** Sections F and G are independent, like the rest of the
  backlog. The build order in `IDEAS.md` is a suggestion weighted toward the
  spine.
- **Not final.** Concepts get added to the matrix as the map grows;
  `evidence-index` (#90) reports loudly on any concept with no measurement
  behind it, which is the point.
