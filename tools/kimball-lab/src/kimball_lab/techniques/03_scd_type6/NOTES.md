# 03 · Type 6: hybrid SCD (1+2+3)

**Question:** what was 2025 fee revenue by customer segment, counting every fee
a customer ever paid under the segment they are in today?

## What it is

Type 6 carries all three of Kimball's single-attribute responses on the same
dimension row instead of picking one. The name is arithmetic: 1 + 2 + 3 = 6.

- **Type 2** (kept from `dim_customer`): `segment`, with `valid_from` /
  `valid_to` -- the segment as it was when that version was current.
- **Type 1**: `current_segment`, overwritten on every version of a customer
  whenever the customer changes segment again, so all of a customer's rows
  agree on where they stand today.
- **Type 3**: `previous_segment`, the segment on the row immediately before
  the current one, `NULL` for a customer who has never changed.

## How it works here

`build.sql` adds a view, `dim_customer_scd6`, over `dim_customer`. It does not
touch `dim_customer` itself or `core/40_fact_transaction.sql`'s customer_sk
lookup, so `dim_customer_scd6` is a second way to read the same type 2 rows,
not a replacement dimension. Two CTEs supply the added columns:
`current_row` picks the `is_current` row's segment per customer,
`previous_row` ranks each customer's non-current rows by `valid_from`
descending and takes the first.

`naive.sql` is technique 02's `correct.sql` with a renamed key: join on the
surrogate key, group by `segment`, stop. That answers "as it was traded",
which is technique 02's question. It answers this one only for a customer
who has never changed segment, because a customer who did has fees split
across two or more surrogate keys, each carrying the segment of its own
version. `correct.sql` reads the same fact rows through the same join and
groups by `current_segment` instead, so every fee a customer ever paid lands
under the one segment value that changes together across all of that
customer's rows.

## The number

`kimball-lab seed --scale 10 --seed 42`. 160 of 2,005 customers change
segment at some point in the eighteen months (technique 02's count -- the
same population, read a different way).

| segment | naive (type 2 alone) | correct (type 6) | ground truth |
|---|---:|---:|---:|
| affluent | 32,860.00 | 36,342.00 | 36,342.00 |
| mass | 79,280.00 | 74,882.00 | 74,882.00 |
| private | 6,423.00 | 7,339.00 | 7,339.00 |

The naive query understates affluent by 9.6% and private by 12.5%, and
overstates mass by 5.9%. The total is 118,563.00 either way, for the same
reason it was in technique 02: fees move between segments, not off the
books.

These are technique 02's numbers, exchanged. 03's correct figures
(36,342.00 / 74,882.00 / 7,339.00) match 02's naive figures to the cent: the
type 1 answer, which 02 marks wrong for "as was". 03's naive figures
(32,860.00 / 79,280.00 / 6,423.00) match 02's ground truth to the cent: the
type 2 answer, which this technique marks wrong for "as is". Each figure has
a question it answers correctly and one it doesn't, which is why
`dim_customer_scd6` keeps both `segment` and `current_segment` on the row
instead of choosing.

## Why

A single overwritten segment column (type 1 alone) cannot answer "as it was
traded", because the history it would need is gone. A single type 2 history
can answer "as it stands today" too, but only by adding a second join back to
the current row for every customer -- the same repeated-logic problem
technique 02 raises for the date-range join, moved from a date interval to a
self-join on `customer_id`. `build.sql` runs that second join once, when
`dim_customer_scd6` is built, rather than leaving it for every query that
wants "as is" to write again.

## When not to use it

- **When only one question is ever asked.** If the business only ever wants
  "as is", `current_segment` alone on a type 1 dimension is `dim_customer_scd6`
  with the other two columns removed -- simpler, and nothing downstream needs
  the interval columns.
- **When the attribute changes fast.** The same limit technique 02 states
  applies here first, since type 6 still carries the type 2 history that type
  1 and type 3 sit on top of.
- **As a materialized table without a reason to pay for it.** This lab
  builds `dim_customer_scd6` as a view because `dim_customer` is small enough
  (2,170 rows at scale 10, unknown member included) that recomputing
  `current_row` and `previous_row` per query costs nothing measurable. A
  dimension with many more versions per entity would want it as a table,
  rebuilt by `build.sql` the way `dim_txn_profile` is in technique 08.

## Files

- `build.sql`: `dim_customer_scd6`, the view adding `current_segment` and
  `previous_segment` to `dim_customer`
- `naive.sql`, `correct.sql`: the two queries above
