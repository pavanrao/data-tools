-- Naive: start from what happened -- account openings -- and see which
-- promotions line up with one.
--
-- This can only find promotions that sold something. If nothing opened under
-- a promoted branch, product and month, there is no opening row to start
-- from, so that promotion is not merely miscounted -- it is invisible to this
-- query. "Promotions without openings" cannot be computed by narrowing an
-- openings-first query; the answer it gives is 0 every time, because nothing
-- in the working set was ever built from a promotion, only from an opening
-- that happened to match one.

WITH opened_matches AS (
    SELECT DISTINCT p.branch_id, p.product_code, p.promo_month
    FROM dim_account a
    JOIN dim_date d ON d.date_key = CAST(strftime(a.open_date, '%Y%m%d') AS INTEGER)
    JOIN hist_promotions p
      ON p.branch_id = a.branch_id
     AND p.product_code = a.product_code
     AND p.promo_month = d.year_month
)
SELECT 'promotions' AS key, count(*) AS value FROM opened_matches
UNION ALL
SELECT 'promotions_without_openings' AS key, 0 AS value
ORDER BY key;
