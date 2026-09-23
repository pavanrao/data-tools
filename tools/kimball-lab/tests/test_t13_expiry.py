"""Technique 13: once snapshots expire, the as-reported answer is gone.

This test builds its own lake rather than using the shared ``lake`` fixture,
because expiring snapshots would break every other DuckLake test after it.
"""

from __future__ import annotations

import pytest
from kimball_lab import runner
from kimball_lab.engine import ducklake_loadable, open_engine


@pytest.fixture
def own_lake(seed_dir, tmp_path):
    reason = ducklake_loadable(install=False)
    if reason is not None:
        pytest.skip(f"ducklake extension not installed locally: {reason}")
    engine = open_engine(tmp_path / "lab.ducklake", kind="ducklake", install=False)
    runner.load(engine, seed_dir)
    yield engine
    engine.close()


def _technique():
    return next(t for t in runner.techniques() if t.number == "13")


def test_expiry_removes_the_as_reported_answer(own_lake, truth):
    t = _technique()
    assert runner.demo(own_lake, t, truth).correct == truth["13"]

    latest = own_lake.latest_snapshot()
    older = ", ".join(str(i) for i in range(latest))
    own_lake.execute(f"CALL ducklake_expire_snapshots('lab', versions => [{older}])")

    with pytest.raises(Exception, match="No snapshot found"):
        runner.demo(own_lake, t, truth)

    # the effective-time answer never depended on a snapshot
    effective = own_lake.rows(
        """SELECT 'as_effective|' || c.segment, round(sum(-f.amount_usd), 2)
           FROM fact_transaction f JOIN dim_customer c ON c.customer_sk = f.customer_sk
           JOIN dim_date d ON d.date_key = f.trade_date_key
           WHERE f.txn_type = 'fee'
             AND d.full_date BETWEEN DATE '2025-10-01' AND DATE '2025-12-31'
           GROUP BY c.segment"""
    )
    expected = {k: v for k, v in truth["13"].items() if k.startswith("as_effective|")}
    assert {k: str(v) for k, v in effective} == expected
