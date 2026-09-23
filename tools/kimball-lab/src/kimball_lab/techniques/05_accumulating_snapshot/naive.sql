-- Naive: track pipeline status by the latest event recorded for the
-- application, the way a dashboard built straight off the event feed would.
--
-- Events do not always arrive in milestone order. A resubmitted "applied"
-- event can be dated after the decision that followed the original
-- submission, so "the most recent row for this application" is sometimes an
-- earlier milestone landing late, not a status change. And every funded
-- application gets a first_payment event thirty days later, so by the time
-- anyone asks, "funded" is rarely the latest row for a loan that funded --
-- "first_payment" is, which makes this naive count of applications sitting at
-- "funded" undercount the true number that ever funded.
--
-- The average makes the paired mistake: it joins each funded event to every
-- "applied" event on the same application, so a resubmission (a second
-- "applied" row) is counted as a second, shorter attempt at the same loan.

WITH latest AS (
    SELECT application_id, event_type,
           row_number() OVER (
               PARTITION BY application_id ORDER BY event_date DESC, event_type DESC
           ) AS rn
    FROM hist_loan_events
),
status AS (
    SELECT application_id, event_type AS latest_status FROM latest WHERE rn = 1
)
SELECT 'in_underwriting_2026-06-30' AS key, count(*) AS value
FROM status WHERE latest_status = 'applied'
UNION ALL
SELECT 'funded' AS key, count(*) AS value
FROM status WHERE latest_status = 'funded'
UNION ALL
SELECT 'avg_days_applied_to_funded' AS key,
       round(
           sum(date_diff('day', ap.event_date, fu.event_date))
           / CAST(count(*) AS DECIMAL(18,0)),
           2
       ) AS value
FROM hist_loan_events ap
JOIN hist_loan_events fu
     ON fu.application_id = ap.application_id AND fu.event_type = 'funded'
WHERE ap.event_type = 'applied'
ORDER BY key;
