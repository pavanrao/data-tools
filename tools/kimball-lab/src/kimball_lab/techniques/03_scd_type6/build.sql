-- dim_customer_scd6: type 1 + type 2 + type 3 carried on the same row.
--
-- Every version row of dim_customer already has its own segment (type 2: "as
-- was"). This adds two more columns to each of those rows:
--   current_segment   type 1 -- the segment on today's row, copied onto every
--                      version of the customer, so it changes on all of them
--                      at once when the customer changes segment again
--   previous_segment  type 3 -- the segment on the row immediately before the
--                      current one, NULL for a customer who has never changed
--
-- The type 2 columns (segment, valid_from, valid_to) are untouched, so this
-- view answers both "as was" (technique 02) and "as is" (this one) without
-- picking one and losing the other.

CREATE OR REPLACE VIEW dim_customer_scd6 AS
WITH current_row AS (
    SELECT customer_id, segment AS current_segment
    FROM dim_customer
    WHERE is_current
),
previous_row AS (
    SELECT customer_id, segment AS previous_segment
    FROM (
        SELECT customer_id, segment,
               row_number() OVER (PARTITION BY customer_id ORDER BY valid_from DESC) AS rn
        FROM dim_customer
        WHERE NOT is_current
    ) ranked
    WHERE rn = 1
)
SELECT
    d.customer_sk, d.customer_id, d.full_name, d.segment, d.home_branch_id, d.city,
    d.customer_since, d.valid_from, d.valid_to, d.is_current, d.etl_batch_id,
    c.current_segment, p.previous_segment
FROM dim_customer d
JOIN current_row c ON c.customer_id = d.customer_id
LEFT JOIN previous_row p ON p.customer_id = d.customer_id;
