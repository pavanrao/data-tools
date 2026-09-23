-- fact_transaction: the transaction fact. Grain is one posted transaction.
--
-- Declaring the grain comes first; everything else follows from it. At this
-- grain a transaction amount is additive across every dimension. A measure that
-- belongs to an account-month (a plan fee) or an account-day (a balance) does not
-- belong here -- technique 01 shows what happens when one is added anyway.
--
-- Dimension lookups:
--   customer  as of the trade date, against the SCD2 intervals (not the current
--             row), so a late-arriving fact still gets the segment it was traded in
--   account   by natural key; an unknown account becomes an inferred member first
--   branch, product  through the account
--
-- Both currencies are stored: the local amount the account moved by, and the
-- USD amount at the trade-date rate. The rate is NOT NULL, so a missing rate
-- fails the load instead of dropping the row.

CREATE TABLE IF NOT EXISTS fact_transaction (
    txn_id VARCHAR NOT NULL,                -- degenerate dimension: no attributes of its own
    account_sk BIGINT NOT NULL, customer_sk BIGINT NOT NULL, branch_sk BIGINT NOT NULL,
    product_sk BIGINT NOT NULL,
    trade_date_key INTEGER NOT NULL, posting_date_key INTEGER NOT NULL,
    txn_type VARCHAR NOT NULL, channel VARCHAR NOT NULL, is_reversal BOOLEAN NOT NULL,
    is_international BOOLEAN NOT NULL, is_contactless BOOLEAN NOT NULL,
    currency_code VARCHAR NOT NULL,
    amount_local DECIMAL(18,2) NOT NULL,
    fx_rate DECIMAL(12,6) NOT NULL,
    amount_usd DECIMAL(18,8) NOT NULL,
    etl_batch_id VARCHAR NOT NULL);

-- Inferred members for accounts the warehouse has not been told about yet.
INSERT INTO dim_account
SELECT (SELECT coalesce(max(account_sk), 0) FROM dim_account)
           + row_number() OVER (ORDER BY account_id),
       account_id, 'UNKNOWN', currency_code, NULL, NULL, NULL, NULL, NULL,
       true, getvariable('batch_id'), NULL, getvariable('batch_id')
FROM (SELECT DISTINCT account_id, currency_code FROM stg_transactions t
      WHERE NOT EXISTS (SELECT 1 FROM dim_account d WHERE d.account_id = t.account_id));

INSERT INTO fact_transaction
SELECT
    t.txn_id,
    a.account_sk,
    coalesce(c.customer_sk, 0),
    coalesce(b.branch_sk, 0),
    coalesce(p.product_sk, 0),
    CAST(strftime(t.trade_date, '%Y%m%d') AS INTEGER),
    CAST(strftime(t.posting_date, '%Y%m%d') AS INTEGER),
    t.txn_type, t.channel, t.is_reversal, t.is_international, t.is_contactless,
    t.currency_code,
    t.amount,
    fx.usd_per_unit,
    t.amount * fx.usd_per_unit,
    getvariable('batch_id')
FROM stg_transactions t
JOIN dim_account a ON a.account_id = t.account_id
LEFT JOIN dim_customer c
       ON c.customer_id = a.primary_customer_id
      AND t.trade_date >= c.valid_from AND t.trade_date < c.valid_to
LEFT JOIN dim_branch b ON b.branch_id = a.branch_id
LEFT JOIN dim_product p ON p.product_code = a.product_code
LEFT JOIN fx_rate fx ON fx.currency_code = t.currency_code AND fx.rate_date = t.trade_date;

-- Re-key facts loaded in earlier batches whose correct keys changed in this one:
-- an inferred account that was just resolved, or a customer with a new version
-- that starts on or before the trade date (the backdated correction).
MERGE INTO fact_transaction f
USING (
    SELECT f.txn_id,
           coalesce(c.customer_sk, 0) AS customer_sk,
           coalesce(b.branch_sk, 0)   AS branch_sk,
           coalesce(p.product_sk, 0)  AS product_sk
    FROM fact_transaction f
    JOIN dim_account a ON a.account_sk = f.account_sk
    JOIN dim_date td ON td.date_key = f.trade_date_key
    LEFT JOIN dim_customer c
           ON c.customer_id = a.primary_customer_id
          AND td.full_date >= c.valid_from AND td.full_date < c.valid_to
    LEFT JOIN dim_branch b ON b.branch_id = a.branch_id
    LEFT JOIN dim_product p ON p.product_code = a.product_code
    WHERE f.etl_batch_id < getvariable('batch_id')
      AND (a.account_id IN (SELECT account_id FROM batch_resolved_accounts)
           OR a.primary_customer_id IN (SELECT customer_id FROM batch_changed_customers))
) k ON f.txn_id = k.txn_id
WHEN MATCHED AND (f.customer_sk <> k.customer_sk OR f.branch_sk <> k.branch_sk
                  OR f.product_sk <> k.product_sk)
    THEN UPDATE SET customer_sk = k.customer_sk, branch_sk = k.branch_sk,
                    product_sk = k.product_sk;
