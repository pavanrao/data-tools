-- Naive: join the account's monthly fee onto every transaction and sum.
--
-- fact_transaction's grain is one posted transaction. monthly_fee is an
-- attribute of the account, not the transaction, so the join copies it onto
-- every row of that account: an account with fourteen transactions in a month
-- gets its fee counted fourteen times that month, not once. The fan-out is
-- silent -- the query reads like a normal join-and-sum, and the mistake is in
-- the grain, not the syntax.

SELECT 'plan_fee_usd_2025' AS key, round(sum(a.monthly_fee), 2) AS value
FROM fact_transaction f
JOIN dim_account a ON a.account_sk = f.account_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE a.product_code = 'CHK' AND d.calendar_year = 2025;
