# 10 · Conformed dimensions and drill-across

**Question:** by branch, how many transactions traded in December 2025 and
what was the month-end balance?

## What it is

A dimension is **conformed** when two fact tables use it with the same
meaning: the same keys and attributes, at the same grain of dimension row.
`dim_branch` is conformed across every fact in this warehouse -- `B01` means
Midtown whether it is read off a transaction or a balance snapshot. Kimball
calls the map of which business processes use which conformed dimensions the
**bus matrix**. It is the plan for which facts can be compared at all, drawn
before any of them are built.

Conformance is what makes **drill-across** possible: aggregating two facts
separately down to a shared conformed dimension, then joining the two small
aggregates on that dimension's key. The two facts don't need to share a
grain, or know about each other's existence -- only the dimension key has to
mean the same thing on both sides.

## How it works here

| business process | date | customer | account | branch | product |
|---|:---:|:---:|:---:|:---:|:---:|
| transactions (`fact_transaction`) | X | X | X | X | X |
| daily balances (`fact_account_daily_balance`) | X | via account | X | via account | via account |
| loan applications (`hist_loan_events`) | X | X | -- | X | -- |
| promotion coverage (`hist_promotions`) | month only | -- | -- | X | X |

`fact_transaction` and `fact_account_daily_balance` are built at different
grains, one posted transaction and the other an account-day, and neither
carries a foreign key to the other. `branch_id` is the dimension both conform
to: `fact_transaction` stores `branch_sk` straight from `dim_branch` at load
time, and `fact_account_daily_balance` reaches the same `dim_branch` row
through `dim_account.branch_id`, because the balance fact has no branch key
of its own (`docs` note in the module header: "no branch key, reach branch
via dim_account").

`correct.sql` aggregates each fact to `branch_id` in its own CTE, then
`UNION ALL`s the two result sets, which is what makes it a drill-across
rather than a join. `naive.sql` joins the two facts to each other directly,
on `account_sk`, before aggregating: a fact-to-fact join across mismatched
grains, which is the fan trap this technique is named for.

## The number

`kimball-lab seed --scale 10 --seed 42`. Six branches; the correct query
finds 24,199 transactions traded across all of them in December 2025.

| branch | naive txn count | correct txn count | naive balance usd | correct balance usd |
|---|---:|---:|---:|---:|
| B01 | 118,830 | 3,860 | 4,761,156,141.01 | 20,022,363.73 |
| B02 | 126,934 | 4,165 | 5,375,147,382.02 | 21,925,702.65 |
| B03 | 121,375 | 3,954 | 4,477,487,035.32 | 19,870,299.44 |
| B04 | 122,618 | 4,006 | 5,318,920,290.17 | 21,702,138.07 |
| B05 | 123,270 | 4,027 | 5,554,040,095.53 | 22,411,510.97 |
| B06 | 128,939 | 4,187 | 5,191,125,463.07 | 21,995,537.49 |

Every branch's naive transaction count is 30.5-30.8 times the correct count
(30.66 times, summed across branches: 741,966 against 24,199), and every
naive balance is 225-248 times the correct balance (239.81 times, summed:
30,677,876,407.12 against 127,927,552.35). Both ratios track December's day
count: the naive join pairs each of a branch's December transactions with
each of that branch's accounts' December daily-balance rows, up to 31 of
them, so a transaction count multiplies by close to 31 and a balance sum,
which is already a sum over accounts, multiplies again by however many of
those 31 days survive the join for each account.

## Why

Drill-across is what lets a warehouse answer questions that cross business
processes without forcing every fact into one enormous table, or forcing two
facts of different grains into a join that cannot be correct at either grain.
The two aggregates in `correct.sql` are each computed from a single fact and
joined only at the end, on `branch_id`, which means the same thing in both
because both were loaded against the same `dim_branch`. That agreement has
to be designed in at load time, one `dim_branch` whose surrogate keys every
fact references the same way. A query written afterward has no way to
manufacture it if the load didn't provide it.

## When not to use it

- **When a fact-to-fact join is at a shared grain.** Two facts that really
  do share a grain -- account-month plan fees and account-month interest, say
  -- can join directly with no fan-out, because one row on each side matches
  one row on the other.
- **When one process is a strict subset of another at the same grain.**
  Then a single fact table with a few extra flag columns is simpler than two
  facts and a bus matrix.
- **Don't drill across dimensions that aren't conformed.** If two
  facts assigned branch codes from different source systems with different
  meanings, aggregating both to "branch" and joining would silently combine
  numbers that were never comparable. Conformance has to be verified, not
  assumed from column names matching.

## Files

- `core/40_fact_transaction.sql`, `core/50_fact_account_daily_balance.sql`:
  the two facts, at their different grains
- `core/15_dim_branch_product.sql`: `dim_branch`, the conformed dimension
- `correct.sql`, `naive.sql`: the two queries above
