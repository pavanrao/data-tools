# 01 · Declare the grain

**Question:** what total checking-plan fees did the bank earn in 2025?

## What it is

The grain of a fact table is the answer to "what does one row mean?" It is
the first decision Kimball's design process makes, before a single dimension
is picked, because every measure in the table has to be true at that grain.
`fact_transaction`'s grain is one posted transaction. A measure that is true
at a coarser grain -- an account's plan fee, true once per month, not once
per transaction -- does not belong on that table, and a query that sums it
across the transaction grain fans out: it counts the same monthly fact once
for every transaction that happens to share the month.

## How it works here

`monthly_fee` lives on `dim_account`: one value per account, in USD, not tied
to any particular transaction. `core/40_fact_transaction.sql` does post a fee
transaction once a month (`txn_type = 'fee', channel = 'system'`), so the fee
is charged correctly in the ledger sense -- but that is a separate fact row
from the account attribute, and nothing stops a query from joining the
attribute onto the wrong grain instead of reading the fact that was already
posted at the right one.

`build.sql` declares the grain the question is asked at:
`fact_account_month`, one row per checking account per month it was open at
month end, carrying that month's fee. `correct.sql` sums the table as built.
`naive.sql` joins `dim_account.monthly_fee` onto `fact_transaction` and sums
across every transaction row instead -- the plausible mistake, because the
join itself is unremarkable and the query reads like any other join-and-sum.

## The number

`kimball-lab seed --scale 10 --seed 42`. 1,764 non-inferred checking accounts
exist by the end of the load; 1,172 of them carry a nonzero monthly fee. CHK
accounts averaged 10.78 transactions per account-month in 2025.

| | naive | correct | ground truth |
|---|---:|---:|---:|
| plan_fee_usd_2025 | 981,909.00 | 88,288.00 | 88,288.00 |

The naive query reports 11.12 times the true 2025 plan fee total. That factor
sits close to the 10.78 average transactions per account-month: each month's
$5 or $12 fee gets multiplied by however many transactions that account made
that month.

## Why

Declaring the grain up front is what keeps a fact table additive along every
dimension it exposes. Once `fact_account_month` exists at account-month
grain, summing rows sums months: there is no dimension left to fan out
along, because the table only has one row per month per account. Without
that table, the correctness of a query like this one depends on someone
remembering, every time, that `monthly_fee` cannot be pulled through
`fact_transaction`. A join cannot enforce that memory; only a comment next
to the column can ask for it.

## When not to use it

- **A measure whose grain already is the transaction never needs this.** A
  purchase amount or an interest payment is one-per-transaction by nature,
  and belongs on `fact_transaction` as is.
- **Don't build a new fact table for every coarser measure.** If the coarser
  grain is a simple `GROUP BY` away and nothing joins an unrelated attribute
  onto it, a view or an ad hoc aggregate is enough. `fact_account_month`
  earns its place here because `monthly_fee` is an attribute of a *different*
  grain (the account) that would otherwise get joined straight onto the fact.

## Files

- `build.sql`: `fact_account_month`, the account-month grain
- `correct.sql`, `naive.sql`: the two queries above
- `core/40_fact_transaction.sql`: where the transaction-grain fee fact is
  posted each month, for comparison
