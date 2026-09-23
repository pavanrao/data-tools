-- Correct: dim_trade_date, joined through trade_date_key. The role-prefixed
-- view makes it impossible to write this join against the wrong key by
-- accident -- there is no trade_date_key column on dim_posting_date.

SELECT 'txn_count_2025-12' AS key, count(*) AS value
FROM fact_transaction f
JOIN dim_trade_date d ON d.trade_date_key = f.trade_date_key
WHERE d.trade_year_month = '2025-12';
