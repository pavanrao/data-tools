-- Correct: dim_txn_profile already holds one row per combination that
-- occurs, so counting it answers "observed" directly. "Possible" is the size
-- of the domain the junk dimension draws from -- six channels, each with
-- three independent flags -- not the dimension's own row count.

SELECT 'flag_combinations_observed' AS key, count(*) AS value FROM dim_txn_profile
UNION ALL
SELECT 'flag_combinations_possible' AS key, 6 * 2 * 2 * 2 AS value
ORDER BY key;
