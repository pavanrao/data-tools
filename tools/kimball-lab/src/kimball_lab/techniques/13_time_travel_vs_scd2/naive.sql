-- Naive: each tool pointed at the other one's question.
--
--   as_reported   from today's SCD2 tables, on the reasoning that type 2
--                 "keeps history". It keeps the history of the customer. It
--                 does not keep the history of the warehouse: the correction
--                 closed the old row in batch 2026-03 by overwriting its
--                 valid_to, and the re-key rewrote customer_sk on the facts.
--                 The December state is no longer in any current row.
--   as_effective  from the year-end snapshot, on the reasoning that time
--                 travel "shows the past". It shows what was known then, so it
--                 has neither the late facts nor the backdated correction.

SET VARIABLE close_snapshot = (
    SELECT snapshot_id FROM etl_batch_log WHERE batch_id = '2025-12');

SELECT 'as_reported|' || c.segment AS key, round(sum(-f.amount_usd), 2) AS value
FROM fact_transaction f
JOIN dim_customer c ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.full_date BETWEEN DATE '2025-10-01' AND DATE '2025-12-31'
GROUP BY c.segment

UNION ALL

SELECT 'as_effective|' || c.segment, round(sum(-f.amount_usd), 2)
FROM fact_transaction f AT (VERSION => getvariable('close_snapshot'))
JOIN dim_customer c AT (VERSION => getvariable('close_snapshot'))
  ON c.customer_sk = f.customer_sk
JOIN dim_date d ON d.date_key = f.trade_date_key
WHERE f.txn_type = 'fee' AND d.full_date BETWEEN DATE '2025-10-01' AND DATE '2025-12-31'
GROUP BY c.segment
ORDER BY key;
