# 000 — Project Organization

How `data-tools` is put together, and why. This is the orienting document: read
it first, and read it before adding a tool.

`CONVENTIONS.md` at the repo root is the short, normative version — the rules a
tool must satisfy. This document is the reasoning behind those rules, plus the
history of how they were arrived at, including the decisions that were tried and
replaced.

---

## 1. What this repo is

A collection of small, independent data-pipeline tools, built one at a time, as
a way to learn MCP and RAG in anger. [`IDEAS.md`](../IDEAS.md) holds the running
backlog of 218 ideas; sections A–D are RAG/MCP tools and infrastructure, section
E is generic pipeline plumbing, and F onward are the later axes described in
[`../README.md`](../README.md).

The collection is built under one governing tension, and nearly every structural
decision below is an answer to it:

> It should be usable as **one thing**, yet every tool must be **independently
> installable and runnable**, and any tool that grows up must be able to **leave
> for its own repo** without a rewrite.

"One monolith" fails the second and third clauses. "Forty-eight unrelated
repos" fails the first. A **uv workspace** is the shape that satisfies all three.

## 2. Layout

```
data-tools/
├── CONVENTIONS.md              # the normative rules (short)
├── IDEAS.md                    # the running backlog of tool ideas
├── Makefile                    # sync / lint / test / demo
├── pyproject.toml              # workspace root — NOT a package
├── .python-version             # 3.13
├── docs/                       # this directory; see §9
├── shared/
│   └── data-tools-core/        # dist: data-tools-core   import: data_tools_core
│       └── src/data_tools_core/
│           ├── provenance.py   # the one type every tool agrees on
│           ├── ledger.py       # shared SQLite ledger schema + connection conventions
│           ├── registry.py     # the `dt` meta-CLI (entry-point discovery)
│           ├── config.py       # DATA_TOOLS_* settings (stdlib only)
│           └── llm.py          # OPTIONAL model layer (see §6)
└── tools/
    ├── ingest-ledger/          # dist: data-tools-ingest-ledger
    ├── docs-rag/               # dist: data-tools-docs-rag
    └── repo-rag/               # dist: data-tools-repo-rag
```

The workspace root is **not a package**. It exists only to declare the
workspace and hold shared lint/test configuration. Nothing in it is required to
run a tool — which is what makes a tool's independence real rather than claimed.

## 3. The three seams

Tools **never import each other**. That is the load-bearing rule; everything
else in this section is how tools cooperate anyway. They compose along exactly
three seams:

### CLI seam
Every tool is an independently installable distribution with a console script,
so one tool can be used with nothing else present:

```bash
uvx --from "git+https://github.com/pavanrao/data-tools#subdirectory=tools/docs-rag" \
    docs-rag ask "..."
```

### Data seam
Tools exchange **artifacts, not objects**: JSONL records and a SQLite ledger
whose schema lives in `data_tools_core.ledger`. Every record that crosses a
tool boundary carries a `Provenance` (source path, content hash, unit kind, unit
id), so any value can be traced back to the bytes it came from.

This is what lets `ingest-ledger` feed `docs-rag` without either knowing the
other exists.

### MCP seam
A tool useful to an agent advertises a server factory in the `data_tools.mcp`
entry-point group, so `mcp-gateway` (#16) can one day mount every installed one
behind a single endpoint. `repo-rag` is the first to do this.

## 4. Packaging rules

| Rule | Value |
|---|---|
| Directory | `tools/<tool-name>/`, kebab-case |
| Distribution | `data-tools-<tool-name>` |
| Import package | `<tool_name>`, snake_case, under `src/` |
| Console script | `<tool-name> = "<tool_name>.cli:main"` |
| Discovery | register in the `data_tools.tools` entry-point group |
| Module invocation | ship a `__main__.py` so `python -m <tool_name>` also works |
| Python | `>=3.13` |

Two of these earn a word of explanation.

**Dual invocation is deliberate.** A tool ships *both* a console script and a
`__main__.py`. The console script is the ergonomic path; `python -m` is the one
that still works when a client launches the tool from an unknown working
directory, or when the scripts directory is not on `PATH`.

**Discovery is by entry point, never a hardcoded list.** `dt ls` shows exactly
the tools that are installed, and imports none of them until one is invoked.
Adding a tool to the collection is therefore a packaging act, not an edit to a
central registry.

## 5. The spin-out seam

The mechanism that makes "a tool can leave for its own repo" true rather than
aspirational. Each tool declares a **normal** dependency on the shared library
plus a **dev-only** source override:

```toml
dependencies = ["data-tools-core", "sqlite-vec>=0.1"]

[tool.uv.sources]
data-tools-core = { workspace = true }
```

uv **strips `[tool.uv.sources]` from built wheels**. So in development the
dependency resolves to the local `shared/data-tools-core/`, and deleting that
one block is the entire "decouple from the workspace" step — the published
wheel is then resolved from an index instead.

The full recipe:

```bash
git subtree split -P tools/<name> -b <name>-split   # keeps history
# push that branch to a new repo
# delete the [tool.uv.sources] block from its pyproject.toml
# depend on the published data-tools-core
```

Three standing rules keep this a non-event rather than a project:

1. Tools import only `data_tools_core` — **never each other**.
2. Everything a tool needs lives under its own directory.
3. `data_tools_core` is versioned like a real library, because it is one.

## 6. The model layer is optional

Tools depend only on two protocols, and that is the entire contract:

```python
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class ChatProvider(Protocol):
    def complete(self, prompt: str, **opts) -> str: ...
```

LiteLLM satisfies them today. **No tool imports LiteLLM, or any vendor.** The
indirection is two layers deep on purpose — tools talk to protocols, protocols
are satisfied by a backend — so replacing LiteLLM touches
`data_tools_core/llm.py` and nothing else.

Configuration is by environment, not code. Defaults run locally on Ollama at no
cost:

```bash
export DATA_TOOLS_CHAT_MODEL=ollama/llama3.1      # or anthropic/…, openai/…
export DATA_TOOLS_EMBED_MODEL=ollama/nomic-embed-text
# DATA_TOOLS_API_BASE / DATA_TOOLS_API_KEY as needed
```

Two properties are enforced, not merely intended:

- **`data_tools_core` has no base dependencies.** `config.py` is stdlib-only for
  exactly this reason — it would have been one line shorter with
  pydantic-settings and would have broken the rule.
- **The backend imports lazily.** `import data_tools_core.llm` never reaches for
  litellm; the import happens inside the call. This is what lets every tool's
  deterministic core be tested on a machine with no model stack, and it is
  asserted directly in `shared/data-tools-core/tests/test_llm.py`.

Install the backend when you actually want to call a model: `uv sync --extra llm`.

## 7. Storage

SQLite for everything — file-based, no server, no daemon.

- `data_tools_core.ledger` owns the `runs` table and the connection conventions
  (WAL, `foreign_keys=ON`, `row_factory`). Tools own their own tables in the
  same database, so several tools writing one ledger stay consistent.
- `sqlite-vec` provides vector KNN where a tool needs semantic search.
- FTS5 (built into SQLite) provides keyword/BM25 where a tool needs exact
  identifier matching. `repo-rag` fuses the two with Reciprocal Rank Fusion.

A tool whose retrieval must run with nothing installed can use a deterministic
in-process embedder instead; `ingest-ledger`'s `HashingEmbedder` is the example,
and it is deliberately not competitive with a trained encoder.

## 8. Testing

- **Every tool's deterministic core is testable with no model installed.** Tools
  inject fake `EmbeddingProvider`/`ChatProvider` implementations; the shared
  layer patches its one lazy backend accessor. The suite needs no network and
  no Ollama.
- **`--import-mode=importlib`.** Three tools now ship a `test_cli.py`. Under
  pytest's default import mode those equal basenames collide outright ("import
  file mismatch"). importlib mode lets every member keep a conventional
  `tests/` directory with no `__init__.py` files. A consequence worth knowing:
  a bare `from conftest import X` no longer resolves — pass such values as
  fixtures.
- **A failing test is a product regression, not flake.** `ingest-ledger`'s
  `hostile` marker exists to say so out loud: if a known-bad fixture stops being
  detected, the claim this repo makes has broken.
- CI runs `ruff check`, the full suite, and the hostile corpus separately.

## 9. Documentation

Four kinds of document, deliberately separated. Putting a verdict in a design
doc, or craft in a decision log, is how all three become unsearchable.

| Where | What | Cadence |
|---|---|---|
| `CONVENTIONS.md` | The normative rules. What a tool **must** do. | Edited in place |
| `docs/NNN_*.md` | Design + decision records, one per feature or tool. | Append the next number |
| `docs/LEARNINGS.md` | Reusable **craft** — transferable beyond any one tool. | Prepend `## Iteration N` |
| `docs/FINDINGS.md` | Project **verdicts** — what we're building, parking, and why. | Prepend `## Iteration N` |

Both running logs prepend the newest iteration at the **top**. The numbered
series is append-only: superseded decisions are annotated in place, never
deleted, because the reasoning is the point.

Per-tool `README.md` is the user-facing reference for that tool; the numbered
doc is the design record behind it.

## 10. Adding a new tool

The checklist. Build one tool at a time.

1. **Pick an idea** from `IDEAS.md`.
2. **Scaffold** `tools/<name>/` with `pyproject.toml`, `README.md`,
   `src/<name>/`, `tests/`. Copy the packaging table in §4 exactly.
3. **Declare the spin-out seam** (§5) — the `[tool.uv.sources]` block — from day
   one, not later.
4. **Keep the deterministic core model-free.** If the tool cannot run without a
   model, it cannot be tested; put the model behind
   `data_tools_core.llm` and make it optional.
5. **Make heavy or optional backends extras**, never base dependencies. Degrade
   gracefully and *record which path ran* rather than silently substituting.
6. **Pin third-party integrations** and isolate each behind one adapter module,
   so an upstream break costs one file. (`repo-rag`'s `mcp_server.py` is the
   worked example.) Note the limit: confinement bounds the API surface you must
   edit, not the runtime assumptions a dependency makes about your code — the
   mcp 2.x upgrade cost three lines in the adapter and a threading fix in the
   store. Bound the major version; let patch and minor float.
7. **Register** the console script, the `data_tools.tools` entry point, and a
   `__main__.py`. Add a one-line docstring to `main()` — `dt ls` prints it.
8. **Write the tests first**, and make every non-obvious status evidence-bearing:
   when a tool reports a verdict, the record should say which code produced it
   and what it saw.
9. **Add `docs/NNN_<name>.md`** with the design and the decisions.
10. **Append to `LEARNINGS.md` / `FINDINGS.md`** — craft in one, verdicts in the
    other.
11. `make lint && make test` before you call it done.

## 11. Decision history

Decisions are recorded so the reasoning survives, including where it was later
overturned. Full context in
[`001_architecture-and-decisions.md`](001_architecture-and-decisions.md).

| # | Decision | Status |
|---|---|---|
| D1 | uv **workspace**, not one package with subpackages | **Current** |
| D1a | Root as an umbrella *metapackage* depending on every tool | **Superseded** — root is not a package (§2) |
| D2 | Model-pluggability via narrow protocols over LiteLLM | **Current**, now optional (§6) |
| D3 | SQLite storage (`sqlite-vec`, FTS5) and the official MCP SDK | **Current** |
| D4 | Spin-out seam via `[tool.uv.sources]` | **Current** (§5) |
| D5 | TDD throughout, model backend mocked | **Current** (§8) |
| D6 | Build `docs-rag` and `repo-rag` first | **Historical** — both built; see FINDINGS |
| D7 | Three seams; artifacts, not objects | **Current** (§3) |
| D8 | Provenance on every cross-tool record | **Current** (§3) |
| D9 | Python 3.13 across the workspace | **Current** |

Two of these deserve their reasoning restated here, because they were arrived at
twice, independently, from different directions — which is the best evidence
they are right:

- **Tools never import each other.** Reached in D4 as a precondition for
  spin-out, and again in `CONVENTIONS.md` rule 1 as a precondition for a tool
  running alone. Same rule, two motivations.
- **The deterministic core must be testable without a model.** Reached in D5 by
  mocking the backend, and again in `ingest-ledger` by making the core
  model-free by construction. The stronger form won: the model is now optional
  rather than merely mockable.
