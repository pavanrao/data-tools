-- fact_account_month: the grain a plan fee actually belongs to.
--
-- One row per checking account per month it was open at month end, holding
-- the fee charged for that month. Declaring this grain is the whole point of
-- 01: fact_transaction's grain is one posted transaction, and a plan fee is
-- not a transaction -- it is charged once a month whether the account moved
-- money four times that month or forty.

CREATE OR REPLACE TABLE fact_account_month AS
SELECT a.account_sk, d.year_month, a.monthly_fee AS plan_fee_usd
FROM dim_account a
JOIN dim_date d ON d.is_month_end AND d.full_date >= a.open_date
WHERE a.product_code = 'CHK' AND NOT a.is_inferred;
