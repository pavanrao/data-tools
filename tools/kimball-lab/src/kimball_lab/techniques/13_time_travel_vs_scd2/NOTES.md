# 13 · DuckLake time travel vs SCD type 2

**Question:** what was Q4 2025 fee revenue by segment, as reported when December
closed, and as it is known now?

This technique needs the DuckLake engine. On plain DuckDB, `demo` skips it and
says why.

## What it is

A warehouse has two different kinds of "when", and they need different tools.

- **Effective time:** when something was true in the business. A customer was
  affluent from 1 September. SCD type 2 records this in `valid_from` and
  `valid_to` (technique 02).
- **Recorded time:** when the warehouse knew it. That customer's upgrade was
  delivered in the March batch. Kimball's type 2 does not record this. A
  lakehouse snapshot does: `AT (VERSION => n)` reads a table as it stood after
  commit `n`.

A model that keeps both axes is called bitemporal. The lake gives you the
recorded-time axis without any modelling, until the snapshots are expired.

## How it works here

The runner commits each batch in one transaction, so each batch is one DuckLake
snapshot, and `etl_batch_log` records which. Batch 2025-12 is the year-end
close.

Two things the warehouse learned after that close change Q4:

- **Late facts.** Some Q4 transactions arrive in January or February.
- **A backdated correction.** Batch 2026-03 moves four customers from mass to
  affluent with effect from 2025-09-01. `core/20_dim_customer.sql` closes their
  old rows by overwriting `valid_to`, and `core/40_fact_transaction.sql` re-keys
  their facts from that date. Both are updates in place.

`correct.sql` answers each question with its own axis: as reported from the
snapshot of batch 2025-12, as effective from today's SCD2 tables.
`naive.sql` swaps them. Both substitutions are ones people make: "type 2 keeps
history, so last year's report is in there" and "time travel shows the past, so
Q4 is in the year-end snapshot".

`AT (VERSION => ...)` does not accept a subquery, so the snapshot id is passed
through `SET VARIABLE`. The table alias goes before the `AT` clause:
`fact_transaction f AT (VERSION => ...)`.

## The number

`kimball-lab seed --scale 10 --seed 42`, loaded on DuckLake 1.0 (duckdb 1.5.5).

| figure | naive | correct | ground truth |
|---|---:|---:|---:|
| as reported · affluent | 9,774.00 | 9,563.00 | 9,563.00 |
| as reported · mass | 21,994.00 | 21,830.00 | 21,830.00 |
| as reported · private | 1,867.00 | 1,855.00 | 1,855.00 |
| as effective · affluent | 9,563.00 | 9,774.00 | 9,774.00 |
| as effective · mass | 21,830.00 | 21,994.00 | 21,994.00 |
| as effective · private | 1,855.00 | 1,867.00 | 1,867.00 |

The naive column is the correct column with its two halves swapped, since each
tool answers the other question correctly. Q4 was reported at 33,248.00 and is
now known to be 33,635.00. The difference comes from two sources, measured
separately on the same lake:

- 37 fee transactions worth 387.00 arrived after the close. That accounts for
  the whole change in the total.
- The correction moved 125.00 from mass to affluent and did not change the
  total. Restricted to facts loaded by the close, effective-time Q4 is affluent
  9,688.00, mass 21,705.00, private 1,855.00. The correction re-keyed 790 facts
  across all transaction types.

Then the expiry. On a copy of that lake, `ducklake_expire_snapshots` removed 39
of 40 snapshots, and the as-reported query failed:

```
Invalid Input Error: No snapshot found at version 26
```

The effective-time query gave the same answer as before;
`tests/test_t13_expiry.py` checks both. Expiring snapshots deleted no files.
The space came back only after `ducklake_cleanup_old_files`, which took the
lake from 184 files and 19,753,875 bytes to 165 files and 19,288,499 bytes. So
eighteen months of recorded-time history cost 465,376 bytes, 2.4% of the lake,
for a workload that mostly appends.

## Why

Time travel does not replace SCD2, and SCD2 does not replace time travel. They
record different axes. Snapshots can't supply the effective axis, because a
snapshot can't hold information that had not arrived yet.

Only the effective axis survives in the tables. Once the correction closed a
row and the re-key rewrote the facts, the warehouse's current state had no
record of what December's report said. If the year-end numbers were filed with
a regulator, the snapshot is the only place they can be reproduced from.

## When not to use it

- **As the only audit trail.** An as-reported answer lasts only as long as
  snapshot retention. Once a snapshot is expired, the as-reported figure is
  gone for good. If a figure must be reproducible for seven years, either keep
  the snapshot for seven years or model recorded time in the tables: an
  `etl_batch_id` on facts, plus a load-date interval on dimension rows that is
  closed rather than overwritten.
- **In place of modelling change.** Reading a dimension at an old snapshot to
  get a customer's old segment is effective-time reasoning done with the
  recorded-time tool. It gives the right answer only when nothing arrived late
  and nothing was backdated.
- **On plain DuckDB, or any engine without snapshots.** There is no recorded
  axis unless you build one.

## Files

- `runner.py`: one transaction per batch, one snapshot per batch, `etl_batch_log`
- `core/20_dim_customer.sql`, `core/40_fact_transaction.sql`: the two updates
  in place that remove the December state from the current tables
- `naive.sql`, `correct.sql`: the swap described above
- `tests/test_t13_expiry.py`: expiry removes the as-reported answer and leaves
  the effective one
