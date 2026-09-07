# chunking-lab — compare chunking strategies, and recommend one

**Status: design only. No code yet.** This document is the complete handoff from
the web session that designed it. Everything needed to start building is here.

`chunking-lab` is idea **#25** in [`IDEAS.md`](../../IDEAS.md). It takes one
corpus, runs it through many chunking strategies, and produces a score per
strategy — then, given a few sample documents, recommends which strategy to use
before you build a RAG pipeline at all.

---

## Table of contents

1. [Why this file exists](#1-why-this-file-exists)
2. [Read this first if you are continuing in the CLI](#2-read-this-first-if-you-are-continuing-in-the-cli)
3. [Research — the chunking taxonomy](#3-research--the-chunking-taxonomy)
4. [Research — how chunking is evaluated](#4-research--how-chunking-is-evaluated)
5. [Research — what the evidence says](#5-research--what-the-evidence-says)
6. [Research — does RAGAS do this?](#6-research--does-ragas-do-this)
7. [The key distinction: intrinsic vs extrinsic](#7-the-key-distinction-intrinsic-vs-extrinsic)
8. [Design](#8-design)
9. [The recommender](#9-the-recommender)
10. [Model strategy: API now, local later](#10-model-strategy-api-now-local-later)
11. [Decisions and their reasoning](#11-decisions-and-their-reasoning)
12. [Open questions](#12-open-questions)
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

**Every claim below is tagged with how it was verified.** Section 2 lists
exactly what to re-fetch first in the CLI, where there is no such restriction.

> Note: the same restriction would *not* apply to the local CLI by default. The
> local CLI uses your own network. Its Bash sandbox (`/sandbox`) can restrict
> domains, but it prompts rather than hard-failing, and it does not apply to
> `WebFetch`. Beware that `claude --cloud` from your terminal creates a *cloud*
> session and would hit the same policy.

## 2. Read this first if you are continuing in the CLI

```bash
git fetch origin claude/rag-chunking-evaluation-uy5f9p
git checkout claude/rag-chunking-evaluation-uy5f9p
```

**The unfinished research.** Fetch these four, in this order. They are the only
gaps in the design.

| # | URL | What to extract | Why it matters |
|---|---|---|---|
| 1 | `https://research.trychroma.com/evaluating-chunking` | Exact definition of **Precision Ω**; how the 5 corpora and their gold excerpts were built; the full results table | §4's formulas are reconstructed from source code, not the report. Precision Ω is the headline metric of this tool — confirm the definition before implementing it. |
| 2 | `https://github.com/brandonstarxel/chunking_evaluation` (clone it) | `chunking_evaluation/evaluation_framework/` — the real metric implementation; `SyntheticEvaluation` — the question/excerpt generation and its filter thresholds (0.36 similarity for poor excerpts, 0.6 for duplicates) | This is the reference implementation of both the metric and the ground-truth generator. Read it before writing either. |
| 3 | `https://arxiv.org/abs/2410.13070` — *Is Semantic Chunking Worth the Computational Cost?* (NAACL 2025 Findings) | The experimental setup and where semantic chunking *did* win | Only the abstract's conclusion was available. This paper is the main argument for keeping semantic chunking in Tier 1 rather than the default. |
| 4 | `https://arxiv.org/abs/2504.19754` — *Reconstructing Context: Evaluating Advanced Chunking Strategies for RAG* | How it evaluates late chunking and contextual retrieval | Only the title was available. Directly relevant to Tier 2. |

Secondary, lower priority: `https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/`
(confirm §6), `https://arxiv.org/abs/2409.04701` (late chunking),
`https://aclanthology.org/2025.coling-main.384/` (Mix-of-Granularity, §9 prior art).

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

The method that works, from Chroma's technical report: **evaluate at the token
level against highlighted ground-truth spans, with no generation step at all.**

You need a corpus plus questions, where each question is annotated with the
exact character spans that answer it. Then, for a given chunker + retriever + k:

```
numerator   = |retrieved_spans ∩ relevant_spans|          # measured in tokens
recall      = numerator / |relevant_spans|
precision   = numerator / |retrieved_spans|
IoU         = numerator / |retrieved_spans ∪ relevant_spans|
precision Ω = the precision ceiling implied by the chunk boundaries
```

*Verification: `recall`, `precision` and `IoU` were read from the reference
implementation's source (`base_evaluation.py`) — reliable. **`precision Ω` was
not.** The code extract available was ambiguous between Precision Ω and IoU. The
report describes it as "maximum achievable precision under perfect recall". The
reading assumed here is: take the minimal set of chunks that fully covers the
gold spans, and compute that set's token precision. **Confirm against source 1
in §2 before implementing.***

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
  baseline.** Chroma found it never won outright but was consistently high
  across every metric. *(search summary of the report; unverified against primary)*
- **Semantic chunking may not earn its cost.** "Is Semantic Chunking Worth the
  Computational Cost?" (NAACL 2025 Findings) tested document retrieval, evidence
  retrieval and answer generation, and concluded gains over plain fixed-size
  splitting are inconsistent and do not justify the compute. *(abstract only)*
- **Context augmentation has the strongest reported numbers.** Anthropic's
  contextual retrieval reports failed retrievals down 35% with contextual
  embeddings, 49% adding contextual BM25, 67% adding a reranker — at roughly one
  LLM call per chunk at index time. *(figures corroborated across several
  independent sources; high confidence)*
- **Chunk size interacts with everything** and is frequently a bigger lever than
  the strategy choice itself.
- Reported Chroma bests: `ClusterSemanticChunker` at 400 tokens had near-top
  recall (~91.3%); at 200 tokens it led precision (~8.0%), Precision Ω (~34.0%)
  and IoU (~8.0%). *(search summary; treat as indicative, re-verify)*

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
    start: int           # char offset into the normalized document
    end: int
    retrieval_text: str  # what gets indexed   (may be augmented — family 6)
    return_text: str     # what reaches the model (may be a wider window — family 6)
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

**Mix-of-Granularity** (COLING 2025) trains a router to select chunk granularity
*per query at runtime*. Different problem: a trained component inside the
pipeline. This is an **offline, design-time advisor** that runs before the
pipeline exists and emits a configuration a human accepts or rejects. No tool
was found doing that, which is mild evidence it is worth building. See also
`FreeChunker` (arXiv 2510.20356) and query-adaptive semantic chunking.

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
silently corrupting results. (Chroma's pipeline filters similarly — reported
thresholds 0.36 for poor excerpts, 0.6 for duplicates; verify in source 2.)

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
| C2 | **Precision Ω is the headline metric** | It is the only metric that isolates the chunker from the retriever — the best any retriever could do given these cuts | Firm; **formula needs verifying** (§2 source 1) |
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
| C14 | **Semantic chunking is Tier 1, not default** | The NAACL 2025 finding that it may not justify its compute; making it default would assert the opposite of the evidence | Firm, pending source 3 |
| C15 | Report relative comparisons, never absolute precision | Token precision is single-digit by construction at k>1; absolute numbers look broken | Firm |

## 12. Open questions

These were put to the user in the web session and were **not answered** before
the handoff. Decide them first.

1. **Scope of the first cut.** Ship Tier 0 + hostile corpus + metrics + report,
   leaving Tiers 1–2 declared but unimplemented? (Recommended: yes — gets a real
   measured number fast and keeps it model-free.) Or go straight to all tiers?
2. **Corpus.** Synthetic hostile corpus only (reproducible, zero-dependency,
   CI-safe), or also ingest a real document folder from day one?
3. **`suggest` timing.** In the first cut, or land `score` first and build the
   advisor once the metrics are proven? (Recommended: `score` first.)

## 13. Implementation checklist

Follows `docs/000_project-organization.md` §10.

- [ ] Re-fetch the four blocked sources in §2; correct §4 and §5 where they differ
- [ ] Answer the three open questions in §12
- [ ] Scaffold `tools/chunking-lab/` — `pyproject.toml` (dist `data-tools-chunking-lab`),
      `src/chunking_lab/`, `tests/`; copy the packaging table in `docs/000` §4 exactly
- [ ] Declare the spin-out seam (`[tool.uv.sources] data-tools-core = { workspace = true }`) **on day one**
- [ ] Register the console script, the `data_tools.tools` entry point, a `__main__.py`,
      and a one-line `main()` docstring for `dt ls`
- [ ] Declare `embeddings` and `llm` as extras, never base dependencies
- [ ] **Write the tests first** — start with the chunker invariant (spans in bounds,
      ordered, coverage == 1.0 modulo declared overlap)
- [ ] Implement `Span`, the chunker protocol, Tier 0 chunkers
- [ ] Implement the intrinsic metrics (§7) — these need no ground truth, so they
      are the fastest path to something useful
- [ ] Build the hostile corpus generator; mark its tests `hostile`
- [ ] Implement the extrinsic metrics (§4) over BM25/FTS5
- [ ] `score`, then `report`, then `explain`
- [ ] `annotate` (quote-then-locate, behind the `llm` extra) and `suggest`
- [ ] Write the evidence card; wire `make demo`
- [ ] Add `docs/006_chunking-lab.md` as the design record (this README is the
      user-facing reference; per `docs/000` §9 the numbered doc holds the design
      and decisions — §11 above is its seed)
- [ ] Append to `docs/LEARNINGS.md` (craft) and `docs/FINDINGS.md` (verdicts)
- [ ] Mark #25 as built in `IDEAS.md`; note the #53 boundary in both READMEs
- [ ] `make lint && make test`

## 14. Sources

Verified reachable and used:

- [Chroma — Evaluating Chunking Strategies for Retrieval](https://www.trychroma.com/research/evaluating-chunking) — *report blocked; used via search summaries*
- [brandonstarxel/chunking_evaluation](https://github.com/brandonstarxel/chunking_evaluation) — *reference implementation; metric code read via raw.githubusercontent.com*
- [Is Semantic Chunking Worth the Computational Cost? (NAACL 2025 Findings)](https://aclanthology.org/2025.findings-naacl.114/) — *abstract only*
- [Anthropic — Contextual Retrieval in AI Systems](https://www.anthropic.com/engineering/contextual-retrieval) — *figures corroborated across several sources*
- [Jina — Late Chunking in Long-Context Embedding Models](https://jina.ai/news/late-chunking-in-long-context-embedding-models/)
- [Mix-of-Granularity (COLING 2025)](https://aclanthology.org/2025.coling-main.384/) — *abstract/summary only*
- [Ragas — available metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) — *blocked; used via search summaries*
- [Ragas — testset generation for RAG](https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/) — *blocked; used via search summaries*
- [Reconstructing Context: Evaluating Advanced Chunking Strategies for RAG (arXiv 2504.19754)](https://arxiv.org/abs/2504.19754) — *blocked; title only*
- [Late Chunking (arXiv 2409.04701)](https://arxiv.org/abs/2409.04701) — *not read*

In-repo references: [`IDEAS.md`](../../IDEAS.md) #25, #53, #24, #23, #50, #90 ·
[`CONVENTIONS.md`](../../CONVENTIONS.md) rules 1–6 ·
[`docs/000_project-organization.md`](../../docs/000_project-organization.md) §4, §8, §9, §10 ·
[`docs/005_concept-coverage.md`](../../docs/005_concept-coverage.md) (evidence card, showcase criteria) ·
`tools/repo-rag/src/repo_rag/chunk.py` (AST chunking) ·
`tools/ingest-ledger/src/ingest_ledger/chunk.py` (paragraph-greedy split) ·
`tools/ingest-ledger/src/ingest_ledger/embed.py` (`HashingEmbedder`) ·
`tools/docs-rag/src/docs_rag/ingest.py` (fixed-size split)
