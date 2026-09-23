-- Correct: read the pipeline off fact_loan_application, one row per
-- application, already resolved to its first-occurrence milestones.
--
-- The value column holds both integer counts and a two-decimal average, so it
-- is typed as a two-member union (i for the counts, d for the average). Without
-- it, DuckDB would pick one common type for the whole column -- decimal, since
-- that is the only type that can hold both -- and every count would come back
-- as a Decimal like 42.00 instead of the integer 42 the ground truth expects.

WITH counts AS (
    SELECT
        count(*) FILTER (WHERE approved_date_key IS NULL AND declined_date_key IS NULL)
            AS in_underwriting,
        count(*) FILTER (WHERE funded_date_key IS NOT NULL) AS funded,
        round(
            sum(days_applied_to_funded) FILTER (WHERE funded_date_key IS NOT NULL)
            / CAST(count(*) FILTER (WHERE funded_date_key IS NOT NULL) AS DECIMAL(18,0)),
            2
        ) AS avg_days
    FROM fact_loan_application
)
SELECT 'in_underwriting_2026-06-30' AS key,
       union_value(i := in_underwriting)::UNION(i BIGINT, d DECIMAL(18,2)) AS value
FROM counts
UNION ALL
SELECT 'funded' AS key,
       union_value(i := funded)::UNION(i BIGINT, d DECIMAL(18,2)) AS value
FROM counts
UNION ALL
SELECT 'avg_days_applied_to_funded' AS key,
       union_value(d := avg_days)::UNION(i BIGINT, d DECIMAL(18,2)) AS value
FROM counts
ORDER BY key;
