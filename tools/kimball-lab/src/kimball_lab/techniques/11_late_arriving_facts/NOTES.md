# 11 · Late-arriving facts and inferred members

**Question:** how many facts arrived after their posting month, and how many
were loaded against an account the warehouse hadn't been told about yet?

## What it is

A fact arrives **late** when the batch that loads it is not the batch of the
period it belongs to -- a transaction posted in March, loaded in May. A fact
refers to an **inferred member** when it names a dimension row the warehouse
has never seen: an account that transacts before its own `accounts.csv` row
has arrived. Kimball's answer to the second problem is to create a
placeholder dimension row on the spot (an inferred member) rather than drop
the fact or block the load, and to overwrite the placeholder in place once
the real row shows up. Getting this wrong -- inner-joining facts to known
dimension rows, or dropping anything the load doesn't recognize -- loses the
facts that arrived in the least ordinary way, with no error to flag it.

## How it works here

`core/40_fact_transaction.sql` inserts a placeholder into `dim_account` for
any `account_id` in staged transactions that `dim_account` doesn't already
have, flagged `is_inferred = true` and stamped `inferred_in_batch`.
`core/30_dim_account.sql` overwrites that placeholder in place when the real
account record arrives, flips `is_inferred` to false, and stamps
`resolved_in_batch` -- the surrogate key never changes, so facts already
loaded against the placeholder stay valid without a re-key. Both stamps
persist after resolution, which is what lets a query ask, after the fact,
which rows were ever inferred.

`correct.sql` reads those stamps directly: a fact is late if `etl_batch_id`
is later than its posting month, and a fact is against an inferred member if
it loaded (`etl_batch_id`) before its account's `resolved_in_batch`.
`naive.sql` makes two plausible mistakes instead: it judges lateness by trade
month rather than posting month, and it finds inferred-member facts by
filtering on `dim_account.is_inferred` as it stands today -- which is false
for every account, because every inferred account in this warehouse has
since been resolved. That second mistake is what an inner join at load time
would have produced: zero, because the join would have dropped these facts
rather than keeping them under a placeholder.

## The number

`kimball-lab seed --scale 10 --seed 42`. Late facts and inferred-member facts
sit far apart in scale: 5,766 of the former, 115 of the latter.

| figure | naive | correct | ground truth |
|---|---:|---:|---:|
| late_facts | 13,296 | 5,766 | 5,766 |
| inferred_member_facts | 0 | 115 | 115 |
| inferred_member_amount_usd | 0.00 | 24,745.02 | 24,745.02 |

The naive late-fact count is 2.31 times the correct one (13,296 against
5,766) -- trade-month and posting-month disagree whenever a transaction's
payment lag crosses a month boundary, which a transaction traded in the
last few days of a month does often enough to more than double the naive
count. The naive inferred-member figures read zero straight across, because
`is_inferred` is a point-in-time flag and this query reads it after every
placeholder has already been resolved.

Five accounts were ever inferred (`A003403`-`A003407`), each opened and
transacting two to five months before its own account record arrived. They
carried 22, 22, 22, 27 and 22 facts respectively before resolution -- 115 in
total, summing to $24,745.02.

## Why

`resolved_in_batch` and `inferred_in_batch` exist so the answer to "was this
ever inferred" doesn't depend on when you ask. A flag that only holds the
current state answers a different question -- "is this inferred right now" --
and that question's answer trends toward "no" for every account the longer
the warehouse has run, regardless of how many facts were affected along the
way. Keeping the batch stamps costs two nullable columns that get written
once and never updated again after the placeholder resolves.

**A further case, not in the ground truth above: late fees across a segment
change.** The seed plants six fee transactions whose trade date is the last
day of the month before a customer's segment change, arriving in the same
batch as the change itself. `fact_transaction`'s as-of-trade-date lookup
(technique 02) puts these on the segment the customer held on the trade
date. A query that instead reads the customer's *current* segment (the type 1
mistake) gets these wrong -- the fee moves to whatever segment the customer
changed into, not the one they were in when they paid it. Counted directly
from the warehouse:

```sql
SELECT f.txn_id, a.account_id, ver.segment AS as_of_trade_date_segment,
       cur.segment AS current_segment, pd.full_date AS trade_date, f.etl_batch_id
FROM fact_transaction f
JOIN dim_account a ON a.account_sk = f.account_sk
JOIN dim_customer ver ON ver.customer_sk = f.customer_sk
JOIN dim_customer cur ON cur.customer_id = ver.customer_id AND cur.is_current
JOIN dim_date pd ON pd.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND f.channel = 'system'
  AND f.etl_batch_id = strftime(cur.valid_from, '%Y-%m')
  AND pd.full_date = date_trunc('month', cur.valid_from) - INTERVAL 1 DAY
  AND ver.segment <> cur.segment
ORDER BY f.txn_id;
```

| txn_id | account | as-of-trade segment | current segment | trade date | loaded |
|---|---|---|---|---|---|
| T00137945 | A001320 | private | affluent | 2025-07-31 | 2025-08 |
| T00205413 | A001152 | affluent | private | 2025-10-31 | 2025-11 |
| T00277387 | A000714 | mass | private | 2026-01-31 | 2026-02 |
| T00302193 | A000210 | mass | affluent | 2026-02-28 | 2026-03 |
| T00330555 | A003013 | mass | affluent | 2026-03-31 | 2026-04 |
| T00355291 | A001118 | mass | affluent | 2026-04-30 | 2026-05 |
| T00356792 | A002920 | affluent | mass | 2026-04-30 | 2026-05 |

Seven rows turn up, one more than the six the seed deliberately plants. Six
of these customers (`C00108`, `C00569`, `C01596`, `C01677`, `C00353`,
`C00552`) are the planted cases. The seventh, `T00137945` on account
`A001320`, belongs to `C00654`: a segment-changer the seed did not target
for this plant, whose July month-end fee was delayed by the general "one
fact in seventy" random feed-delay mechanism into landing, by chance, in the
same batch as its own segment change. The query and the seed are both doing
what they were built to do; the same failure mode simply happened twice,
once by design and once by coincidence. `manifest.json` records the planted
count, 6; the warehouse, queried directly, holds 7.

## When not to use it

- **A dimension row that will never resolve doesn't need this.** If a fact
  can reference nothing at all (a free-text field with no matching
  reference table, say), a fixed "unknown member" row like `dim_customer`'s
  `customer_sk = 0` is enough; there is nothing to wait for and nothing to
  re-key.
- **Don't infer members for data you can reject instead.** Inferred members
  are for facts you must keep now and can correct later. A load that can
  reject and replay bad rows on a retry path is simpler without this
  machinery.
- **Lateness by posting period is not always the right definition.** Some
  questions want "as originally reported" as the answer (technique 13); this
  technique's `late_facts` counts rows against the period they now belong to,
  not the period they were first booked under.

## Files

- `core/30_dim_account.sql`: inferred members, `inferred_in_batch`,
  `resolved_in_batch`
- `core/40_fact_transaction.sql`: where the placeholder row is created
- `correct.sql`, `naive.sql`: the two queries above
