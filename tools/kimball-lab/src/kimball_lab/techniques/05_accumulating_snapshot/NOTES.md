# 05 · Accumulating snapshots: the loan pipeline

**Question:** how many loan applications are still in underwriting as of
2026-06-30, how many have funded, and how long does funding take on average?

## What it is

An accumulating snapshot fact tracks something that moves through a fixed,
known sequence of milestones toward completion: an application, an order, a
shipment. Unlike a transaction fact, whose rows are never revisited once
written, or a periodic snapshot, which adds a new row every period, an
accumulating snapshot has one row per pipeline instance, and that row is
updated in place every time the instance reaches a new milestone. The columns
are the milestones: one date key per stage, filled in left to right as they
happen, `NULL` for a stage not yet reached.

## How it works here

`build.sql` builds `fact_loan_application` from `hist_loan_events`, which
keeps every loan event ever delivered across all 18 batches. For each
`application_id` it takes the first occurrence of each milestone
(`applied`, `approved`, `declined`, `funded`, `first_payment`), stores its
date key, computes the lag between milestones, and derives `current_status`
as the furthest milestone reached.

Two complications are planted in the event feed on purpose. First, about one
application in six carries a second `applied` event -- the applicant
resubmits documents -- so the milestone date has to be the *first*
occurrence, not just any row where `event_type = 'applied'`. Second, a
customer who is declined can reapply; that reapplication gets a brand new
`application_id`, so it is a second row in this fact, not a change to the
first one.

At `kimball-lab seed --scale 10 --seed 42`, 131 applications exist. 21 of them
have a duplicate `applied` event. Their status splits: 9 `applied` (still in
underwriting), 10 `approved` (awaiting funding), 29 `declined`, 8 `funded`
(awaiting the first payment), 75 `first_payment` (funded and past the first
payment). "Funded" in the ground truth means *ever reached funded* --
`funded_date_key IS NOT NULL` -- so it is 8 + 75 = 83, not just the 8 rows
still sitting at that exact status.

## The number

`kimball-lab seed --scale 10 --seed 42`, then `kimball-lab load` and
`kimball-lab demo 05`. 131 applications exist at this scale.

| figure | naive | correct | ground truth |
|---|---:|---:|---:|
| in_underwriting_2026-06-30 | 10 | 9 | 9 |
| funded | 8 | 83 | 83 |
| avg_days_applied_to_funded | 18.48 | 19.31 | 19.31 |

## Why

The naive query does not build the accumulating snapshot at all. It asks,
per application, "what does the most recent event row say," the way a
dashboard wired straight to the event feed would, and treats that event's
type as the current status.

That undercounts `funded` by 90.4% (8 of 83) for a structural reason: every
funded application gets a `first_payment` event 30 days later, so by the time
anyone asks, the most recent row is `first_payment` for 75 of the 83 loans
that funded, and only `funded` for the other 8 -- those still inside the
30-day window before their own `first_payment` event lands. The
milestone-column design in `fact_loan_application` does not have this
problem, because reaching `first_payment` does not erase the
`funded_date_key` that was already filled in.

`in_underwriting_2026-06-30` overcounts by one for the opposite reason: events
do not always arrive in milestone order. One application's resubmitted
`applied` event is dated *after* its decision, so the most recent row for
that already-decided application is an `applied` row, and the naive query
misreads it as still pending.

`avg_days_applied_to_funded` understates by 4.3% because the naive join pairs
every `applied` event with an application's `funded` event, and 12 of the 83
funded applications have two `applied` rows. Each of those 12 contributes two
day-counts to the average instead of one -- the true first application and
the shorter gap from its later resubmission -- pulling the naive average down.

## When not to use it

- **The stages are not fixed or not few.** Columns are milestones here. A
  process with an open-ended or highly variable number of steps does not fit
  a handful of date-key columns; a bridge or a separate event-history fact
  suits it better.
- **"Current state" can be read safely off the latest event.** That
  assumption only holds when events are guaranteed to arrive in the order
  they happened. This lab plants a counterexample -- a resubmission dated
  after its own decision -- specifically because that guarantee does not
  always hold in a real feed.
- **The snapshot needs to be as of a past date.** This fact answers "where
  does every application stand right now." Answering "how many were in
  underwriting as of 2026-03-31" means comparing the milestone dates to that
  date directly; `current_status` only ever holds today's answer.

## Files

- `build.sql`: the accumulating snapshot build
- `naive.sql`, `correct.sql`: the two queries above
