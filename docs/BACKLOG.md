# BACKLOG

Known defects and deferred work: things that are **wrong or unfinished in the
code as it stands**, written down so they stop being rediscovered.

This is the fifth document class, and it exists because the other four had
nowhere to put a known-broken test. `FINDINGS.md` holds verdicts about what to
build and park. `LEARNINGS.md` holds craft worth reusing. The numbered series
holds design and decisions. None of them is the right home for "this is broken,
here is exactly how, nobody has fixed it yet".

**Cadence:** edited in place. An entry is added when a defect is found and
deleted when it is fixed, with the fix's reasoning going to `LEARNINGS.md` if it
earned any. Entries are numbered `B1`, `B2`, … and numbers are not reused.

**The bar.** An entry states what is wrong, how to reproduce it, why it is wrong
rather than merely surprising, and what a fix would have to decide. An entry that
cannot say why it is wrong is a preference, and belongs in `IDEAS.md`.

---

## B1 — Two `ingest-ledger` tests fail when the optional extras are absent

> **Status: open.** Found 2026-09-08 while upgrading the MCP SDK (D10). Not
> introduced by that change — it reproduces on the previous lock.

**Reproduce.**

```bash
uv sync                     # base environment, no extras
uv run pytest tools/ingest-ledger/tests/test_cli.py::test_manifest_never_extracts \
              tools/ingest-ledger/tests/test_compare.py::test_comparison_flags_every_silently_damaged_input
# 2 failed

uv sync --all-extras        # what `make sync` does
uv run pytest               # 312 passed, 7 skipped
```

**What is actually happening.** Both tests use the session-scoped `hostile`
fixture in `tools/ingest-ledger/tests/conftest.py`, whose docstring states the
contract plainly:

> Fixtures whose optional dependency is missing are omitted from the mapping
> rather than faked, so a test that needs one skips instead of lying.

Three builders in `tools/ingest-ledger/corpus/generate.py` return `False` when
their optional dependency is missing, and the fixture then drops those files:

| Builder | Needs | Supplies |
| --- | --- | --- |
| `multi_sheet_xlsx` | `openpyxl`, the `xlsx` extra | the `sheets` line in the manifest |
| `scanned_pdf` | `fitz` / PyMuPDF, the `pdf` extra | the `pages` line, and a flagged row |
| `whitebox_pdf` | `fitz` / PyMuPDF, the `pdf` extra | a flagged row |

The corpus therefore shrinks to five files. The two tests assert against the full
one:

- `test_cli.py:25` asserts `"sheets" in out and "pages" in out`. Neither file
  that produces those lines was built, so neither string appears.
- `test_compare.py:52` asserts `flagged >= 3` and gets `2`. The third flag comes
  from a PDF that was not built. `liar.pdf` (HTML behind a `.pdf` extension) also
  degrades: with PyMuPDF the naive extractor reads 26 characters of HTML and the
  row is flagged, and without it the extractor raises `ModuleNotFoundError` and
  the row is not.

**Why this is wrong and not merely surprising.** `CONVENTIONS.md` rule 6 says
*tests run with nothing optional installed*. These two do not. The fixture
already anticipates exactly this and says a dependent test should **skip**; these
two accept the reduced corpus and then assert against the full one. The repo has
a working pattern for it, used three times already —
`pytest.importorskip("pdfmux")` at `test_hostile_corpus.py:89`, and
`pytest.mark.skipif` at `chunking-lab/tests/test_reproduction.py:27`.

The failure mode is the bad one: a green suite on a developer machine that has
run `make sync`, and a red suite for anyone who runs a bare `uv sync`. CI does
not catch it either — both workflow jobs run `uv sync --all-extras`
(`.github/workflows`, lines 16 and 27), so the extras are always present there.
Nothing anywhere currently exercises the bare environment that rule 6 describes,
which is why this went unnoticed, and it makes rule 6 untrue in a way that is
worse than the two tests being wrong.

**What a fix has to decide.** Not obvious enough to do in passing, which is why
this is an entry rather than a commit:

1. **Skip, matching the existing pattern.** Cheapest and consistent. Costs real
   coverage: on a bare environment nothing then checks that the manifest reports
   structure for the formats that need a library to read.
2. **Split each test.** Keep the structural assertions that hold on the reduced
   corpus running bare, and move the extras-dependent assertions into separate
   tests that skip. More faithful to rule 6, and more test code.
3. **Assert against the corpus that was actually built.** Derive the expected
   flag count from the fixture rather than hard-coding `3`. Removes the coupling
   entirely, and weakens the test — a builder silently returning `False` would
   stop being visible.

Option 2 is the one that keeps rule 6 honest without losing coverage, but it is a
judgment call about how much test code the tool's owner wants for a corpus that
is itself a test fixture.

**Not in scope when found.** The MCP SDK upgrade touched neither `ingest-ledger`
nor its extras. Fixing it there would have mixed an unrelated change into a
dependency bump.
