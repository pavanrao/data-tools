from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "corpus"))

import generate  # noqa: E402

#: Large enough that an eager parse exceeds OOM_CAP_MB, small enough to write
#: in well under a second. Verified reproducible at 96MB; see test_extract.py.
OVERSIZED_RECORDS = 200_000
OOM_CAP_MB = 96


def _small_oversized_xml(path: Path) -> bool:
    """Same defect, sized for the cap the extraction tests use."""
    return generate.oversized_xml(path, records=OVERSIZED_RECORDS)


@pytest.fixture(scope="session")
def hostile(tmp_path_factory) -> dict[str, Path]:
    """Build the hostile corpus once per session.

    Fixtures whose optional dependency is missing are omitted from the mapping
    rather than faked, so a test that needs one skips instead of lying.
    """
    out = tmp_path_factory.mktemp("hostile")
    builders = {**generate.BUILDERS, "oversized.xml": _small_oversized_xml}
    out.mkdir(parents=True, exist_ok=True)
    built = {name: builder(out / name) for name, builder in builders.items()}
    return {name: out / name for name, ok in built.items() if ok}


@pytest.fixture
def fixture_path(hostile):
    def _get(name: str) -> Path:
        if name not in hostile:
            pytest.skip(f"{name} needs an optional dependency that is not installed")
        return hostile[name]

    return _get


@pytest.fixture(scope="session")
def rfp(tmp_path_factory) -> dict[str, Path]:
    """A small realistic corpus whose answer lives in a sheet that never read."""
    out = tmp_path_factory.mktemp("rfp")
    built = generate.rfp_corpus(out)
    if not built.get("pricing.xlsx"):
        pytest.skip("rfp corpus needs openpyxl")
    return {name: out / name for name in built}


@pytest.fixture
def indexed_rfp(rfp):
    """Reconcile and index the RFP corpus into an in-memory ledger."""
    import sqlite3

    from data_tools_core import ledger
    from ingest_ledger import index as index_mod
    from ingest_ledger.manifest import walk
    from ingest_ledger.probes import for_path
    from ingest_ledger.reconcile import reconcile

    root = next(iter(rfp.values())).parent
    rows = []
    for entry in walk(root):
        probe = for_path(entry.path) if entry.declared is not None else None
        rows.append(reconcile(entry, probe.extract(entry.path) if probe else None))

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(ledger.SCHEMA)
    run_id = ledger.start_run(conn, "test", [])
    index_mod.build(conn, run_id, rows)
    try:
        yield conn, run_id, rows
    finally:
        conn.close()
