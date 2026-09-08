# 006 — chunking-lab

**Idea #25.** Take one corpus, run it through many chunking strategies, and score
each one *at the character level against gold spans* — so the number reflects
where the cuts landed, not how good the retriever or the model happened to be.

The user-facing reference, the research behind every choice, and the sixteen
decisions live in [`tools/chunking-lab/README.md`](../tools/chunking-lab/README.md).
The concepts themselves — what a span is, what Precision Ω measures, why intrinsic
metrics screen but cannot rank — are defined in
[`007_chunking-concepts.md`](007_chunking-concepts.md).

This document is the design record: what is built, how each part works, and why
it is shaped that way. Per `docs/000` §9 the numbered doc holds the design; the
README holds the usage.

**Status.** All six Tier 0 chunkers, both Tier 1 semantic chunkers, the invariant
that governs them, the query-free intrinsic metrics, and the extrinsic metrics —
**whose Precision Ω reproduces Chroma's published column exactly** (6.7 / 13.9 /
17.7 / 29.9), and `chunking-lab score`, which ranks strategies against gold spans
over three retrievers (BM25, vector, hybrid-RRF), the hostile corpus, `explain`,
`axes`, `annotate`, and `correlate` —
which has now **run** the §9 experiment. `report`, `annotate` and `suggest` are
not built yet.

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
- **`corpus/generate.py`** — the hostile corpus: five documents built so specific
  strategies provably fail, with gold spans known by construction because the
  generator wrote the answer text. Generated, not committed.
- **`annotate.py`** — the model half of C9: prompt for a question plus verbatim
  excerpts, locate every quote in the **whole** document, discard the question if
  any quote cannot be found, and report the `Yield` — how many survived, why the
  rest did not, and which stage of the cascade found each excerpt.
- **`locate.py`** — quote-then-locate (C9): exact match, then whitespace-tolerant,
  then a sentence-level fuzzy match that must score at least 98. `locate_all`
  returns what it found *and* what it could not, which is the yield.
- **`corpus.py`** — `Corpus` and `Question`, the `DocumentBuilder` that makes a
  generated gold span exact by construction, and `load_dir` / `write_dir`, which
  are also the bring-your-own-corpus path: any directory of documents plus a
  `gold.jsonl` can be scored.
- **`retrieve.py`** — `BM25Retriever` (needs nothing), `VectorRetriever` and
  `HybridRetriever` (reciprocal-rank fusion, `k=60`), plus `build()`. The
  retriever is held **fixed** across a chunker comparison; varying both at once
  measures neither (C5).
- **`correlate.py`** — the §9 experiment as a query over accumulated `score --out`
  rows: tie-corrected Spearman, a partial correlation to remove the chunk-size
  confound, and a constant-signal check so "never varied" cannot be printed as
  "no relationship".
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

- **The hostile corpus found two failure modes where the design had one.** README
  §8.4 lists five documents as one idea. Building them separated it:

  - **Severing** — the answer is cut across chunks, so no single chunk holds it.
    `straddle.md` puts the answer across a paragraph break, which is the *first*
    place a recursive splitter cuts; `code_fence.md` puts blank lines inside a
    code fence.
  - **Orphaning** — the chunk holding the answer is perfectly intact and still
    unusable, because what makes it meaningful is in a different chunk.
    `heading_subject.md` puts the region name only in the heading;
    `rate_table.md` separates a row from its header; `back_reference.md` opens
    with "as described above".

  The second is the interesting one, because **no boundary placement fixes it** —
  the boundary is already correct. That is the argument for the context-augmenting
  strategies stated as a test rather than a paragraph, and it produced the
  sharpest demonstration in the suite: on `heading_subject.md`, sentence-window
  still *indexes* a chunk with no "Northeast" in it, so retrieval is no easier,
  but what it *returns* does contain it. Score the wrong field and the strategy
  looks either better or worse than it is.

- **A test helper broke rule 1 before any dependency could.** The first version of
  `test_hostile.py` did `sys.path.insert(...)` then `import generate` — and
  `ingest-ledger` ships a `corpus/generate.py` too, so 29 of its tests started
  failing on an attribute that had never existed. Tools not importing each other
  is a rule about *test* code as much as source, and the fix is to load the module
  by explicit path under a unique name. (Registering it in `sys.modules` before
  `exec_module` is required: `@dataclass` resolves its own module while the class
  body is processed.)

- **`explain` exists because Precision Ω can be high and the chunking still
  broken.** This was the sharpest thing `explain` taught, and it was not
  anticipated. On `straddle.md` at `recursive:120` the answer is severed — the word
  "accounts" sits alone in its own chunk — and Precision Ω reads **98.4%**. Both
  are correct: Ω is the *ceiling* the cuts impose on precision, and two tight
  chunks that between them contain almost nothing but the answer impose a high
  one. It says nothing about whether any single chunk is usable. A score column
  cannot show you a stranded word; a rendered chunk can, and that is the argument
  for the command.

- **The fuzzy floor is deliberately severe.** A near-miss quote produces a *wrong*
  gold span, which then scores every strategy against the wrong answer — strictly
  worse than having no gold span at all. So the cascade rejects anything under 98
  and the question is discarded. That is C9's inversion: a weak model produces
  *less* ground truth, never wrong ground truth, and the loss is a number you can
  read.

- **The experiment was an afternoon because the schema was designed for it.**
  Open question 4 was answered "yes" before any result row was written, so
  intrinsic and extrinsic metrics land together keyed by strategy and corpus.
  Collecting on that was a `GROUP BY`, two statistics functions and a CLI command
  — no re-running and no separate harness. See `FINDINGS.md` F8 for the result.

- **Reporting the correlation honestly took more care than computing it.** Three
  things had to be right or the table would mislead:

  1. **The mechanical confound.** `median_length` predicts Precision Ω at −0.95 on
     every corpus, and Ω divides by the chunks holding the answer — so smaller
     chunks raise it by construction. Real, reproducible, evidence of nothing.
     Hence `--control`, which reports the partial correlation.
  2. **Controlling can make a signal look *better*.** `boundary_fidelity` is ~+0.15
     raw and looks useless; controlled for size it is **+0.44**. Size was masking
     it, because strategies that cut cleanly also cut larger. A raw correlation
     near zero can be two relationships cancelling.
  3. **`0.00` and "no variance" must not print the same way.** `mid_table_rate` is
     constant on all five Chroma corpora — they contain no tables — so there is
     nothing to correlate. Printed as `+0.00` beside real numbers it reads as
     "tested, found useless". It is *untested*. One `len(set(xs)) <= 1` check and a
     different label is the difference between a table you can trust and one that
     launders missing data into a result.

- **The second corpus exists because a signal cannot be tested where it never
  varies.** All five Chroma corpora contain zero Markdown tables and zero code
  fences — even `finance.md`, whose ConvFinQA source tables were flattened into
  prose — so `mid_table_rate` and `split_fence_rate` were *constant*, and F8 had to
  report them as untested. `corpus/generate_docs.py` produces documentation-shaped
  text with both, and gold spans known by construction.

  Downloading a document would not have worked, and the reason is worth keeping:
  the detectors match **Markdown syntax**, so extracted PDF text trips neither, and
  more fundamentally no downloaded document carries **character-level gold spans**.
  This repo's own docs have 346 table rows sitting unusable for exactly that
  reason. Annotation, not format, is the binding constraint.

  The generator decides where the tables and the answers are. It does **not**
  decide whether shredding them hurts — that is measured, and it came back
  negative (`FINDINGS.md` F9). The limitation is external validity, not rigging.

- **`--by-question-type` is C13, and it is the tool's most load-bearing honesty
  check.** A single ranking is always a ranking *against some distribution of
  questions*; printing one without saying which is not a simpler answer, it is the
  same answer with the assumption hidden. The effect is not small — on the
  generated corpus, `sentence-window:1` is **1st** for prose and table-row
  questions and **11th of 14** for code examples, on the same documents and the
  same cuts.

  Two details that took a second pass. The category has to be a **short closed
  set** (`Question.kind`), kept separate from the free-form `about`: the first
  version grouped on `about` and produced fifteen categories with sentence-long
  column headers. And the kind travels **on the result row**, not just in the
  corpus, so a JSONL file stays interpretable months later without the corpus that
  produced it.

- **Running against a local model is the default, not the fallback.** The shared
  config already defaults to `ollama/nomic-embed-text` on `DATA_TOOLS_API_BASE`, so
  reaching for a hosted API is the *override*. `--embedder` takes three shapes:
  `hashing` (offline, weak, for exercising the path), `provider` (whatever the
  environment says), or an explicit LiteLLM model string like
  `ollama/qwen3-embedding`, which beats the environment so a run states its encoder
  rather than inheriting one.

- **The offline embedder is dangerous here in a way it was not for Tier 1.** For
  semantic *chunking* a weak encoder produces a weak chunking, and `code_path`
  records it. For *retrieval comparison* it produces a systematically biased
  answer: a vector retriever built on a bag of words underperforms BM25 at BM25's
  own game, so the experiment would conclude "the chunker matters more" as an
  artifact of the encoder. So `score` and `axes` both print a warning when
  `hashing` appears in the retriever name. The number is not wrong; the inference
  from it would be.

- **`CachingEmbedder` is a precondition, not an optimisation.** Fourteen strategies
  over one corpus re-embed heavily overlapping text fourteen times, and against a
  local model each is an HTTP round trip. In-process only — a cache that survives
  between runs is `embeddings-cache` (#23) and belongs in its own tool.

- **`axes` refuses Precision Ω, and that refusal is the interesting part.** Ω is
  retriever-independent by construction, so the retriever axis would show a spread
  of exactly 1.0 — not because the retriever does not matter, but because *that
  metric cannot see it*. Comparing the axes has to happen on IoU or recall. A tool
  that silently allowed Ω here would produce a confident, meaningless answer.

- **`axes` reports a distribution because a median hid the finding.** It first
  printed two medians and a verdict — chunker 5.6×, retriever 1.3×, "the chunker
  moves this metric more". True, and it buried the result: the two axes have nearly
  identical *maxima* (14.4× and 14.9×) and completely different *frequencies*
  (15/15 versus 4/25). One matters always, the other seldom and then
  catastrophically, and no median can say that. It now prints n, min, median, max
  and the over-2× count, and tells the reader to prefer the per-row table. The
  outliers were only noticed because that table is printed above the summary.

- **`annotate` locates against the whole document, not the sampled window.** The
  model sees 4000 characters, but the offsets have to address the text that will
  actually be chunked. Locating within the window and adding its start looks
  equivalent and is not: the model often quotes text that appears elsewhere too,
  and the window is an artefact of sampling rather than a real boundary.

- **One bad excerpt discards the whole question.** Partial ground truth is still
  wrong ground truth — a question scored against two spans where one is misplaced
  is worse than a question that does not exist.

- **The yield counters are named for what actually happened**, which took a second
  pass. The first version had `unparseable` counting *provider exceptions* while
  bad JSON landed in `malformed`, so the report could say "unreadable JSON: 0" for
  a run where every reply was unreadable. Now `call_failed` and `malformed`. A
  report that miscounts its own failure modes is worse than one that says less.

- **`annotate` pins temperature 0, and that is a correctness requirement.** The
  instruction is "copy this text character for character"; sampling injects
  variation into the one thing that must not vary, and the damage is invisible —
  a slightly reworded quote reads naturally and simply fails to be found. We
  learned this the expensive way: passing no generation options meant inheriting
  Ollama's default of 0.8, and a four-model comparison then appeared to show a 14B
  model doing *worse* than a 7B. That looked like a finding about model size and
  was an artefact of our own config, hitting the larger model hardest because more
  capacity means more plausible variations to sample from. At temperature 0 the
  effect vanished (`FINDINGS.md` F12). A test asserts the option reaches the
  provider, so nobody removes it thinking it is a tuning knob.

- **`--model` is repeatable, and the comparison writes nothing.** Given several
  models it runs each over the *same* windows — same documents, same seed — and
  reports yields side by side. Sharing the seed is the whole point: otherwise a
  yield difference could just be one model drawing easier text. It answers "which
  model should I annotate with", after which the real pass runs with the winner.

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

# which local model annotates best? identical windows, yields side by side
make chunking-models

# make gold spans for your own documents (local model by default)
uv run chunking-lab annotate ./my-docs --out ./my-corpus --model ollama/llama3.1
uv run chunking-lab score --corpus-dir ./my-corpus --strategy recursive:200

# which knob matters more: the chunker or the retriever?
make chunking-axes                                          # local Ollama
make chunking-axes EMBEDDER=ollama/qwen3-embedding          # another local model
make chunking-axes EMBEDDER=openai/text-embedding-3-small   # hosted

# the section 9 experiment: do query-free signals predict the ranking? (~100s)
make chunking-correlate

# the same, on documentation with tables and code fences (~10s)
make chunking-correlate-structured

# score your own corpus: a directory of documents plus a gold.jsonl
uv run chunking-lab score --corpus-dir ./my-corpus --strategy recursive:400

uv run chunking-lab chunkers

# Tier 0 -- nothing installed, fully deterministic
uv run chunking-lab split README.md --strategy recursive:400/200
uv run chunking-lab split README.md --strategy structural
uv run chunking-lab split README.md --strategy sentence-window:1

# Tier 1 -- offline by default, and the output says so
uv run chunking-lab split README.md --strategy semantic:95
uv run chunking-lab split README.md --strategy cluster-semantic:400

# see one answer against the chunks it actually landed in
uv run python tools/chunking-lab/corpus/generate.py corpus/hostile
uv run chunking-lab explain corpus/hostile/straddle.md --strategy recursive:120 \
    --answer "An incident is escalated when it has been open for four hours"

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

## The explainer

[`docs/where-the-cut-falls.html`](where-the-cut-falls.html) is the piece written for
someone who has never heard of chunking. It carries four hand-drawn SVG diagrams,
a live figure and a glossary:

- **the pipeline** — where chunking sits, and why judging the final answer cannot
  tell you which of three stages to blame;
- **the six families** — and, as a comparison rather than a list, the one thing
  family 6 does differently: identical cuts, different unit;
- **the metric anatomy** — the same document twice, showing that recall, precision
  and IoU divide by what the *retriever* picked while Precision Ω divides by what
  the *cuts* produced. This is the diagram that makes "no retriever is involved"
  something you can see rather than something you are told;
- **severing vs orphaning** — the two failure modes side by side, with the second
  annotated to show that its boundary is already correct.

Plus the live figure: a chunk-size and overlap slider over a real paragraph with a
marked answer, recomputing Precision Ω as the boundaries move. Its arithmetic was
checked against `chunking_lab.extrinsic.precision_omega` rather than written twice
by eye, and the diagram geometry is validated programmatically — every shape
inside its viewBox, no colliding labels.

The concepts are defined in prose, at length, in
[`007_chunking-concepts.md`](007_chunking-concepts.md); the page is the version
with pictures.

It also carries the correlation findings (F8, F9) in the same register: chunk size
"predicting" the score and meaning nothing, the check that looked useless turning
out to be the sturdiest, and a fifth diagram for the counterintuitive one — cutting
a table row destroys it *and raises Precision Ω*, because shrinking the text around
an answer is exactly what lifts a precision ceiling. That figure's arithmetic (15%
whole, 31% severed) was checked against `extrinsic.precision_omega` rather than
worked out by hand.

Published as an artifact:
<https://claude.ai/code/artifact/079203e3-348b-4231-8437-e80827eaf5ff>

## Next

README §13 is the checklist. In order: the intrinsic metrics (§7, no ground truth
needed, so the fastest path to something useful), the hostile corpus generator,
then the extrinsic metrics with the Precision Ω reproduction as their correctness
proof (C17).
