-- Naive: add the local-currency amounts together as if they were all one
-- currency.
--
-- A savings account can hold EUR or GBP as well as USD; checking accounts are
-- always USD. Summing amount_local across every account adds euros and pounds
-- to dollars at parity, as if a one-unit deposit were worth the same
-- regardless of currency.

SELECT 'deposits_usd_2025' AS key,
       round(sum(f.amount_local), 2) AS value
FROM fact_transaction f
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'deposit' AND d.calendar_year = 2025;
