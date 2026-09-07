# 006 — chunking-lab

**Idea #25.** Take one corpus, run it through many chunking strategies, and score
each one *at the character level against gold spans* — so the number reflects
where the cuts landed, not how good the retriever or the model happened to be.

The user-facing reference, the research behind every choice, and the sixteen
decisions live in [`tools/chunking-lab/README.md`](../tools/chunking-lab/README.md).
This document is the design record: what is built, how each part works, and why
it is shaped that way. Per `docs/000` §9 the numbered doc holds the design; the
README holds the usage.

**Status.** Tier 0 chunkers and the invariant that governs them. The metrics, the
hostile corpus, and `score` are not built yet — see the checklist in README §13.

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
- **`chunkers/__init__.py`** — `from_spec` parses the strategy specs
  (`recursive:400/200`) that name a run on the command line and in every result row.
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
uv run chunking-lab split README.md --strategy recursive:400/200
uv run chunking-lab split README.md --strategy fixed:400 --limit 0
```

## Next

README §13 is the checklist. In order: the intrinsic metrics (§7, no ground truth
needed, so the fastest path to something useful), the hostile corpus generator,
then the extrinsic metrics with the Precision Ω reproduction as their correctness
proof (C17).
