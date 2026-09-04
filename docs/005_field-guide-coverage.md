# 005 — Field-guide coverage: every concept, and what covers it

**Status:** plan · **Date:** 2026-09-04
**Source:** *Technical Field Guide v2 — STG · Senior Technologist* (interview
reference, 21 sections + method sections, 104 concept cards).

## The verdict

Yes — every card in the guide can be covered, and most of them by something that
runs on a laptop for free. The split is roughly:

| Track | What it is | Cards |
| --- | --- | --- |
| **F · Labs** (#50–#90, 41 new tools) | small tools that produce a measured number | 84 |
| **G · Notes** (N1–N6, markdown + prompts) | positions and trade-offs where no tool earns its keep | 20 |
| **Existing backlog** (#1–#49) | ideas already in `IDEAS.md`, some already built | 24 (shared) |

Cards are counted where their *primary* coverage sits; many are touched twice
(a note states the trade-off, a lab produces the number). Nothing is skipped —
the matrix below lists all 104.

## Why this shape

The guide is not a syllabus, it is a **detector**. Every card names a "tell": a
detail that people who did the work mention without being asked, and people who
only read never mention. A rank. A WER before and after. A p95 at a stated
concurrency. The rejection rate on generated data. `salting`. `q_proj`. The
alert you deleted.

That has one consequence for how to learn this, and it drives the whole plan:

> **Reading a card produces the vocabulary. Only running something produces the
> tell.** So every lab in section F must end by writing down a number that
> didn't exist before it ran.

Hence the **evidence card** — a JSONL record under `evidence/`, keyed by the
guide card, carrying: what was run, the configuration, the number, the baseline
it improved on, and what surprised you. It reuses the collection's existing data
seam (`Provenance` in `data-tools-core`), so `viva` (#90) can read the whole set
back and tell you which of the 104 cards you can still only *describe*.

The three practical constraints, stated honestly:

1. **GPU-dependent cards** — LoRA (#54), DPO (#56), vLLM (#62), quantization
   (#63). All are real at 135M–1.1B parameters on CPU, and the *mechanics* you
   are asked about — rank, alpha, target module names, continuous batching, KV
   cache arithmetic — are identical at that scale. Budget one or two rented GPU
   hours (~$3) for the runs where the comparison needs to be honest.
2. **Infrastructure cards** — Spark (#79–80), Kafka (#81), Kubernetes (#86–87),
   Terraform (#85). All run locally: PySpark in local mode, single-node
   Redpanda, `kind`, a local Terraform backend. The failure modes the guide asks
   about (skew, poison messages, OOMKill, state locking) reproduce faithfully at
   laptop scale — they are properties of the model, not of the cluster size.
3. **Cards that are genuinely a claim about experience** — operating a hundred
   clusters, a petabyte migration, real annotator panels. `fleet-conf` (#87) and
   `cutover-kit` (#84) give you the mechanism and the vocabulary; they do not
   give you the scale, and the guide's own advice is that saying so plainly is
   a *positive* signal. The notes are written to make that boundary easy to
   state: "here is what I built, here is where my experience stops."

## Coverage matrix

`§` numbers are the guide's sections. **CORE** marks the sections the req
actually requires; **BREADTH** the ones to cover only as far as your résumé
claims them.

### §1 · LLM foundations — CORE

| Card | Covered by |
| --- | --- |
| Token | #50 `token-ledger` · N1 |
| Context window | #50 `token-ledger` (drop policies) · N1 |
| Embedding | #53 `retrieval-bench` · #23 `embeddings-cache` · N1 |
| Temperature & sampling | #51 `decode-lab` · N1 |
| Hallucination | #51 `decode-lab` · #49 `ingest-ledger` (refusal path) · N1 |
| Structured output / function calling | #52 `schema-guard` · N1 |

### §2 · RAG & grounding — CORE

| Card | Covered by |
| --- | --- |
| The RAG pipeline | #1 `docs-rag` ✅ · #2 `repo-rag` ✅ · #53 `retrieval-bench` |
| Chunking | #25 `chunking-lab` · #2 `repo-rag` (AST-aware) ✅ |
| Hybrid search | #53 `retrieval-bench` (exact-code query set) · #2 `repo-rag` ✅ |
| Re-ranking | #53 `retrieval-bench` (two-stage, cost/benefit measured) |
| Grounding, citations & the empty case | #49 `ingest-ledger` ✅ (refuses when evidence is absent) · #1 `docs-rag` ✅ |

### §3 · Fine-tuning — CORE

| Card | Covered by |
| --- | --- |
| Decision triangle: prompt vs. RAG vs. fine-tune | N2 (written as "when I would not") |
| LoRA configuration — rank, alpha, target modules | #54 `lora-lab` |
| Catastrophic forgetting | #54 `lora-lab` (general held-out benchmark) |
| Training data prep & synthetic generation | #55 `synthdata-forge` (rejection rate) |
| Pre-training vs. fine-tuning vs. inference | #54 `lora-lab` · #64 `trainer-lab` (a small model genuinely trained from scratch) · N2 |

### §4 · RLHF & alignment — CORE

| Card | Covered by |
| --- | --- |
| The three stages | #56 `preference-forge` · N4 |
| DPO vs. PPO | #56 `preference-forge` (DPO run; PPO argued) · N4 |
| Preference data collection | #56 `preference-forge` (agreement measured) · N4 |

### §5 · Evaluation — CORE (highest-signal section)

| Card | Covered by |
| --- | --- |
| Golden set / eval set | #9 `eval-harness` · N5 |
| Retrieval metrics vs. generation metrics | #9 `eval-harness` (faithfulness vs. context precision) · #53 `retrieval-bench` · N5 |
| LLM-as-judge | #57 `judge-lab` (calibrated against human labels) |
| Task metrics vs. vibes | #57 `judge-lab` · #66 `tabular-lab` (hard metrics where they exist) |

### §6 · Agentic AI — CORE

| Card | Covered by |
| --- | --- |
| Agent vs. pipeline | #58 `agent-governor` (same task three ways) · N2 |
| The ReAct loop | #58 `agent-governor` (iteration ceiling, spend cap, cost per run) |
| Tool calling & MCP | #58 `agent-governor` (arg validation) · #16 `mcp-gateway` · #2 `repo-rag` ✅ · N3 (MCP as standardisation) |
| Memory & context management | #58 `agent-governor` (overflow + staleness) · #50 `token-ledger` |
| Frameworks: LangChain / LangGraph / crewAI / Pydantic AI | #58 `agent-governor` (chain vs. graph, built both) · N3 |
| Guardrails & human-in-the-loop | #58 `agent-governor` (read/write split, confirmation gates, audit log) |

### §7 · LLMOps — CORE

| Card | Covered by |
| --- | --- |
| Model version pinning & provider drift | #60 `model-pin` |
| Prompts as versioned artifacts | #59 `promptops` (eval gate blocks the merge) |
| Cost & token economics | #50 `token-ledger` · #24 `model-router` · #41 `finops-attributor` |
| Observability for LLM systems | #61 `llm-trace` (trace a complaint to the call) |
| Failure handling & degradation | #24 `model-router`, extended: timeouts, backoff, circuit breaking, shedding, degraded-but-useful fallback |

### §8 · LLM serving & inference

| Card | Covered by |
| --- | --- |
| KV cache | #62 `serve-bench` (cache-size calculator; concurrency ceiling) |
| Serving engines: vLLM, TGI, TensorRT-LLM | #62 `serve-bench` (continuous batching, PagedAttention, measured against naive) |
| Throughput vs. latency | #62 `serve-bench` (p50/p95/TTFT at stated concurrency) |
| Quantization | #63 `quant-check` (method, precision, quality delta) |
| Self-host vs. hosted API | #62 `serve-bench` (cost crossover) · N2 |
| Real-time, batch & streaming inference | #62 `serve-bench` (three modes) · #78 `job-runner` · N2 |

### §9 · ML & deep learning — CORE

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

### §10 · Classical & tabular ML

| Card | Covered by |
| --- | --- |
| Gradient boosting: XGBoost, LightGBM | #66 `tabular-lab` |
| Feature engineering & leakage | #66 `tabular-lab` (temporal leakage hunt) |
| Hyperparameter tuning | #66 `tabular-lab` (Optuna on validation; measured against feature work) |
| Class imbalance | #66 `tabular-lab` (threshold tuning as the lever) |
| Explainability: SHAP & feature importance | #66 `tabular-lab` (global vs. local) · #89 `fairness-audit` (appeal packet) |

### §11 · Speech & audio — BREADTH

| Card | Covered by |
| --- | --- |
| Word Error Rate (WER) | #67 `asr-bench` (baseline and after, per intervention) |
| Diarization & DER | #68 `diarize-id` (overlap, unknown speaker count) |
| Denoising & the audio front-end | #67 `asr-bench` (measured both ways — including where it hurt) |
| Speaker identification & enrolment | #68 `diarize-id` (false match vs. false reject curve) |
| Differential accuracy across speakers | #67 `asr-bench` (WER by group) · #89 `fairness-audit` |

### §12 · Computer vision — BREADTH

| Card | Covered by |
| --- | --- |
| Classification, detection, segmentation | #69 `vision-task-lab` (annotation time recorded per task) |
| CNNs vs. vision transformers | #69 `vision-task-lab` (data-hunger curve) |
| Multimodal vision-language models | #70 `doc-vlm-verify` (verification step; failure catalogue) |

### §13 · Recommenders & ranking — BREADTH

| Card | Covered by |
| --- | --- |
| Collaborative filtering & matrix factorization | #71 `recsys-lab` (implicit vs. explicit; negative sampling) |
| Cold start | #71 `recsys-lab` (fallbacks; long-tail coverage) |
| Attribution — proving it worked | #72 `ab-lift` (holdout design, power, offline↔online gap) |

### §14 · Knowledge graphs & text-to-SQL — BREADTH

| Card | Covered by |
| --- | --- |
| Knowledge graphs vs. vector retrieval | #73 `kg-hop` (the multi-hop query vectors can't answer) · #38 `lineage-explorer` |
| Stopping hallucinated schema | #74 `sql-safeguard` (catalogue validation, retry with the error, semantic layer) |
| Execution safety | #74 `sql-safeguard` (read-only first, EXPLAIN gate, limits, tenancy) · #11 `sqlite-mcp` |

### §15 · ML platform & serving

| Card | Covered by |
| --- | --- |
| Experiment tracking (MLflow, W&B) | #75 `runcard` (reproducibility contract) |
| Model registry & promotion | #75 `runcard` (approval gate, rollback drill) |
| Data drift vs. concept drift | #76 `drift-sentry` (PSI, KL, quantiles) |
| Ground-truth lag | #76 `drift-sentry` (lag registry; proxy monitoring) |
| Metrics systems can't store distributions | #76 `drift-sentry` (the scalar it emits, and why) |

### §16 · Python service layer

| Card | Covered by |
| --- | --- |
| The blocking-call-in-async trap | #77 `async-trap` (reproduced under rising concurrency) |
| Loading the model | #77 `async-trap` (memory × workers; readiness gated on load) |
| Validation at the boundary (Pydantic) | #52 `schema-guard` (schema-valid vs. semantically valid) |
| Long-running work & background jobs | #78 `job-runner` (idempotency; worker killed mid-task) |

### §17 · Spark & Databricks — BREADTH

| Card | Covered by |
| --- | --- |
| Execution model & lazy evaluation | #79 `spark-clinic` (stage timings from the event log) |
| Data skew | #79 `spark-clinic` (poisoned key; salting, broadcast, hot-key isolation, AQE) |
| Shuffle, partitions & broadcast joins | #79 `spark-clinic` (including a broadcast that OOMs the driver) |
| Parquet, Delta & maintenance operations | #80 `delta-keeper` (pushdown measured; OPTIMIZE/ZORDER/VACUUM; time-travel drill) |
| Scala vs. PySpark | #79 `spark-clinic` (UDF serialisation benchmark) |

### §18 · Pipelines & streaming — BREADTH

| Card | Covered by |
| --- | --- |
| Batch vs. streaming | #81 `stream-lab` · N2 (the case for choosing batch) |
| Kafka: topics, partitions, consumer groups | #81 `stream-lab` (ordering within a partition; idle consumers) |
| Poison messages & dead letter queues | #81 `stream-lab` · #78 `job-runner` (DLQ, alerting, replay) |
| CDC, MERGE & idempotency | #82 `backfill-drill` (atomic marker; re-run proves stable counts) · #39 `cdc-inspector` |
| Data quality & schema evolution | #19 `data-contract-linter` · #27 `schema-drift-detector` · #35 `dq-rule-suggester` — extended with hard gates that stop the pipeline and a reject table carrying reasons |

### §19 · Cloud & migration — BREADTH

| Card | Covered by |
| --- | --- |
| Spot instances & interruption handling | #83 `spot-runner` (reclamation; work lost; recovery time) |
| Large migrations & cutover | #84 `cutover-kit` (dual-write, reconciliation, tested rollback) · #28 `load-reconciler` |
| Cost optimisation — the real levers | #83 `spot-runner` · #41 `finops-attributor` (levers named, baseline stated, one-off vs. recurring) |
| Terraform & infrastructure as code | #85 `deploy-kit` (remote state, locking, drift detection) |
| CI/CD | #85 `deploy-kit` (gates that block a merge) |

### §20 · Kubernetes at scale — BREADTH

| Card | Covered by |
| --- | --- |
| Operating vs. deploying onto | #86 `k8s-lab` (OOMKill, crash loop, probes, rollback — provoked) |
| Multi-cluster & fleet management | #87 `fleet-conf` (config drift, central policy, cost per cluster) |
| Observability & alert discipline | #87 `fleet-conf` (SLO alerts; the one you deleted) · #61 `llm-trace` |

### §21 · AI security & compliance — CORE

| Card | Covered by |
| --- | --- |
| PII detection & redaction | #20 `pii-scanner` — extended to redact **before the model call and before logging** · #61 `llm-trace` |
| Guardrails & jailbreak resistance | #88 `jailbreak-range` (bypass rate *and* false-positive rate) |
| Bias, fairness & differential performance | #89 `fairness-audit` (disaggregated metrics) · #67 `asr-bench` |
| Human-in-the-loop as a control | #89 `fairness-audit` (threshold, review capacity, audit trail) · #58 `agent-governor` |

### Method sections (how the guide is used)

| Card | Covered by |
| --- | --- |
| Reading depth / the depth ladder | N6 · #90 `viva` (drills rung 3 and rung 4) |
| The calibration bar | N6 (the shape of a strong answer, applied to my own) |
| Reading by role level | N6 (Specialist Programmer vs. Senior Technologist) |
| Floor questions | N6 (each answered in one line) · #90 `viva` |
| Universal red flags | N6 (audited against my own résumé bullets) |
| Writing it up | #90 `viva` (drafts the defensible one-liner per concept) |

## What this is not

- **Not a shortcut past experience.** Running `lora-lab` at 135M parameters
  lets you say "rank 16, alpha 32, `q_proj`/`v_proj`, 1,200 examples, and here
  is what it broke" — truthfully, about your own lab. It does not let you claim
  production fine-tuning, and the guide is explicit that the claim without the
  numbers is what destroys credibility. Every evidence card records the scale it
  was produced at, so the honest sentence is always available.
- **Not sequential.** Sections F and G are independent, like the rest of the
  backlog. The build order in `IDEAS.md` is a suggestion weighted toward the
  CORE sections.
- **Not final.** New cards get added to the matrix as the guide is revised;
  `viva` (#90) fails loudly on any card with no evidence behind it, which is the
  point.
