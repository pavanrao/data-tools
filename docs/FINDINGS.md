# Findings (running log)

Project **verdicts, conclusions, and direction decisions** — what's useful, what
we're building or parking, and why. Append a new `## Iteration N` section at the
**top** each sprint.

> For reusable craft, see [LEARNINGS.md](./LEARNINGS.md).

---

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
