# Learnings (running log)

Reusable, transferable **craft** — technical and process know-how that applies
beyond any single tool. Append a new `## Iteration N` section at the **top** each
sprint; keep entries concrete.

> For project verdicts and direction calls, see [FINDINGS.md](./FINDINGS.md).
> For per-feature design + decision records, see the numbered docs (`001_…`).

---

## Iteration 3 — 2026-09-03 — MCP SDK 1.x -> 2.x

### Migrating an SDK major
- Read the **installed package**, not the error message's summary. The 2.x error
  helpfully names the rename but mentions none of what actually broke us. An
  hour with `inspect.signature` in a throwaway venv beat guessing from release
  notes.
- `inspect.signature` does **not** render `async`. `list_tools` printed as a
  plain function and is a coroutine; check `inspect.iscoroutinefunction` before
  concluding an API went sync.
- Prototype the new API in a scratch venv *before* touching the repo. Three
  ten-line probes established the whole migration surface: the rename, the
  structured-output behaviour, and the `CallToolResult` shape.

### Registration is not dispatch
- A test that asserts `await server.list_tools()` returns the right names proves
  the **decorator ran**. It says nothing about whether a call survives the
  dispatch path — argument coercion, threading, result serialisation.
- Our whole suite passed on 2.x while the server was broken for **every** call
  over the wire. Both defects were invisible to registration-only tests with a
  fake store.
- **Drive one real call through the seam, against your real resources.** The
  fake store could not exhibit SQLite's thread affinity; a real `CodeStore`
  through `call_tool` reproduced the failure instantly.
- Then prove the regression test earns its place: revert the fix, watch it fail,
  restore. A regression test never seen red is a guess.

### Threading reaches through your abstractions
- mcp 2.x runs tool handlers on a **worker thread**. SQLite connections are
  thread-affine, so a connection opened at server construction is unusable in
  the handler: *"SQLite objects created in a thread can only be used in that
  same thread."*
- Fix: `sqlite3.connect(..., check_same_thread=False)` **plus** a lock — the flag
  alone only silences the check, it does not serialise access. Use an `RLock`
  when a guarded method calls other guarded methods (`search` calls
  `search_vector` and `search_keyword`).
- The general shape: **isolating a dependency behind one adapter module bounds
  the API surface you must edit, not the runtime assumptions it makes about your
  code.** The rename cost three lines in the adapter; the threading model cost a
  change in a module the adapter merely calls.

### Typed returns are part of an MCP tool's contract
- In mcp 2.x the output schema is generated from the return annotation. A bare
  `-> dict` produces **no** schema and the SDK then sends
  `structured_content=None`; `-> dict[str, object]` produces one and the client
  gets real data. The annotation is behaviour, not documentation.

---

## Iteration 2 — 2026-09-03 — consolidating two rival scaffolds onto one

Context: `docs-rag` + `repo-rag` had been built on a branch with their own
workspace conventions while `ingest-ledger` landed on main with a different set.
This iteration merged them. Most of the craft below came out of that collision.

### Two scaffolds are worse than either scaffold
- Both branches independently invented: *tools never import each other*, *each
  tool independently installable*, *SQLite as the substrate*, *MCP as a seam*,
  and *the core must be testable without a model*. **Convergent design is the
  strongest evidence a rule is right** — when two efforts reach the same rule
  from different motivations, keep it.
- Where they differed it was mechanics, not principle (package names, whether
  the root is installable, extras vs base deps). **Mechanics are cheap to
  reconcile; principles are not.** Resolve the mechanics by picking one and
  writing down why, which is what `000_project-organization.md` now is.
- The tell that a merge is overdue: a convention document referencing a module
  that does not exist. `CONVENTIONS.md` promised `data_tools_core.llm`; nothing
  implemented it, because the implementation was sitting on the other branch.

### Optional dependencies, done properly
- "Make it an extra" is not just a packaging change. If the module does
  `import litellm` at the top, the extra is a lie — importing the module still
  fails. **Import the backend inside the call**, behind one accessor, and raise
  a named error when it is missing.
- One accessor is also the whole testing story: patch `llm._litellm` and the
  suite runs with no model stack installed. Patching a module-level `litellm`
  attribute (what we did in Iteration 1) requires the package to be present,
  which quietly defeats the point.
- Keeping a shared library at `dependencies = []` is worth a little friction:
  it cost a stdlib rewrite of a 30-line pydantic-settings config, and bought the
  guarantee that importing the shared contracts can never drag in a model stack.

### pytest `--import-mode=importlib`, the second-order effect
- Iteration 1 learned that duplicate test basenames collide under the default
  import mode. Now proven at scale: three tools, three `test_cli.py`.
- **The consequence nobody warns you about:** under importlib mode the test
  directory is not on `sys.path`, so a bare `from conftest import CONSTANT`
  stops resolving. Pass such values as **fixtures** instead. Switching import
  mode is not a config-only change — grep for `from conftest import` first.

### Upstream majors land while your branch sits
- A branch parked for three months came back to `mcp>=1.0` resolving to 2.x,
  where `FastMCP` had been renamed and tool registration changed. An
  unpinned `>=` on a pre-1.0-culture SDK is a time bomb on any branch that
  waits.
- The saving grace was structural: the SDK was already confined to one adapter
  module, so the blast radius was one file and a pin. **"Isolate each
  integration behind one adapter" pays off precisely when you are not looking.**
- Pin, then record the owed upgrade somewhere it will be seen. A pin with no
  follow-up note is how a project ends up two majors behind.

### Landing someone else's code in a linted repo
- Code written before a repo had a linter will not pass it. Budget for this:
  13 ruff findings across ~1,500 lines, all mechanical (`typing.Sequence` →
  `collections.abc`, missing `zip(strict=)`).
- `zip(strict=True)` was the one that mattered. `zip(chunks, embeddings)`
  silently truncates to the shorter side — in a repo whose flagship tool exists
  to catch silent truncation, that is not a lint nit.
- Check the blast radius before committing a formatter run: `git diff
  --name-only` against the pre-existing paths. A reformat that churns files you
  did not mean to touch makes the real change unreviewable.

---

## Iteration 1 — 2026-06-08 — workspace scaffold + docs-rag + repo-rag

### uv / packaging
- A **uv workspace** gives one lockfile / one `uv sync`, while each member stays a
  real, independently-importable package. The umbrella root can be a code-less
  metapackage via hatchling `bypass-selection = true`.
- **Spin-out seam:** a member declares a normal dep *plus* a dev-only
  `[tool.uv.sources] X = { workspace = true }`. uv sources are stripped from built
  wheels, so deleting that one line is the entire "decouple from the workspace" step.
- `uv run --directory <abs-path> <tool> …` runs a workspace tool from anywhere —
  used to launch the MCP server regardless of the client's cwd.

### pytest in a multi-package workspace
- Several `test_smoke.py` files with the same basename **collide** under the default
  import mode ("import file mismatch"). Fix: `addopts = "--import-mode=importlib"`,
  which lets each member keep a conventional `tests/` layout without `__init__.py`.

### sqlite-vec
- KNN needs its limit **on the vec0 scan itself**: `WHERE embedding MATCH ? AND k = ?`.
  A `LIMIT` on an outer JOIN raises *"A LIMIT or 'k = ?' constraint is required"* —
  do the match in a subquery, then JOIN the metadata.
- Persist the embedding `dim` in a `meta` table so a store can be **reopened** for
  querying without re-specifying it.

### Hybrid retrieval
- Fuse sqlite-vec (semantic) + FTS5 (keyword/BM25) with **Reciprocal Rank Fusion**
  (k=60). RRF needs no score calibration across the two very different scales.
- FTS5 **external-content** table (`content='chunks', content_rowid='id'`) keeps a
  single source of truth for text.
- **Gotcha (open):** building the FTS `MATCH` as an OR of *all* query tokens pulls in
  stopwords (`what OR data OR in OR use`), so common words dominate BM25 and pollute
  results. Drop stopwords / weight identifiers.

### Code chunking
- stdlib `ast` yields clean per-function/class chunks with exact line spans; include
  decorators by taking `min(decorator linenos)`. Fall back to fixed line-windows on
  `SyntaxError` or when a file has no top-level defs, so nothing is lost.

### Model-pluggability
- Keeping our own `EmbeddingProvider`/`ChatProvider` protocols in front of **LiteLLM**
  means a provider swap is a model-string/env change and tools never import a vendor.
  Tests **mock `litellm`** → fast, hermetic, no live model needed (41 tests).

### MCP
- `FastMCP` + `@server.tool()` (renamed `MCPServer` in SDK 2.x — see Iteration 3).
  Keep tool logic in plain `*_impl` functions so it's
  testable without a transport; assert registration via `await server.list_tools()`.
- Connect to Claude Code via a project `.mcp.json` (`command`/`args`); absolute
  `--directory`/`--db` avoid launch-cwd ambiguity.

### RAG question shapes
- Top-k retrieval serves **"needle"** questions ("where is X") but not
  **"survey/aggregate"** ones ("what tests exist"). With k=5 over 131 chunks the model
  simply can't enumerate 56 tests — that's a *recall* failure, not generation. Different
  question classes need different mechanisms (high recall, or structured listing).
