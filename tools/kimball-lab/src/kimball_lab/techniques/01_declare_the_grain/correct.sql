-- Correct: query the account-month grain build.sql declared.
--
-- Each row already is one account's fee for one month, so summing rows sums
-- months. Nothing here can fan out, because the grain the table is built at
-- is the grain the question is asked at.

SELECT 'plan_fee_usd_2025' AS key, round(sum(plan_fee_usd), 2) AS value
FROM fact_account_month
WHERE year_month BETWEEN '2025-01' AND '2025-12';
