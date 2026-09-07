# 006 — chunking-lab

**Idea #25.** Take one corpus, run it through many chunking strategies, and score
each one *at the character level against gold spans* — so the number reflects
where the cuts landed, not how good the retriever or the model happened to be.

The user-facing reference, the research behind every choice, and the sixteen
decisions live in [`tools/chunking-lab/README.md`](../tools/chunking-lab/README.md).
This document is the design record: what is built, how each part works, and why
it is shaped that way. Per `docs/000` §9 the numbered doc holds the design; the
README holds the usage.

**Status.** All six Tier 0 chunkers, both Tier 1 semantic chunkers, the invariant
that governs them, the query-free intrinsic metrics, and the extrinsic metrics —
**whose Precision Ω reproduces Chroma's published column exactly** (6.7 / 13.9 /
17.7 / 29.9), and `chunking-lab score`, which ranks strategies against gold spans
over a fixed BM25 retriever. The hostile corpus and `suggest` are not built yet.

## Pipeline

```
document ─▶ chunker ─▶ Chunking(spans, provenance, strategy)
                           │
                           ├─▶ invariant.check   (always; a violation is a chunker bug)
                           ├─▶ intrinsic metrics (query-free)  ─▶ screening verdict
                           └─▶ extrinsic metrics vs gold spans
                                 precision_omega   (no retrieval at all)
                                 recall / precision / iou   (top-k retrieved)
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
- **`intrinsic.py`** — the query-free metrics: coverage and **content coverage**,
  duplication and return amplification, size distribution, boundary fidelity,
  mid-table and split-fence rates, orphaned-reference rate, and — only with an
  embedder — cohesion and separation. `Intrinsic.disqualifications()` is the
  screening verdict.
- **`ranges.py`** — half-open character-range arithmetic: `total`, `union`,
  `intersect`, `difference`. Every metric is built from these four, kept separate
  so that when a score looks wrong this is the layer you can rule out first.
- **`extrinsic.py`** — `precision_omega` (no retrieval involved) and `score`
  (recall, precision, IoU at k). Implemented to the definitions verified against
  the report *and* the reference implementation, including the parts the prose
  omits.
- **`benchmark.py`** — loads the five Chroma corpora and their 472 gold-span
  questions, and holds `PUBLISHED_PRECISION_OMEGA`, the numbers we check against.
- **`retrieve.py`** — `BM25Retriever`, held fixed by design (C5), over an
  in-memory SQLite FTS5 index. Indexes `retrieval_text`, which for family 6 is
  deliberately not what gets returned. Drops stopwords from the query.
- **`score.py`** — `run` produces one `Result` per (strategy, corpus, question)
  carrying **intrinsic and extrinsic metrics on the same row**; `summarise` means
  them per strategy; `write_jsonl` appends so results accumulate.
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

- **Screening says "eligible", never "best".** `disqualifications()` returns
  *faults* — content lost, chunks past the embedding window, a code fence cut in
  half — and nothing else. It deliberately has no scoring function and no ordering,
  because intrinsic metrics cannot rank two reasonable configurations: chunk
  quality is only defined relative to the questions asked (README §7). The CLI
  prints "intrinsic metrics screen; they do not rank" on every run, and a test
  asserts that line is still there, so making them rank means deleting an
  assertion that says not to.

- **Content coverage exists because plain coverage was useless for screening.**
  The first version disqualified a configuration whenever coverage dipped below
  1.0 — which fires on every trimming strategy, for whitespace. `content_coverage`
  counts only non-whitespace characters, matching what the invariant enforces.
  Plain coverage is still reported: it is informative, just not a fault.

- **Every intrinsic signal names its prior art in its own docstring.** Boundary
  fidelity is Adaptive Chunking's Block Integrity, the oversize rate is its Size
  Compliance, the orphaned-reference rate is its References Completeness. Putting
  those attributions at the point of definition rather than only in a README §9
  table is what stops the claim drifting back to "possibly unclaimed" the next
  time someone summarises the tool. The genuine difference — no model needed — is
  stated in the same place, once.

- **Cohesion and separation are included with a warning attached.** They are the
  only intrinsic signals that cost anything, and MoC reports that plain semantic
  dissimilarity metrics of exactly this shape did *not* track RAG performance
  while their perplexity-based ones did. They are here because the correlation
  experiment (README §9) needs them measured, not because they are known to work.

- **Precision Ω is validated against a published table, not against our own
  understanding** (C17). This is the design note that matters most here. The
  metric had already been implemented once from a misreading of the report, and
  every unit test written against that misreading passed. Because Precision Ω
  involves **no retrieval**, and the benchmark is MIT-licensed and public, the
  claim "our implementation is correct" can be a falsifiable offline test instead
  of an assurance. It reproduces all four published values exactly:

  | recursive | published | ours | the original misreading |
  |---|---|---|---|
  | 800 / 400 | 6.7 | **6.7** | 8.6 |
  | 400 / 200 | 13.9 | **13.9** | 16.8 |
  | 400 / 0 | 17.7 | **17.7** | 17.8 |
  | 200 / 0 | 29.9 | **29.9** | 30.7 |

  The fourth column is the payoff. The misreading is ~28% high on the overlapping
  configurations and nearly right without overlap — so it would have looked
  perfectly plausible in isolation, and it would have quietly recommended overlap.
  `test_the_original_misreading_would_not_have_reproduced_the_table` keeps that
  gap under test, and fails if the two readings ever stop diverging.

- **The overlap asymmetry is reproduced, not repaired.** `precision` divides by
  the *sum* of the retrieved chunks' widths, charging an overlapping chunker twice
  for the same characters; `precision_omega` divides by their *union*, which does
  not. That looks like an inconsistency and arguably is one, but the published
  numbers come from code that does exactly this. A faithful port is what makes the
  reproduction meaningful; "improving" either one silently forks the metric.

- **k is adaptive by default.** With no `--k`, each question is scored at its own
  number of gold-bearing chunks, matching the reference's `retrieve=-1`. Every
  result row records the value used, because two runs at different k are not
  comparable and nothing about the numbers makes that obvious.

- **The retriever is fixed, and the stopword fix was not optional.**
  `docs/LEARNINGS.md` logged an open gotcha against `repo-rag`: building the FTS5
  query as an OR of every token lets stopwords dominate BM25. That is a quality
  problem there and a *correctness* problem here — a polluted retriever returns
  near-random chunks for every strategy alike, which makes them all look equally
  mediocre and hides precisely the differences this tool exists to show. Dropping
  stopwords is reusing a recorded learning rather than rediscovering it.

- **One row per question, carrying both metric families.** Open question 4 asked
  whether the correlation experiment is a design goal. It is, so the schema is
  built for it: intrinsic and extrinsic scores are computed over the *same* run
  and stored together, keyed by strategy, corpus and question, which makes "do
  query-free signals predict retrieval ranking?" a `GROUP BY` over accumulated
  JSONL rather than a separate script. The chunking-level intrinsic values repeat
  on every row of that chunking — deliberate redundancy, so a row is interpretable
  on its own months later without the run that produced it.

- **`structural` scoring 100% recall and 0.39 Precision Ω is the tool working.**
  On the State of the Union transcript there are no Markdown headings, so the
  structural splitter emits one chunk containing the whole document. It retrieves
  the answer every single time and is useless. No chunk-level metric can express
  that — it would score a perfect hit — and it is the clearest one-line argument
  for measuring inside the chunk.

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
# the correctness proof: reproduce a published column, offline, no model
make chunking-benchmark

uv run chunking-lab chunkers

# Tier 0 -- nothing installed, fully deterministic
uv run chunking-lab split README.md --strategy recursive:400/200
uv run chunking-lab split README.md --strategy structural
uv run chunking-lab split README.md --strategy sentence-window:1

# Tier 1 -- offline by default, and the output says so
uv run chunking-lab split README.md --strategy semantic:95
uv run chunking-lab split README.md --strategy cluster-semantic:400

# rank strategies against gold spans (needs the benchmark fetched)
uv run chunking-lab score --corpus state_of_the_union.md \
    --strategy recursive:200 --strategy fixed:800/400 --strategy structural

# screen several strategies with no questions and no model
uv run chunking-lab metrics README.md \
    --strategy fixed:800/400 --strategy recursive:200 \
    --strategy structural --strategy sentence:4

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
