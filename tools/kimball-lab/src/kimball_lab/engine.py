"""The one module that imports duckdb (CONVENTIONS rule 4).

Two engines run the same SQL:

- ``ducklake``: a DuckLake catalog in a DuckDB file, with Parquet data files
  beside it. Every committed batch is a snapshot, so the warehouse can be
  queried as it stood after any batch. This is the default.
- ``duckdb``: a plain DuckDB file. No snapshots, so technique 13 cannot run, but
  it needs no extension and is what the tests use when the extension is not
  already installed.

Which one ran is recorded in ``lab_meta`` and printed by ``demo``, so a result
never leaves out the engine that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

CATALOG = "lab"


class EngineUnavailable(RuntimeError):
    """The requested engine cannot be opened here, and the reason is the message."""


@dataclass
class Engine:
    con: duckdb.DuckDBPyConnection
    kind: str  # "ducklake" | "duckdb"
    path: Path

    def execute(self, sql: str, params=None):
        return self.con.execute(sql, params) if params is not None else self.con.execute(sql)

    def rows(self, sql: str, params=None) -> list[tuple]:
        return self.execute(sql, params).fetchall()

    def columns(self) -> list[str]:
        return [d[0] for d in self.con.description or []]

    def latest_snapshot(self) -> int | None:
        if self.kind != "ducklake":
            return None
        return self.rows(f"SELECT max(snapshot_id) FROM {CATALOG}.snapshots()")[0][0]

    def close(self) -> None:
        self.con.close()


def ducklake_loadable(install: bool = False) -> str | None:
    """None if the ducklake extension loads here, else the reason it does not.

    With ``install=False`` nothing is downloaded, so the check is safe offline.
    """
    con = duckdb.connect()
    try:
        if install:
            con.execute("INSTALL ducklake")
        con.execute("LOAD ducklake")
        return None
    except duckdb.Error as e:
        return f"{type(e).__name__}: {e}"
    finally:
        con.close()


def is_ducklake_catalog(path: Path) -> bool:
    if not path.exists():
        return False
    con = duckdb.connect(str(path), read_only=True)
    try:
        sql = "SELECT count(*) FROM information_schema.tables WHERE table_name = ?"
        return bool(con.execute(sql, ["ducklake_snapshot"]).fetchone()[0])
    finally:
        con.close()


def open_engine(path: str | Path, kind: str | None = None, install: bool = True) -> Engine:
    """Open or create a warehouse. ``kind=None`` detects it from an existing file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind is None:
        kind = "ducklake" if is_ducklake_catalog(path) else "duckdb"
    if kind == "duckdb":
        return Engine(duckdb.connect(str(path)), "duckdb", path)
    if kind != "ducklake":
        raise ValueError(f"unknown engine: {kind}")
    reason = ducklake_loadable(install=install)
    if reason is not None:
        raise EngineUnavailable(f"the ducklake extension did not load ({reason})")
    con = duckdb.connect()
    con.execute("LOAD ducklake")
    data = path.with_name(path.name + ".files")
    con.execute(f"ATTACH 'ducklake:{path}' AS {CATALOG} (DATA_PATH '{data}/')")
    con.execute(f"USE {CATALOG}")
    return Engine(con, "ducklake", path)
