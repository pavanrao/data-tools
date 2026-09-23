-- bridge_account_holder: the many-to-many between accounts and customers.
--
-- Most accounts have one holder. A joint account has two or three, each
-- owning a share recorded in account_holders.csv (hist_account_holders keeps
-- the full history; an account's holders arrive once, with the account, and
-- never change). Reporting a fact through this bridge without a weight counts
-- the fact once per holder. weighting_factor is each holder's share of the
-- account, exact, so a query that sums balance * weighting_factor recovers
-- the account's real balance no matter how many holders it has.
--
-- customer_sk is the holder's current (type 1) version, because ownership is
-- a fact about the account today, not about which segment the holder was in
-- when they were added.

CREATE OR REPLACE TABLE bridge_account_holder AS
SELECT
    a.account_sk,
    c.customer_sk,
    h.customer_id,
    h.holder_role,
    CAST(CAST(h.ownership_pct AS DECIMAL(9,4)) / 100 AS DECIMAL(9,4)) AS weighting_factor
FROM hist_account_holders h
JOIN dim_account a ON a.account_id = h.account_id
JOIN dim_customer c ON c.customer_id = h.customer_id AND c.is_current;
