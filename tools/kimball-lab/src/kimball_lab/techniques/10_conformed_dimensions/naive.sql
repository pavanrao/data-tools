-- Naive: join the two facts to each other, on account, and aggregate.
--
-- fact_transaction and fact_account_daily_balance share no grain: one is a
-- transaction, the other an account-day. Joining them directly on account_sk
-- pairs every December transaction with every December daily-balance row for
-- that account -- up to 31 of them -- so both the transaction count and the
-- balance sum are multiplied by however many days happen to survive the join,
-- not by anything the question asked for.

SELECT 'txn_count_2025-12|' || branch_id AS key, count(*) AS value
FROM (
    SELECT a.branch_id
    FROM fact_transaction f
    JOIN dim_date td ON td.date_key = f.trade_date_key
    JOIN fact_account_daily_balance fb ON fb.account_sk = f.account_sk
    JOIN dim_date bd ON bd.date_key = fb.date_key
    JOIN dim_account a ON a.account_sk = f.account_sk
    WHERE td.year_month = '2025-12' AND bd.year_month = '2025-12'
) joined
GROUP BY branch_id
UNION ALL
SELECT 'month_end_balance_usd_2025-12|' || branch_id AS key, round(sum(balance_usd), 2) AS value
FROM (
    SELECT a.branch_id, fb.balance_usd
    FROM fact_transaction f
    JOIN dim_date td ON td.date_key = f.trade_date_key
    JOIN fact_account_daily_balance fb ON fb.account_sk = f.account_sk
    JOIN dim_date bd ON bd.date_key = fb.date_key
    JOIN dim_account a ON a.account_sk = f.account_sk
    WHERE td.year_month = '2025-12' AND bd.year_month = '2025-12'
) joined
GROUP BY branch_id
ORDER BY key;
