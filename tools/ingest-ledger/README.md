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
   so an OOM kill becomes an exit code instead of a shrug.
3. **Reconcile** — join the two, assign `complete` / `partial` / `failed` /
   `unsupported` / `empty` with a coverage percentage, and quarantine anything
   below threshold rather than folding it silently into the index.

If the two counts came from the same system, their agreement would prove
nothing. That constraint drives the whole design.

## Usage

```bash
uv sync --all-extras
make demo                                  # build the hostile corpus, reconcile it

ingest-ledger manifest ./corpus            # declare only; never extracts
ingest-ledger report ./rfp.zip --strict    # non-zero exit if anything quarantined
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
  audits *other* extractors' output too. The PDF lane delegates to it behind
  `probes/pdf.py`, pinned to `1.8.7`, with a native PyMuPDF fallback that
  records which path ran. The declared count stays ours — pdfmux's verdict
  comes from re-extraction, so using it for both sides would collapse two
  measurements into one system's opinion of itself.
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

Scaffold. Manifest, extract, reconcile, report, ledger and the hostile corpus
work end to end. Not yet built:

- [ ] Wire the subprocess memory cap into the walk (one `xfail` marks the gap)
- [ ] Verify the pdfmux `verify_extraction()` signature against the installed wheel
- [ ] Chunk + embed + index over reconciled content only
- [ ] Query path: coverage statement per answer, abstention on overlapping gaps
- [ ] Baseline comparison in `make demo` (naive extractor vs. this, side by side)
