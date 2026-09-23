-- dim_trade_date, dim_posting_date: dim_date, played in each of the fact's
-- two date roles.
--
-- fact_transaction carries trade_date_key and posting_date_key. A card
-- purchase posts one to three days after it trades, so purchases traded in
-- the last days of a month mostly post in the next one. Joining both keys to
-- the same unaliased dim_date invites a query to filter the wrong column, or
-- to join it twice with columns that collide. These views rename every
-- column with its role's prefix, so each key gets its own dimension with no
-- ambiguity at the point the SQL is written.

CREATE OR REPLACE VIEW dim_trade_date AS
SELECT
    date_key         AS trade_date_key,
    full_date        AS trade_full_date,
    calendar_year    AS trade_calendar_year,
    calendar_quarter AS trade_calendar_quarter,
    calendar_month   AS trade_calendar_month,
    year_month       AS trade_year_month,
    month_name       AS trade_month_name,
    day_of_month     AS trade_day_of_month,
    day_name         AS trade_day_name,
    is_weekend       AS trade_is_weekend,
    is_month_end     AS trade_is_month_end,
    fiscal_year      AS trade_fiscal_year,
    fiscal_quarter   AS trade_fiscal_quarter
FROM dim_date;

CREATE OR REPLACE VIEW dim_posting_date AS
SELECT
    date_key         AS posting_date_key,
    full_date        AS posting_full_date,
    calendar_year    AS posting_calendar_year,
    calendar_quarter AS posting_calendar_quarter,
    calendar_month   AS posting_calendar_month,
    year_month       AS posting_year_month,
    month_name       AS posting_month_name,
    day_of_month     AS posting_day_of_month,
    day_name         AS posting_day_name,
    is_weekend       AS posting_is_weekend,
    is_month_end     AS posting_is_month_end,
    fiscal_year      AS posting_fiscal_year,
    fiscal_quarter   AS posting_fiscal_quarter
FROM dim_date;
