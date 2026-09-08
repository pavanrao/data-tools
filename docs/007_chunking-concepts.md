# 007 — Chunking concepts

The concepts `chunking-lab` is built out of, defined properly and in an order that
builds. This is the **reference**; [`006_chunking-lab.md`](006_chunking-lab.md) is
the design record (what was built and why it is shaped that way), and
[`tools/chunking-lab/README.md`](../tools/chunking-lab/README.md) is the usage.

For a version of this written for someone who has never heard of chunking, with
diagrams, see [`where-the-cut-falls.html`](where-the-cut-falls.html).

Every concept below carries three things: **what it is**, **the trade-off it
forces** — because none of these are free — and **where it lives in the code**, so
the definition and the implementation cannot drift apart.

Concepts marked ⚑ are ones this collection has now *measured* rather than merely
described. Cards in `§` refer to the concept map in
[`005_concept-coverage.md`](005_concept-coverage.md).

---

## Contents

1. [The setting](#1-the-setting)
2. [The chunking decision](#2-the-chunking-decision)
3. [Retrieval](#3-retrieval)
4. [Ground truth](#4-ground-truth)
5. [Measurement](#5-measurement)
6. [The failure modes](#6-the-failure-modes)
7. [The advanced strategies](#7-the-advanced-strategies)
8. [Engineering concepts](#8-engineering-concepts)

---

## 1. The setting

### Retrieval-augmented generation (RAG) — `§2 The RAG pipeline`

A language model answers from what is in its prompt. A corpus is far larger than
any prompt, so a **retriever** selects a small number of passages and only those
go into the prompt. Everything downstream — whether the answer is right, whether
it is grounded, whether it can be cited — depends on that selection.

**The trade-off.** More passages means more chance the answer is present and less
room for anything else, plus more cost and more distraction. The whole discipline
is choosing what to leave out.

### The three variables

A RAG answer is produced by a **chunker**, a **retriever** and a **generator**, and
a change in quality can come from any of them. This is why "run the pipeline and
judge the answers" is a poor instrument: it measures all three at once.

**Where it lives.** `chunking-lab` holds the retriever fixed and removes the
generator entirely. `retrieval-bench` (#53) does the opposite — varies the
retriever with chunking fixed. Neither subsumes the other, and a benchmark that
moves both measures neither.

### Token and character — `§1 Token`

A **token** is the unit a model actually consumes: roughly a short word or word
fragment. A **character** is a character. Model limits, prices and chunk sizes are
usually quoted in tokens; counting them requires the model's tokenizer.

**The trade-off.** Tokens are the honest unit for anything a model touches, and
they cost a dependency: a tokenizer, a download, a version to pin.

**Where it lives.** Everything `chunking-lab` measures is **character**-based, which
is what keeps the whole measurement path free of a tokenizer and therefore
deterministic and offline. Chroma's report says "tokens" throughout while its
implementation counts characters — we followed the implementation, since that is
what produced the published numbers. `tiktoken` appears only behind the
`benchmark` extra, and only because the published table's *sizes* are in tokens.

### The embedding window, and silent truncation ⚑

An embedding model has a maximum input length. Feed it more and it does not
error — it **silently truncates**, and you get a vector for the first part of your
chunk with no indication that the rest was discarded.

**The trade-off.** Large chunks carry more context and are more likely to be cut
off unnoticed. The failure is invisible at every layer: the run succeeds, the
vectors look fine, retrieval quietly degrades.

**Where it lives.** `intrinsic.oversize_rate`, screened at `DEFAULT_MAX_CHARS`
(2000 ≈ a 512-token window). A crude proxy on purpose: reaching for a real
tokenizer would drag a model dependency into the deterministic core for a number
whose only job is to say "this chunk is at risk".

---

## 2. The chunking decision

### Chunk, boundary, span — `§2 Chunking`

A **chunk** is a piece of a document that gets indexed and retrieved as a unit. A
**boundary** (or cut) is where one ends and the next begins. A **span** is a chunk
expressed as a character range back into the source: `(start, end)`.

**The trade-off.** Chunks as *strings* are simpler and lose the addresses. Chunks
as *spans* cost a little bookkeeping and buy three things: character-level metrics
become computable at all, the context-augmenting family becomes expressible, and
"did this chunker drop a paragraph?" becomes a checkable invariant.

**Where it lives.** `chunking_lab.spans.Span`. This is decision C1, and everything
else follows from it.

### Retrieval unit vs return unit

What gets **indexed** and what gets **handed to the model** need not be the same
text. Indexing a single sentence keeps the embedding sharp; returning that
sentence with its neighbours keeps it comprehensible.

**The trade-off.** They are optimised against different things — retrieval wants
precision, generation wants context — and separating them is the only way to have
both. The cost is that every metric now has to say **which one it measured**. Score
the wrong field and a strategy looks better or worse than it is.

**Where it lives.** `Span.retrieval_text` and `Span.return_text`, with
`Chunking.augmented` declaring when they diverge, checked by the invariant.

### The six families

Ordered by what supplies the boundary signal, which is also the cost ordering.

| # | Family | Boundary signal | Cost |
|---|---|---|---|
| 1 | Fixed-size | a character or token counter | free |
| 2 | Recursive / separator | a priority list of separators | free |
| 3 | Structural | the document's own markup — headings, tables, code fences | free |
| 4 | Semantic | embedding similarity between adjacent sentences | one embedding pass |
| 5 | LLM / agentic | a model reads the text and picks boundaries | one LLM call per window |
| 6 | Context-augmenting | **boundaries unchanged**; the representation or return unit changes | varies |

**Family 6 is the one most write-ups get wrong**, by listing it alongside the
others as another way to cut. It does not move the cuts at all.

**Where it lives.** `chunkers/fixed.py`, `recursive.py`, `structural.py`,
`semantic.py`, `context.py`. Families 1–3 and 6 are Tier 0; family 4 is Tier 1;
family 5 is Tier 2 and unbuilt.

### Chunk size ⚑

The single biggest lever, and frequently a bigger one than the strategy choice.

**The trade-off.** Small chunks: high precision, high chance of severing an answer,
and less context per hit. Large chunks: the answer is intact and buried in padding,
and the ceiling on precision drops hard.

**Evidence.** Chroma's report, verbatim: *"the heuristic
`RecursiveCharacterTextSplitter` with chunk size 200 and no overlap performs well.
While it does not achieve the best result, it is consistently high performing
across all evaluation metrics."* Its own default — 800 with 400 overlap — is near
the bottom of the same table.

### Overlap ⚑

Repeating the tail of each chunk at the head of the next, so an answer straddling a
boundary appears whole in at least one chunk.

**The trade-off.** It genuinely reduces severing. It also multiplies index size,
and it **lowers the precision ceiling**, because more chunks now contain part of any
given answer and all of them count against you. It is a real trade, not a safety
setting to leave on.

**Evidence.** Precision Ω for recursive splitting at 400 tokens: **17.7 with no
overlap, 13.9 with 200**. Same chunker, same corpus, same questions.

---

## 3. Retrieval

### Lexical retrieval and BM25 — `§2 Hybrid search`

Rank documents by the words they share with the query, weighted so rare words
count for more and long documents are not rewarded for length alone. **BM25** is the
standard formulation. SQLite's **FTS5** provides it with no dependency.

**The trade-off.** Exact and fast and explainable; blind to synonyms. "Backoff"
does not match "retries".

**Where it lives.** `retrieve.BM25Retriever`. It is the **default** because it is
deterministic — a comparison of chunkers run over an embedding retriever would
depend on the encoder, and the point is to isolate the cuts.

### Stopwords ⚑

Words so common they carry no retrieval signal. Left in a query built as an OR of
every token, they dominate the ranking.

**The trade-off.** Dropping them sharpens the ranking and can empty a query
entirely, so there has to be a fallback.

**Where it lives.** `retrieve.STOPWORDS`. Logged as an open gotcha against
`repo-rag` in `LEARNINGS.md` and reused here — and it matters *more* here: in
`repo-rag` a polluted query degraded result quality, but in a chunker comparison it
returns near-random chunks for **every strategy alike**, which makes them all look
equally mediocre and erases the differences being measured.

### Dense retrieval and embeddings — `§1 Embedding`

An **embedding** is a vector representing a passage's meaning; similar passages get
nearby vectors, and similarity is usually **cosine** of the angle between them.

**The trade-off.** Catches meaning that shares no words; costs a model, a vector
index, and determinism.

**Where it lives.** `embeddings.py`, behind the `embeddings` extra. Used both to
*place boundaries* (Tier 1 chunking) and to *retrieve* (`VectorRetriever`) — two
different jobs for the same vectors, and a result records which encoder produced
them either way.

**Local is the default.** `DATA_TOOLS_EMBED_MODEL` defaults to
`ollama/nomic-embed-text`, so running against a model on your own machine is the
ordinary path and a hosted API is the override. `--embedder` also takes an explicit
model string, which beats the environment so a run states its encoder rather than
inheriting one.

**The trap, and it is worse here than for chunking.** The offline `HashingEmbedder`
is a bag of words. For semantic *chunking* it produces a weak chunking, and
`code_path` records that. For a *retriever comparison* it produces a
**systematically biased** answer — a vector retriever built on it loses to BM25 at
BM25's own game, so the experiment would conclude "the chunker matters more" as an
artefact of the encoder. Both `score` and `axes` warn when it is in play.

### Hybrid retrieval and reciprocal-rank fusion ⚑ — `§2 Hybrid search`

Run both retrievers and combine their rankings. **Reciprocal-rank fusion** does it
using only *positions*: each chunk scores `1 / (60 + rank)` in each list and the
scores are added, so a chunk ranked highly by either does well and one ranked
highly by both does best.

**The trade-off, and why fusion beats a weighted sum.** BM25 scores and cosine
similarities are not on comparable scales, so blending the *scores* needs a weight
that has to be re-tuned per corpus. Ranks have no scale, so RRF needs no
calibration at all. What it gives up is the ability to express "this match was
overwhelming" — a first place is a first place however far ahead it was.

**Where it lives.** `retrieve.HybridRetriever`, `RRF_K = 60`. Same constant and
same reasoning as `repo-rag`.

### Which matters more, the chunker or the retriever? ⚑

Not a concept so much as the question the two preceding sections raise, and it now
has a measurement (`FINDINGS.md` F10, `make chunking-axes`).

Each axis is measured with the other **held fixed** — moving both at once measures
neither — and compared by the ratio between its best and worst configuration.

| axis | median spread | max | exceeded 2× |
|---|---|---|---|
| chunker | 5.6× | 14.4× | **15 of 15** |
| retriever | 1.3× | 14.9× | **4 of 25** |

The medians say "the chunker matters more", and that is true and misleading. The
two axes have almost identical **maxima**; what differs is **frequency**.

> **Chunking matters consistently. Retrieval matters rarely and then enormously.**

Every one of the four cases where retrieval mattered is BM25 collapsing and a
semantic retriever rescuing it — 1.3 IoU against 19.7 in the worst. The tempting
explanation, that retrieval matters more when chunking is worse, is **false**: the
rank correlation between a configuration's quality and its retriever spread is
−0.04.

**One methodological point this cannot be separated from.** Precision Ω cannot be
used to compare these axes. It is retriever-independent by construction, so the
retriever axis would show a spread of exactly 1.0 — not because the retriever does
not matter, but because that metric cannot see it. `axes` refuses it outright.

### Retrieval depth, k ⚑

How many chunks are fetched per question.

**The trade-off.** Larger k almost always raises recall and always lowers
precision. Because of this, **two runs at different k are not comparable** and a
number quoted without its k means nothing.

**Where it lives.** `extrinsic.score(k=...)`. The default is *adaptive*: each
question is scored at its own number of gold-bearing chunks, matching the reference
implementation's `retrieve=-1`. Every result row records the value used.

---

## 4. Ground truth

### Gold spans — `§5 Golden set / eval set`

For each question, the exact character ranges that answer it. Not "which document",
not "which chunk" — which **characters**.

**The trade-off.** Far more expensive to produce than document-level labels, and the
only thing that makes character-level scoring possible.

### Synthetic ground truth, and its filters

Generating question/answer pairs with a model instead of annotating by hand.
Chroma's pipeline: sample a window of the corpus, ask an LLM for a question plus
verbatim excerpts, accept only excerpts with a full-text match, then filter for
near-duplicate questions and for excerpts that are poorly related to their question.

**The trade-off.** Cheap and scalable, and the generator's biases become the
benchmark's biases. Thresholds are corpus-dependent: the paper tuned them per
corpus by binary search (excerpt relevance 0.40–0.43, duplicates 0.67–0.73), while
the reference code's defaults are 0.36 and 0.78. Quoting the defaults as though
they were the paper's numbers is a mistake this repo made and corrected.

### Quote-then-locate, and yield ⚑

**Do not ask a model for character offsets** — they are unreliable at it. Ask for
the answer quoted **verbatim**, then find that string in the source
deterministically, and **discard anything you cannot find**.

**The trade-off.** You get less ground truth, and what you get is correct. A weaker
model produces *fewer* questions rather than *wrong* ones, so model quality shows
up as a **yield** you can read off instead of a silent corruption.

**Where it lives.** `locate.py` — exact match, then whitespace-tolerant, then a
sentence-level fuzzy match that must score ≥ 98. The floor is severe on purpose: a
near-miss quote is a *wrong* gold span, which scores every strategy against the
wrong answer, and that is strictly worse than a missing one.

*Note the difference from the reference implementation: it retries the model until
it has enough questions, so a weak model shows up as a longer run and a larger
bill. Reporting the yield instead is the point of the decision.*

**Measured** (`FINDINGS.md` F11). `ollama/llama3.1` over four real documents, 20
attempts: **70% usable**. The failures are almost all the model *paraphrasing*
when asked to copy verbatim — the exact failure this design anticipates — and every
one was discarded rather than written in with plausible wrong offsets.

**The number moves with the document, not just the model.** Prose yielded 4/5;
56KB of dense markdown — tables, code fences, nested lists — yielded 2/5. Copying a
table row verbatim has far more to get exactly right than copying a sentence. So a
yield is a property of the **(model, corpus) pair**, and quoting one without saying
which corpus it came from means little.

*An earlier run reported 25% from 8 attempts. That was too small a sample to state
a rate at all — see the note in F11.*

**The generation temperature is part of this concept, not a detail.** Sampling is
variation, and this task's whole requirement is *no* variation. Run at a default
temperature and quotes come back subtly reworded — invisible in the reply, fatal at
locate time. `annotate` pins temperature 0. Skipping that once turned a four-model
comparison into an apparent finding that a 14B model was worse than a 7B, which was
purely an artefact of the sampling config (`FINDINGS.md` F12).

**And yield is not the only thing to read.** Across four local models the yields
cluster at 75–90%, which makes them look interchangeable; the *stage* breakdown
does not. `llama3.1` reproduced 15 excerpts exactly, `phi4` only 2 — leaning on
whitespace tolerance for nearly every match. Same yield, materially weaker
artefact, because a gold span recovered by normalising whitespace rests on a looser
guarantee than one matched character for character.

### Hostile corpora ⚑

Documents written so that a specific strategy provably fails on them, with the
answer's location known **by construction** because the generator wrote it.

**The trade-off.** No annotation, no model, no fuzzy matching, and perfectly
reproducible — but synthetic, so it demonstrates a failure mode rather than
measuring how often it occurs in the wild.

**Where it lives.** `corpus/generate.py`, tests marked `hostile` so a strategy that
*stops* failing is treated as a fixture that has drifted, not as a win.

### Question-type bias

A generator producing single-sentence factoid questions systematically favours
small chunks; multi-hop and aggregation questions favour large or hierarchical ones.

**The trade-off.** Any ranking is a ranking *for a distribution of questions*. A
tool that hides which distribution it used has a thumb on the scale.

---

## 5. Measurement

### Chunk-level vs character-level ⚑

**Chunk-level** metrics score each retrieved chunk relevant or not, as an atom.
**Character-level** metrics score the characters inside it.

**The trade-off.** Chunk-level is far easier to label and cannot see the failures
that are specific to chunking: a chunk holding the answer plus 1,800 characters of
padding scores identically to a tight one; an answer severed across two chunks
scores as two partial hits; a boundary landing mid-table is invisible.

**Evidence.** On a transcript with no headings, the structural splitter emits one
chunk containing the whole document. Recall **100%**. Precision Ω **0.39%**. A
chunk-level metric scores that a flawless hit.

### Recall, precision, IoU

With *gold* = the characters that answer the question and *retrieved* = the
characters in the top-k chunks:

```
recall     = |gold ∩ retrieved| / |gold|
precision  = |gold ∩ retrieved| / |retrieved|
IoU        = |gold ∩ retrieved| / |gold ∪ retrieved|
```

**The trade-off between them.** Recall alone is trivially gamed by retrieving
everything. Precision alone is gamed by retrieving nothing. IoU balances both and,
like the other two, moves when the *retriever* changes — so none of them isolates
the chunker.

**Where it lives.** `extrinsic.score`. One implementation detail is reproduced
rather than repaired: the precision denominator is a plain **sum** over retrieved
chunks, so an overlapping chunker is charged twice for the same characters, while
the Precision Ω denominator is a **union** and is not. It looks inconsistent, and
the published numbers come from code that does exactly this.

### Precision Ω ⚑

> Precision for the case that **all chunks containing excerpt tokens are
> successfully retrieved**. An upper bound on token efficiency given perfect recall.

Take every chunk in the corpus holding any part of the answer, and ask what
fraction of that text is the answer:

```
Precision Ω = |gold| / |union of every chunk containing any gold character|
```

**Why it is the headline.** It involves **no retrieval**. It is the ceiling the
boundaries impose before any retriever runs — the chunking decision isolated from
everything downstream. It is also what makes the implementation checkable against a
published table with no model, no vector store and no network.

**The trade-off, and the thing to watch.** A high Ω does not mean the chunking is
good. It is a ceiling on *precision*, and says nothing about whether any single
chunk is usable: on `straddle.md` at `recursive:120` the answer is severed across
two chunks — one holds the single word "accounts" — and Ω reads **98.4%**, because
two tight chunks containing almost nothing but the answer impose a high ceiling.
Read Ω next to recall and the severing count, never alone.

**Where it lives.** `extrinsic.precision_omega`, validated by
`tests/test_reproduction.py`.

### Why absolute numbers are tiny

Retrieving k chunks to answer a one-sentence question means most of what comes back
is padding by construction. Chroma reports single-digit token precision throughout.

**The consequence.** These are **relative comparisons only**. Any report built on
them has to say so or it looks broken.

### Intrinsic vs extrinsic ⚑

**Intrinsic** metrics are computable from the document and the spans alone: no
questions, no retriever, no model. **Extrinsic** metrics need questions with gold
spans.

**The relationship, and the limit:** **intrinsic metrics screen; extrinsic metrics
rank.** Coverage below 1.0, chunks past the embedding window, or 40% of cuts
landing mid-sentence disqualify a configuration before an evaluation set exists.
But they **cannot** rank two reasonable configurations, because "good chunking" is
only defined relative to the questions asked. Any tool claiming a universal
chunk-quality score without queries is overselling.

**Where it lives.** `intrinsic.measure` and `Intrinsic.disqualifications()`, which
returns *faults* only and has no scoring function and no ordering — deliberately.

### The intrinsic signals

| Signal | What it catches | Published counterpart |
|---|---|---|
| **Coverage** / **content coverage** | text present in no chunk at all — silent data loss | — |
| **Duplication** | characters indexed ÷ characters in source; the direct index cost of overlap | — |
| **Return amplification** | characters returned ÷ characters in source; diverges from duplication only for family 6 | — |
| **Boundary fidelity** | cuts landing inside a sentence rather than at a natural break | Adaptive Chunking's *Block Integrity* |
| **Size distribution** | p95 length, oversize rate (truncation risk), runt rate | its *Size Compliance* |
| **Mid-table rate** | cuts inside a Markdown table | — |
| **Split-fence rate** | chunks holding an odd number of code fences | — |
| **Orphaned-reference rate** | chunks opening "as described above", "the table below", a bare "it" | its *References Completeness* |
| **Cohesion / separation** | similarity within chunks vs across boundaries — *needs an embedder* | MoC's *Boundary Clarity* |

The last row carries a warning: MoC reports that plain semantic-dissimilarity
metrics of exactly this shape did **not** track RAG performance, while their
perplexity-based ones did. They are measured here because the correlation
experiment needs them, not because they are known to work.

---

## 6. The failure modes

Building the hostile corpus separated what the design had recorded as one idea.

### Severing

The answer is cut across chunks, so no single chunk holds it. Retrieve either half
and you get a fragment that reads like an answer.

**Fix:** a boundary in a different place — larger chunks, better separators, or
overlap. This one **is** a boundary problem.

### Orphaning ⚑

The chunk holding the answer is perfectly intact, and still unusable, because what
makes it meaningful is in a different chunk: a heading, a table's header row, the
noun a pronoun refers to.

**Fix: none, at the boundary.** The boundary is already correct. This is precisely
why the context-augmenting family exists, and it produced the sharpest result in
the suite — on `heading_subject.md`, sentence-window still *indexes* a chunk with
no "Northeast" in it, so retrieval is no easier, but what it **returns** does
contain it.

### Silent data loss

A chunker drops a trailing paragraph. The run succeeds and the scores look
plausible.

**Where it lives.** The chunker invariant. Note the rule that is actually
enforceable: not "coverage == 1.0" — which fires on any strategy that trims
whitespace at its boundaries — but **"no non-whitespace character is in zero
spans"**, with coverage reported as a number alongside.

### Shredding structure

A table separated from its header row is four numbers with no column names. A code
fence cut in half is a fragment that looks like code. Neither shows up in an
average chunk size.

---

## 7. The advanced strategies

### Semantic chunking ⚑

Embed each sentence and cut where adjacent sentences are least alike.
**Percentile-breakpoint** thresholds against the document's own distance
distribution; **clustering** solves for the partition maximising total within-chunk
similarity, which is a dynamic program rather than a threshold and can beat the
greedy rule on identical embeddings.

**The trade-off.** One embedding pass over the corpus, and the evidence is not what
the marketing suggests. Qu, Tu & Bao found no consistent gain over fixed-size
splitting — and **measured no cost or latency at all**, which their title rather
overstates. The useful finding is buried: semantic chunking wins *decisively* on
topically heterogeneous documents (F1@5 **81.89 vs 69.45** on stitched Miracl) and
loses on natural ones, because evidence sentences in a real document cluster by
position anyway.

**The consequence.** Topic heterogeneity is a concrete corpus-profiling signal, and
this is the strongest single piece of evidence for the tool's premise: **the
ranking depends on your corpus, so compute it on your corpus.**

### Late chunking

Embed the whole document at token level first, then mean-pool per chunk, so each
chunk's vector carries document context. Boundaries unchanged. Needs a long-context
embedding model.

### Contextual retrieval

Prepend an LLM-written 50–100 token blurb to each chunk before indexing.

**The trade-off, and a tension worth knowing.** Anthropic reports failed retrievals
down 35% with contextual embeddings, 49% adding contextual BM25, 67% adding a
reranker — at roughly one LLM call per chunk at index time. But *Reconstructing
Context* (ECIR 2025 workshop) evaluated the same family independently and found
**near-noise margins**: NDCG@5 0.317 contextual vs 0.312 baseline, 0.445 late vs
0.443 early. Report both whenever this is cited.

### Sentence-window and parent-document

Retrieve on a small unit, return a larger one. Tier 0 — they need no model at all,
which is why they are the earliest test of whether the `Span` design works.

**The trade-off.** More context reaches the model at no cost to retrieval sharpness;
in exchange, the return payload grows, and window size is a real parameter — on
`back_reference.md` a one-sentence window is *not* enough, because the subject is
two sentences back.

---

## 8. Engineering concepts

### Tiers, and the model-free core

**Tier 0** needs nothing installed. **Tier 1** needs an encoder. **Tier 2** needs a
chat model.

**The trade-off.** Keeping the deterministic core model-free constrains what it can
do and buys a suite that runs anywhere with no network, no key and no GPU
(`CONVENTIONS.md` rules 3 and 6). `embeddings` and `llm` are separate extras
because they are separate *claims*, not just separate dependencies.

### Recording the code path ⚑

Every result carries the lane that produced it — `tier-0/model-free`,
`tier-1/embeddings:hashing-bow-v1/512`.

**Why.** A semantic run against a hosted encoder and one against the offline
hashing fallback are not comparable, and the fallback is a bag of words that would
make semantic chunking look worthless. Shipping a deliberately weak embedder is
what makes Tier 1 testable with nothing installed; recording the path is what stops
someone quoting the resulting number as evidence.

### Provenance

Every record carries source path, content hash and unit — so a score traces back to
bytes, and a row is interpretable months later without the run that produced it.

### Reproducibility ⚑

The strongest form available: check your number against **someone else's published
table**.

**Why it worked here.** Precision Ω needs no retrieval and the benchmark is
MIT-licensed and public, so "our implementation is correct" became a falsifiable
offline test rather than an assurance. It reproduces 6.7 / 13.9 / 17.7 / 29.9
exactly. The reading originally assumed scores 8.6 / 16.8 / 17.8 / 30.7 — nearly
right without overlap, ~28% high with it, and it would have passed every unit test
written against it.

**Generalises to:** before implementing a metric, check whether a public benchmark
plus a published results table exists. Reproducing three of someone else's numbers
is worth more than thirty tests written against your own understanding.

---

## Where these are measured

| Concept | Command |
|---|---|
| Intrinsic signals, screening | `make demo-chunking` |
| Precision Ω against the published table | `make chunking-benchmark` |
| Recall / precision / IoU / Ω ranking | `chunking-lab score --strategy …` |
| Severing and orphaning, rendered | `chunking-lab explain <doc> --answer "…"` |
| The failure modes, as tests | `uv run pytest -m hostile` |
