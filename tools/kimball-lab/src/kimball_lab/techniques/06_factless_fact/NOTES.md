# 06 · Factless facts: promotion coverage

**Question:** how many branch-product promotions ran, and how many of them
opened no accounts at all?

## What it is

A factless fact has no measure column. Its rows record that a combination of
dimensions occurred together -- a student attended a class, a promotion ran
at a branch -- and the count of matching rows is the only number it ever
gives up on its own. Its real use is a coverage question, asked by joining it
against something else: which combinations happened, and, by anti-joining
against the thing the combination was supposed to cause, which combinations
that could have happened did not.

## How it works here

`build.sql` builds `fact_promotion_coverage` from `hist_promotions`, which
keeps every promotion delivered across all 18 batches: every branch runs one
or two product promotions a month, for the life of the lab, so the row count
does not depend on the seed's customer count. Each row is `branch_sk`,
`product_sk`, and a `month_date_key`, no measure. `correct.sql` anti-joins
that table against `dim_account`, defining an opening as an account whose
`open_date` falls in the promotion's branch, product and month.

At `kimball-lab seed --scale 10 --seed 42`, there are 161 promotions across 6
branches and 18 months. 16 of them (9.9%) opened no account, spread 2 or 3 per
branch:

| branch | promotions without an opening |
|---|---:|
| B01 | 3 |
| B02 | 3 |
| B03 | 3 |
| B04 | 2 |
| B05 | 2 |
| B06 | 3 |

## The number

`kimball-lab seed --scale 10 --seed 42`, then `kimball-lab load` and
`kimball-lab demo 06`. `fact_promotion_coverage` carries no measure column, so
`count(*)` is the only aggregate either query below can use.

| figure | naive | correct | ground truth |
|---|---:|---:|---:|
| promotions | 145 | 161 | 161 |
| promotions_without_openings | 0 | 16 | 16 |

## Why

The naive query starts from `dim_account` -- what happened -- and
joins to `hist_promotions` to see which openings landed inside a promoted
branch, product and month. That finds only the 145 promotions that produced
at least one opening; the other 16 have no opening row to join from, so the
query's whole working set is built out of openings that happened to match a
promotion, never out of the promotions themselves. Asked directly for "how
many promotions had no openings," that same query can only return zero: the
promotions with nothing to show for them were never loaded into it.

Seeing the 16 requires enumerating the promotions first and asking what, if
anything, matches each. That anti-join direction is what `fact_promotion_coverage`
is built for, and what `correct.sql` runs below.

## When not to use it

- **The question needs an amount.** A factless fact carries no measure
  column; `count(*)` is the only aggregate it offers. A question of "how
  much," rather than "how many" or "which," needs a measure column added --
  and the fact stops being factless once it has one.
- **The universe of possibilities is not well defined.** This coverage check
  only works because every branch-product-month combination that could be
  promoted is enumerable and delivered every batch. A coverage question is
  only as trustworthy as the completeness of the "could have happened" side
  of the anti-join.

## Files

- `build.sql`: the factless fact build
- `naive.sql`, `correct.sql`: the two queries above
