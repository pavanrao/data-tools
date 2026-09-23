-- Correct: sum through the bridge with the weighting factor applied.
--
-- Every account's holders own shares that add to 100%, so weighting_factor
-- turns "once per holder" back into "once per account, split among holders".
-- The weighted sum equals the sum of account balances directly -- the bridge
-- changes nothing about the total, which is the point of carrying a weight.

SELECT 'month_end_balance_usd_2025-12' AS key,
       round(sum(b.balance_usd * br.weighting_factor), 2) AS value
FROM fact_account_daily_balance b
JOIN bridge_account_holder br ON br.account_sk = b.account_sk
WHERE b.date_key = 20251231;
