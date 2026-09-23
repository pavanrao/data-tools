-- Correct: an opening is an account in dim_account whose open_date falls in
-- the promotion's branch, product and month. Anti-join fact_promotion_coverage
-- against dim_account for the promotions that have no matching opening.

SELECT 'promotions' AS key, count(*) AS value
FROM fact_promotion_coverage
UNION ALL
SELECT 'promotions_without_openings' AS key, count(*) AS value
FROM fact_promotion_coverage c
JOIN dim_branch b ON b.branch_sk = c.branch_sk
JOIN dim_product p ON p.product_sk = c.product_sk
JOIN dim_date d ON d.date_key = c.month_date_key
WHERE NOT EXISTS (
    SELECT 1 FROM dim_account a
    JOIN dim_date ad ON ad.date_key = CAST(strftime(a.open_date, '%Y%m%d') AS INTEGER)
    WHERE a.branch_id = b.branch_id
      AND a.product_code = p.product_code
      AND ad.year_month = d.year_month
)
ORDER BY key;
