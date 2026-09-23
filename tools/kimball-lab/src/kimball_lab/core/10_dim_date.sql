-- dim_date: one row per calendar day, built once.
--
-- The key is the date as an integer (20251231). Kimball allows a meaningful key
-- for dates alone: it is stable, it sorts, and it partitions. Every other
-- dimension gets a meaningless surrogate. The bank's fiscal year starts on
-- 1 April, so FY2026 runs from April 2025 to March 2026.

CREATE TABLE IF NOT EXISTS dim_date AS
SELECT
    CAST(strftime(d, '%Y%m%d') AS INTEGER)              AS date_key,
    CAST(d AS DATE)                                     AS full_date,
    year(d)                                             AS calendar_year,
    quarter(d)                                          AS calendar_quarter,
    month(d)                                            AS calendar_month,
    strftime(d, '%Y-%m')                                AS year_month,
    monthname(d)                                        AS month_name,
    day(d)                                              AS day_of_month,
    dayname(d)                                          AS day_name,
    isodow(d) IN (6, 7)                                 AS is_weekend,
    CAST(d AS DATE) = last_day(CAST(d AS DATE))         AS is_month_end,
    year(d) + CASE WHEN month(d) >= 4 THEN 1 ELSE 0 END AS fiscal_year,
    ((month(d) + 8) % 12) // 3 + 1                      AS fiscal_quarter
FROM range(TIMESTAMP '2024-01-01', TIMESTAMP '2027-01-01', INTERVAL 1 DAY) t(d);
