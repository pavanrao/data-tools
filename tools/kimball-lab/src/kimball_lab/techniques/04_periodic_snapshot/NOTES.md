# 04 · Periodic snapshots: semi-additive measures

**Question:** what was the bank's total USD balance at the end of December
2025, and the average daily balance across that month?

## What it is

Kimball sorts a fact's measures by how far they can be summed:

- **Additive** measures sum across every dimension. A transaction amount is
  additive: add it across accounts, across days, across branches, and the
  result still means something.
- **Semi-additive** measures sum across some dimensions but not others. An
  account balance sums across accounts (many accounts make a bank's total) but
  not across time: a balance is a level, not a flow, so adding Monday's
  balance to Tuesday's does not produce a meaningful two-day figure.
- **Non-additive** measures, like a rate or a ratio, cannot be summed at all;
  they have to be recomputed from their parts.

A periodic snapshot fact exists to hold a semi-additive measure. It takes a
reading of every entity on a regular interval, whether or not anything
happened, so "the balance on day X" is always a row already sitting in the
warehouse.

## How it works here

`core/50_fact_account_daily_balance.sql` builds `fact_account_daily_balance`,
grain one account per day. Every batch extends every open account's rows
through the end of the batch month, computing each day's balance as the prior
balance plus that day's postings, running as a window sum over
`fact_transaction`. A late-arriving transaction, or an inferred account
resolving with its opening balance, deletes and rebuilds the affected days
from that point forward, so the snapshot always agrees with the transaction
fact. Each row carries `balance_local`, the day's `fx_rate`, and `balance_usd`
(the two multiplied).

The month-end figure sums `balance_usd` for the one day, 2025-12-31, across
every account. The daily average sums `balance_usd` per day across accounts
first, then averages those 31 day-totals: 31 numbers go into that average, one
per day, regardless of how many accounts were open on any given day.

## The number

`kimball-lab seed --scale 10 --seed 42`, then `kimball-lab load` and
`kimball-lab demo 04`. December has 92,904 account-day rows.

| figure | naive | correct | ground truth |
|---|---:|---:|---:|
| month_end_balance_usd_2025-12 | 3,690,929,059.49 | 127,927,552.36 | 127,927,552.36 |
| avg_daily_balance_usd_2025-12 | 39,728.42 | 119,062,227.73 | 119,062,227.73 |

The naive month-end figure is 28.9 times the correct one (2,785% too high):
it sums 31 days' worth of bank-wide balances instead of reading the single
day, 2025-12-31. The naive average is 0.033% of the correct one: it divides
that same 31-days-of-balances sum by the *count of account-day rows*, 92,904
of them for December, landing close to a single account's typical daily
balance -- a different question from the bank's daily total.

## Why

Summing a balance over time answers a question nobody asked. It is the
same mistake as adding up your bank balance on every day of the month and
reporting the sum as "your balance": the total tracks how many days you
looked, which has nothing to do with what you have. The two queries above
show the reductions that do answer something -- an ending value for the
month-end figure, an average for the daily one -- and both need each day
counted once, which is what summing every account-day row skips.

Storing the reading every day, rather than computing it on demand, is what
makes "the balance on 2025-06-15" and "the balance on 2025-12-31" equally cheap
to ask for. Without the snapshot, either figure would need a query that sums
every `fact_transaction` row posted from the account's opening up to that
date -- a running total that gets more expensive the longer an account has
existed. `fact_account_daily_balance` runs that sum once per batch, at load
time, so no query has to replay it.

## When not to use it

- **The measure is additive.** A transaction amount does not need a
  periodic snapshot; summing it directly, the way `fact_transaction` is
  queried, is already correct. Building a snapshot for an additive measure
  only adds storage and a reduction step nobody needs.
- **The entity changes state rarely and moves through known stages.** A loan
  application does not need a balance reading every day of its life; it needs
  one row that fills in as milestones happen. That is technique 05.
- **The grain is too fine for the volume.** A row per account per day is
  affordable at this lab's scale. A row per account per minute for every
  account at a real bank would not be; the interval has to match what the
  business asks for.

## Files

- `core/50_fact_account_daily_balance.sql`: the periodic snapshot build
- `naive.sql`, `correct.sql`: the two queries above
