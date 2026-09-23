"""The core load: the warehouse agrees with the seed before any technique runs."""

from __future__ import annotations


def q(engine, sql):
    return engine.rows(sql)


def test_every_batch_reconciles(warehouse, manifest):
    by_batch = {
        r.batch_id: (r.staged_transactions, r.loaded_transactions) for r in warehouse.load_results
    }
    assert list(by_batch) == manifest["batches"]
    for batch, (staged, loaded) in by_batch.items():
        assert staged == loaded == manifest["transactions_per_batch"][batch]


def test_every_transaction_loaded_once(warehouse, manifest):
    total, distinct = q(warehouse, "SELECT count(*), count(DISTINCT txn_id) FROM fact_transaction")[
        0
    ]
    assert total == distinct == manifest["transactions"]


def test_no_fact_left_on_the_unknown_member(warehouse):
    assert q(warehouse, "SELECT count(*) FROM fact_transaction WHERE customer_sk = 0")[0][0] == 0
    assert q(warehouse, "SELECT count(*) FROM dim_account WHERE is_inferred")[0][0] == 0


def test_inferred_members_were_created_then_resolved(warehouse, manifest):
    rows = q(
        warehouse,
        """SELECT account_id FROM dim_account
                           WHERE inferred_in_batch IS NOT NULL AND resolved_in_batch IS NOT NULL
                           ORDER BY 1""",
    )
    assert [r[0] for r in rows] == sorted(manifest["planted"]["inferred_member_accounts"])


def test_type2_history(warehouse, manifest):
    rows = q(
        warehouse,
        """SELECT customer_id, count(*) FROM dim_customer
                           WHERE customer_sk > 0 GROUP BY 1 HAVING count(*) > 1""",
    )
    versioned = {r[0] for r in rows}
    planted = set(manifest["planted"]["segment_changes"])
    planted |= set(manifest["planted"]["backdated_corrections"])
    assert versioned == planted
    # exactly one current row per customer, and intervals that do not overlap
    assert (
        q(
            warehouse,
            """SELECT count(*) FROM (SELECT customer_id FROM dim_customer
                           GROUP BY 1 HAVING sum(is_current::INT) <> 1)""",
        )[0][0]
        == 0
    )
    assert (
        q(
            warehouse,
            """SELECT count(*) FROM dim_customer a JOIN dim_customer b
                           ON a.customer_id = b.customer_id AND a.customer_sk < b.customer_sk
                           AND a.valid_from < b.valid_to AND b.valid_from < a.valid_to""",
        )[0][0]
        == 0
    )


def test_balance_snapshot_has_one_row_per_account_day(warehouse):
    dupes = q(
        warehouse,
        """SELECT count(*) FROM (SELECT account_sk, date_key FROM
                            fact_account_daily_balance GROUP BY ALL HAVING count(*) > 1)""",
    )
    assert dupes[0][0] == 0


def test_balance_agrees_with_the_transaction_fact(warehouse):
    """Month-end balance equals opening balance plus every posting, for every account."""
    diff = q(
        warehouse,
        """
        WITH posted AS (
            SELECT account_sk, sum(amount_local) AS amt FROM fact_transaction
            WHERE posting_date_key <= 20260630 GROUP BY 1)
        SELECT count(*) FROM fact_account_daily_balance b
        JOIN dim_account a USING (account_sk)
        LEFT JOIN posted p USING (account_sk)
        WHERE b.date_key = 20260630
          AND b.balance_local <> a.opening_balance + coalesce(p.amt, 0)""",
    )
    assert diff[0][0] == 0
