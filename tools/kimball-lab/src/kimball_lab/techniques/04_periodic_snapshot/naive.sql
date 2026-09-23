-- Naive: treat the semi-additive balance as if it were additive.
--
-- The natural query for "the December total" sums every row it can find. That
-- is right for a transaction amount, which is additive over everything. It is
-- wrong for a balance: summing it across days as well as accounts counts each
-- account's balance once for every day it was open that month, which is not a
-- month-end total or anything else meaningful.
--
-- The average makes the matching mistake in the other direction: it averages
-- over every account-day row instead of over the days. A day with more open
-- accounts, or accounts with larger balances, pulls harder on this average
-- than a day counted once.

SELECT 'month_end_balance_usd_2025-12' AS key,
       round(sum(f.balance_usd), 2) AS value
FROM fact_account_daily_balance f
JOIN dim_date d ON d.date_key = f.date_key
WHERE d.year_month = '2025-12'
UNION ALL
SELECT 'avg_daily_balance_usd_2025-12' AS key,
       round(sum(f.balance_usd) / CAST(count(*) AS DECIMAL(18,0)), 2) AS value
FROM fact_account_daily_balance f
JOIN dim_date d ON d.date_key = f.date_key
WHERE d.year_month = '2025-12'
ORDER BY key;
