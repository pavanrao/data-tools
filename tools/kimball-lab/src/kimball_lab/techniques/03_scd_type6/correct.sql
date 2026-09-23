-- Correct: group by current_segment, the type 1 column carried on every
-- version of the customer, instead of segment, the type 2 column that names
-- only the version the fact happened under.

SELECT 'fee_revenue_usd_2025_as_is|' || c.current_segment AS key,
       round(sum(-f.amount_usd), 2) AS value
FROM fact_transaction f
JOIN dim_customer_scd6 c ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.calendar_year = 2025
GROUP BY c.current_segment
ORDER BY key;
