-- fact_account_daily_balance: a periodic snapshot. Grain is one account per day.
--
-- The snapshot records the end-of-day balance of every open account, whether or
-- not anything happened that day. Its balance is semi-additive: it adds across
-- accounts, and must not be added across days (technique 04).
--
-- Each batch extends every account through the end of the batch month. It also
-- rebuilds the days a batch disturbed after they were written: a late fact
-- posted in an earlier month, or an inferred account resolved with its opening
-- balance. The rows from that date on are deleted and recomputed from
-- fact_transaction, so the snapshot always agrees with the transaction fact.
-- The balance is in account currency and in USD at that day's rate.

CREATE TABLE IF NOT EXISTS fact_account_daily_balance (
    account_sk BIGINT NOT NULL, date_key INTEGER NOT NULL,
    balance_local DECIMAL(18,2) NOT NULL, fx_rate DECIMAL(12,6) NOT NULL,
    balance_usd DECIMAL(18,8) NOT NULL, etl_batch_id VARCHAR NOT NULL);

CREATE OR REPLACE TEMP TABLE batch_balance_scope AS
WITH bounds AS (
    SELECT CAST(getvariable('batch_id') || '-01' AS DATE) AS m_start,
           last_day(CAST(getvariable('batch_id') || '-01' AS DATE)) AS m_end,
           CAST(getvariable('lab_start') AS DATE) AS lab_start
),
known AS (
    SELECT a.account_sk, greatest(a.open_date, bounds.lab_start) AS first_day, a.resolved_in_batch
    FROM dim_account a, bounds
    WHERE NOT a.is_inferred AND a.open_date <= bounds.m_end
),
from_dates AS (
    -- extend through this month
    SELECT k.account_sk, greatest(k.first_day, bounds.m_start) AS from_date FROM known k, bounds
    UNION ALL
    -- a late posting reopens the days from its posting date
    SELECT k.account_sk, greatest(k.first_day, pd.full_date)
    FROM fact_transaction f
    JOIN known k ON k.account_sk = f.account_sk
    JOIN dim_date pd ON pd.date_key = f.posting_date_key
    WHERE f.etl_batch_id = getvariable('batch_id')
    UNION ALL
    -- a resolved inferred account is built from its first day
    SELECT account_sk, first_day FROM known WHERE resolved_in_batch = getvariable('batch_id')
)
SELECT account_sk, min(from_date) AS from_date, max(bounds.m_end) AS to_date
FROM from_dates, bounds
GROUP BY account_sk;

DELETE FROM fact_account_daily_balance
WHERE EXISTS (
    SELECT 1 FROM batch_balance_scope s
    WHERE s.account_sk = fact_account_daily_balance.account_sk
      AND fact_account_daily_balance.date_key >= CAST(strftime(s.from_date, '%Y%m%d') AS INTEGER));

INSERT INTO fact_account_daily_balance
WITH postings AS (
    SELECT f.account_sk, f.posting_date_key, sum(f.amount_local) AS amount
    FROM fact_transaction f
    WHERE f.account_sk IN (SELECT account_sk FROM batch_balance_scope)
    GROUP BY ALL
),
before_scope AS (
    SELECT s.account_sk, coalesce(sum(p.amount), 0) AS amount
    FROM batch_balance_scope s
    LEFT JOIN postings p
           ON p.account_sk = s.account_sk
          AND p.posting_date_key < CAST(strftime(s.from_date, '%Y%m%d') AS INTEGER)
    GROUP BY s.account_sk
),
grid AS (
    SELECT s.account_sk, d.date_key, d.full_date
    FROM batch_balance_scope s
    JOIN dim_date d ON d.full_date BETWEEN s.from_date AND s.to_date
)
SELECT
    g.account_sk,
    g.date_key,
    CAST(a.opening_balance + bs.amount
         + sum(coalesce(p.amount, 0)) OVER (PARTITION BY g.account_sk ORDER BY g.date_key)
         AS DECIMAL(18,2)) AS balance_local,
    fx.usd_per_unit,
    CAST(a.opening_balance + bs.amount
         + sum(coalesce(p.amount, 0)) OVER (PARTITION BY g.account_sk ORDER BY g.date_key)
         AS DECIMAL(18,2)) * fx.usd_per_unit AS balance_usd,
    getvariable('batch_id')
FROM grid g
JOIN dim_account a ON a.account_sk = g.account_sk
JOIN before_scope bs ON bs.account_sk = g.account_sk
LEFT JOIN postings p ON p.account_sk = g.account_sk AND p.posting_date_key = g.date_key
LEFT JOIN fx_rate fx ON fx.currency_code = a.currency_code AND fx.rate_date = g.full_date;
