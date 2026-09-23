-- Correct: drill-across. Aggregate each fact to the conformed dimension
-- (branch) on its own, then join the two aggregates.
--
-- fact_transaction (grain: one posted transaction) and
-- fact_account_daily_balance (grain: one account-day) never join to each
-- other directly here -- there is no shared grain between them, only a shared
-- dimension. branch_id means the same thing in both, assigned from the same
-- dim_branch, so the two totals can sit side by side even though neither
-- fact knows the other exists.

WITH txn_by_branch AS (
    SELECT b.branch_id, count(*) AS n
    FROM fact_transaction f
    JOIN dim_date d ON d.date_key = f.trade_date_key
    JOIN dim_branch b ON b.branch_sk = f.branch_sk
    WHERE d.year_month = '2025-12'
    GROUP BY b.branch_id
),
bal_by_branch AS (
    SELECT b.branch_id, round(sum(fb.balance_usd), 2) AS m
    FROM fact_account_daily_balance fb
    JOIN dim_account a ON a.account_sk = fb.account_sk
    JOIN dim_branch b ON b.branch_id = a.branch_id
    WHERE fb.date_key = 20251231
    GROUP BY b.branch_id
)
SELECT 'txn_count_2025-12|' || branch_id AS key, n AS value
FROM txn_by_branch
UNION ALL
SELECT 'month_end_balance_usd_2025-12|' || branch_id AS key, m AS value
FROM bal_by_branch
ORDER BY key;
