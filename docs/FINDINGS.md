# Findings (running log)

Project **verdicts, conclusions, and direction decisions** — what's useful, what
we're building or parking, and why. Append a new `## Iteration N` section at the
**top** each sprint.

> For reusable craft, see [LEARNINGS.md](./LEARNINGS.md).

---

## Iteration 7b — 2026-09-07 — which knob matters more

### F10 — the chunker always matters; the retriever usually doesn't, and occasionally matters just as much
Run against a real encoder (`ollama/nomic-embed-text`, 768-dim, local — 21
seconds). Five strategies × three retrievers × five corpora, each axis measured
with the other held fixed, compared by the best/worst ratio in IoU.

| axis | n | min | median | max | exceeds 2× |
|---|---|---|---|---|---|
| chunker | 15 | 4.2× | **5.6×** | 14.4× | **15/15** |
| retriever | 25 | 1.0× | **1.3×** | 14.9× | **4/25** |

**The median answer — "the chunker matters more" — is true and hides the
interesting half.** The two axes do not differ in *size*; their maxima are
effectively identical (14.4× vs 14.9×). They differ in **how often**. Changing the
chunker moved IoU by more than 2× in *every case tested*. Changing the retriever
did so in 4 of 25, and was under 1.2× in half of them.

So the honest statement is not "chunking is the big knob". It is:

> **Chunking matters consistently. Retrieval matters rarely and then enormously.**

That is a different piece of advice. It says: fix chunking first because it always
pays, but do not assume retrieval is settled — the cases where it matters are
catastrophic, not marginal.

**Every one of the four cases is BM25 collapsing and a semantic retriever rescuing
it.** `recursive:200` on `spec.md`: BM25 scores 1.3 IoU, vector scores 19.7.
`structural` on `runbook.md`: 2.7 against 33.6. Semantic retrieval beat BM25 on
*every* strategy tested, but usually by 1.05–1.26× — and once by 2.01×.

**A hypothesis that did not survive.** The obvious explanation is that the
retriever matters more when the chunking is worse. It does not: the rank
correlation between a configuration's IoU and its retriever spread is **−0.04**,
which is nothing. Whatever makes BM25 collapse is not simply bad chunking.

**Caveats that travel with this.** Five strategies and three retrievers, so a
spread is only as wide as the options offered — adding a worse chunker or a
reranker moves these numbers. Synthetic documentation corpus. One encoder. And the
comparison is on IoU: Precision Ω cannot be used, because it is
retriever-independent by construction and would report no retriever effect at all.
`make chunking-axes`.

## Iteration 7 — 2026-09-07 — the structural signals, finally tested

### F9 — `mid_table_rate` does not predict retrieval quality. `split_fence_rate` barely does.
F8 left these two **untested**: the Chroma corpora contain no Markdown tables and
no code fences, so both signals were constant and there was nothing to correlate.
A generated documentation corpus — 5 documents, 180 questions, tables and fences
throughout, gold spans known by construction — closes that gap. The answer is a
clean negative, which is worth more than the guess it replaces.

| signal | vs Ω, per corpus | vs IoU, per corpus | partial (size removed) |
|---|---|---|---|
| `mid_table_rate` | −0.47, +0.34, −0.40, +0.18, *const* | −0.50, +0.24, −0.05, +0.07, *const* | +0.20 / +0.15 |
| `split_fence_rate` | **−0.63\***, *const*, +0.07, +0.29, −0.47 | **−0.82\***, *const*, −0.00, −0.38, **−0.69\*** | +0.04 / −0.29 |

**`mid_table_rate` fails outright.** Not significant on any corpus against any
target, and the sign flips between corpora. And there is a mechanism, which is the
useful part: cutting through a table row makes the chunks holding the answer
*smaller*, which **raises** the precision ceiling. Precision Ω is structurally the
wrong target for a "did you damage the content" signal — the damage is to whether
a retrieved chunk is *usable*, which no ceiling metric measures.

**`split_fence_rate` is directionally right where code is dense.** Significant and
negative on `api_reference` (−0.82 vs IoU) and `tutorial` (−0.69), the two corpora
with the most fenced code; nothing on the others. Real but weak, and it collapses
to −0.29 once size is controlled.

**Two findings from F8 replicate on an independent corpus**, which is the stronger
result here:

- `duplication`: partial −0.64 on Chroma, **−0.62** here. Overlap costs beyond size.
- `boundary_fidelity`: partial +0.44 on Chroma, **+0.34** here, and significant on
  3 of 5 corpora against IoU. The signal that looks worthless raw is the one that
  holds up across two unrelated corpora.

**Verdict, and it vindicates §7's original framing.** These structural signals are
**disqualification** signals, not **ranking** signals. "This configuration shreds
40% of your tables" is a reason to reject it; it is not a prediction of where it
will place. The correlation experiment now says so with evidence rather than
assertion, and `disqualifications()` — which returns faults and has deliberately
never had a scoring function — was the right shape all along.

**Stated limitation.** The corpus is synthetic. The generator decides where the
tables are and where the answers are; it does **not** decide whether shredding
them hurts, which is measured. So this says how the signals behave on documentation
*shaped* like this, not how often such documents occur. `make chunking-correlate-structured`.

## Iteration 6 — 2026-09-07 — the chunking correlation experiment

### F8 — model-free intrinsic signals do predict the ranking, and mostly by proxying chunk size
The §9 experiment, run: 14 strategies × 5 corpora × 472 questions, 70 points, no
model. Spearman rank correlation of each query-free signal against Precision Ω,
per corpus, with the partial correlation controlling for median chunk length.

| signal | ρ vs Ω (range over 5 corpora) | partial, size removed |
|---|---|---|
| `median_length` | −0.94 … −0.97 | *(control)* |
| `p95_length` | −0.78 … −0.96 | +0.26 |
| `chunks` | +0.75 … +0.88 | −0.63 |
| `duplication` | −0.69 … −0.78 | **−0.64** |
| `runt_rate` | +0.71 … +0.79 | +0.35 |
| `orphan_rate` | +0.41 … +0.66 | +0.50 |
| `oversize_rate` | −0.23 … −0.45 | +0.09 |
| `boundary_fidelity` | +0.04 … +0.24 | **+0.44** |
| `mid_table_rate`, `split_fence_rate` | *constant — untested* | — |

**The headline is a caution, not a win.** Chunk size correlates at −0.95 and that
is very close to a tautology: Precision Ω is `|gold| / |the chunks holding gold|`,
so smaller chunks shrink the denominator by construction. Anyone reporting that
number as evidence that intrinsic screening works would be reporting arithmetic.

Three things survive that caveat:

- **`duplication` carries real information** (partial −0.64 against Ω, −0.50
  against IoU). Overlap costs you *beyond* what its effect on size explains. This
  is the one signal that is both cheap and independently predictive.
- **`boundary_fidelity` is the opposite of what the raw number says.** Raw ρ is
  ~+0.15 and looks useless; controlling for size it rises to **+0.44**. Size was
  masking it — strategies that cut cleanly also cut larger. The signal that looked
  worthless is the one most improved by asking the question properly.
- **`orphan_rate` and `runt_rate` are positive**, which does *not* mean orphans
  help. Both rise as chunks shrink, and shrinking chunks raises Ω. They are size
  proxies that partialling only partly removes. Do not screen on them.

**And the honest gap:** `mid_table_rate` and `split_fence_rate` are *constant* on
all five corpora, because the benchmark contains no Markdown tables and no code
fences. They are **untested here, not disproven** — which matters, because they are
the two signals aimed at the structural failures the hostile corpus is built
around. Testing them needs a corpus with structure. That is the next measurement,
not a conclusion.

**Verdict.** Query-free screening is worth doing for *disqualification* (§7's
original claim) and `duplication` is worth trusting as a ranking hint. Screening
on the rest is screening on chunk size wearing a hat. `make chunking-correlate`.

## Iteration 5 — 2026-09-07 — ingest-ledger

### F7 — `ingest-ledger`'s memory cap never worked on macOS, and the ledger said it did
The subprocess memory cap is one of the tool's two headline safety mechanisms.
`RLIMIT_AS` is not settable on Darwin, the worker called `setrlimit`
unconditionally, and so every file extracted through the default (subprocess) path
came back `FAILED — exit 1: ValueError`. On the hostile corpus: 0 of 9 files read
before the fix, 6 of 9 after.

Two lessons, and the second is the one to carry.

**Cross-tool test suites earn their keep.** This was found by running `make test`
while working on an unrelated tool. Nobody was looking at `ingest-ledger`.

**The tool committed its own cardinal sin.** Its thesis is "never report a status
the probe did not earn", and its evidence recorded `memory_cap_mb: 512` for runs
with no cap. Fixed by making the cap best-effort and recording whether it applied.
Worth a periodic audit of every other capability this collection *claims* in an
evidence dict without checking: a claim in a record is a claim, and unverified
claims are what these tools exist to find.

## Iteration 4 — 2026-09-07 — chunking-lab

### F4 — chunking-lab's contribution is reproducibility, not novelty
The design record proposed that query-free intrinsic metrics screening chunking
configurations was an unclaimed mechanism, and that measuring whether they predict
retrieval ranking was the contribution. A proper related-work sweep says otherwise:
**Adaptive Chunking** (LREC 2026) selects a chunking method per document from five
intrinsic metrics with no retrieval run; **MoC** (ACL 2025) and **ChunkScore**
(QChunker) have both already correlated query-free metrics against downstream QA.

What survives is narrow and real: every one of those needs a model — perplexity,
embeddings, or an LLM — and this one does not. Tier 0 runs with nothing installed,
offline, deterministically. **No novelty claim goes in the shipped docs.** The tool
is worth building as an instrument; it is not a result.

### F5a — the reproduction worked, and the misreading is measured

F5 proposed checking Precision Ω against Chroma's published column instead of
against our own understanding. Done, and it reproduces **all four values exactly**
— 6.7 / 13.9 / 17.7 / 29.9 — over 472 questions, offline, with no retriever and no
model, because Precision Ω involves no retrieval.

The counterfactual is the part worth keeping. Implemented from the design record's
original reading, the same code scores **8.6 / 16.8 / 17.8 / 30.7**: nearly right
with no overlap, ~28% high wherever chunks overlap. It would have passed every
unit test written against it, looked entirely plausible, and **quietly recommended
overlap** — on the exact axis the tool exists to compare. Both readings are kept
implemented so the gap stays under test.

Cost: about an hour of re-fetching sources plus a 1.6MB download. Do this whenever
a tool's headline number has a published counterpart.

### F5 — a published table is a better correctness test than a unit test
Precision Omega touches no retrieval, and Chroma's five corpora with 472 gold-span
questions are MIT-licensed. So "is our headline metric implemented correctly?" can
be a **falsifiable offline check against someone else's published numbers**, not an
assurance. Given the metric had already been reconstructed wrong once, that is the
difference between a tool and a tool you would quote.

Generalises: before writing a metric, check whether a public benchmark plus a
published results table exists. Reproducing three numbers is worth more than thirty
tests you wrote against your own understanding.

### F6 — the semantic-chunking verdict is corpus-dependent, which is the thesis
"Is Semantic Chunking Worth the Computational Cost?" is read as "no". The full
paper is more useful than its title: it **measures no cost or latency at all** (a
stated limitation), and semantic chunking *wins decisively* on topically
heterogeneous documents — F1@5 81.89 vs 69.45 on Miracl — while losing on natural
ones. So the honest summary is "no consistent gain", and **topic heterogeneity
becomes a corpus-profiling signal** for the recommender rather than a caveat in a
footnote. This is the strongest single piece of evidence for the tool's premise:
the ranking depends on your documents, so measure on your documents.

## Iteration 3 — 2026-09-03

### F7 — Confining an integration bounds its API surface, not its runtime assumptions
`repo-rag` is now on the MCP SDK 2.x (`mcp>=2.1.1,<3`). The rename that caused
the original pin (`FastMCP` → `MCPServer`) cost **three lines** in the one
adapter module — CONVENTIONS r4 working exactly as designed.

The upgrade's real content was elsewhere, and r4 gave no protection from it:

1. **2.x dispatches tool calls on a worker thread.** `CodeStore` opened its
   SQLite connection on the main thread, and SQLite connections are
   thread-affine. Every `search_code`/`get_chunk` **over the wire** failed with
   *"SQLite objects created in a thread can only be used in that same thread"*.
   The fix — `check_same_thread=False` behind an `RLock` — landed in `store.py`,
   not the adapter. A dependency's threading model reaches through any
   confinement you put around its API.
2. **A bare `-> dict` annotation now yields no structured output.** 2.x builds an
   output schema from the return type; unparameterised `dict` produces none, and
   the SDK sends `structured_content=None`. Clients reading structured content
   got nothing. `dict[str, object]` is load-bearing.

**The verdict that matters:** the whole suite passed on 2.x *before* either
defect was found, because the tests asserted **tool registration** with a
**fake store**. Registration proves the decorator ran. It does not prove
dispatch works, and a fake store cannot exhibit the real store's threading
constraints. Tests now drive a real `CodeStore` through `call_tool`, and that
test was verified to fail without the fix.

Generalised: **for an integration, test the seam the way the dependency will
actually use it** — through its dispatch path, against your real resources.
Anything less tests your own decorator.

### Note — the pin policy changed
`mcp` is bounded `>=2.1.1,<3` rather than pinned exactly. The unbounded `>=1.0`
is what let the break happen; the **major bound** is the part that prevents a
repeat. Patch and minor releases of a protocol SDK are left to float so security
fixes are not gated on a manual bump. Where a dependency's *behaviour* (not just
its API) determines a tool's verdicts — `ingest-ledger`'s `pdfmux==1.8.7` — pin
exactly instead.

---

## Iteration 2 — 2026-09-03

### F4 — The collection now has three tools and one set of conventions
`docs-rag` (#1) and `repo-rag` (#2) were merged onto main and adapted to the
`ingest-ledger` conventions: distributions renamed `data-tools-<tool>`, the
shared model layer moved from `dt_shared` to `data_tools_core.llm` as an
optional extra, entry-point discovery added, workspace unified on Python 3.13.
Rationale in [`001`](001_architecture-and-decisions.md) (D1a, D2a, D9); the
current shape in [`000`](000_project-organization.md).

### F5 — The two branches agreed on principles and differed only on mechanics
Independently, both lines of work arrived at: tools never import each other,
each tool independently installable, SQLite as the substrate, MCP as a seam, and
a deterministic core testable without a model. That convergence is why the merge
was a reconciliation rather than a rewrite — and why those five rules are the
ones to defend hardest.

Where they differed (umbrella root vs. non-package root; `dt_shared` vs.
`data_tools_core`; extras policy) the `ingest-ledger` position won on every
point, because in each case it took "a tool must run alone" more literally.

### F6 — The model layer became optional, not merely mockable
`CONVENTIONS.md` rule 3 has always said a tool that cannot run without a model
cannot be tested. Iteration 1 satisfied that by *mocking* litellm; the shared
library still depended on it. It is now genuinely optional: `data-tools-core`
carries no base dependencies, `litellm` is imported inside the call and ships as
the `llm` extra. The stronger form is worth the small cost — it makes the rule
checkable rather than aspirational, and `test_llm.py` now asserts it directly.

### Owed — upgrade `repo-rag` to the MCP SDK 2.x
**Done.** See F7 below for what it turned up.

### Carried forward, unchanged
The Iteration 1 verdicts still stand and still direct the work:
- **F2** — a RAG-as-MCP tool's value depends on the consumer. `ingest-ledger`
  is the constructive answer: it does what a capable model with file access
  cannot do for itself, namely prove what it *failed to read*.
- **repo-rag stays parked.** It was merged to preserve the exercise and its
  design record, not because the F2 verdict changed. Its real home remains a
  no-filesystem consumer.
- **docs-rag is the more defensible RAG tool** — and is now better understood as
  a *downstream* of `ingest-ledger` (grounded generation over an already
  reconciled index) than as a standalone folder-Q&A tool. `CONVENTIONS.md`
  anticipates exactly this in the data seam.
- The Tier-1 retrieval fixes (stopword-aware keyword search, excluding docs from
  the index, larger/diverse k) remain valid if `repo-rag` is resurrected.

---

## Iteration 1 — 2026-06-08

### F1 — Agentic consumption >> single-shot retrieval
Driving repo-rag's MCP from Claude (looping `search_code` / `get_chunk`) clearly
beat the single-shot `ask` CLI: the client iterates and a strong model synthesizes.
The weakness in `ask` was retrieval breadth + an 8B local synthesizer — not "RAG."

### F2 — A RAG-as-MCP tool's value depends on the *consumer*, not the retriever
In **Claude Code** (which already has Grep/Glob/Read), `search_code`/`get_chunk` are
largely **redundant** — Claude itself said it would answer better by reading files
directly. The tool earns its keep only for:
- **semantic "by meaning"** queries grep can't phrase (e.g. "retries" when the code
  says "backoff"), and
- **consumers with no filesystem** (Claude Desktop, hosted agents, custom apps),
  where it *is* the retrieval layer.

### F3 — Enumeration needs structured tools, not fuzzy search
"What tests are in my project?" can't be answered reliably by top-k semantic search
at any k. It needs deterministic `list_files` / `list_symbols`.

### Decision — park `repo-rag`, move on
repo-rag was a high-value **exercise** (AST chunking, hybrid retrieval, MCP serving,
agentic consumption, and the meta-lesson in F2) but is structurally **redundant for
our primary client, Claude Code**. We are **not investing further in repo-rag** now.
Next effort goes to tools that are non-redundant precisely because the host can't do
them itself:
- **`docs-rag`** — semantic Q&A over PDFs/arbitrary docs with citations (the host
  can't read your documents and ground an answer). The more defensible RAG tool.
- a **system-access MCP** such as `sqlite-mcp` (#11) — touches a system Claude can't
  reach, so it never competes with built-in file tools.

### Carried forward
- If repo-rag is ever revisited, its real home is a **no-filesystem consumer** — test
  it in Claude Desktop, where it stops competing with grep.
- The Tier-1 retrieval fixes (stopword-aware keyword search, exclude docs from the
  index, larger/diverse k) remain valid *if* repo-rag is resurrected — but are not
  worth doing for the Claude Code use case.
