# kimball-lab

A runnable Kimball reference. A seeded retail bank arrives as eighteen monthly
extracts, plain-SQL ETL loads it into a star schema on DuckLake, and each of
thirteen dimensional-modelling techniques is shown as two queries: the one
people write without the technique, and the one that uses it. Next to both is
the answer the seed computed in Python, so every technique ends in the number
it fixes.

Idea [#220](../../IDEAS.md). Design and decisions: [`docs/015`](../../docs/015_kimball-lab.md).

```bash
make demo-kimball          # seed, load, and show all thirteen, ~15 s
```

## The ready reckoner

Seed 42, scale 10: 2,005 customers, 3,407 accounts, 410,779 transactions over
January 2025 to June 2026. Each row links to that technique's notes: what it is,
how this warehouse implements it, why, and when not to use it.

| # | Technique | The question | Naive | Correct |
|---|---|---|---:|---:|
| [01](src/kimball_lab/techniques/01_declare_the_grain/NOTES.md) | Declare the grain | 2025 checking-plan fees | 981,909.00 | 88,288.00 |
| [02](src/kimball_lab/techniques/02_scd_type2/NOTES.md) | SCD type 1 vs type 2 | 2025 fee revenue, affluent, as segmented when paid | 36,342.00 | 32,860.00 |
| [03](src/kimball_lab/techniques/03_scd_type6/NOTES.md) | SCD type 6 (1+2+3) | the same, by today's segment | 32,860.00 | 36,342.00 |
| [04](src/kimball_lab/techniques/04_periodic_snapshot/NOTES.md) | Periodic snapshot, semi-additive | bank balance at 2025-12-31 | 3,690,929,059.49 | 127,927,552.36 |
| [05](src/kimball_lab/techniques/05_accumulating_snapshot/NOTES.md) | Accumulating snapshot | loans funded | 8 | 83 |
| [06](src/kimball_lab/techniques/06_factless_fact/NOTES.md) | Factless fact (coverage) | promotions that opened no account | 0 | 16 |
| [07](src/kimball_lab/techniques/07_bridge_weighting/NOTES.md) | Bridge with weighting factor | bank balance at 2025-12-31, through account holders | 145,711,047.75 | 127,927,552.36 |
| [08](src/kimball_lab/techniques/08_junk_dimension/NOTES.md) | Junk dimension | transaction flag combinations that occur | 48 | 14 |
| [09](src/kimball_lab/techniques/09_role_playing_date/NOTES.md) | Role-playing date | transactions traded in December 2025 | 24,202 | 24,199 |
| [10](src/kimball_lab/techniques/10_conformed_dimensions/NOTES.md) | Conformed dimensions, drill-across | December transactions, branch B01 | 118,830 | 3,860 |
| [11](src/kimball_lab/techniques/11_late_arriving_facts/NOTES.md) | Late-arriving facts, inferred members | facts loaded before their account existed | 0 | 115 |
| [12](src/kimball_lab/techniques/12_multi_currency/NOTES.md) | Multi-currency facts | 2025 deposits in USD | 159,000,970.16 | 160,142,635.04 |
| [13](src/kimball_lab/techniques/13_time_travel_vs_scd2/NOTES.md) | DuckLake time travel vs SCD2 | Q4 2025 affluent fees, as reported at close | 9,774.00 | 9,563.00 |

Most techniques report more than one figure; the table shows one each, and
`kimball-lab demo NN` shows the rest. The correct column equals the seed's
ground truth in every row, on both engines; `tests/test_techniques.py` checks
it.

Each naive query is one a competent analyst could plausibly write, and each
technique's notes say why. The size of the error varies a lot. Technique 09's is three transactions in
24,199, because trades crossing into the next month nearly cancel those
crossing in, and the notes say so. Technique 04's is a factor of 29.

## How it runs

```bash
kimball-lab seed --out bank                    # 18 batch=YYYY-MM/ directories, ground_truth.json
kimball-lab load bank --db lake/lab.ducklake   # core SQL per batch, then each technique's build.sql
kimball-lab demo --db lake/lab.ducklake        # naive, correct and truth, per technique
kimball-lab demo 04 --db lake/lab.ducklake --json
kimball-lab list
```

- **The seed** (`seed.py`) writes CSV extracts shaped like an OLTP change feed:
  customers and their segment changes, accounts and joint holders, transactions
  in USD, EUR and GBP, daily FX rates, loan events and branch promotions. The
  cases each technique needs are planted and listed in `manifest.json`: segment
  changes, a backdated correction, late facts, accounts that transact before
  they are delivered.
- **The load** (`runner.py` running `core/*.sql`) handles one batch per
  transaction. With DuckLake that means one snapshot per batch. It reconciles
  staged against loaded transactions, and writes a batch marker inside the same
  transaction, so a re-run skips what is already loaded.
- **The core model**: `dim_date`, `dim_customer` (type 2), `dim_account` (type
  1, with inferred members), `dim_branch`, `dim_product`, `fact_transaction`
  (one posted transaction) and `fact_account_daily_balance` (one account-day).
- **A technique** is a directory with `naive.sql`, `correct.sql`, an optional
  `build.sql` and `NOTES.md`. Each query returns `key, value` rows. The test
  suite finds new techniques on its own.

`--engine duckdb` runs everything on a plain DuckDB file with no extension;
technique 13 is then skipped, with the reason printed.

## Install

```bash
# just this tool
uvx --from "git+https://github.com/pavanrao/data-tools#subdirectory=tools/kimball-lab" \
    kimball-lab list

# in the workspace
make sync && uv run kimball-lab list
```

`duckdb` is pinned to 1.5.5. The `ducklake` extension downloads on first
use (DuckLake 1.0). No model is used anywhere.

## Prior art

The Kimball Group's [Dimensional Modeling
Techniques](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
page is the canonical list, in prose. The runnable examples found on 2026-09-23
([dbt-dimensional-modelling](https://github.com/Data-Engineer-Camp/dbt-dimensional-modelling)
is the most used) cover the basics on AdventureWorks. The closest in scope, a
Snowflake-only portfolio repo, lists most of the techniques here with some
financial-services examples. None of them runs locally on seeded data and shows
a technique through the wrong number it prevents.
