# 07 · Bridge table with a weighting factor

**Question:** what was the bank's total account balance on 2025-12-31?

## What it is

A bridge table resolves a many-to-many relationship between a fact and a
dimension -- here, one account can have more than one customer holding it, and
one customer can hold more than one account. Reporting through a bridge
without a weight double-counts every fact on the many side: an account with
two holders contributes its balance to the total twice, once per holder. A
**weighting factor** on each bridge row is that holder's share of the account,
so a query that multiplies by it before summing gets the account's true total
back, split however the shares divide it, no matter how many holders the
account has.

## How it works here

`build.sql` builds `bridge_account_holder` from `hist_account_holders`, the
full-history table `core/05_history.sql` populates from every batch's
`account_holders.csv`. The extract contract says an account's holders arrive
once, with the account, and never change (`seed.py`'s module docstring), so
`hist_account_holders` has one row per account-customer pair and needs no
deduplication.

Each bridge row carries `account_sk`, the holder's current `customer_sk`, and
`weighting_factor`, computed as `ownership_pct / 100` cast to
`DECIMAL(9,4)`. DuckDB's `/` promotes a `DECIMAL` divided by an integer
literal to `DOUBLE` -- confirmed by running it (`SELECT typeof(CAST(50 AS
DECIMAL(9,4)) / 100)` returns `DOUBLE`) -- so the expression casts the
division back to `DECIMAL(9,4)` explicitly. Left as `DOUBLE`, summing
`balance_usd * weighting_factor` over thousands of rows would drift from the
exact total by float rounding, not by the bug this technique is about.

`naive.sql` sums `fact_account_daily_balance.balance_usd` through the bridge
per customer, then totals across customers, with no weight. `correct.sql`
sums `balance_usd * weighting_factor` directly. Every account's holder shares
add to 100% (single-holder accounts are 100%, joint accounts split 50/50 or
40/30/30 in this seed), so multiplying by the weight before summing turns
each holder's row back into that holder's slice of one account balance,
instead of a second copy of the whole thing.

## The number

`kimball-lab seed --scale 10 --seed 42`. 220 of 3,407 accounts (6.5%) have
more than one holder.

| figure | naive (unweighted) | correct (weighted) | ground truth |
|---|---:|---:|---:|
| month_end_balance_usd_2025-12 | 145,711,047.75 | 127,927,552.36 | 127,927,552.36 |

The naive total overstates the bank's balance by 17,783,495.39, 13.9% over
the correct figure -- well above the 6.5% share of accounts that are joint,
because the overstatement scales with how many holders each of those
accounts has. A two-holder account's balance is counted twice; a
three-holder account's is counted three times.

## Why

The alternative to a weighted bridge is picking one holder per account and
crediting the whole balance to them, which drops the other holders from
every report that groups by customer, or -- as `naive.sql` shows -- crediting
the balance to all of them, which inflates every total the customer
dimension touches. A bank-wide total sidesteps the bridge and this error by summing
`fact_account_daily_balance` directly, with no customer join; a
segment-level or branch-level breakdown of the same balance cannot, because
it needs the bridge to reach a customer.

## When not to use it

- **When the relationship is one-to-many, not many-to-many.** A single
  primary holder per account needs no bridge; a foreign key on the fact
  reaches the customer directly, the way `fact_transaction.customer_sk` does.
- **When the weight is not exact.** Kimball's other option is to report an
  unweighted "impact" count (this fact touches N customers) alongside a
  separate, correctly-weighted allocation. Mixing the two into one number, as
  `naive.sql` does, is the error this technique corrects.
- **When ownership changes over time.** `bridge_account_holder` here is type
  1 (one row per account-customer pair, no history), because the seed never
  changes a holder's share after the account arrives. A bank where ownership
  is renegotiated would need the bridge rows themselves dated, closer to a
  type 2 dimension than a plain lookup table.

## Files

- `build.sql`: `bridge_account_holder`, from `hist_account_holders`
- `naive.sql`, `correct.sql`: the two queries above
