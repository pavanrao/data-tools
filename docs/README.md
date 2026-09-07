# docs

Four kinds of document, deliberately kept apart. A verdict filed in a design doc
— or craft filed in a decision log — is a thing nobody finds again.

| Document | Holds | Cadence |
|---|---|---|
| [`../CONVENTIONS.md`](../CONVENTIONS.md) | The **normative rules**. What a tool must do. | Edited in place |
| [`000_project-organization.md`](000_project-organization.md) | How the project is shaped and **why**; how to add a tool. | Edited in place |
| `NNN_*.md` | **Design + decision records**, one per feature or tool. | Append the next number |
| [`LEARNINGS.md`](LEARNINGS.md) | Reusable **craft** — transferable beyond any one tool. | Prepend `## Iteration N` |
| [`FINDINGS.md`](FINDINGS.md) | Project **verdicts** — what we build, park, and why. | Prepend `## Iteration N` |

**Start here:** [`000_project-organization.md`](000_project-organization.md).

## The numbered series

| Doc | Subject | Status |
|---|---|---|
| [`000`](000_project-organization.md) | Project organization — the orienting document | Current |
| [`001`](001_architecture-and-decisions.md) | Architecture & decisions (ADR log, D1–D9) | Current, append-only |
| [`002`](002_implementation-plan.md) | The original build plan for the RAG tools | Historical |
| [`003`](003_docs-rag.md) | `docs-rag` (#1) — RAG over a document folder | Parked |
| [`004`](004_repo-rag.md) | `repo-rag` (#2) — ask-your-codebase + MCP server | Parked |
| [`005`](005_concept-coverage.md) | Concept coverage — 98 AI/data-engineering concepts mapped to sections F–G of `IDEAS.md`, plus the showcase criteria | Current, plan |
| [`006`](006_chunking-lab.md) | `chunking-lab` (#25) — compare chunking strategies, scored at the character level | Current |
| [`007`](007_chunking-concepts.md) | Chunking concepts — the reference: every concept `chunking-lab` is built from, with its trade-off and where it lives | Current |

The series is **append-only**. A superseded decision is annotated in place with
a status line and a pointer to what replaced it, never deleted — see D1a and D2a
in `001` for the pattern. Reconstructing why a decision was made is the whole
reason the log exists.

## Where each tool's record lives

| Tool | User-facing | Design record |
|---|---|---|
| `ingest-ledger` | [README](../tools/ingest-ledger/README.md), [GETTING-STARTED](../tools/ingest-ledger/GETTING-STARTED.md) | those, plus [`double-entry-for-documents.html`](double-entry-for-documents.html) |
| `docs-rag` | [README](../tools/docs-rag/README.md) | [`003`](003_docs-rag.md) |
| `repo-rag` | [README](../tools/repo-rag/README.md) | [`004`](004_repo-rag.md) |
| `chunking-lab` | [README](../tools/chunking-lab/README.md), [`where-the-cut-falls.html`](where-the-cut-falls.html) | [`006`](006_chunking-lab.md), concepts in [`007`](007_chunking-concepts.md) |

New tools take the next number in the series.

## A note on "parked"

`docs-rag` and `repo-rag` are built, tested, and installed as part of the
collection, but are not under active development. `FINDINGS.md` records why —
in short, `repo-rag` is largely redundant next to a capable model that can
already read files, and `docs-rag` is more useful downstream of `ingest-ledger`
than as a standalone tool. They were merged so the code and the reasoning stay
together and findable; parking is a direction call, not a quality judgment.
