-- Source history: extracts the warehouse keeps as delivered, batch by batch.
--
-- Staging is replaced every batch. These three sources feed structures built
-- after the load (the bridge, the accumulating snapshot, the coverage fact), so
-- their full history is kept here, stamped with the batch that brought each row.
-- FX rates are reference data every later batch may need, so they are kept too.

CREATE TABLE IF NOT EXISTS hist_account_holders (
    account_id VARCHAR NOT NULL, customer_id VARCHAR NOT NULL, holder_role VARCHAR NOT NULL,
    ownership_pct INTEGER NOT NULL, etl_batch_id VARCHAR NOT NULL);
INSERT INTO hist_account_holders SELECT *, getvariable('batch_id') FROM stg_account_holders;

CREATE TABLE IF NOT EXISTS hist_loan_events (
    application_id VARCHAR NOT NULL, customer_id VARCHAR NOT NULL, branch_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL, event_date DATE NOT NULL, etl_batch_id VARCHAR NOT NULL);
INSERT INTO hist_loan_events SELECT *, getvariable('batch_id') FROM stg_loan_events;

CREATE TABLE IF NOT EXISTS hist_promotions (
    branch_id VARCHAR NOT NULL, product_code VARCHAR NOT NULL, promo_month VARCHAR NOT NULL,
    etl_batch_id VARCHAR NOT NULL);
INSERT INTO hist_promotions SELECT *, getvariable('batch_id') FROM stg_promotions;

CREATE TABLE IF NOT EXISTS fx_rate (
    currency_code VARCHAR NOT NULL, rate_date DATE NOT NULL,
    usd_per_unit DECIMAL(12,6) NOT NULL, etl_batch_id VARCHAR NOT NULL);
INSERT INTO fx_rate SELECT *, getvariable('batch_id') FROM stg_fx_rates;
