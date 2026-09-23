# 015 — `kimball-lab`: the wrong number each technique prevents

Idea **#220**. A runnable reference for Kimball dimensional modelling on seeded
retail-bank data, with plain-SQL ETL on DuckLake. It is not a novel tool, and
unlike most of section F it is not a measurement of something unknown. It is a
reference you can run, and it is built to the section F rule anyway: every
technique ends in a number.

---

## 1. Why it exists

Kimball's techniques are well documented in prose. The Kimball Group keeps the
canonical list, and *The Data Warehouse Toolkit* explains each one. What a prose
list can't show is the cost of skipping a technique. "A balance is
semi-additive" is easy to agree with. Seeing a month-end balance of
3,690,929,059.49 against a true 127,927,552.36 shows what the rule is for.

A prior-art search on 2026-09-23 turned up
[dbt-dimensional-modelling](https://github.com/Data-Engineer-Camp/dbt-dimensional-modelling)
(about 181 stars, AdventureWorks, facts and dimensions only), a Snowflake-only
portfolio repo with no stars that lists most techniques, and several sets of
chapter notes. None runs locally on seeded data with a naive query beside the
correct one. That pairing is what this tool adds.

## 2. Shape

```
seed.py ──▶ batch=2025-01/ … batch=2026-06/   (CSV extracts)
        └─▶ ground_truth.json                  (computed in Python)

runner.py, per batch, one transaction:
    core/00_staging … core/50_fact_account_daily_balance
    reconcile staged vs loaded; write the batch marker; commit

runner.py, after the last batch:
    techniques/NN_*/build.sql

demo: techniques/NN_*/naive.sql and correct.sql, beside ground_truth.json
```

**The contract.** A technique is a directory with `meta.json`, `naive.sql`,
`correct.sql`, `NOTES.md` and an optional `build.sql`. Both queries return
`key, value` rows. The test suite discovers each directory and asserts, on
every available engine, that `correct.sql` equals the ground truth and
`naive.sql` does not.

## 3. Decisions

**D1 — Ground truth is computed in Python, from the generator's own records.**
Were `correct.sql` also the source of truth, a wrong query would agree with
itself. `ground_truth()` in `seed.py` replays each rule directly: segment as of a
date, a balance as opening plus postings, a rate lookup. The first core load
matched it on every figure checked (02, 04, 12, 01) before any technique
existed, which is evidence that the core is right and not merely consistent.

**D2 — Plain SQL, run by a small Python CLI.** Pavan's call. The runner passes
three values through `SET VARIABLE` (`batch_id`, `batch_dir`, `lab_start`).
The SQL reads them with `getvariable`, so every file can be read and run on its
own, with no templating.

**D3 — DuckLake by default, plain DuckDB as a fallback.** A spike on duckdb
1.5.5 with DuckLake 1.0, before any code, settled what the SQL could use:

| checked | result |
|---|---|
| `CREATE SEQUENCE` | `DuckLake does not support sequences` |
| `PRIMARY KEY` | `PRIMARY KEY/UNIQUE constraints are not supported in DuckLake` |
| `NOT NULL`, views, `MERGE INTO`, `SET VARIABLE` | work |
| multi-table transaction | one snapshot |
| `AT (VERSION => n)` after expiring `n` | `No snapshot found at version 5` |

So surrogate keys are assigned in the ETL as the current maximum plus
`row_number()`, which is where Kimball puts key assignment anyway. The same
SQL runs on both engines. The tests use plain DuckDB. They build a DuckLake
warehouse too when the extension already loads without a download, so the
suite needs no network. Technique 13 declares `"requires": "ducklake"`, and on
DuckDB it is skipped with the reason printed. The CLI never falls back
silently: it names the engine in every demo line (CONVENTIONS rule 2).

**D4 — One transaction per batch, with the marker inside it.** With DuckLake,
each batch is then one snapshot, which technique 13 depends on.
`etl_batch_log` is written before the commit, so a batch is either loaded and
marked, or neither, and a re-run skips marked batches. The snapshot id exists
only after the commit, so it is filled in by an update after.

**D5 — The core handles the hard cases once, generically.** Four behaviours
that techniques rely on live in the core, not in any technique:

- SCD2 with half-open intervals. A change closes the current row at its
  effective date.
- Inferred members. An unknown account gets a placeholder row, and the fact is
  kept. The real record overwrites the placeholder in place, with the same key.
- As-of lookup. The customer key is looked up at the trade date, not from the
  current row. A `MERGE` re-keys earlier facts when an account is resolved or a
  backdated change lands.
- The balance snapshot is rebuilt from the earliest date a batch disturbed. That
  date is either a late posting or a resolved account.

**Known limit:** a change dated earlier than the current row's start would need
history split. The load doesn't do that, and the seed never sends one.

**D6 — Figures compare by value.** A column has one type, so a count unioned
with an amount comes back as DECIMAL: 83.00, not 83. Two build agents, working
separately, typed the value column as a DuckDB `UNION(i BIGINT, d DECIMAL)` to
get an exact match. The fix belonged in the comparison
(`runner.same_figures`), and the three queries went back to plain `UNION ALL`.

**D7 — Built by one Opus session and three Sonnet agents.** Opus wrote the
spike, seed, core, runner, CLI and technique 02 as the template, then 13.
Three Sonnet agents, each in its own worktree branched from the template
commit, built 01, 03–12. They were allowed to edit only their own technique
directories. Every number in the docs comes from a clean `make demo-kimball`
run by Opus after the merges, not from the agents' reports. The reports and
that run agreed on every figure.

## 4. Results

Seed 42, scale 10: 2,005 customers, 3,407 accounts, 410,779 transactions.
`make demo-kimball` runs seed, load and all thirteen demos in 14 seconds on
DuckLake. The per-technique table is the
[README's ready reckoner](../tools/kimball-lab/README.md#the-ready-reckoner).
The errors range from three transactions in 24,199 (09, where month-end
crossings in and out nearly cancel) to a factor of 29 (04, balances summed
across days).

**The one result that is not a textbook restatement is technique 13.**
Lakehouse time travel and SCD type 2 record different time axes, and each one
answers the other's question wrongly:

- Q4 2025 fee revenue was reported at 33,248.00 when December closed. It is
  now known to be 33,635.00.
- The 387.00 difference is 37 fee transactions that arrived after the close.
- Separately, a backdated correction moved 125.00 from mass to affluent. That
  correction re-keyed 790 facts.

Once the correction closed the old dimension row and the re-key rewrote the
facts, the current tables held no record of what December's report said. Only
the snapshot did. After `ducklake_expire_snapshots`, the as-reported query
fails with `No snapshot found at version 26`. Expiry deleted no files.
`ducklake_cleanup_old_files` then took the lake from 184 files and 19,753,875
bytes to 165 files and 19,288,499 bytes, so eighteen months of recorded-time
history cost 2.4% of storage here.

## 5. Limits

- The seed is designed to contain each case, which means the size of each
  error depends on the seed's parameters, not on any real bank. The size of an
  error here says nothing about how often it happens in real warehouses.
- The techniques' `build.sql` runs once after the last batch, so the bridge,
  the accumulating snapshot and the coverage fact are rebuilt, not maintained
  incrementally. The core facts are incremental.
- No backdated change earlier than the current version (D5).
- Kimball's full list has well over a hundred techniques; this covers thirteen,
  chosen for finance and for having a number to show.
