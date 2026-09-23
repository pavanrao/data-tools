-- Naive: segment by the customer's row as it stands today.
--
-- This is what a type 1 dimension gives you, because type 1 overwrites: the
-- only segment it holds is the current one. The fact's surrogate key is used
-- only to find the customer, and the join then jumps to the current row.
-- A customer who moved from mass to affluent in November has all of 2025's
-- fees reported as affluent.

SELECT 'fee_revenue_usd_2025|' || cur.segment AS key,
       round(sum(-f.amount_usd), 2) AS value
FROM fact_transaction f
JOIN dim_customer ver ON ver.customer_sk = f.customer_sk
JOIN dim_customer cur ON cur.customer_id = ver.customer_id AND cur.is_current
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.calendar_year = 2025
GROUP BY cur.segment
ORDER BY key;
