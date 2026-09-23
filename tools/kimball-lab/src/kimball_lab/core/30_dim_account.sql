-- dim_account: type 1, with inferred members.
--
-- An account can transact before its account record is delivered. The fact
-- load in 40_ creates a placeholder row for it (is_inferred = true) so the
-- fact is kept, not dropped by an inner join. When the real record arrives, it
-- overwrites the placeholder in place. The surrogate key does not change, so
-- facts already loaded against it stay valid.
--
-- inferred_in_batch and resolved_in_batch record when each happened, so the
-- rows an inner join would have dropped can still be counted afterwards.

CREATE TABLE IF NOT EXISTS dim_account (
    account_sk BIGINT NOT NULL, account_id VARCHAR NOT NULL, product_code VARCHAR NOT NULL,
    currency_code VARCHAR, branch_id VARCHAR, primary_customer_id VARCHAR, open_date DATE,
    opening_balance DECIMAL(18,2), monthly_fee DECIMAL(18,2),
    is_inferred BOOLEAN NOT NULL, inferred_in_batch VARCHAR, resolved_in_batch VARCHAR,
    etl_batch_id VARCHAR NOT NULL);

CREATE OR REPLACE TEMP TABLE batch_resolved_accounts AS
SELECT d.account_id
FROM dim_account d JOIN stg_accounts s USING (account_id)
WHERE d.is_inferred;

MERGE INTO dim_account d USING stg_accounts s ON d.account_id = s.account_id
WHEN MATCHED AND d.is_inferred THEN UPDATE SET
    product_code = s.product_code, currency_code = s.currency_code, branch_id = s.branch_id,
    primary_customer_id = s.primary_customer_id, open_date = s.open_date,
    opening_balance = s.opening_balance, monthly_fee = s.monthly_fee,
    is_inferred = false, resolved_in_batch = getvariable('batch_id'),
    etl_batch_id = getvariable('batch_id');

INSERT INTO dim_account
SELECT (SELECT coalesce(max(account_sk), 0) FROM dim_account)
           + row_number() OVER (ORDER BY s.account_id),
       s.account_id, s.product_code, s.currency_code, s.branch_id, s.primary_customer_id,
       s.open_date, s.opening_balance, s.monthly_fee,
       false, NULL, NULL, getvariable('batch_id')
FROM stg_accounts s
WHERE NOT EXISTS (SELECT 1 FROM dim_account d WHERE d.account_id = s.account_id);
