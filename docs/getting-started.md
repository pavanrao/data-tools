# Getting started

**Five minutes, three commands, and you'll have watched a document pipeline
catch a mistake it would normally have made silently.**

No prior knowledge of RAG, embeddings, or MCP required. If you can run a
terminal command, you can follow this.

---

## The problem, in one paragraph

You hand a folder of documents to an AI system. Somewhere in there is a
spreadsheet whose fourth tab never got opened, a scanned PDF that produced no
text at all, and a Word file whose footnotes were skipped. Nothing crashes.
Nothing warns you. The AI answers your questions confidently, using the 70% it
managed to read, and you have no way to know which 30% is missing.

The tool in this repo, `ingest-ledger`, exists to make that 30% visible.

---

## Setup

You need [uv](https://docs.astral.sh/uv/) (a fast Python package manager) and
Python 3.11+.

```bash
git clone https://github.com/pavanrao/data-tools
cd data-tools
make sync
```

That's it. `make sync` installs everything into a local virtual environment.

---

## Step 1 — Make some broken documents

The repo can generate a set of deliberately problematic files. Every one of them
is the kind of thing that shows up in a real folder of business documents.

```bash
uv run python tools/ingest-ledger/corpus/generate.py /tmp/demo
```

You now have eight files in `/tmp/demo`. Among them:

- a spreadsheet with data spread across four tabs
- a scanned PDF — pictures of text, with no actual text in the file
- a Word document whose footnotes live in a separate part of the file
- a `.zip` with another `.zip` inside it
- a file named `liar.pdf` that is secretly an HTML page

## Step 2 — Reconcile them

```bash
uv run ingest-ledger report --in-process /tmp/demo
```

```
file                                declared     read    cov  status
---------------------------------------------------------------------
bom_mixed.csv                         4 rows        4  100%  COMPLETE
liar.pdf                                   -        -    0%  UNSUPPORTED ?
                                -> extension claims pdf, content is html - content not indexed
multi_sheet.xlsx                    4 sheets        3   75%  PARTIAL !
                                -> missing sheets: Notes
scanned.pdf                          3 pages        0    0%  PARTIAL !
                                -> missing pages: 1, 2, 3
...

files: 6 of 9 complete, 3 quarantined
  pages       25.0%   <-- gap
  sheets      75.0%   <-- gap
```

### How to read this

Each row compares two numbers:

- **declared** — what the file says it contains, counted by looking at its
  structure. A PDF's page count. A workbook's tab names. It never reads the
  content to work this out.
- **read** — what actually came back when the content was extracted.

When those two disagree, something went missing. `coverage` is simply
`read ÷ declared`.

**Why two numbers instead of one?** Because a single number can only ever be
the extractor grading its own homework. If the thing that failed is also the
thing reporting, a failure and a success look identical. Two independent counts
can contradict each other — and that contradiction is the entire signal.

Files below the threshold are **quarantined**: held back rather than fed into
the AI's index. Better to know something is missing than to answer from it.

---

## Step 3 — See what a normal pipeline would have done

```bash
uv run ingest-ledger compare --in-process /tmp/demo
```

```
input                  naive extractor           ingest-ledger
-----------------------------------------------------------------------------
liar.pdf               ok, 26 chars              UNSUPPORTED (0%)            <--
multi_sheet.xlsx       ok, 34 chars              PARTIAL (75%)               <--
nested.zip             ok, 21 chars              2 members, 311 chars        <--
scanned.pdf            ok, 0 chars               PARTIAL (0%)                <--
textbox_footnote.docx  ok, 135 chars             COMPLETE (100%)             <--

5 of 8 inputs would enter the index silently damaged under the naive extractor.
```

The left column is a deliberately ordinary extractor — the kind found in a lot
of shipped code. Notice it says **ok** on all of them. It never throws an
error. It reports success on the scanned PDF while returning zero characters.

Every `<--` is a file that would have quietly entered your search index in a
damaged state.

---

## Step 4 — Watch it refuse to answer

This is the part that matters most.

```bash
# a small, realistic set of contract documents
uv run python tools/ingest-ledger/corpus/generate.py /tmp/rfp --rfp

# read them, index the good ones, and record what went wrong with the rest
uv run ingest-ledger index --in-process --ledger /tmp/rfp.db /tmp/rfp
```

One of those files is a pricing workbook with a tab called **Payment Schedule**
that contains nothing. Now ask two questions.

```bash
uv run ingest-ledger ask --ledger /tmp/rfp.db "who owns the intellectual property?"
```

```
[ANSWERED] Answered from 2 indexed passages; 1 unread file(s) do not bear on it.

  0.346  general_terms.md@0
         Intellectual property created under this agreement vests in the State...
```

Fine — the answer is in a file that was read completely. Now:

```bash
uv run ingest-ledger ask --ledger /tmp/rfp.db "what are the payment schedule milestones?"
```

```
[ABSTAINED] Refused: the most relevant material for this question was not
successfully read. pricing.xlsx (missing sheets: Payment Schedule).
Re-run ingestion for these files before trusting an answer.
```

**It refused.** A normal RAG system cannot do this. An unread file contributes
no passages, so search simply never sees it — and the system answers from
whatever else it has, confidently and wrongly.

The trick is that we are not blind to an unread file. We still know its name,
its tab names, and why it failed. Those get indexed too. When your question
matches a *gap* better than it matches anything we actually read, refusing is
the honest answer.

The command exits with code `3` when it refuses, so a script can branch on it.

---

## Step 5 — Point it at your own files

```bash
uv run ingest-ledger report ~/Documents/some-folder
uv run ingest-ledger report ~/Downloads/big-archive.zip --strict
```

`--strict` exits non-zero if anything was quarantined — drop it into CI to fail
a build when a document set stops ingesting cleanly.

Leaving off `--in-process` runs each file in its own subprocess with a memory
cap and a timeout. Slower, but a file that gets killed for using too much memory
then shows up as `FAILED` instead of quietly returning half its contents.

```bash
uv run ingest-ledger report --memory-mb 256 --timeout 60 ~/Documents/reports
```

---

## Common questions

**Does this need an API key or a model?**
No. The whole reconciliation path is deterministic and offline. The default
embedder is a plain hashing function with no dependencies, so the refusal logic
is testable on any machine. You can swap in a real encoder later.

**Is my data sent anywhere?**
No. Everything runs locally and writes to a SQLite file you control.

**What formats are supported?**
PDF, XLSX, DOCX, XML, CSV, TSV, plain text and Markdown, plus recursive `.zip`.
Anything else is marked `UNSUPPORTED` rather than skipped quietly — an honest
gap beats a silent one.

**What if I already use a PDF tool I like?**
Good. PDF page-level checking is delegated to
[pdfmux](https://github.com/NameetP/pdfmux), which is excellent at it. The other
formats are where this tool adds something.

---

## Where to go next

- **[`tools/ingest-ledger/README.md`](../tools/ingest-ledger/README.md)** — the
  detailed reference: architecture, the hostile corpus, prior art, and what is
  still unbuilt.
- **[`CONVENTIONS.md`](../CONVENTIONS.md)** — how tools in this repo are shaped,
  and how to add one.
- **[`IDEAS.md`](../IDEAS.md)** — 49 tool ideas. Pick one and build it.

```bash
make test   # 48 tests, including the hostile corpus
make demo   # everything above in one command
```
