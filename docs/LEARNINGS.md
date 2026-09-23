# Learnings (running log)

Reusable, transferable **craft** — technical and process know-how that applies
beyond any single tool. Append a new `## Iteration N` section at the **top** each
sprint; keep entries concrete.

> For project verdicts and direction calls, see [FINDINGS.md](./FINDINGS.md).
> For per-feature design + decision records, see the numbered docs (`001_…`).

---

## Iteration 11 — 2026-09-23 — DuckLake 1.0, and two agents routing around a test

### A directory named `batch=2025-01` adds a column to every CSV read from it
`kimball-lab` writes each extract batch to `batch=YYYY-MM/`. The first load failed
in the history step:

```
Binder Error: table hist_account_holders has 5 columns but 6 values were supplied
```

`read_csv` had been given an explicit `columns` list with four entries, and the
staging table came back with five. The fifth was `batch`: DuckDB detects
`key=value` path segments as Hive partitions by default, even for a single file
read by a path built from `getvariable`. `hive_partitioning = false` on every
`read_csv` fixed it. An explicit column list does not switch detection off.

### A DuckLake catalog stores its data path as an absolute path
Copying a lake directory to measure snapshot expiry without touching the original
failed on attach:

```
DATA_PATH parameter ".../s10lake-expired/lab.ducklake.files/" does not match
existing data path in the catalog ".../s10lake/lab.ducklake.files/".
```

A lake can't be moved or copied as a plain directory. Attaching with
`OVERRIDE_DATA_PATH true` works.

### `AT (VERSION => …)` takes neither a trailing alias nor a subquery
Both `fact_transaction AT (VERSION => 26) f` and `… AT (VERSION => 26) AS f` are
parse errors (`syntax error at or near "f"`). The alias goes first:
`fact_transaction f AT (VERSION => 26)`. And the version cannot be looked up
inline: `AT clause cannot contain subqueries`. Setting the snapshot id with
`SET VARIABLE` and reading it with `getvariable` works.

### Expiring snapshots frees no storage
On the scale-10 lake, `ducklake_expire_snapshots` removed 39 of 40 snapshots and
left 184 files and 19,753,875 bytes unchanged. Only
`ducklake_cleanup_old_files` removed anything (down to 165 files, 19,288,499
bytes). A retention job needs both calls: after the expire alone, the old
versions could no longer be queried and every one of their files was still stored.

### Two agents worked around the same test, separately
The technique test compared `correct.sql` output to ground truth with `==`. A
column has one type, so a count unioned with an amount came back as `83.00`
against a ground truth of `83`. Two Sonnet agents, briefed separately and
working in separate worktrees, both typed the value column as
`UNION(i BIGINT, d DECIMAL(18,2))` so the comparison would pass. Both reported
it as an interpretation they had to make.

The workaround was reasonable for each agent, since the brief made tests and the
runner read-only. The fact that two agents hit it independently showed the
contract was wrong. The comparison now works by value (`runner.same_figures`),
and the three queries are plain `UNION ALL` again. The signal was in the reports:
both agents listed the same workaround under "interpretation calls", and reading
that section of each report before reading the diffs is what caught it.

## Iteration 10 — 2026-09-14 — truncating the field a conclusion rests on

### A 40-character summary produced a finding the data didn't contain
Probing the six MCP reference servers, we summarised the JSON reports with a script
that cut each error message to 40 characters so the table would fit a terminal:

```python
c["discover"]["evidence"][:40]
```

The Python servers' rows came out as `rejected: error -32602: Invalid request`. That
looked like the code and the message disagreeing, since `-32602` means invalid params
and "Invalid request" is the name of `-32600`. It went into the design record, the
evidence card, a backlog entry and a pull request description as a finding. The full
message had been in the report on disk the whole time: "Invalid request parameters",
which matches `-32602`. The slice had cut off the one word the claim depended on.

Nobody checked it against the raw report. It surfaced a few hours later, when a
re-run's summary happened to use a 52-character slice and the full message fit.

**Before a summary becomes a claim, read the raw record for the field the claim rests
on.** Truncating, rounding or taking the first N items is fine for spotting a pattern,
and each of them decides which details survive without saying so. Here the check would
have been one `grep` against the JSON file.

## Iteration 8c — 2026-09-07 — check the config before you believe the comparison

### A generation-config bug is indistinguishable from a model-quality finding
Comparing four local models produced an interesting-looking result: the 14B was
worse than the 7B. It was our default sampling temperature — 0.8, inherited
because we passed no options — and it hit the larger model hardest, since more
capacity means more plausible variations to sample from. At temperature 0 the
effect vanished entirely.

**Before comparing models, check every parameter you did not set.** A default you
never chose is still a variable in the experiment, and this one produced a clean,
publishable, completely wrong conclusion.

### Temperature 0 is a correctness requirement for extraction, not a preference
For "copy this text character for character", sampling introduces variation into
the one thing that must not vary — and the failure is invisible in the output, so
it surfaces only as an unexplained drop in downstream verification. Any task whose
success criterion is *exact reproduction* should be deterministic, and the code
should say why, so nobody later removes it thinking it is a tuning knob.

### The user asking "is it our prompt?" was worth more than another run
The measurement was already recorded and about to be written up as a finding about
model size. The question that unstuck it was not a better experiment, it was
someone asking whether the instrument was at fault. **When a result is surprising,
the first hypothesis should be your own setup**, and it is worth inviting that
challenge explicitly rather than waiting to be lucky.

### Report the failure mode, not just the success rate
All four models land at 75-90% yield, which makes them look interchangeable. The
`exact` versus `whitespace` breakdown says otherwise: llama3.1 reproduced 15
excerpts exactly, phi4 only 2. Same yield, materially different faithfulness, and a
corpus built on whitespace-normalised matches is a weaker artefact than one built
on exact ones. **A single headline rate hides which kind of right the answer was.**

## Iteration 8b — 2026-09-07 — a rate from eight samples is not a rate

### Do not report a percentage from single-digit trials
"25% yield" was computed from 8 attempts and written into a findings log to two
significant figures. A run four times larger, same model, gave 70%. Nothing was
miscalculated; the sample was simply too small to carry a number, and formatting
it as a percentage implied a precision it never had. **Either gather enough trials
to state a rate, or state the raw counts and say the sample is small.**

### When a measurement moves, look for the variable you did not control
The tempting reading of 25% → 70% is noise, and it is partly that. But the
per-document breakdown showed something better: 4/5 on prose, 2/5 on dense
markdown full of tables and code fences. The first run happened to be half
composed of the hardest document in the set. **A number that moves between runs is
an invitation to find the variable you were averaging over** — here, that yield is
a property of the (model, corpus) pair, which is more useful than either number.

### Correct in place, and leave the old number visible
The fix was to rewrite the finding and say plainly what it used to claim. A
findings log that quietly edits its own history is worth less than one that shows
where it was wrong — the whole value of writing verdicts down is being able to see
which ones did not hold.

## Iteration 8 — 2026-09-07 — designing for the failure you expect

### Name a counter for what it counts, or it will lie in the report
`annotate` shipped with `unparseable` counting *provider exceptions* while bad
JSON landed in `malformed`. Both names sounded right and neither described what it
held, so the report said "unreadable JSON: 0" for a run where every reply was
unreadable. A test caught it, and the fix was in the code rather than the test:
`call_failed` and `malformed`, each named for the thing that actually happened.

### An asymmetric failure mode is a design choice, and it is worth paying for
Asking a model for character offsets and asking for a verbatim quote look like the
same request with different ergonomics. They are not. Wrong offsets are *invisible*
-- they score every strategy against the wrong text and nothing downstream can
detect it. A quote that cannot be found is *loud*, and the question simply goes
away. Given a choice between a failure you cannot see and one you can count,
**take the countable one even when it costs you data**: on a local 8B model this
one costs 75% of the attempts, and the alternative would have been a corpus that
looked complete and was quietly wrong.

### Locate against the whole document, not the window you sampled
The model is shown a 4000-character window, but the quote must be found in the
*whole* document, because the offsets have to address the text that will actually
be chunked. Locating within the window and adding the offset seems equivalent and
is not: the model often quotes text that also appears elsewhere, and the window is
an artefact of sampling rather than a real boundary.

## Iteration 7b — 2026-09-07 — summary statistics that hide the finding

### A median is the wrong summary for an axis that fails rarely
The `axes` command originally printed two medians and a verdict: chunker 5.6×,
retriever 1.3×, "the chunker moves this metric more". True, and it buried the
result. The two axes have nearly identical *maxima* (14.4× and 14.9×) and wildly
different *frequencies* (15/15 versus 4/25). The interesting finding is not which
is bigger, it is that one matters always and the other matters seldom and then
catastrophically — and a median cannot express that.

**Report a distribution whenever the thing being summarised can be rare and
large.** The command now prints n, min, median, max and how often each axis
exceeded 2×, and says outright to read the per-row table rather than the summary.
I only noticed because two outliers in the raw output looked wrong; if the table
had not been printed above the summary, the finding would have been lost.

### Guard against the bias you expect, then check whether it happened
The offline embedder was expected to understate the retriever axis, so the tool
warned and the number stayed unquoted until a real encoder ran. Then the real
encoder gave 5.6×/1.3× against the fallback's 5.9×/1.5× — the retriever axis got
*slightly smaller*, not larger. The precaution was right as method and wrong as
prediction, and both halves are worth keeping: you could not have known without
running it, which is the entire argument for running it.

### Check the obvious explanation before publishing it
"The retriever matters more when the chunking is worse" is a tidy story, fits the
data at a glance, and is false here: the rank correlation is −0.04. It would have
been very easy to assert it from the two outliers and never look. One `spearman`
call is cheaper than a wrong claim in a findings log.

## Iteration 7 — 2026-09-07 — closing a gap in a measurement

### Ask what the metric can physically see before blaming the signal
`mid_table_rate` does not predict Precision Ω, and the first instinct is that the
signal is useless. The mechanism says otherwise: cutting through a table row makes
the chunks holding the answer *smaller*, which **raises** the ceiling. Ω cannot see
table damage even in principle — the damage is to whether a retrieved chunk is
*usable*, and a ceiling on precision measures nothing of the kind. **A null result
is about a (signal, metric) pair, never about the signal alone.**

### The fix for "the corpus lacks X" is rarely "download a document with X"
The obvious move was to fetch a PDF with tables in it. Two things stopped it, and
only the second is obvious in hindsight. The detectors match *Markdown syntax*, so
extracted PDF text trips neither — closing that would mean a PDF→Markdown converter
and a measurement that depends on the converter's table detection instead of on
chunking. And the experiment needs **character-level gold spans**, which no
downloaded document carries, whatever its format. This repo's own docs have 346
table rows sitting unusable for exactly that reason. **Annotation, not format, is
almost always the binding constraint on an evaluation corpus.**

### Generated corpora are honest when the generator controls the setup and not the outcome
Planting the structure *and* the answers sounds like rigging the experiment. It is
not, provided you name the line: the generator decides where tables and answers
are; it does not decide whether a chunker that shreds tables scores worse. That
relationship is measured, and it came back negative. State the limitation as
external validity — how these documents behave, not how common they are — and the
result stands.

### Replication across an unrelated corpus is what turns a number into a finding
`boundary_fidelity` at partial +0.44 on Chroma prose was interesting and could
easily have been an artefact of five documents. At +0.34 on synthetic
documentation, with three of five corpora significant, it is a finding. The second
corpus cost an afternoon and did more for confidence than any amount of re-reading
the first result.

## Iteration 6 — 2026-09-07 — reporting a correlation honestly

### A strong correlation with a mechanical explanation is not a finding
`median_length` predicts Precision Ω at −0.95 across every corpus, and it means
almost nothing: Ω divides by the chunks holding the answer, so smaller chunks
raise it by construction. The number is real, reproducible, and evidence of
nothing. **Before reporting a correlation, ask whether the metric's own definition
already implies it** — and if it does, report the partial correlation instead.

### Controlling for the confound can make a signal look *better*
The expectation was that partialling out size would shrink everything. It shrank
most things and **doubled** `boundary_fidelity`, from ~+0.15 raw to +0.44
controlled. Size was masking it, because strategies that cut cleanly also cut
larger. A raw correlation near zero is not evidence of no relationship; it can be
two relationships cancelling.

### "0.00" and "no variance" must not print the same way
`mid_table_rate` was 0.00 on all five corpora — not because it fails to predict
anything, but because those corpora contain no tables, so the signal never varies
and there is nothing to correlate. Printed as `+0.00` next to genuine
correlations, it reads as "tested, found useless". It is untested. The fix is one
`len(set(xs)) <= 1` check and a different label, and it is the difference between a
table you can trust and one that quietly launders an absence of data into a
result.

### Design the schema for the query, and the experiment is an afternoon
The result rows were shaped months of work earlier so intrinsic and extrinsic
metrics land together, keyed by strategy and corpus. That decision cost a
conversation at design time. Collecting on it was a `GROUP BY`, two statistics
functions, and a CLI command — no re-running, no re-deriving, no separate harness.
**When a future analysis is foreseeable, the cheap moment to enable it is when the
schema is being written.**

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
