-- Naive: build the junk dimension as the full cartesian product of the flag
-- domains -- six channels times three independent booleans -- instead of
-- reading what occurs off the fact table.
--
-- Counting this dimension's rows to answer "how many combinations are
-- observed" then just reports the size of the domain, 48, whether or not a
-- transaction with that combination of flags has ever been posted.

WITH channels(channel) AS (
    VALUES ('branch'), ('atm'), ('online'), ('mobile'), ('pos'), ('system')
),
booleans(v) AS (VALUES (true), (false)),
junk AS (
    SELECT c.channel, r.v AS is_reversal, i.v AS is_international, k.v AS is_contactless
    FROM channels c
    CROSS JOIN booleans r
    CROSS JOIN booleans i
    CROSS JOIN booleans k
)
SELECT 'flag_combinations_observed' AS key, count(*) AS value FROM junk
UNION ALL
SELECT 'flag_combinations_possible' AS key, count(*) AS value FROM junk
ORDER BY key;
