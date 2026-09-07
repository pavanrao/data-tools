# `ingest-ledger`

**Reconcile what a document pipeline was *given* against what it actually *read*.**

Hand a pile of real-world documents to an LLM pipeline and extraction fails
partially and silently: a subprocess is OOM-killed on an oversized XML, a
workbook's fourth sheet is never opened, a DOCX's footnotes are skipped, a
scanned PDF yields an empty string. None of it raises. The model answers
confidently from the fragment it received, its citations look solid — because
the chunks they point to are real. It's the missing chunks that lie.

The usual remedy is to ask the model what it processed. That's a confession
from the system that already failed to notice. This is a checksum instead.

## How it works

Two counts, from **independent code paths**:

1. **Manifest** — declare units per file by reading structure only, never
   content: PDF pages, XLSX sheets, DOCX body blocks *including footnotes and
   headers*, XML top-level nodes, CSV rows, recursive zip members.
2. **Extract** — run each file in a subprocess under a memory cap and timeout,
   so an OOM kill becomes an exit code instead of a shrug. The cap is
   **best-effort**: `RLIMIT_AS` is not settable on every platform (macOS rejects
   any finite value), so each row records whether it was actually applied —
   `memory_cap: rlimit_as`, or `memory_cap: unenforced: …`. The timeout always
   applies.
3. **Reconcile** — join the two, assign `complete` / `partial` / `failed` /
   `unsupported` / `empty` with a coverage percentage, and quarantine anything
   below threshold rather than folding it silently into the index.

If the two counts came from the same system, their agreement would prove
nothing. That constraint drives the whole design.

New to the repo? Start with
**[GETTING-STARTED.md](./GETTING-STARTED.md)** — a five-minute
walkthrough with no prerequisites. This file is the reference.

## Usage

```bash
uv sync --all-extras
make demo                                  # reconcile, compare, then ask

ingest-ledger manifest ./corpus            # declare only; never extracts
ingest-ledger report ./rfp.zip --strict    # non-zero exit if anything quarantined
ingest-ledger compare ./corpus             # naive extractor, side by side
ingest-ledger index ./corpus --ledger l.db # index reconciled content + the gaps
ingest-ledger ask --ledger l.db "..."      # answer, disclose, or refuse
```

```
file                                declared     read    cov  status
---------------------------------------------------------------------
liar.pdf                                   -        -    0%  UNSUPPORTED ?
                                -> extension claims pdf, content is html - content not indexed
multi_sheet.xlsx                    4 sheets        3   75%  PARTIAL !
                                -> missing sheets: Notes
scanned.pdf                          3 pages        0    0%  PARTIAL !
                                -> missing pages: 1, 2, 3

files: 6 of 9 complete, 3 quarantined
  pages       25.0%   <-- gap
  sheets      75.0%   <-- gap
```

Coverage is reported **per unit kind and never summed across kinds**. One
corpus-wide ratio is a trap: 240,000 XML nodes drown out three lost PDF pages
and the headline reads 100% while the table below lists quarantined files.

## Query-time abstention

`index` writes two tables. `chunks` holds what was read. `gaps` holds a
searchable descriptor of what was not — filename, container, declared unit ids
(sheet names are often the exact words a question uses), the failure reason, and
any partial text.

That second table is the point. Retrieval alone cannot see an ingestion gap: an
unread file contributes no chunks, so similarity search never ranks it and the
system answers confidently from the remainder. `ask` scores every question
twice — against what was read, and against what was not — and refuses when the
best match is something ingestion failed to read.

```
$ ingest-ledger ask --ledger rfp.db "what are the payment schedule milestones?"

[ABSTAINED] Refused: the most relevant material for this question was not
successfully read. pricing.xlsx (missing sheets: Payment Schedule).
```

Three verdicts: `ANSWERED` (no gap bears on the question), `ANSWERED_WITH_GAPS`
(answered, gaps disclosed in the statement), `ABSTAINED` (exit code `3`). Every
answer carries a coverage statement regardless.

Embeddings sit behind an `Embedder` protocol. The default is a dependency-free
hashing bag-of-words: not competitive with a trained encoder, and not meant to
be — it exists so the gating logic is testable offline on any machine. What the
tool refuses to answer must not depend on which embedder is installed.

## The hostile corpus

`corpus/generate.py` builds documents that a naive pipeline reads
*successfully* and gets wrong. They're generated, not committed, so the repo
stays free of binaries and each defect is described in code rather than
folklore.

| Fixture | What a naive extractor does wrong |
|---|---|
| `multi_sheet.xlsx` | reads the active sheet; sheets 2–4 never happened |
| `textbox_footnote.docx` | `document.paragraphs` skips footnotes and headers |
| `oversized.xml` | eager parse trips the memory cap mid-document |
| `nested.zip` | never descends into the inner archive |
| `bom_mixed.csv` | BOM corrupts the first header; latin-1 byte breaks decoding |
| `liar.pdf` | HTML behind a `.pdf` extension; forgiving probes return plausible junk |
| `scanned.pdf` | no text layer — returns `""` and calls it success |
| `whitebox.pdf` | text hidden under a white rectangle; print hides it, extraction reads it |

`pytest -m hostile` asserts every one is flagged and **none silently succeeds**.
That suite is the product claim, so CI runs it as its own job.

> The `liar.pdf` fixture caught a real bug during the first run of this tool:
> PyMuPDF happily opened the HTML file and it reconciled as `COMPLETE`. That's
> what added `sniff.py`.

## Prior art, and how this differs

Silent-drop detection for **PDF pages is solved**, and this tool does not
reimplement it:

- **[pdfmux](https://github.com/NameetP/pdfmux)** (MIT) finds pages where source
  text exists but the engine returned nothing while reporting success, and
  audits *other* extractors' output. We extract, hand it our per-page output,
  and record its verdict as evidence. Pinned to `1.8.7` and confined to
  `probes/pdf.py`; without it installed, that evidence line reads
  `fidelity_audit: unavailable` rather than being silently absent.

  **The two tools answer different questions**, which is worth stating plainly
  because it justifies not simply deferring to it. pdfmux measures *fidelity*:
  given this source and this output, did the engine drop text that was there?
  On our 3-page scanned fixture it returns `PASS` at coverage `1.00` — correctly,
  because a page with no text layer has nothing to drop. Measured against the
  declared page count, that same file yielded **zero** content, which is exactly
  the gap an index would inherit. So we measure *yield*, pdfmux measures
  fidelity, and a page is missing if either says so.
- **[Docling](https://github.com/docling-project/docling)** grades conversion
  quality per page (`mean_grade`, `low_grade`). That's a heuristic on what it
  produced; it cannot tell you a file was never opened.
- **[AWS Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_KnowledgeBaseDocumentDetail.html)**
  does real document-level reconciliation (`INDEXED` / `PARTIALLY_INDEXED` /
  `FAILED`) — but it's AWS-locked and stops at the file boundary.

What nothing above covers, and this does:

1. **Formats that aren't PDF.** The sheet nobody opened, the footnote nobody
   walked, the XML that OOM'd, the zip inside the zip — the actual shape of a
   real corpus.
2. **Manifest-first reconciliation.** Declared counts computed before, and
   independently of, extraction.
3. **Coverage carried to the answer.** Provenance from chunk → file → unit, so
   a downstream RAG tool can attach a coverage statement to every response and
   abstain when a known gap overlaps the question. The abstention literature
   covers *retrieval* gaps ("the corpus lacks the answer"); this is *ingestion*
   coverage ("we failed to read the file that has it").

The problem is live in paid tooling: a 2026 comparison found
[LlamaParse and Mistral silently dropping rows from an oversized sheet, and
Extend returning empty confidence fields so errors looked exactly like correct
answers](https://www.unsiloed.ai/blog/unsiloed-ai-vs-extend-reducto-mistral-claude).

## Status

Working end to end, with 48 tests. Manifest, supervised extraction, reconcile,
report, ledger, chunk, index, query-time abstention, the naive baseline
comparison, and the hostile corpus are all built.

Known limits and next steps:

- **The default embedder is a hashing bag-of-words**, so gap matching is
  lexical. A question that shares no vocabulary with a gap descriptor will not
  trigger abstention. Swapping in a real encoder is a one-line change and would
  materially improve recall on paraphrase.
- **`ABSTAIN_RATIO` and `GAP_RELEVANCE` are policy constants**, tuned against
  the demo corpus rather than derived. They deserve an eval set.
- **No generation step.** `ask` returns grounded passages and a verdict; wiring
  an LLM behind `data_tools_core.llm` is deliberately left to the caller, so the
  deterministic core stays model-free and testable.
- Archive members are unpacked into a caller-supplied `workdir`; without one
  their paths dangle after the walk. The CLI passes one, library callers must.
