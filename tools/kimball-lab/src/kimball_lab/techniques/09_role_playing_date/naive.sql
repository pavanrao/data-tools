-- Naive: "the" date dimension, joined through posting_date_key.
--
-- This counts transactions posted in December, not traded in December. A
-- card purchase traded on 2025-12-30 typically posts in January, so it drops
-- out; a purchase traded in late November that posts on 2025-12-01 or 12-02
-- gets counted in. Nothing about the query looks wrong -- dim_date has no hint
-- that it was asked the wrong question.

SELECT 'txn_count_2025-12' AS key, count(*) AS value
FROM fact_transaction f
JOIN dim_date d ON d.date_key = f.posting_date_key
WHERE d.year_month = '2025-12';
