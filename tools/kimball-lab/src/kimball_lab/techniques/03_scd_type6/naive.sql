-- Naive: join on the surrogate key and stop there, the way technique 02 says to.
--
-- That answers "as was" -- each fee under the segment the customer held on the
-- trade date. It is the right query for 02's question and the wrong one for
-- this one, which asks for every customer's segment as it stands today.

SELECT 'fee_revenue_usd_2025_as_is|' || c.segment AS key,
       round(sum(-f.amount_usd), 2) AS value
FROM fact_transaction f
JOIN dim_customer c ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.calendar_year = 2025
GROUP BY c.segment
ORDER BY key;
