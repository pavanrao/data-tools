-- Correct: each question gets the time axis it is about.
--
--   as_reported   what the warehouse said when December closed. That is a
--                 question about when the warehouse knew something, and only
--                 the snapshot taken after batch 2025-12 still holds it.
--   as_effective  what was true in Q4, including what the warehouse learned
--                 later: the facts that arrived late and the segment correction
--                 delivered in batch 2026-03 with effect from 2025-09-01. That is
--                 a question about when something was true, which the SCD2
--                 intervals answer.
--
-- AT (VERSION => ...) takes no subquery, so the snapshot id goes through a
-- variable.

SET VARIABLE close_snapshot = (
    SELECT snapshot_id FROM etl_batch_log WHERE batch_id = '2025-12');

SELECT 'as_reported|' || c.segment AS key, round(sum(-f.amount_usd), 2) AS value
FROM fact_transaction f AT (VERSION => getvariable('close_snapshot'))
JOIN dim_customer c AT (VERSION => getvariable('close_snapshot'))
  ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.full_date BETWEEN DATE '2025-10-01' AND DATE '2025-12-31'
GROUP BY c.segment

UNION ALL

SELECT 'as_effective|' || c.segment, round(sum(-f.amount_usd), 2)
FROM fact_transaction f
JOIN dim_customer c ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.full_date BETWEEN DATE '2025-10-01' AND DATE '2025-12-31'
GROUP BY c.segment
ORDER BY key;
