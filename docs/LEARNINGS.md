# Learnings (running log)

Reusable, transferable **craft** — technical and process know-how that applies
beyond any single tool. Append a new `## Iteration N` section at the **top** each
sprint; keep entries concrete.

> For project verdicts and direction calls, see [FINDINGS.md](./FINDINGS.md).
> For per-feature design + decision records, see the numbered docs (`001_…`).

---

## Iteration 5 — 2026-09-07 — a broken cap, found by a neighbouring tool's suite

### A test that fails on one machine is a claim about that machine
Two `ingest-ledger` tests failed locally while everything else passed, which is
the shape that invites "environment thing, ignore it". It was not. `setrlimit`
worked fine — lowering `RLIMIT_NOFILE` succeeded — but `RLIMIT_AS`, `RLIMIT_DATA`
and even *re-setting `RLIMIT_STACK` to the values it already held* all returned
EINVAL. That last one is the tell: nothing about the requested size was wrong, the
resource simply is not settable on Darwin, which aliases `RLIMIT_AS` to
`RLIMIT_RSS`.

The consequence was not two flaky tests. The worker called `setrlimit`
unconditionally, so it died before opening the file and **every subprocess
extraction on macOS returned `exit 1`** — the tool's entire default mode, broken,
with the in-process path masking it in every other test.

**The discriminating experiment is worth stealing:** before concluding "platform
limitation", find something in the same API that *does* work. "setrlimit is
blocked here" and "this particular resource is not settable here" call for
completely different fixes.

### Degrading silently is worse than failing, and both are worse than saying so
There were two obvious fixes and both were wrong. Let it raise, and the tool stays
broken. Swallow the error, and the ledger records `memory_cap_mb: 512` for a run
that had no cap at all — a status the probe never earned, which is the exact
failure `ingest-ledger` exists to catch, committed by `ingest-ledger` about
itself.

The fix is the third option, and it is what CONVENTIONS rules 2 and 5 already
said: apply the cap best-effort and **record the outcome**, so a row says
`rlimit_as` or `unenforced: …` and no reader can mistake one for the other.

### Gate a skip on the observed capability, never on `sys.platform`
The OOM test cannot pass where no cap can be applied — there is no OOM. It now
skips on what the run *reported* (`memory_cap != "rlimit_as"`) rather than on a
platform string. That stays correct if an OS gains or loses the capability, works
under a sandbox that changes it, and the skip reason names the actual cause
instead of "macOS".

## Iteration 4 — 2026-09-07 — chunking-lab: verifying a design record

### Verification tags are worth what they cost
The chunking-lab design record was written in a session whose egress policy
blocked several primary sources, so every claim carried a tag saying **how** it
was verified — "read from source", "search summary", "abstract only". Re-fetching
the six blocked sources found that two of the load-bearing claims were wrong.
Both were tagged as unverified. The tags did not prevent the errors; they made
them **findable instead of inherited**, and they told you exactly which paragraphs
to re-read. Do this on any research handoff.

### Reconstructing a formula from prose is not verification
Precision Omega had been reconstructed from an ambiguous code extract as "the
minimal set of chunks covering the gold spans". The real definition is "**every**
chunk containing an excerpt token". Those coincide for a non-overlapping
partition and diverge as soon as chunks overlap — so the reconstruction was
plausible, tested fine against any example you would think to try by hand, and
wrong in exactly the case the tool exists to measure. If a number is the headline
of a tool, read the implementation, not the paper.

### Prose and implementation disagree, and the implementation is what ran
The same source's report says "tokens" throughout; its code measures **characters**.
It describes one denominator; the code uses a *sum* for one metric and a *union*
for another, so overlap is penalised twice in one and once in the other. Published
numbers come from the code. Reproduce the code.
- Useful side effect: following the implementation removed the tokenizer, and with
  it the only model dependency in the whole measurement path.

### An invariant proves well-formedness, never sameness
The recursive splitter is a port. It satisfied every invariant — in bounds,
ordered, no content dropped — and matched the reference on four of five sizes by
coincidence. It was still wrong: the reference keeps a separator as the **prefix
of the following piece** and the port had it as a suffix. Only a **differential
test against golden output captured from the original** caught it. When porting
something whose numbers you intend to reproduce, capture its output first and
diff against it; the invariant is a different question.

### Write the invariant you can actually enforce
The design specified "coverage == 1.0 modulo declared overlap". That is wrong for
any chunker that trims whitespace at its boundaries — which the reference does.
The enforceable version is "**no non-whitespace character is in zero spans**",
with coverage reported as a number alongside. Same bug caught, no false positives,
and the softer signal stays visible instead of being asserted away.

### A metric that needs no retrieval is a metric you can reproduce
Precision Ω is computed over every chunk in the corpus with no retriever
involved. That one property is what made an external correctness proof possible:
no embedding model, no vector store, no API key, no network. The other columns in
the same published table (recall, precision, IoU) all depend on a retriever, and
reproducing them would have meant reproducing someone else's embedding model too.
**When picking a headline metric, retriever-independence is worth real weight** —
not for purity, but because it is the difference between a number you can check
and a number you can only assert.

### Fetch-and-verify beats commit, when the fixture is big and public
The benchmark is 1.6MB and the repo's whole history is 260KB. Committing it would
have roughly tripled the pack for one test. A pinned upstream commit plus a
per-file SHA-256 gives the same reproducibility at ~90 lines: a changed byte
upstream is a failed check, not a silently different number. The trade is one
network round trip, once.

### Reuse the learnings log, or stop keeping one
The FTS5 stopword gotcha was logged as *open* against `repo-rag` and was reused
here before it could be rediscovered. It also mattered more in the new context: in
`repo-rag` it degraded result quality, but in a chunker comparison a polluted
query returns near-random chunks for **every** strategy alike, which makes them
all look equally mediocre and erases the differences being measured. A logged
gotcha is worth re-reading in each new setting, because its severity is not a
property of the gotcha.

### Prior art for a simple mechanism is usually there; you have to look properly
An earlier draft claimed no prior work screened chunking configurations without
running retrieval. A one-hour sweep across SIGIR, ECIR and the ACL Anthology found
a LREC 2026 paper doing exactly that from five intrinsic metrics — including the
one the draft singled out as having "no located antecedent" — plus two papers that
had already run the correlation experiment being proposed as the contribution.
**A few targeted searches is not a literature review**, and the gap between them is
where novelty claims go to die.

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
