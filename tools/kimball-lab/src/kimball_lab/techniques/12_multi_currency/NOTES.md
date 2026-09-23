# 12 · Multi-currency facts

**Question:** what were 2025 deposits across the bank in USD, when a savings
account can hold EUR or GBP as well as USD?

## What it is

A fact whose accounts can be denominated in more than one currency has to
carry both the amount as it moved (local currency) and the amount in
one common currency every report can add up (here, USD), plus the rate that
connects them. A single-currency fact needs none of that: one amount column
is enough, because there is nothing to convert.

## How it works here

Checking accounts are always USD. Savings accounts are opened in USD, EUR or
GBP, drawn 70/20/10 by the generator. `core/40_fact_transaction.sql` stores
`amount_local`, `fx_rate` and `amount_usd` on every row, the rate looked up
for the account's currency on the transaction's own `trade_date` -- the day
the money moved. `core/50_fact_account_daily_balance.sql` does the
same for balances, `balance_local` and `balance_usd`, but the rate it looks up
is that day's rate for whichever day the snapshot row is.

The two use the same mechanism -- multiply by that day's rate -- for different
reasons. A transaction is a completed, historical event: it traded at one
rate, on one day, and `amount_usd` is fixed from then on. A balance is a level
that is re-reported every day it is snapshotted; its USD value moves with the
exchange rate even on a day with zero transactions, because the euros or
pounds sitting in the account are worth a different number of dollars than
they were yesterday.

At `kimball-lab seed --scale 10 --seed 42`, 999 savings accounts exist: 709
USD, 188 EUR, 102 GBP (29.0% non-USD). Of 26,048 deposit transactions traded
in 2025, 1,748 are EUR and 906 are GBP (10.2% by count, smaller than the
account share because checking, always USD, accounts for 83.0% of 2025
deposit volume in USD terms, 132,971,607.56 of 160,142,635.04).

## The number

`kimball-lab seed --scale 10 --seed 42`, then `kimball-lab load` and
`kimball-lab demo 12`. 999 savings accounts exist across the three currencies.

| figure | naive | correct | ground truth |
|---|---:|---:|---:|
| deposits_usd_2025 | 159,000,970.16 | 160,142,635.04 | 160,142,635.04 |

## Why

The naive query sums `amount_local` directly, adding euros and pounds to
dollars as if one unit of each were worth the same. It understates the true
figure by 0.71% (1,141,664.88 of 160,142,635.04), because both EUR and GBP
trade above parity to the dollar throughout 2025 (EUR 1.070021-1.098569, GBP
1.238917-1.283629 USD per unit): a euro or a pound was worth more than a
dollar on every day of the year, so dropping the rate discards that premium
on every non-USD deposit. The error stays under 1% here because only 10.2% of
2025 deposit transactions are non-USD, and neither rate strays far from 1.

## When not to use it

- **Every account is in one currency.** Carrying `amount_local`, `fx_rate`
  and `amount_usd` on a fact where they would always be identical and 1.0
  triples the columns for nothing. Add the currency columns when the fact
  needs them.
- **The question wants today's rate applied to historical flows**, the way a
  mark-to-market report would. `amount_usd` is fixed at the trade-date rate on
  purpose, so a completed deposit's reported value does not move after the
  fact; revaluing history at a later rate takes a fresh join to `fx_rate`
  keyed on the report date instead.

## Files

- `core/40_fact_transaction.sql`, `core/50_fact_account_daily_balance.sql`:
  where local, rate and USD are stored, and why each is converted when it is
- `naive.sql`, `correct.sql`: the two queries above
