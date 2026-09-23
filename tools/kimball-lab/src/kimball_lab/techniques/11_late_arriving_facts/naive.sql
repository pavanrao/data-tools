-- Naive: two plausible mistakes.
--
-- late_facts is judged by trade date instead of posting month. A fact loads
-- in the batch of its posting month, not its trade month, so a purchase
-- traded on the 30th and posted three days later, in the next month, arrives
-- right on time by posting month but looks late if you check trade month
-- instead.
--
-- inferred_member_facts (and its amount) are read off dim_account's current
-- is_inferred flag. That flag is true only until the real account record
-- arrives and overwrites the placeholder, which has happened for every
-- account by the time this query runs -- so this always finds none, as if an
-- inner join at load time had dropped them rather than kept them.

SELECT 'late_facts' AS key, count(*) AS value
FROM fact_transaction f
JOIN dim_date td ON td.date_key = f.trade_date_key
WHERE f.etl_batch_id > td.year_month
UNION ALL
SELECT 'inferred_member_facts' AS key, count(*) AS value
FROM fact_transaction f
JOIN dim_account a ON a.account_sk = f.account_sk
WHERE a.is_inferred
UNION ALL
SELECT 'inferred_member_amount_usd' AS key, round(coalesce(sum(f.amount_usd), 0), 2) AS value
FROM fact_transaction f
JOIN dim_account a ON a.account_sk = f.account_sk
WHERE a.is_inferred
ORDER BY key;
