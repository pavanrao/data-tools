# 02 · Surrogate keys: SCD type 1 vs type 2

**Question:** what was 2025 fee revenue by customer segment, counting each fee
under the segment the customer was in when they paid it?

## What it is

A slowly changing dimension is a dimension whose attributes change now and then:
a customer moves from the mass segment to affluent, or moves house. Kimball names
the responses by type. Two of them matter here:

- **Type 1** overwrites the attribute. The dimension holds one row per customer,
  and that row describes the customer as they are today.
- **Type 2** keeps the old row, closes it, and adds a new one. Each version gets
  its own **surrogate key**, a meaningless integer the warehouse assigns, and
  each fact stores the key of the version that was current when it happened.

## How it works here

`core/20_dim_customer.sql` maintains `dim_customer` as type 2. Every row has
`valid_from` (inclusive), `valid_to` (exclusive, `9999-12-31` while open) and
`is_current`. A batch that changes a customer's segment closes the current row
at the change's effective date and inserts a new row under the next surrogate
key.

`core/40_fact_transaction.sql` looks the customer up **as of the trade date**,
against those intervals, and stores the surrogate key it finds. A fact loaded
late still gets the version it was traded under. The lookup happens once, at
load time. Queries never repeat it.

DuckLake has no sequences, so the load assigns keys as the current maximum plus a
row number. Kimball puts key assignment in the ETL anyway.

The query that shows the difference is two joins long:

- `naive.sql` goes from the fact to its customer version, then jumps to that
  customer's current row. That is the only row a type 1 dimension would have.
- `correct.sql` joins on the surrogate key and stops.

## The number

`kimball-lab seed --scale 10 --seed 42`. 160 of 2,005 customers change segment
at some point in the eighteen months.

| segment | naive (type 1) | correct (type 2) | ground truth |
|---|---:|---:|---:|
| affluent | 36,342.00 | 32,860.00 | 32,860.00 |
| mass | 74,882.00 | 79,280.00 | 79,280.00 |
| private | 7,339.00 | 6,423.00 | 6,423.00 |

The naive query overstates affluent revenue by 10.6% and private by 14.3%, and
understates mass by 5.5%. The total is 118,563.00 either way. That is why this
error survives review: reconciling against the ledger total shows nothing
wrong. The naive query moved revenue between segments without changing the sum.

The shift runs one way because the seed makes most changes upgrades: four in
five mass customers who change move to affluent. Everything a customer paid
before the upgrade is counted under the segment they upgraded to.

## Why

Type 1 changes the past. After an overwrite, last year's report comes out
different when you run it again, and nothing records that it changed. With
type 2, the report for a closed period stays fixed.

The surrogate key is what keeps the query simple. Without it, every query that
wants history has to repeat the date-range join that the load already did once:
`trade_date >= valid_from AND trade_date < valid_to`. Every copy is a chance to
write `<=`, or to forget that the interval is half-open. The key moves that
logic into the load, where it can be tested once.

## When not to use it

- **Corrections.** If a customer's name was misspelt, the old spelling was never
  true, so type 1 is correct. Kimball's rule is to decide per attribute, not per
  table. `dim_customer` tracks segment, home branch and city as type 2 because
  each of those changes how facts group.
- **Fast-changing attributes.** An attribute that changes monthly for most rows
  multiplies the dimension by that factor. Move it to a mini-dimension or keep
  it on the fact.
- **When "as it is today" is the question.** Type 2 answers "as it was". If a
  report wants every customer under their current segment, that is technique 03
  (type 6). Don't rewrite this query to get it.

A backdated change can also be earlier than the current row's start, which
means history has to be split. This load does not handle that case, and the seed
never sends one. See `docs/015`.

## Files

- `core/20_dim_customer.sql`: the type 2 load
- `core/40_fact_transaction.sql`: the as-of lookup, and the re-key after a
  backdated change
- `naive.sql`, `correct.sql`: the two queries above
