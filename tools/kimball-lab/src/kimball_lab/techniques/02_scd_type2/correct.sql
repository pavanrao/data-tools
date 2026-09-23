-- Correct: join on the surrogate key and stop there.
--
-- Under type 2 the key the fact carries already identifies the version of the
-- customer that was current on the trade date, because the load looked it up
-- against the valid_from / valid_to intervals. No date logic is needed at query
-- time. That is the point of the surrogate key.

SELECT 'fee_revenue_usd_2025|' || c.segment AS key,
       round(sum(-f.amount_usd), 2) AS value
FROM fact_transaction f
JOIN dim_customer c ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.calendar_year = 2025
GROUP BY c.segment
ORDER BY key;
