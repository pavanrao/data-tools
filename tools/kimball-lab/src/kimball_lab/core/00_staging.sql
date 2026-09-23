-- Staging: this batch's extracts, typed on the way in.
--
-- Staging tables are TEMP, so they live in the session and never become part of
-- the warehouse or of a DuckLake snapshot. The column lists are the extract
-- contract written down in seed.py; a file that does not match fails here,
-- before anything downstream reads it.

CREATE OR REPLACE TEMP TABLE stg_branches AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/branches.csv', header = true, hive_partitioning = false,
    columns = {'branch_id': 'VARCHAR', 'branch_name': 'VARCHAR', 'city': 'VARCHAR',
               'region': 'VARCHAR'});

CREATE OR REPLACE TEMP TABLE stg_products AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/products.csv', header = true, hive_partitioning = false,
    columns = {'product_code': 'VARCHAR', 'product_name': 'VARCHAR',
               'product_category': 'VARCHAR'});

CREATE OR REPLACE TEMP TABLE stg_customers AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/customers.csv', header = true, hive_partitioning = false,
    columns = {'customer_id': 'VARCHAR', 'full_name': 'VARCHAR', 'segment': 'VARCHAR',
               'home_branch_id': 'VARCHAR', 'city': 'VARCHAR', 'customer_since': 'DATE',
               'effective_date': 'DATE'});

CREATE OR REPLACE TEMP TABLE stg_accounts AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/accounts.csv', header = true, hive_partitioning = false,
    columns = {'account_id': 'VARCHAR', 'product_code': 'VARCHAR', 'currency_code': 'VARCHAR',
               'branch_id': 'VARCHAR', 'primary_customer_id': 'VARCHAR', 'open_date': 'DATE',
               'opening_balance': 'DECIMAL(18,2)', 'monthly_fee': 'DECIMAL(18,2)'});

CREATE OR REPLACE TEMP TABLE stg_account_holders AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/account_holders.csv', header = true, hive_partitioning = false,
    columns = {'account_id': 'VARCHAR', 'customer_id': 'VARCHAR', 'holder_role': 'VARCHAR',
               'ownership_pct': 'INTEGER'});

CREATE OR REPLACE TEMP TABLE stg_transactions AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/transactions.csv', header = true, hive_partitioning = false,
    columns = {'txn_id': 'VARCHAR', 'account_id': 'VARCHAR', 'trade_date': 'DATE',
               'posting_date': 'DATE', 'txn_type': 'VARCHAR', 'channel': 'VARCHAR',
               'is_reversal': 'BOOLEAN', 'is_international': 'BOOLEAN',
               'is_contactless': 'BOOLEAN', 'currency_code': 'VARCHAR',
               'amount': 'DECIMAL(18,2)'});

CREATE OR REPLACE TEMP TABLE stg_fx_rates AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/fx_rates.csv', header = true, hive_partitioning = false,
    columns = {'currency_code': 'VARCHAR', 'rate_date': 'DATE',
               'usd_per_unit': 'DECIMAL(12,6)'});

CREATE OR REPLACE TEMP TABLE stg_loan_events AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/loan_events.csv', header = true, hive_partitioning = false,
    columns = {'application_id': 'VARCHAR', 'customer_id': 'VARCHAR', 'branch_id': 'VARCHAR',
               'event_type': 'VARCHAR', 'event_date': 'DATE'});

CREATE OR REPLACE TEMP TABLE stg_promotions AS
SELECT * FROM read_csv(getvariable('batch_dir') || '/promotions.csv', header = true, hive_partitioning = false,
    columns = {'branch_id': 'VARCHAR', 'product_code': 'VARCHAR', 'promo_month': 'VARCHAR'});
