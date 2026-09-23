-- Correct: read the pipeline off fact_loan_application, one row per
-- application, already resolved to its first-occurrence milestones.

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
SELECT 'in_underwriting_2026-06-30' AS key, in_underwriting AS value FROM counts
UNION ALL
SELECT 'funded' AS key, funded AS value FROM counts
UNION ALL
SELECT 'avg_days_applied_to_funded' AS key, avg_days AS value FROM counts
ORDER BY key;
