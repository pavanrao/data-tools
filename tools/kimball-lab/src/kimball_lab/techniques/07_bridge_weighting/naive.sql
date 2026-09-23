-- Naive: sum each customer's accounts through the bridge, then total across
-- customers, without applying the weighting factor.
--
-- A joint account belongs to every one of its holders, so this counts its
-- balance in full for each of them. Two holders means the account's balance
-- is added to the bank total twice.

WITH per_customer AS (
    SELECT br.customer_sk, sum(b.balance_usd) AS balance_usd
    FROM fact_account_daily_balance b
    JOIN bridge_account_holder br ON br.account_sk = b.account_sk
    WHERE b.date_key = 20251231
    GROUP BY br.customer_sk
)
SELECT 'month_end_balance_usd_2025-12' AS key, round(sum(balance_usd), 2) AS value
FROM per_customer;
