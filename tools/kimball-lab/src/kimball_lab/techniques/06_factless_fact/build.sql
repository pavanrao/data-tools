-- fact_promotion_coverage: a factless fact. Grain is one promotion running at
-- one branch, for one product, in one month. No measure column, because there
-- is nothing to sum -- the row records that the promotion happened, not an
-- amount. A factless fact answers a coverage question: which combinations of
-- dimensions occurred together, and, by anti-joining against another fact or
-- dimension, which combinations that could have occurred did not.
--
-- Built once, after all batches load, from hist_promotions, which keeps every
-- promotion ever delivered (branches run 1 or 2 product promotions a month,
-- every month, for the life of the lab).

CREATE OR REPLACE TABLE fact_promotion_coverage AS
SELECT
    row_number() OVER (ORDER BY h.promo_month, h.branch_id, h.product_code) AS promotion_sk,
    coalesce(b.branch_sk, 0) AS branch_sk,
    coalesce(p.product_sk, 0) AS product_sk,
    d.date_key AS month_date_key
FROM hist_promotions h
LEFT JOIN dim_branch b ON b.branch_id = h.branch_id
LEFT JOIN dim_product p ON p.product_code = h.product_code
LEFT JOIN dim_date d ON d.full_date = CAST(h.promo_month || '-01' AS DATE);
