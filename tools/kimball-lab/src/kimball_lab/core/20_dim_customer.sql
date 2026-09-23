-- dim_customer: a type 2 slowly changing dimension.
--
-- A change to a tracked attribute (segment, home branch, city) does not
-- overwrite the row. It closes the current row and opens a new one, each with
-- its own surrogate key, so a fact keeps pointing at the version that was true
-- when it happened. Intervals are half-open: valid_from inclusive, valid_to
-- exclusive, and the open row ends on 9999-12-31.
--
-- Sequence per batch:
--   1. record which customers change, for the fact re-key in 40_
--   2. close the current row of each changed customer at the new effective date
--   3. insert a new current row for every changed or new customer
--
-- A change whose effective date is earlier than the current row's start would
-- need the history split, and this load does not do that. The seed never sends
-- one; the backdated correction in batch 2026-03 is later than the row it
-- closes. docs/015 records the limit.

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk BIGINT NOT NULL, customer_id VARCHAR NOT NULL, full_name VARCHAR,
    segment VARCHAR NOT NULL, home_branch_id VARCHAR, city VARCHAR, customer_since DATE,
    valid_from DATE NOT NULL, valid_to DATE NOT NULL, is_current BOOLEAN NOT NULL,
    etl_batch_id VARCHAR NOT NULL);

-- The unknown member: surrogate key 0, for a fact whose customer is not known yet.
INSERT INTO dim_customer
SELECT 0, 'UNKNOWN', 'Unknown', 'Unknown', NULL, NULL, NULL,
       DATE '1900-01-01', DATE '9999-12-31', true, getvariable('batch_id')
WHERE NOT EXISTS (SELECT 1 FROM dim_customer WHERE customer_sk = 0);

CREATE OR REPLACE TEMP TABLE batch_changed_customers AS
SELECT s.customer_id, s.effective_date
FROM stg_customers s
WHERE NOT EXISTS (
    SELECT 1 FROM dim_customer d
    WHERE d.customer_id = s.customer_id AND d.is_current
      AND d.segment IS NOT DISTINCT FROM s.segment
      AND d.home_branch_id IS NOT DISTINCT FROM s.home_branch_id
      AND d.city IS NOT DISTINCT FROM s.city);

MERGE INTO dim_customer d USING stg_customers s
    ON d.customer_id = s.customer_id AND d.is_current
WHEN MATCHED AND (d.segment IS DISTINCT FROM s.segment
               OR d.home_branch_id IS DISTINCT FROM s.home_branch_id
               OR d.city IS DISTINCT FROM s.city)
    THEN UPDATE SET valid_to = s.effective_date, is_current = false;

INSERT INTO dim_customer
SELECT (SELECT coalesce(max(customer_sk), 0) FROM dim_customer)
           + row_number() OVER (ORDER BY s.customer_id),
       s.customer_id, s.full_name, s.segment, s.home_branch_id, s.city, s.customer_since,
       s.effective_date, DATE '9999-12-31', true, getvariable('batch_id')
FROM stg_customers s
WHERE NOT EXISTS (
    SELECT 1 FROM dim_customer d WHERE d.customer_id = s.customer_id AND d.is_current);
