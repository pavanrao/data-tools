-- dim_txn_profile: a junk dimension for four low-cardinality flag columns.
--
-- channel, is_reversal, is_international and is_contactless describe every
-- transaction but correlate with nothing else on the fact and would each add
-- a join if left as separate columns. A junk dimension moves them into one
-- surrogate key. Its rows are the combinations that occur in
-- fact_transaction, found with DISTINCT, not the full cross product of the
-- four domains: a reversal is never international in this data, a system
-- transaction is never contactless, and so on, so most of the 48 possible
-- combinations never happen.
--
-- fact_transaction_profile carries the degenerate dimension key (txn_id) and
-- the profile_sk it maps to, standing in for a fact table rebuilt on
-- profile_sk instead of the four flag columns.

CREATE OR REPLACE TABLE dim_txn_profile AS
SELECT
    row_number() OVER (ORDER BY channel, is_reversal, is_international, is_contactless)
        AS profile_sk,
    channel, is_reversal, is_international, is_contactless
FROM (SELECT DISTINCT channel, is_reversal, is_international, is_contactless
      FROM fact_transaction) observed;

CREATE OR REPLACE TABLE fact_transaction_profile AS
SELECT f.txn_id, p.profile_sk
FROM fact_transaction f
JOIN dim_txn_profile p
  ON p.channel IS NOT DISTINCT FROM f.channel
 AND p.is_reversal IS NOT DISTINCT FROM f.is_reversal
 AND p.is_international IS NOT DISTINCT FROM f.is_international
 AND p.is_contactless IS NOT DISTINCT FROM f.is_contactless;
