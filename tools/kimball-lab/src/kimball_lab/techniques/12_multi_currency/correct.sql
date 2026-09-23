-- Correct: sum the USD amount fact_transaction already stored, converted at
-- the rate on the day the transaction traded.

SELECT 'deposits_usd_2025' AS key,
       round(sum(f.amount_usd), 2) AS value
FROM fact_transaction f
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'deposit' AND d.calendar_year = 2025;
