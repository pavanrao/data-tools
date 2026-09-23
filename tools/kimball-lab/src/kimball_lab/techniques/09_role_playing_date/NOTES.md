# 09 · Role-playing dimension: trade date vs. posting date

**Question:** how many transactions traded in December 2025?

## What it is

A role-playing dimension is one physical dimension, `dim_date`, that a fact
references more than once, in different roles. `fact_transaction` carries
both `trade_date_key` (when the transaction happened) and `posting_date_key`
(when it landed in the ledger); `seed.py`'s transaction generator adds a
posting lag to card purchases of zero to three days. Joining both keys to
the same unaliased `dim_date` needs a fresh alias and a column-collision
workaround in every query that does it; role-played views give each key its
own dimension, with its own column names, so there is nothing to alias.

## How it works here

`build.sql` creates two views over `dim_date`, `dim_trade_date` and
`dim_posting_date`, each renaming every column with its role's prefix:
`trade_date_key`, `trade_year_month`, `trade_is_month_end`, and so on, or the
same set under `posting_`. Neither view adds or changes data; both read the
same underlying `dim_date` row for a given `date_key`.

`naive.sql` joins `fact_transaction` to plain `dim_date` on
`posting_date_key` and filters `year_month = '2025-12'`. The question as
asked ("how many transactions traded in December 2025") names the trade
date, but nothing forces a query written from that question to use it:
`dim_date` gives no signal that the wrong key was used, because it has one
`year_month` column, correct for whichever key was joined to it.

`correct.sql` uses `dim_trade_date` and `trade_date_key` instead, filtering
`trade_year_month = '2025-12'`. Because `dim_trade_date` has no column named
`posting_date_key`, and `dim_posting_date` has none named `trade_date_key`,
writing the naive join against either role-played view raises a binder error
at query time, surfacing the mistake before the report ships rather than
after someone checks the count against another source.

## The number

`kimball-lab seed --scale 10 --seed 42`. The mismatch below is not a planted
case; it comes from the ordinary posting lag every card purchase gets.

| figure | naive (via posting_date_key) | correct (via trade_date_key) | ground truth |
|---|---:|---:|---:|
| txn_count_2025-12 | 24,202 | 24,199 | 24,199 |

The naive count is off by 3, net, small next to 24,199 because two
mismatches run in opposite directions and mostly cancel. Querying the loaded
warehouse directly: 486 transactions traded in December 2025 but posted
outside it (mostly card purchases from late December that post in January),
missing from the naive count; 489 transactions posted in December but traded
outside it (mostly from late November), wrongly included. 489 minus 486 is 3,
the naive count's overstatement. A report asking about a narrower window than
a full month -- the last three days of December, say -- would see a much
larger fraction of its transactions on the wrong side of the naive join,
because that window is where the posting lag moves transactions across the
month boundary.

## Why

A fact with two roles for the same dimension needs the technique whenever a
report can be asked against either role, because "traded in December" and
"posted in December" are different sets of transactions -- the breakdown
above puts the overlap at 23,713 and the disagreement at 975 (486 + 489).
Renaming the columns per role, rather than aliasing the table at query time,
moves the choice of which role means what out of every query and into the
dimension's own column names.

## When not to use it

- **When only one date role is ever queried.** If nothing downstream cares
  when a transaction posted, `dim_posting_date` need not exist; a
  role-played view is worth building only for a role that gets used.
- **When the two roles' calendars differ.** This lab plays one `dim_date`
  twice because trade and posting share the same calendar (both are ordinary
  dates). A fiscal calendar that applies to one role and not the other would
  need two different underlying date tables, not two views over one.
- **When the join key, not the date, is what varies.** A shipped-date and a
  delivered-date on an order fact are the same kind of role-playing; a
  customer's billing address and shipping address, both foreign keys into
  one address dimension, are the identical pattern on a non-date dimension.

## Files

- `build.sql`: `dim_trade_date`, `dim_posting_date`
- `naive.sql`, `correct.sql`: the two queries above
