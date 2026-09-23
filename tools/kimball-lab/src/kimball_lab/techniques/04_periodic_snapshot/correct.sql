-- Correct: sum across accounts, never across days.
--
-- A balance is semi-additive: it adds across accounts (many accounts make a
-- bank), but a day's balance is not a portion of the month's balance the way a
-- day's transaction amount is a portion of the month's transactions. The
-- month-end figure sums every account's balance on 2025-12-31 alone. The
-- average sums each day's bank-wide total first, then divides by the number of
-- days -- one total per day, not one row per account-day.

WITH daily_totals AS (
    SELECT d.full_date, sum(f.balance_usd) AS total_usd
    FROM fact_account_daily_balance f
    JOIN dim_date d ON d.date_key = f.date_key
    WHERE d.year_month = '2025-12'
    GROUP BY d.full_date
)
SELECT 'month_end_balance_usd_2025-12' AS key,
       round((SELECT total_usd FROM daily_totals WHERE full_date = DATE '2025-12-31'), 2) AS value
UNION ALL
SELECT 'avg_daily_balance_usd_2025-12' AS key,
       round(sum(total_usd) / CAST(count(*) AS DECIMAL(18,0)), 2) AS value
FROM daily_totals
ORDER BY key;
