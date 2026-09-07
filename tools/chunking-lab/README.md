# chunking-lab — compare chunking strategies, and recommend one

> **Its Precision Ω reproduces Chroma's published column exactly — 6.7 / 13.9 /
> 17.7 / 29.9 over 472 gold-span questions — offline, with no retriever, no
> embedding model and no API key.** `make chunking-benchmark`
>
> The reading this document originally assumed would have scored 8.6 / 16.8 /
> 17.8 / 30.7: nearly right without overlap, ~28% high with it, and it would have
> passed every test written against it. That is what §2 is about.

**Status: Tier 0 and Tier 1 chunkers, both metric families, `score` and `explain`
built and green.** `report`, `annotate` and `suggest` are specified below and not
built — see the checklist in §13.

This document is the design record. It began as a handoff from the web session
that designed it; the sources that session could not reach have since been
fetched and read, and §§4, 5, 9 and 11 are corrected against them.

```bash
uv run chunking-lab chunkers   # what is implemented, and what each strategy needs
make demo-chunking             # screen strategies: no model, no questions, no corpus
make chunking-benchmark        # reproduce the published column
```

**New to chunking?** Start with the explainer,
[`docs/where-the-cut-falls.html`](../../docs/where-the-cut-falls.html) — written
for someone who has never heard of it, with diagrams.
**Want the concepts defined properly?**
[`docs/007_chunking-concepts.md`](../../docs/007_chunking-concepts.md) covers every
one this tool is built from, with the trade-off each forces and where it lives in
the code.

`chunking-lab` is idea **#25** in [`IDEAS.md`](../../IDEAS.md). It takes one
corpus, runs it through many chunking strategies, and produces a score per
strategy — then, given a few sample documents, recommends which strategy to use
before you build a RAG pipeline at all.

---

## Table of contents

1. [Why this file exists](#1-why-this-file-exists)
2. [The sources that were blocked — now fetched](#2-the-sources-that-were-blocked--now-fetched)
3. [Research — the chunking taxonomy](#3-research--the-chunking-taxonomy)
4. [Research — how chunking is evaluated](#4-research--how-chunking-is-evaluated)
5. [Research — what the evidence says](#5-research--what-the-evidence-says)
6. [Research — does RAGAS do this?](#6-research--does-ragas-do-this)
7. [The key distinction: intrinsic vs extrinsic](#7-the-key-distinction-intrinsic-vs-extrinsic)
8. [Design](#8-design)
9. [The recommender](#9-the-recommender)
10. [Model strategy: API now, local later](#10-model-strategy-api-now-local-later)
11. [Decisions and their reasoning](#11-decisions-and-their-reasoning)
12. [Open questions — answered](#12-open-questions--answered)
13. [Implementation checklist](#13-implementation-checklist)
14. [Sources](#14-sources)

---

## 1. Why this file exists

The design work happened in a Claude Code **web** session. That session runs in
a sandboxed cloud VM whose outbound HTTPS goes through a policy-enforcing egress
proxy, and several primary sources were refused:

```
WebFetch https://research.trychroma.com/evaluating-chunking  -> EGRESS_BLOCKED
WebFetch https://www.trychroma.com/research/evaluating-chunking -> EGRESS_BLOCKED
WebFetch https://arxiv.org/abs/2504.19754                    -> EGRESS_BLOCKED
WebFetch https://docs.ragas.io/.../available_metrics/         -> EGRESS_BLOCKED
```

This is an organization/environment egress policy, not a network fault, and it
must not be routed around from inside that session. `raw.githubusercontent.com`
and `github.com` *were* reachable, and web **search** worked throughout (it runs
server-side), so the research below is real — but parts of it rest on search
summaries and source code rather than the primary prose.

**Every claim below is tagged with how it was verified**, and the tags are kept
honest as sources are read. Section 2 lists what was re-fetched in the CLI, where
there is no such restriction, and what each source changed.

**It was worth doing.** The headline metric had been reconstructed wrong, and the
one prior-art claim the earlier draft was most confident about was false. Both
are corrected below. This is the argument for the verification tags: they made
the gap findable instead of inherited.

> Note: the same restriction would *not* apply to the local CLI by default. The
> local CLI uses your own network. Its Bash sandbox (`/sandbox`) can restrict
> domains, but it prompts rather than hard-failing, and it does not apply to
> `WebFetch`. Beware that `claude --cloud` from your terminal creates a *cloud*
> session and would hit the same policy.

## 2. The sources that were blocked — now fetched

**Status: done.** Every source below was fetched and read in a local CLI session
on 2026-09-07, and checked against what §§4, 5 and 9 recorded. Three corrections
were material. Those sections are corrected in place below and their
verification tags updated; this table is the index of what each source settled.

| # | Source | What it settled |
|---|---|---|
| 1 | [Chroma — Evaluating Chunking Strategies](https://research.trychroma.com/evaluating-chunking) | **Precision Ω was reconstructed wrong**, in a way that would have flattered overlap — §4. Also the corpus build and the per-corpus filter thresholds (§5's were wrong), and the full results table (§5's reported numbers check out) |
| 2 | [`brandonstarxel/chunking_evaluation`](https://github.com/brandonstarxel/chunking_evaluation) | The metric implementation is **character-based**, treats overlap asymmetrically between two of its own metrics, and defaults to a per-question adaptive *k*. Its generator retries rather than reporting a yield — §4, §10 |
| 3 | [AutoRAG (arXiv 2410.20878)](https://arxiv.org/abs/2410.20878) | **The paper does not optimize chunking.** It fixes the corpus at 512/50 and names chunking as future work. §9's claim was false of the paper, and understated what the *framework* later added — §9 |
| 4 | [AutoRAGTuner (arXiv 2605.02967)](https://arxiv.org/abs/2605.02967) | Adaptive Bayesian optimization over a declarative config; chunking is not identifiable in its search space from the abstract — §9 |
| 5 | [Is Semantic Chunking Worth the Computational Cost? (arXiv 2410.13070)](https://arxiv.org/abs/2410.13070) | It measures **no cost or latency at all**, and semantic chunking *wins decisively* on topically heterogeneous documents. C14's verdict survives; its stated reasoning did not — §5, §11 |
| 6 | [Reconstructing Context (arXiv 2504.19754)](https://arxiv.org/abs/2504.19754) | Late chunking and contextual retrieval separated by near-noise margins — an independent evaluation that does not reproduce Anthropic's headline figures — §5 |

A prior-art sweep across SIGIR, ECIR, ACL Anthology and arXiv was also run, as §9
requires before any novelty claim is made. It found work close enough to falsify
what §9 called "possibly unclaimed". See §9.

**The finding that shaped the build.** Precision Ω is computed over *every* chunk
in the corpus and involves **no retrieval step at all**, and Chroma's five corpora
with their 472 gold-span questions are MIT-licensed. So the headline metric can be
checked against a published table — offline, model-free and deterministically.
That check is the first test to write, and it is this tool's `make demo`.

**Then** work through the checklist in §13.

## 3. Research — the chunking taxonomy

Six families, ordered by what supplies the boundary signal. That ordering is
also the cost ordering, which is why it is the useful axis.

| # | Family | Boundary signal | Cost | Examples |
|---|---|---|---|---|
| 1 | **Fixed-size** | character / token count | free | 512 chars, ± overlap |
| 2 | **Recursive / separator** | priority list of separators (`\n\n` -> `\n` -> `. ` -> ` `) | free | LangChain `RecursiveCharacterTextSplitter` |
| 3 | **Structural / document-aware** | the document's own markup — headings, tables, code fences, list items | free | Markdown-header splitting, AST chunking (this repo's `repo-rag` already does this), layout-aware PDF |
| 4 | **Semantic** | embedding similarity between adjacent sentences; cut at dissimilarity | 1 embedding pass | percentile-breakpoint, `ClusterSemanticChunker` |
| 5 | **LLM / agentic** | a model reads the text and picks boundaries, or rewrites into propositions | 1 LLM call per window | `LLMChunker`, propositional chunking |
| 6 | **Context-augmenting** | **boundaries unchanged**; the chunk's *representation* or *return unit* changes | varies | late chunking, contextual retrieval, sentence-window, parent-document |

*Verification: families and examples corroborated across multiple independent
sources via search; not controversial. Family 6's framing is this design's own.*

**Family 6 is the one most write-ups get wrong** by listing it alongside the
others. It does not move the cuts. It changes what gets embedded, or what gets
returned:

- **Late chunking** embeds the whole document at token level first, then mean-pools
  per chunk, so each chunk vector carries document context. Needs a long-context
  embedding model.
- **Contextual retrieval** prepends an LLM-written 50–100 token blurb to each
  chunk before embedding and BM25 indexing.
- **Sentence-window / parent-document** retrieve on a small unit but *return* a
  larger one.

**Design consequence:** the retrieval unit and the return unit can differ, so
the evaluator must score **the unit that actually reaches the model**. This is
why `Chunk` in §8 carries both `retrieval_text` and `return_text`. Get this
wrong and family 6 is unmeasurable.

## 4. Research — how chunking is evaluated

The naive approach — run the whole pipeline, have an LLM judge the answers — is
the wrong instrument. It is expensive, non-deterministic, and confounds three
variables (chunker, retriever, generator) when only one is being moved.

The method that works, from Chroma's technical report: **evaluate at the span
level against highlighted ground-truth excerpts, with no generation step at
all.** The report says "tokens" throughout; its implementation measures
**characters**, and so do we — see the table below.

You need a corpus plus questions, where each question is annotated with the
exact character spans that answer it. Then, for a given chunker + retriever + k:

```
gold      = the union of this question's gold spans
retrieved = the top-k retrieved chunks, in rank order
touching  = every chunk in the corpus overlapping gold, retrieval ignored

numerator   = |gold ∩ retrieved|      # union'd: a token counts once
recall      = numerator / |gold|
precision   = numerator / Σ|c| for c in retrieved
IoU         = numerator / (Σ|c| for c in retrieved  +  |gold missed|)
Precision Ω = |gold ∩ touching| / |union(touching) ∪ gold-in-no-chunk|
```

*Verification: all four are now **verified against both the report and
`base_evaluation.py`**, read in full. The earlier reconstruction of Precision Ω
was wrong — see immediately below. Everything in this section is `code`-verified.*

### The Precision Ω correction

The report defines it in one sentence:

> We report precision for the case that all chunks containing excerpt tokens are
> successfully retrieved as Precision_Ω. This gives an upper bound on token
> efficiency given perfect recall.

The earlier draft of this document guessed *"the **minimal** set of chunks that
fully covers the gold spans."* Those two readings coincide **only for a
non-overlapping partition**. Where chunks overlap, every chunk that so much as
touches a gold token enters the denominator, and the non-overlapping tails of
all of them inflate it; a minimal cover would have picked fewer.

The report's own table is the proof: Recursive at 400 with **200 overlap** scores
Precision Ω 13.9, against 17.7 for the same chunker at 400 with **no overlap**.
The old reading would have understated what overlap costs. Overlap is a
first-class knob of this tool, so implementing on the guess would have shipped a
quietly wrong headline number.

### Four more things the source says and the prose does not

| Finding | Consequence for this tool |
|---|---|
| Offsets are **characters**, not tokens, everywhere in the implementation (`sum_of_ranges` is `end - start` over `str` indices), despite the report's prose saying tokens | Our metrics are character-based. No tokenizer, therefore no model and no network — the headline metric is deterministic by construction |
| The retrieval `precision` denominator is a plain **sum** over retrieved chunks, so overlap double-counts; the Precision Ω denominator is a **union**, so it does not | Two different treatments of overlap inside one metric set. Reproduce both as they are, and say so — do not quietly "fix" one to match the other |
| The default `retrieve=-1` sets **k per question** to that question's own number of gold-bearing chunks, rather than a fixed k | k is adaptive unless you pass one. `--k` must be explicit, and every result row must record it, or two runs are not comparable |
| Locating a quoted excerpt is a three-stage cascade: exact match → whitespace-normalised regex → sentence-level fuzzy match at `token_sort_ratio >= 98` | This is the concrete spec for C9's quote-then-locate. Adopt the cascade as-is |

Range intersection, verbatim from the reference implementation:

```python
def intersect_two_ranges(range1, range2):
    start1, end1 = range1
    start2, end2 = range2
    intersect_start = max(start1, start2)
    intersect_end = min(end1, end2)
    if intersect_start <= intersect_end:
        return (intersect_start, intersect_end)
    return None
```

### Why Precision Ω is the headline metric

Recall and precision both move when the retriever changes. Precision Ω asks a
different question: **given where this chunker put its cuts, what is the best
any retriever could possibly achieve?**

A chunker that buries a one-sentence answer inside a 2000-token chunk has capped
your precision before retrieval even runs. Precision Ω is the chunking decision
made visible, isolated from everything downstream. That is the number this tool
exists to produce.

### Reading the numbers honestly

Absolute token-level precision comes out very low — Chroma reports single digits
— because you retrieve *k* chunks to answer a one-sentence question. **These are
relative comparisons only.** Any README written for this tool must say so, or it
will look broken.

## 5. Research — what the evidence says

This section shaped the design more than any other, because the literature does
**not** say "fancier chunking is better."

- **Recursive character splitting at ~200 tokens, no overlap, is a strong
  baseline.** Verbatim from the report: *"We find that the heuristic
  `RecursiveCharacterTextSplitter` with chunk size 200 and no overlap performs
  well. While it does not achieve the best result, it is consistently high
  performing across all evaluation metrics."* Its own default — 800 with 400
  overlap — is near the bottom. *(verified against the report)*
- **Semantic chunking's gains are inconsistent — but they are not absent, and the
  cost was never measured.** "Is Semantic Chunking Worth the Computational Cost?"
  (Qu, Tu & Bao) tested document retrieval, evidence retrieval and answer
  generation, and found no consistent gain. Two things the abstract does not say,
  and C14 originally leaned on the abstract:
  - **It reports no latency or cost figures at all** — the authors list this as a
    limitation. So the honest reading is "no consistent gain", not "measured and
    not worth it".
  - **Semantic chunking wins decisively on topically heterogeneous documents.**
    On stitched corpora it took F1@5 81.89 vs 69.45 on Miracl and 63.93 vs 43.79
    on NQ. It lost on natural documents (HotpotQA 84.79 vs 90.59; fixed-size best
    on 4 of 5 evidence-retrieval sets). The authors attribute the difference to
    evidence sentences clustering by *position* in real documents, and to
    embedding quality mattering more than the strategy.

  **This is a design input, not just a caveat: topic heterogeneity is a concrete
  corpus-profiling signal for `suggest` stage 1, backed by a measurement.**
  *(verified against the full paper)*
- **Context augmentation has the strongest *vendor-reported* numbers, and they do
  not independently replicate.** Anthropic reports failed retrievals down 35% with
  contextual embeddings, 49% adding contextual BM25 and 67% adding a reranker, at
  roughly one LLM call per chunk at index time. But *Reconstructing Context*
  (Merola & Singh, ECIR 2025 workshop) evaluated the same family independently on
  NFCorpus and MSMarco and found **near-noise margins**: NDCG@5 0.317 contextual
  vs 0.312 baseline, and 0.445 late vs 0.443 early. Its conclusion is a trade-off,
  not a win — contextual retrieval preserves coherence at higher cost, late
  chunking is cheaper but sacrifices relevance. Report both figures whenever this
  is cited. *(vendor figures corroborated across sources; independent replication
  verified against the paper)*
- **Chunk size interacts with everything** and is frequently a bigger lever than
  the strategy choice itself.
- Chroma bests, from the report's table: `ClusterSemanticChunker` at 400 took
  recall 91.3; at 200 it led precision (8.0), Precision Ω (34.0) and IoU (8.0).
  Top recall overall went to the **LLM chunker at 91.9**. *(verified — these are
  the exact published figures)*

**The honest summary — and the tool's reason to exist:** the ranking is
corpus-dependent, the expensive strategies frequently lose, and the only way to
know is to measure on your own documents.

## 6. Research — does RAGAS do this?

**No, and the reason it cannot is the reason this tool is worth building.**

Every RAGAS metric — context precision, context recall, context entity recall,
noise sensitivity, faithfulness, response relevancy — takes a `SingleTurnSample`
whose central field is `retrieved_contexts`. A retriever has already run. You
are measuring the pipeline, not the chunking decision.

The closest it gets is `NonLLMContextPrecisionWithReference`, which needs only
`retrieved_contexts` + `reference_contexts` and uses string distance rather than
a judge — deterministic and cheap. But it still requires retrieval to have run,
and, decisively:

**RAGAS treats a chunk as an atom.** Each retrieved chunk is scored relevant or
not, as a unit. That is the wrong granularity. It can tell you "chunk #3 was
irrelevant." It cannot tell you that:

- chunk #1 held the answer *plus 1,800 tokens of padding* (scores identically to a tight chunk)
- the answer was *severed across* chunks #2 and #3, so neither is usable alone
- a boundary landed mid-table

Those are the chunking failures. They require scoring *inside* the chunk — which
is exactly what token-level IoU and Precision Ω do.

**The two are complementary: RAGAS measures retrieval quality; token-span
metrics measure where the boundaries fell.**

One RAGAS component *is* directly useful: its testset generation builds a
knowledge graph from your documents and generates questions, including multi-hop
ones, and supports pre-chunked input. That is proven prior art for §9 stage 3.

*Verification: metric names and required fields from doc-derived search
summaries; `docs.ragas.io` was blocked. Re-verify before citing in the tool's
own docs.*

## 7. The key distinction: intrinsic vs extrinsic

This distinction is this design's central idea and is not, as far as the
research found, packaged anywhere as a tool.

### Intrinsic (query-free)

Computable from the document plus the chunk spans alone. No questions, no
retriever, no embeddings, no model.

| Signal | What it catches |
|---|---|
| **Boundary fidelity** | % of cuts landing inside a sentence, table row, code fence or list — the table-shredding failure |
| **Size distribution** | p95 length, % exceeding the embedding model's token limit (**silent truncation**), % runt chunks under ~50 tokens |
| **Coverage** | fraction of source tokens present in >=1 chunk. Anything below 1.0 is silent data loss — the `ingest-ledger` thesis applied to chunking |
| **Duplication factor** | tokens indexed / tokens in source — the direct index cost of overlap |
| **Orphaned reference rate** | chunks opening with "as described above", "the table below", unbound "it"/"this" — a deterministic proxy for the context loss that motivated late chunking and contextual retrieval |
| **Cohesion / separation** | *(needs embeddings)* intra-chunk sentence similarity vs across-boundary similarity |

### Extrinsic (query-dependent)

Needs questions + gold spans + a retriever. The §4 method.

### The relationship — state this in the shipped README

**Intrinsic metrics screen; extrinsic metrics rank.**

Coverage < 1.0, chunks over the token limit, or 40% of cuts landing mid-table
disqualify a configuration with no questions needed — real value delivered
before any pipeline exists. But intrinsic metrics **cannot** rank two reasonable
configurations, because "good chunking" is only defined relative to the
questions people ask. Any tool claiming a universal chunk-quality score without
queries is overselling.

## 8. Design

### 8.1 The load-bearing decision: chunkers return spans, not strings

```python
@dataclass(frozen=True, slots=True)
class Span:
    start: int  # char offset into the normalized document
    end: int
    retrieval_text: str  # what gets indexed   (may be augmented — family 6)
    return_text: str  # what reaches the model (may be a wider window — family 6)
```

Everything follows from this:

- Token-level IoU is only computable if chunks are addressable back into the source.
- Family 6 strategies become expressible in the same interface, no special case.
- It enables an **invariant every chunker must satisfy** — spans in bounds,
  ordered, and covering the document modulo declared overlap. That catches the
  classic bug where a chunker silently drops a trailing paragraph. This is
  `CONVENTIONS.md` rule 5 applied to the chunkers themselves.

Chunkers must also carry `Provenance` from `data_tools_core.provenance` so a
score traces back to bytes (rule: the data seam).

### 8.2 Tiers — so CONVENTIONS rule 3 holds

| Tier | Extra | Strategies |
|---|---|---|
| **0** | none | fixed-size (± overlap), recursive separator, sentence, structural/Markdown-header, sentence-window, parent-document |
| **1** | `embeddings` | semantic percentile-breakpoint, cluster-semantic |
| **2** | `llm` | LLM boundary detection, contextual-retrieval-style augmentation |

Tier 0 is the whole default experience: model-free, testable with nothing
installed, and it is what CI runs.

### 8.3 The retriever is held fixed

BM25 over SQLite FTS5 (already used in `repo-rag`), with `HashingEmbedder`
(from `ingest-ledger`) as a second deterministic option.

This is what keeps `chunking-lab` (#25) distinct from **`retrieval-bench` (#53)**:
**#53 varies the retriever with chunking fixed; #25 varies the chunker with the
retriever fixed.** Neither subsumes the other. Say so in both READMEs.

Every result row records **which path ran** (rule 2), so a semantic-chunker row
can never be silently compared against a run where the embeddings extra was
absent.

### 8.4 Ground truth without hand annotation

The usual blocker. Two paths, both offline-capable:

1. **A hostile corpus shipped with the tool**, in the exact spirit of
   `ingest-ledger`'s — documents built so specific strategies provably fail:
   - a fact whose subject appears only in the section heading (kills fixed-size)
   - a table split mid-row (kills everything but structural)
   - an answer straddling a paragraph break (kills naive recursive)
   - a code block containing blank lines (kills paragraph-greedy splitting)
   - a document with an "as described above" back-reference (the family 6 case)

   Spans are known **by construction** because the generator wrote them. No
   annotation step, no model in the loop. This is the default and what CI runs,
   and it should carry the `hostile` pytest marker so a strategy that stops
   failing is treated as a product regression, per `docs/000` §8.

2. **`chunking-lab annotate`** for bring-your-own corpora, with LLM-assisted
   span generation behind the `llm` extra.

### 8.5 CLI

```bash
chunking-lab score   --corpus ./samples --questions gold.jsonl \
                     --strategy fixed:512 --strategy recursive:512/64 \
                     --strategy structural --k 5
chunking-lab suggest --corpus ./samples
chunking-lab explain recursive:512/64 q07
chunking-lab annotate --corpus ./samples --out gold.jsonl   # needs `llm` extra
```

`explain` is the intuition-builder: it renders the gold span against what was
actually retrieved, so you *see* the answer sentence cut in half. A score column
cannot convey that.

### 8.6 Output

- A JSONL result per (strategy, config, question) carrying `Provenance`, the
  matched spans, and which code path produced the verdict.
- An **evidence card** under `evidence/` in the shape `docs/005_concept-coverage.md`
  specifies: the number, its baseline, the scale it was measured at, and the
  command that reproduces it. That makes the tool showcase-grade by the five
  criteria in `docs/005`, and readable later by `evidence-index` (#90).
- `make demo` reproduces the headline number in one command.

## 9. The recommender

`suggest` answers: *given a few sample documents, which chunking strategy should
I use?* — before the pipeline exists. Five stages; **only stage 3 needs a model.**

1. **Profile the corpus** — format mix, structural density (headings/tables/code
   per 1k tokens), length distribution, prose vs reference-material. Deterministic.
2. **Screen the grid** — run every candidate config through the intrinsic
   metrics (§7); eliminate the disqualified. Deterministic, fast, no questions.
3. **Manufacture ground truth** — generate question + gold-span pairs from the
   sample docs. The only model-dependent stage. See §10 for how it degrades safely.
4. **Rank survivors** — Precision Ω / IoU / recall (§4).
5. **Recommend with receipts** — winner, runner-up, the margin between them, and
   a confidence statement scaled to how few documents and questions it saw.

### `suggest` must degrade honestly

With no `llm` extra installed, run stages 1–2 only and report:

> *These 4 configurations are disqualified, and why. Ranking the remaining 3
> requires questions; install the `llm` extra or supply `gold.jsonl`.*

Never silently substitute a weaker verdict. `CONVENTIONS.md` rules 2 and 5.

### The risk that must be in the shipped README, not buried

**The recommendation is only as good as the synthetic questions.** A generator
producing single-sentence factoid questions systematically favours small chunks;
multi-hop and aggregation questions favour large or hierarchical ones.

So `suggest` must report the **question-type distribution** it evaluated against
and let the user reweight it. Stage 5 should be able to show the ranking
*flipping* as that weighting changes — because that is the actual lesson of the
tool, and hiding it would make this a recommendation engine with a hidden thumb
on the scale.

### Prior art — position, do not reinvent

**Automated RAG configuration search is established work. The recommender as
described is not novel; read this section before claiming otherwise.**

- **AutoRAG** (arXiv 2410.20878) selects RAG modules per dataset with a greedy
  node-wise search — evaluating a hard-to-score node against the node after it,
  so m+n trials replace m×n — scored with RAGAS Context Precision over 107
  human-reviewed QA pairs. **Distinguish the paper from the framework:**
  - **The paper does not optimize chunking.** §3.2.1 fixes the corpus at "a chunk
    size of 512 tokens and an overlap of 50 tokens", and Future Work names
    "appropriate chunking strategies" as work not yet done. An earlier draft of
    this section said chunk size and overlap were "explicitly among the
    hyperparameters it optimizes". **That is false of the paper.**
  - **The framework did later add it**, but outside the node search: parse →
    chunk → one corpus per configuration, each needing its QA `retrieval_gt`
    remapped, then end-to-end RAG performance on the already-chosen pipeline. Its
    ground truth is **chunk-level** — the same atom-level granularity §6
    criticises in RAGAS, and the reason it cannot see padding or a severed answer.
- **AutoRAGTuner** (arXiv 2605.02967) wraps the same life-cycle in a declarative
  config with a Domain-Element Model and adaptive Bayesian optimization. Whether
  chunking is in its search space is **not determinable from the abstract**; do
  not assert either way without reading the paper.
- **Mix-of-Granularity** (COLING 2025) trains a router to select chunk
  granularity *per query at runtime* — a trained component inside the pipeline,
  so a genuinely different problem from a design-time advisor. See also
  `FreeChunker` (ACL 2026 Findings) and query-adaptive semantic chunking.

An earlier draft of this document claimed no tool did design-time chunker
recommendation. **That was wrong**, and it was based on a few targeted searches
rather than a literature review. Corrected here so the claim is not inherited.

### What is claimed already — the sweep §9 asked for

That review has now been done, across SIGIR, ECIR, ACL Anthology and arXiv. **It
falsifies the "possibly unclaimed" framing.** The mechanism proposed in §7 — that
query-free intrinsic metrics can eliminate chunking configurations before any
retrieval happens — is published work, and so is the correlation experiment.

| Work | What it already does |
|---|---|
| **Adaptive Chunking** (arXiv 2603.25333, LREC 2026) | Selects a chunking method **per document from five intrinsic metrics** — References Completeness, Intrachunk Cohesion, Document Contextual Coherence, Block Integrity, Size Compliance — **with no retrieval or QA run**. This is §9's mechanism. "References Completeness" is the orphaned-reference rate this document called an idea with "no located antecedent" |
| **MoC** (ACL 2025 Long) | Boundary Clarity, `BC(q,d) = ppl(q\|d) / ppl(q)`, and Chunk Stickiness, a structural entropy over a perplexity-weighted chunk graph. Explicitly query-free and downstream-task-free, and shown to trend with RAG performance. Also reports the useful negative: **semantic-dissimilarity metrics do not** |
| **ChunkScore** (in QChunker, arXiv 2603.11650) | A downstream-task-free chunk-quality metric, validated by **correlation with QA performance at r > 0.85**. That is the §9 correlation experiment, already run |
| **Beyond Chunk-Then-Embed** (SIGIR '26) | A taxonomy splitting segmentation method from embedding–chunking ordering, over 36 methods. §3 calls family 6's framing "this design's own"; it is now published elsewhere too |
| **HiChunk / HiCBench** (ACL 2026 Long) | Manually annotated multi-level chunking points with evidence-dense QA — an existing annotated benchmark, and an alternative to §8.4's hostile corpus |

**What actually survives.** Every one of those intrinsic metric sets needs a
model: perplexity, embeddings, or an LLM. The set in §7 is **deterministic and
model-free** — it runs with nothing installed, on a laptop, offline. That is a
narrower and much less exciting distinction than "unclaimed", and it is the only
one this document should make.

**No novelty claim belongs anywhere in the shipped docs.**

### The question this tool makes cheap to re-ask

The tool is the instrument. The experiment below is a **replication**, not a
contribution — MoC, ChunkScore and Adaptive Chunking have each run a version of
it. What is left unanswered is one notch narrower, because all three used a
model to compute their intrinsic signals:

> **Do *model-free* intrinsic metrics predict query-dependent retrieval ranking?**

Method: take N chunker configurations across M corpora. Rank them by intrinsic
metrics alone (§7, no questions). Rank them by Precision Ω / IoU against gold
spans (§4). Report the rank correlation.

- **Correlates** — chunking configurations can be screened at a small fraction
  of the cost of a full evaluation, with no evaluation set at all.
- **Does not correlate** — a plausible-sounding shortcut is dead, which is worth
  knowing and worth writing down.
- **Correlates for some metrics and not others** — the most likely outcome, and
  the most informative: it identifies *which* query-free signals carry
  information about retrieval quality.

Design the result schema (§8.6) so this experiment is a query over accumulated
runs rather than a separate script.

## 10. Model strategy: API now, local later

Already solved by this repo. `data_tools_core.llm` exposes two protocols
(`EmbeddingProvider`, `ChatProvider`) satisfied by LiteLLM; `config.py` reads
`DATA_TOOLS_*`. Switching is configuration, never code:

```bash
# hosted
export DATA_TOOLS_CHAT_MODEL=anthropic/claude-sonnet-4-5
export DATA_TOOLS_EMBED_MODEL=openai/text-embedding-3-small
export DATA_TOOLS_API_KEY=...

# local — same code, same tests, same artifacts
export DATA_TOOLS_CHAT_MODEL=ollama/llama3.1
export DATA_TOOLS_EMBED_MODEL=ollama/nomic-embed-text
export DATA_TOOLS_API_BASE=http://localhost:11434
```

`chunking-lab` depends only on the protocols, so it never learns which side of
that line it is on. **No part of this design assumes a strong local model, and
nothing needs revisiting when one becomes available.**

### The stages need very different model strength

| Stage | Model | Volume | Quality needed | Verdict |
|---|---|---|---|---|
| Tier 0 chunkers, all intrinsic metrics, BM25, scoring | **none** | — | — | Always works. No key, no GPU. |
| Semantic chunking (Tier 1) | embeddings | moderate | moderate | **Local is genuinely fine** — `nomic-embed-text` / `bge-small` are competitive. |
| Contextual augmentation (Tier 2) | chat | **high** — one call per chunk | **low** — one sentence per chunk | **Local is fine, and this is where the volume is.** |
| Question + gold-span generation | chat | **low** — ~50–100 per corpus | **high** | Use the API. Low volume keeps the cost small. |

Convenient result: the stage that would cost real money tolerates a weak model;
the stage needing a strong model barely runs.

### Ground truth is an artifact, not a runtime dependency

**This is the move that makes model strength a non-issue.** Generate the question
set once with a strong hosted model, resolve the spans, write `gold.jsonl`, and
**commit it**. Every run afterwards — every strategy comparison, every CI job,
every rerun years later — is deterministic, offline and free.

You pay the API once per corpus, not once per experiment. It drops straight into
the existing data seam ("artifacts, not objects"), keeps `make test` model-free
per rule 6, and means a weak machine never blocks the measurement.

### The trick that makes weak models degrade safely

Gold spans need exact character offsets, and LLMs are unreliable at emitting
them. **So do not ask for offsets.** Ask the model to quote the answer
**verbatim**, then locate that string in the source deterministically — exact
match first, fuzzy fallback — and **discard any question whose quote cannot be
located.**

This inverts the failure mode. A weaker model does not produce *wrong* ground
truth; it produces *less* of it. You get 40 usable questions instead of 90. The
tool reports the **yield**, so model quality shows up as a number instead of
silently corrupting results.

The reference implementation confirms the locate cascade (exact →
whitespace-normalised regex → sentence-level fuzzy at `token_sort_ratio >= 98`)
but **not** the yield reporting: on a failed locate it discards the question and
*retries the model until it has enough*, so a weak model shows up as a longer
run and a larger bill, not as a number. **Reporting the yield instead is ours,
and it is the point of C9.**

Its two similarity filters are real, but the numbers earlier recorded here were
the *code defaults*, not what the paper used. The paper tunes both **per corpus**
by binary search — poor-excerpt threshold 0.40–0.43, duplicate threshold
0.67–0.73 — while the code defaults to 0.36 and 0.78. Neither "0.36 / 0.6" pair
was right. If we adopt these filters, tune per corpus and record the value used.

Practical consequence: local models are worth trying *today* — run it and read
the yield.

### The provenance rule that matters most here

**Every result row records which model wrote its questions.** Otherwise a run
whose questions came from a hosted model gets compared against one whose
questions came from a local model, and you conclude "chunker X is better" when
the truth is "model Y wrote easier questions."

**`suggest` must refuse to rank across question sets with different provenance.**

### Backlog connections

- **#24 `model-router`** — the table above *is* its use case: high-volume-easy
  local, low-volume-hard hosted.
- **#23 `embeddings-cache`** — pays for itself immediately; comparing N
  strategies re-embeds heavily overlapping text N times.
- **#50 `token-ledger`** — rather than quoting prices that go stale, print tokens
  consumed per stage and let the user price it against current rates.

## 11. Decisions and their reasoning

| # | Decision | Reasoning | Status |
|---|---|---|---|
| C1 | **Chunkers return spans, not strings** | Token-level IoU is uncomputable without offsets back into the source; also makes family 6 expressible and enables the coverage invariant | Firm |
| C2 | **Precision Ω is the headline metric** | It is the only metric that isolates the chunker from the retriever — the best any retriever could do given these cuts. It touches no retrieval at all, which is what makes it reproducible against a published table | Firm; **formula corrected** — the original reconstruction flattered overlap, see §4 |
| C3 | **Token-level metrics, not chunk-level** | Chunk-level (RAGAS-style) treats a chunk as an atom and cannot see padding or severed answers — the actual chunking failures | Firm |
| C4 | **No generation step in the evaluation** | Avoids confounding chunker/retriever/generator, and removes the LLM judge's cost and nondeterminism | Firm |
| C5 | **Retriever held fixed** | Keeps #25 disjoint from #53 `retrieval-bench`, which varies the retriever with chunking fixed | Firm |
| C6 | **Tier 0 is model-free and is the default** | CONVENTIONS rule 3; the deterministic core must be testable with nothing installed | Firm |
| C7 | **Intrinsic metrics screen, extrinsic metrics rank** | Intrinsic signals are cheap and query-free but cannot rank two reasonable configs, because chunk quality is only defined relative to the questions asked | Firm |
| C8 | **Ground truth is a committed artifact** | Pay the API once per corpus, then every run is deterministic, offline and free; keeps CI model-free | Firm |
| C9 | **Quote-then-locate for gold spans** | Turns an LLM weakness (exact offsets) into a filter; a weak model reduces yield rather than corrupting correctness | Firm |
| C10 | **Question-set provenance recorded; no cross-provenance ranking** | Otherwise differences in question difficulty masquerade as differences in chunker quality | Firm |
| C11 | **Hostile corpus as the default ground truth** | Spans known by construction, no annotation, no model; matches `ingest-ledger`'s precedent and the `hostile` marker convention | Firm |
| C12 | **`score` and `suggest` share one measurement engine** | `suggest` is `score` plus a decision rule; no duplicated logic | Firm |
| C13 | **`suggest` reports question-type distribution** | The recommendation is only as good as the questions; hiding that bias would make the tool dishonest | Firm |
| C14 | **Semantic chunking is Tier 1, not default** | Verdict unchanged, **reasoning replaced**. The paper measures no cost or latency at all, so it shows "no consistent gain", not "measured and not worth it". And semantic chunking *wins decisively* on topically heterogeneous corpora (§5). Tier 1 is right because the win is corpus-dependent — which is this tool's whole thesis — not because the method is bad | Firm; reasoning corrected against the full paper |
| C15 | Report relative comparisons, never absolute precision | Token precision is single-digit by construction at k>1; absolute numbers look broken | Firm |
| C16 | **The tool is a reproducible model-free instrument. Nothing here is claimed as novel** | **Rewritten.** The prior-art sweep (§9) found the mechanism already published: Adaptive Chunking screens configurations from intrinsic metrics with no retrieval, and MoC and ChunkScore have both run the correlation experiment. What survives is that all of them need a model and this one does not, plus a headline metric checkable against a published table. That is engineering worth doing and a claim worth making — but it is not a research contribution | Firm; replaces the earlier novelty framing |
| C17 | **Precision Ω is validated against Chroma's published column, not just unit-tested** | The metric was reconstructed wrong once already. Since it needs no retrieval and the benchmark is MIT-licensed, "our implementation is correct" can be a falsifiable offline test rather than an assurance | Firm; new, from the §2 re-fetch |

## 12. Open questions — answered

Put to the user and decided on 2026-09-07, after the §2 research was settled.

1. **Scope of the first cut.** Tier 0 + the hostile corpus + intrinsic and
   extrinsic metrics + report, **plus reproducing Chroma's Precision Ω column**.
   Tiers 1–2 stay declared and unimplemented. The reproduction was not in the
   original three options; it became possible once §4 established that Precision Ω
   needs no retrieval and no tokenizer.
2. **Corpus.** The hostile corpus is the default and is what CI runs. Chroma's
   five corpora ride along as a **validation fixture only** — the thing that
   proves the Precision Ω implementation is right. Not a second evaluation target.
3. **`suggest` timing.** `score` first. `suggest` stays declared and unbuilt until
   the metrics are proven, per C12 — it is `score` plus a decision rule.
4. **The correlation experiment.** Kept, and it does constrain §8.6 — but
   **reframed as a replication** (§9), with the narrower model-free question.
   Intrinsic and extrinsic metrics are computed over the *same* runs and stored on
   the same row, so the rank correlation is a `GROUP BY` over accumulated results
   rather than a separate script.

Two further requirements were added at the same time:

- **Documentation is written as the work proceeds**, not retrofitted: the design,
  the decisions, how each part works, and usage all land in the same commit as the
  code they describe.
- **One HTML blog post**, written for a reader who knows nothing about chunking —
  following the precedent of `docs/double-entry-for-documents.html`.

## 13. Implementation checklist

Follows `docs/000_project-organization.md` §10.

- [x] Re-fetch the blocked sources in §2; correct §4, §5 and §9 where they differ
- [x] Run the related-work sweep §9 requires before any novelty claim
- [x] Answer the four open questions in §12
- [x] Scaffold `tools/chunking-lab/` — `pyproject.toml` (dist `data-tools-chunking-lab`),
      `src/chunking_lab/`, `tests/`; copy the packaging table in `docs/000` §4 exactly
- [x] Declare the spin-out seam (`[tool.uv.sources] data-tools-core = { workspace = true }`) **on day one**
- [x] Register the console script, the `data_tools.tools` entry point, a `__main__.py`,
      and a one-line `main()` docstring for `dt ls`
- [x] Declare `llm` as an extra, never a base dependency; plus `benchmark` for the
      tokenizer the C17 reproduction needs and nothing else does
- [x] **Write the tests first** — the chunker invariant, which turned out to be "no
      non-whitespace character is dropped" rather than "coverage == 1.0": the
      reference implementation trims its boundaries, so the stricter rule is wrong.
      Coverage is reported as a number instead
- [x] Implement `Span`, the chunker protocol, and the first Tier 0 chunkers
      (`fixed`, `recursive`), the recursive one verified **differentially** against
      the reference over 28 cases — which immediately caught a separator-placement
      defect the invariant could not see
- [x] The remaining Tier 0 chunkers: sentence, structural/Markdown-header,
      sentence-window and parent-document. The last two are family 6, and they do
      prove `retrieval_text` / `return_text` earns its place — sentence-window
      indexes one sentence and returns three, so a scorer that reads the wrong
      field credits it for context the model never saw
- [x] Tier 1 (`semantic`, `cluster-semantic`) behind the `embeddings` extra, with
      an offline hashing embedder so they are testable and demonstrable with
      nothing installed — and `code_path` on every result so a run against that
      fallback can never be ranked against one using a real encoder
- [x] Implement the intrinsic metrics (§7) — these need no ground truth, so they
      were indeed the fastest path to something useful: `chunking-lab metrics`
      already separates a fixed-size splitter (boundary fidelity 0.06, cuts 7% of
      code fences) from a structural one (0.83) on any document you have lying
      around, with no model and no questions
- [x] Build the hostile corpus generator; mark its tests `hostile`. Building it
      split §8.4's one idea into two: **severing** (the answer cut across chunks)
      and **orphaning** (the chunk intact, and useless without the heading, header
      row or antecedent that sits elsewhere). Only the first is a boundary problem
- [x] Implement the extrinsic metrics (§4) — character ranges, and the union/sum
      asymmetry between Precision Ω and precision preserved as the reference has it
- [x] Fetch Chroma's five corpora + questions (pinned commit, sha256-verified) and
      **assert Precision Ω reproduces the published column** (C17). It does, exactly:
      6.7 / 13.9 / 17.7 / 29.9. The original misreading would have scored
      8.6 / 16.8 / 17.8 / 30.7 — plausible in isolation, ~28% high wherever chunks
      overlap. `make chunking-benchmark`
- [x] Wire the retriever (BM25 over FTS5, stopwords dropped per `docs/LEARNINGS.md`)
      so recall/precision/IoU can be scored on a real corpus
- [x] `score` — one JSONL row per (strategy, corpus, question) carrying intrinsic
      and extrinsic metrics **together**, so the §9 correlation experiment is a
      group-by over accumulated rows rather than a separate script (open question 4)
- [x] `explain` — the intuition-builder, and it earns its place immediately: on
      `straddle.md` at `recursive:120` it shows the word "accounts" stranded alone
      in its own chunk while **Precision Ω reads a comfortable 98.4%**. The ceiling
      is high and the chunking is still broken, which is exactly what a score
      column cannot tell you
- [x] Quote-then-locate (C9's cascade: exact → whitespace-tolerant → fuzzy at ≥98),
      which `explain` uses to turn a quoted answer into offsets
- [ ] `report` (a rendered comparison), `annotate` and `suggest` — deferred by
      open question 3 until the metrics were proven. They are now
- [ ] `annotate` — the model half of quote-then-locate, behind the `llm` extra.
      The deterministic half (`chunking_lab.locate`) is built and tested; what is
      missing is only the prompt that asks for verbatim quotes, plus reporting the
      **yield** so a weak model shows up as a number rather than as bad ground truth
- [x] Write the evidence card (`evidence/chunking-lab.jsonl`); wire `make demo-chunking`
      and `make chunking-benchmark`
- [x] Write the explainer: [`docs/where-the-cut-falls.html`](../../docs/where-the-cut-falls.html),
      for a reader who has never heard of chunking. Published as an artifact at
      <https://claude.ai/code/artifact/079203e3-348b-4231-8437-e80827eaf5ff>
- [x] Add `docs/006_chunking-lab.md` as the design record, and
      `docs/007_chunking-concepts.md` as the concept reference
- [x] Append to `docs/LEARNINGS.md` (craft) and `docs/FINDINGS.md` (verdicts)
- [x] Mark #25 as built in `IDEAS.md`; note the #53 boundary in both entries
- [x] `make lint && make test` — green: 251 passed, 1 skipped
- [x] **`correlate`** — the §9 experiment, built *and run*. 14 strategies × 5
      corpora × 472 questions, no model, ~100s. The answer is a caution: chunk size
      predicts Precision Ω at −0.95, which is close to a tautology since Ω divides
      by the chunks holding the answer. What survives controlling for size is
      `duplication` (−0.64) and, surprisingly, `boundary_fidelity`, which *doubles*
      from ~+0.15 raw to +0.44. `mid_table_rate` and `split_fence_rate` are
      constant on this benchmark — untested, not disproven. `make chunking-correlate`,
      full result in `docs/FINDINGS.md` F8
- [ ] Re-run `correlate` on a corpus **with structure** — tables and code fences —
      so the two signals aimed at structural failures are actually tested

## 14. Sources

Read in full, and the sections above rest on them:

- [Chroma — Evaluating Chunking Strategies for Retrieval](https://www.trychroma.com/research/evaluating-chunking) — *report read; metric definitions, corpus construction, per-corpus thresholds and the full results table all verified*
- [brandonstarxel/chunking_evaluation](https://github.com/brandonstarxel/chunking_evaluation) — *reference implementation, cloned and read: `evaluation_framework/base_evaluation.py`, `synthetic_evaluation.py`, `utils.py`. MIT (Brandon Smith, 2024) — its five corpora and 472 questions are the C17 validation fixture*
- [AutoRAG (arXiv 2410.20878)](https://arxiv.org/abs/2410.20878) — *full paper read. Does **not** optimize chunking; see §9*
- [Is Semantic Chunking Worth the Computational Cost? (NAACL 2025 Findings)](https://aclanthology.org/2025.findings-naacl.114/) — *full paper read; C14's reasoning corrected against it*
- [Reconstructing Context (arXiv 2504.19754)](https://arxiv.org/abs/2504.19754) — *full paper read; ECIR 2025 workshop, Merola & Singh*

Read as abstract or summary only — tagged so, and not load-bearing:

- [AutoRAGTuner (arXiv 2605.02967)](https://arxiv.org/abs/2605.02967) — *abstract only; chunking not determinable from it*
- [Anthropic — Contextual Retrieval in AI Systems](https://www.anthropic.com/engineering/contextual-retrieval) — *vendor figures, corroborated across sources but not independently replicated — see §5*
- [Jina — Late Chunking in Long-Context Embedding Models](https://jina.ai/news/late-chunking-in-long-context-embedding-models/)
- [Ragas — available metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) and [testset generation](https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/) — *still search summaries only; §6 remains unverified against primary*
- [Late Chunking (arXiv 2409.04701)](https://arxiv.org/abs/2409.04701) — *not read*

Prior art found by the §9 sweep — read before writing `suggest`, or any claim:

- [Adaptive Chunking: Optimizing Chunking-Method Selection for RAG (arXiv 2603.25333)](https://arxiv.org/abs/2603.25333) — LREC 2026. *The closest prior art to §7 and §9*
- [MoC: Mixtures of Text Chunking Learners (ACL 2025 Long)](https://aclanthology.org/2025.acl-long.258/) — *Boundary Clarity and Chunk Stickiness*
- [QChunker / ChunkScore (arXiv 2603.11650)](https://arxiv.org/abs/2603.11650) — *the correlation experiment, already run*
- [Beyond Chunk-Then-Embed (SIGIR '26)](https://doi.org/10.1145/3805712.3808575) — *taxonomy over 36 segmentation methods*
- [HiChunk / HiCBench (ACL 2026 Long)](https://aclanthology.org/2026.acl-long.1372/) — *annotated multi-level chunking points*
- [Mix-of-Granularity (COLING 2025)](https://aclanthology.org/2025.coling-main.384/) — *per-query routing; a different problem*
- [FreeChunker (ACL 2026 Findings)](https://aclanthology.org/2026.findings-acl.730/)

In-repo references: [`IDEAS.md`](../../IDEAS.md) #25, #53, #24, #23, #50, #90 ·
[`CONVENTIONS.md`](../../CONVENTIONS.md) rules 1–6 ·
[`docs/000_project-organization.md`](../../docs/000_project-organization.md) §4, §8, §9, §10 ·
[`docs/005_concept-coverage.md`](../../docs/005_concept-coverage.md) (evidence card, showcase criteria) ·
`tools/repo-rag/src/repo_rag/chunk.py` (AST chunking) ·
`tools/ingest-ledger/src/ingest_ledger/chunk.py` (paragraph-greedy split) ·
`tools/ingest-ledger/src/ingest_ledger/embed.py` (`HashingEmbedder`) ·
`tools/docs-rag/src/docs_rag/ingest.py` (fixed-size split)
