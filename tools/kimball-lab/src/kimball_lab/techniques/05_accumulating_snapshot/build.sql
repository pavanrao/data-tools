-- fact_loan_application: an accumulating snapshot. Grain is one application.
--
-- Unlike fact_transaction (one row per event, never revisited) or
-- fact_account_daily_balance (one row per account per day, extended forward
-- every batch), this fact has a fixed number of rows -- one per application --
-- and each row is revisited as the application moves through the pipeline.
-- Every milestone the application could reach gets its own date-key column;
-- one not yet reached is NULL, not a placeholder date. Lag measures between
-- milestones are computed once here, at build time, instead of by every query
-- that wants them.
--
-- Built once, after all batches load, from hist_loan_events, which keeps
-- every loan event ever delivered. An application can carry more than one
-- "applied" event -- the applicant resubmits documents -- so a milestone's
-- date is the first occurrence, not the last. A customer who is declined and
-- reapplies gets a new application_id: that is a second row here, not a
-- reopened first one.

CREATE OR REPLACE TABLE fact_loan_application AS
WITH milestones AS (
    SELECT application_id, event_type, min(event_date) AS milestone_date
    FROM hist_loan_events
    GROUP BY application_id, event_type
),
pivoted AS (
    SELECT application_id,
           max(CASE WHEN event_type = 'applied' THEN milestone_date END) AS applied_date,
           max(CASE WHEN event_type = 'approved' THEN milestone_date END) AS approved_date,
           max(CASE WHEN event_type = 'declined' THEN milestone_date END) AS declined_date,
           max(CASE WHEN event_type = 'funded' THEN milestone_date END) AS funded_date,
           max(CASE WHEN event_type = 'first_payment' THEN milestone_date END) AS first_payment_date
    FROM milestones
    GROUP BY application_id
),
who AS (
    SELECT application_id, min(customer_id) AS customer_id, min(branch_id) AS branch_id
    FROM hist_loan_events
    GROUP BY application_id
)
SELECT
    row_number() OVER (ORDER BY p.application_id) AS application_sk,
    p.application_id,
    coalesce(c.customer_sk, 0) AS customer_sk,
    coalesce(b.branch_sk, 0) AS branch_sk,
    CAST(strftime(p.applied_date, '%Y%m%d') AS INTEGER) AS applied_date_key,
    CAST(strftime(p.approved_date, '%Y%m%d') AS INTEGER) AS approved_date_key,
    CAST(strftime(p.declined_date, '%Y%m%d') AS INTEGER) AS declined_date_key,
    CAST(strftime(p.funded_date, '%Y%m%d') AS INTEGER) AS funded_date_key,
    CAST(strftime(p.first_payment_date, '%Y%m%d') AS INTEGER) AS first_payment_date_key,
    date_diff('day', p.applied_date, p.approved_date) AS days_applied_to_approved,
    date_diff('day', p.applied_date, p.declined_date) AS days_applied_to_declined,
    date_diff('day', p.approved_date, p.funded_date) AS days_approved_to_funded,
    date_diff('day', p.applied_date, p.funded_date) AS days_applied_to_funded,
    date_diff('day', p.funded_date, p.first_payment_date) AS days_funded_to_first_payment,
    CASE
        WHEN p.first_payment_date IS NOT NULL THEN 'first_payment'
        WHEN p.funded_date IS NOT NULL THEN 'funded'
        WHEN p.approved_date IS NOT NULL THEN 'approved'
        WHEN p.declined_date IS NOT NULL THEN 'declined'
        ELSE 'applied'
    END AS current_status
FROM pivoted p
JOIN who w ON w.application_id = p.application_id
LEFT JOIN dim_customer c
       ON c.customer_id = w.customer_id
      AND p.applied_date >= c.valid_from AND p.applied_date < c.valid_to
LEFT JOIN dim_branch b ON b.branch_id = w.branch_id;
