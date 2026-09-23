-- Correct: read the batch stamps the core load already keeps.
--
-- A fact is late if the batch that loaded it (etl_batch_id) is later than
-- the batch its posting month belongs to. A fact is against an inferred
-- member if its account was still a placeholder (dim_account.is_inferred)
-- when the fact loaded -- which core/30_dim_account.sql records permanently
-- in resolved_in_batch, even after the placeholder is overwritten. Both
-- figures come straight from those stamps; no re-derivation needed.

WITH early AS (
    SELECT f.txn_id, f.amount_usd
    FROM fact_transaction f
    JOIN dim_account a ON a.account_sk = f.account_sk
    WHERE a.resolved_in_batch IS NOT NULL AND f.etl_batch_id < a.resolved_in_batch
)
SELECT 'late_facts' AS key,
       (SELECT count(*) FROM fact_transaction f
        JOIN dim_date pd ON pd.date_key = f.posting_date_key
        WHERE f.etl_batch_id > pd.year_month) AS value
UNION ALL
SELECT 'inferred_member_facts' AS key, (SELECT count(*) FROM early) AS value
UNION ALL
SELECT 'inferred_member_amount_usd' AS key,
       (SELECT round(coalesce(sum(amount_usd), 0), 2) FROM early) AS value
ORDER BY key;
