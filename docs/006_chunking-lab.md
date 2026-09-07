# 006 — chunking-lab

**Idea #25.** Take one corpus, run it through many chunking strategies, and score
each one *at the character level against gold spans* — so the number reflects
where the cuts landed, not how good the retriever or the model happened to be.

The user-facing reference, the research behind every choice, and the sixteen
decisions live in [`tools/chunking-lab/README.md`](../tools/chunking-lab/README.md).
This document is the design record: what is built, how each part works, and why
it is shaped that way. Per `docs/000` §9 the numbered doc holds the design; the
README holds the usage.

**Status.** All six Tier 0 chunkers, both Tier 1 semantic chunkers, and the
invariant that governs them. The metrics, the hostile corpus, and `score` are not
built yet — see the checklist in README §13.

## Pipeline

```
document ─▶ chunker ─▶ Chunking(spans, provenance, strategy)
                           │
                           ├─▶ invariant.check   (always; a violation is a chunker bug)
                           ├─▶ intrinsic metrics (query-free)          [not built]
                           └─▶ retrieve ─▶ extrinsic metrics vs gold   [not built]
                                             precision_omega, iou, precision, recall
```

## Modules (`tools/chunking-lab/src/chunking_lab/`)

- **`spans.py`** — `Span` and `Chunking`. A chunk is a **character range**, not a
  string. `Span` carries `start`/`end` plus `retrieval_text` (what gets indexed)
  and `return_text` (what reaches the model); `Chunking` bundles the spans with
  their `Provenance`, the strategy spec, the declared overlap, and two flags —
  `lossless` and `augmented` — that the invariant checks against.
- **`invariant.py`** — `check` enforces five properties and raises
  `InvariantViolation`; `coverage` reports the fraction of the document present in
  at least one span. See the design note below on why they are separate.
- **`chunkers/base.py`** — the `Chunker` protocol, the `LengthFn` alias, and
  `trim`, the shared whitespace-trim that reproduces the reference
  implementation's boundary behaviour.
- **`chunkers/fixed.py`** — `FixedChunker`: equal character windows, optional
  overlap. The baseline every other strategy has to beat.
- **`chunkers/recursive.py`** — `RecursiveChunker`: split on the highest-priority
  separator present, recurse into anything still too big, then merge back up to
  the size budget. A port of the reference `RecursiveTokenChunker`.
- **`chunkers/structural.py`** — `SentenceChunker` packs N sentences per chunk;
  `MarkdownHeaderChunker` splits at ATX headings **while respecting fenced code
  blocks**, so a `#` comment inside a fence is not mistaken for a section break.
  Getting that wrong shreds every code example in a document and never shows up
  in an average chunk size.
- **`chunkers/context.py`** — family 6. `SentenceWindowChunker` indexes one
  sentence and returns it with its neighbours; `ParentDocumentChunker` indexes a
  small child and returns the enclosing block. Both set `augmented=True`, and both
  are Tier 0 — needing no model is what makes them a good early test of the
  `Span` design rather than a special case bolted on later.
- **`embeddings.py`** — the Tier 1 seam. An `Embedder` protocol (batched, because
  Tier 1 embeds every sentence in the corpus), a `HashingEmbedder` that is
  deterministic, offline and deliberately weak, and a `ProviderEmbedder` that
  resolves `data_tools_core.llm` **lazily** so constructing a chunker never needs
  the extra. Every embedder reports an `id`.
- **`chunkers/semantic.py`** — Tier 1. `PercentileSemanticChunker` cuts where the
  distance between adjacent sentences exceeds the Nth percentile of the
  document's *own* distances; `ClusterSemanticChunker` solves for the partition
  maximising total within-chunk similarity by dynamic programming, subject to a
  size cap.
- **`chunkers/__init__.py`** — `from_spec` parses the strategy specs
  (`recursive:400/200`, `parent-document:200/1000`) that name a run on the command
  line and in every result row.
- **`cli.py`** — `chunking-lab chunkers` lists what is implemented;
  `chunking-lab split` shows where the cuts landed. Also `python -m chunking_lab`.

## Design notes

- **Chunkers return spans, not strings** (README C1). This is the load-bearing
  choice. Character-level Precision Ω and IoU are uncomputable without offsets
  back into the source; the context-augmenting strategies (late chunking,
  contextual retrieval, sentence-window, parent-document) are only expressible if
  `retrieval_text` can differ from `return_text`; and only ranges make the
  coverage invariant checkable at all.

- **The invariant is "no non-whitespace character is dropped", not "coverage ==
  1.0".** The stricter rule reads better and is wrong: the reference
  implementation trims whitespace off its chunk boundaries, so a faithful port
  leaves small gaps and would fail it. Dropping *content*, though, is never
  acceptable — it is the silent-data-loss failure `ingest-ledger` exists to catch,
  applied to chunking. So `check` enforces the content rule and `coverage` is
  reported as a number. A configuration that loses 3% of a corpus is visible
  without being conflated with one that merely normalises whitespace.

- **Offsets are characters, not tokens.** Chroma's report says "tokens"
  throughout; its implementation measures characters. Following the
  implementation is both correct-by-reference and strictly better here: it needs
  no tokenizer, so no model, no network, and no first-run download. The whole
  Tier 0 lane is deterministic (CONVENTIONS rule 3). A tokenizer appears only
  behind the `benchmark` extra, and only to reproduce a published table whose
  *sizes* were expressed in tokens.

- **The recursive port is verified differentially, not just by unit test.** The
  reference was run directly to capture its output for 28 (document, size,
  overlap) combinations; `tests/golden_recursive.json` is that record and
  `test_recursive_matches_reference.py` asserts our spans reproduce it exactly.
  This caught a real defect immediately: the reference keeps a separator as the
  **prefix of the following piece**, and the first port had it as a suffix. Both
  are lossless, so the invariant passed; several sizes agreed by coincidence.
  Only the differential showed it. The lesson generalises — an invariant proves a
  chunker is *well formed*, never that it is the *same* chunker.

- **Family 6 is Tier 0, and that is deliberate.** Sentence-window and
  parent-document need no model at all, so the `retrieval_text` / `return_text`
  split is exercised by the default test suite from the first commit rather than
  waiting for the embeddings extra. A scorer that reads the wrong field credits
  sentence-window for context the model never saw, or penalises it for padding
  that was never indexed. Building the family early is what makes that a test
  failure instead of a footnote.

- **A Tier 1 result records its embedder, and that is not bookkeeping.** A
  semantic run against a hosted encoder and one against the offline hashing
  fallback are not comparable — the hashing embedder is a bag of words and would
  make semantic chunking look worthless. So `Chunking.code_path` carries the
  embedder id, and the CLI prints it. CONVENTIONS rule 2 says degrade gracefully
  and *record which path ran* rather than silently substituting; this is the first
  place in the tool where there is a path to get wrong.

  Shipping the weak embedder at all is the deliberate part. It makes Tier 1
  runnable, testable and demonstrable with nothing installed, which is what lets
  the semantic chunkers be covered by the default suite (rule 6). The cost is that
  someone could quote a meaningless number, and the mitigation is that the number
  arrives with `tier-1/embeddings:hashing-bow-v1` attached to it.

- **The percentile threshold is strictly exceeded, not met.** Found by a test, and
  worth recording because it is not obvious: in a *uniform* passage every adjacent
  distance is equal, so the percentile equals every distance, and `>=` cuts between
  every pair of sentences in the most coherent document it could be handed. The
  inverse case — every sentence unrelated, so the distribution is flat and high —
  yields a single chunk, and that is inherent to a relative threshold rather than a
  bug. `max_size` is the safety valve for it.

- **The cluster chunker is a dynamic program, not another threshold.** The
  percentile rule is greedy and local: it judges one gap at a time and cannot see
  that four sentences ahead form a run. `ClusterSemanticChunker` takes, of every
  partition into chunks under `max_size`, the one with the highest total
  within-chunk pairwise similarity. Summing *pairs* rewards larger chunks — there
  are more of them — which is precisely why the size cap is mandatory rather than
  optional: it is what makes the objective well posed.

- **A spec string is the identity of a run.** `recursive:400/200` names the
  strategy and every parameter that changes its output, and `fixed:512/0`
  normalises to `fixed:512` so one configuration cannot appear as two rows.
  CONVENTIONS rule 5, applied before there is anything to record.

- **The CLI is smaller than the design on purpose.** `score`, `suggest`,
  `explain` and `annotate` are specified in README §8.5 and absent from the
  parser rather than stubbed, so `--help` describes what the tool actually does.
  `chunkers` prints the tier and requirements of each strategy, which makes the
  gap between designed and built visible from the command line.

## Try it

```bash
uv run chunking-lab chunkers

# Tier 0 -- nothing installed, fully deterministic
uv run chunking-lab split README.md --strategy recursive:400/200
uv run chunking-lab split README.md --strategy structural
uv run chunking-lab split README.md --strategy sentence-window:1

# Tier 1 -- offline by default, and the output says so
uv run chunking-lab split README.md --strategy semantic:95
uv run chunking-lab split README.md --strategy cluster-semantic:400

# Tier 1 against a real encoder (needs the `embeddings` extra)
export DATA_TOOLS_EMBED_MODEL=openai/text-embedding-3-small
export DATA_TOOLS_API_KEY=...
uv run chunking-lab split README.md --strategy semantic:95 --embedder provider
```

## Next

README §13 is the checklist. In order: the intrinsic metrics (§7, no ground truth
needed, so the fastest path to something useful), the hostile corpus generator,
then the extrinsic metrics with the Precision Ω reproduction as their correctness
proof (C17).
