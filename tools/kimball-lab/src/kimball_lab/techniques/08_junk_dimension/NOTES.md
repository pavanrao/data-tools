# 08 · Junk dimension: the flags on a transaction

**Question:** how many distinct combinations of channel, reversal,
international and contactless occur in 2025-2026's transactions, against how
many are possible?

## What it is

A junk dimension collects several low-cardinality columns that don't belong
to any other dimension -- flags and indicators, mostly -- into one dimension
keyed by a single surrogate key. The dimension does not need to hold every
combination the columns could produce. Kimball's rule for it is to hold the
combinations that occur, found by running `DISTINCT` over the fact data once,
at load time.

## How it works here

`fact_transaction` carries four flag columns: `channel` (six values),
`is_reversal`, `is_international`, `is_contactless` (each boolean). The full
cross product is 6 x 2 x 2 x 2 = 48 possible combinations.

`build.sql` builds `dim_txn_profile` from `SELECT DISTINCT channel,
is_reversal, is_international, is_contactless FROM fact_transaction`, giving
each combination that occurs its own `profile_sk` by `row_number()`. It also
builds `fact_transaction_profile`, mapping each
`txn_id` to its `profile_sk`, standing in for what a fact table rebuilt on
the junk key instead of the four flag columns would carry.

`naive.sql` builds the same shape of table -- channel crossed with three
booleans -- but as the literal cartesian product of the two domains, using
`VALUES` lists rather than reading the fact table. Counting that table's rows
to answer "how many combinations are observed" reports the size of the
domain, 48, regardless of what has been posted: a system-channel transaction
that is also contactless, or a reversal that is also international, counts
as "observed" even though this bank has never recorded one.

## The number

`kimball-lab seed --scale 10 --seed 42`. 410,779 transactions.

| figure | naive (cartesian) | correct (junk dim) | ground truth |
|---|---:|---:|---:|
| flag_combinations_observed | 48 | 14 | 14 |
| flag_combinations_possible | 48 | 48 | 48 |

14 combinations occur out of 48 possible. `flag_combinations_possible` is
the size of the domain by definition, and the cartesian product built in
`naive.sql` is that domain, so `naive.sql` reports it correctly with no
input from this technique. `flag_combinations_observed` is a different
question -- what the fact table contains -- and `naive.sql` never reads the
fact table to answer it, reporting the domain size again and missing by
3.4x.

My own measurement, not something the seed plants: `dim_txn_profile` holds 14
rows against 410,779 fact rows, a ratio of about 29,341 to 1. Every one of
those 410,779 rows currently stores its own copy of `channel`,
`is_reversal`, `is_international` and `is_contactless`; a fact table rebuilt
on `profile_sk` would store one integer per row and look the four values up
against 14 dimension rows instead. `fact_transaction_profile` in this lab
sits alongside those four columns rather than replacing them, so it
demonstrates the join `profile_sk` supports without this lab's fact table
being rebuilt to use it.

## Why

Each of the four flag columns is nearly free to store on its own, which is
why a real warehouse might leave them on the fact and skip the junk
dimension (see below). The dimension earns its keep when a query
wants to filter or group by the combination itself -- "transactions that are
contactless and domestic, broken out by channel" -- which otherwise means
naming all four columns in every `GROUP BY` and hoping the analyst lists them
consistently across queries. `dim_txn_profile.profile_sk` is one column that
means the same four-way combination everywhere it is used.

## When not to use it

- **When the columns are cheap and rarely filtered together.** Four booleans
  and a six-value string cost little on the fact directly; a junk dimension
  adds a join for a saving that, per row, is real but small.
- **When the domain is dense.** If close to all 48 combinations occurred,
  building the dimension from `DISTINCT` would save little over the
  cartesian product, and the cartesian version would at least be simpler to
  reason about and to extend when a new channel is added.
- **When a new value should appear in the dimension before any fact uses
  it.** `dim_txn_profile` here only has combinations that have already
  happened, so a combination a product team is about to launch is absent
  until the first transaction with it posts. A dimension meant to list every
  combination a new channel or flag could ever take, in advance of any
  transaction, is the cartesian product `naive.sql` builds -- useful for that
  purpose, and still the wrong table to count for "how many are observed".

## Files

- `build.sql`: `dim_txn_profile` and `fact_transaction_profile`
- `naive.sql`, `correct.sql`: the two queries above
