"""Run the plain-SQL ETL, batch by batch, and the technique queries.

Nothing here knows what the SQL does. The runner sets three variables the SQL
reads with ``getvariable`` (``batch_id``, ``batch_dir``, ``lab_start``), runs
the core files in name order inside one transaction per batch, reconciles what
was staged against what was loaded, and then runs each technique's
``build.sql``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources
from pathlib import Path

from .engine import Engine

LAB_START = "2025-01-01"


class ReconciliationError(RuntimeError):
    """The load lost or invented rows. The message says which batch and how many."""


@dataclass
class BatchResult:
    batch_id: str
    staged_transactions: int
    loaded_transactions: int
    snapshot_id: int | None


@dataclass
class Technique:
    number: str
    name: str
    path: Path
    title: str
    question: str
    requires: str | None

    def sql(self, which: str) -> str | None:
        f = self.path / f"{which}.sql"
        return f.read_text() if f.exists() else None


def _package_dir(name: str) -> Path:
    return Path(str(resources.files("kimball_lab") / name))


def core_files() -> list[Path]:
    return sorted(_package_dir("core").glob("*.sql"))


def techniques() -> list[Technique]:
    out = []
    for d in sorted(p for p in _package_dir("techniques").iterdir() if p.is_dir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text())
        number, _, name = d.name.partition("_")
        out.append(
            Technique(number, name, d, meta["title"], meta["question"], meta.get("requires"))
        )
    return out


def batch_dirs(seed_dir: Path) -> list[Path]:
    return sorted(p for p in Path(seed_dir).iterdir() if p.is_dir() and p.name.startswith("batch="))


def load(engine: Engine, seed_dir: Path, through: str | None = None) -> list[BatchResult]:
    """Load every batch (or up to ``through``), then build the technique tables."""
    seed_dir = Path(seed_dir).resolve()
    engine.execute(
        "CREATE TABLE IF NOT EXISTS lab_meta (key VARCHAR NOT NULL, value VARCHAR NOT NULL)"
    )
    engine.execute("DELETE FROM lab_meta")
    engine.execute(
        "INSERT INTO lab_meta VALUES ('seed_dir', ?), ('engine', ?)", [str(seed_dir), engine.kind]
    )
    engine.execute(
        "CREATE TABLE IF NOT EXISTS etl_batch_log (batch_id VARCHAR NOT NULL, "
        "staged_transactions BIGINT NOT NULL, loaded_transactions BIGINT NOT NULL, "
        "snapshot_id BIGINT)"
    )
    engine.execute(f"SET VARIABLE lab_start = '{LAB_START}'")
    results = []
    core = [(p.name, p.read_text()) for p in core_files()]
    done = {r[0] for r in engine.rows("SELECT batch_id FROM etl_batch_log")}
    for d in batch_dirs(seed_dir):
        batch_id = d.name.removeprefix("batch=")
        if through is not None and batch_id > through:
            break
        if batch_id in done:
            continue
        engine.execute(f"SET VARIABLE batch_id = '{batch_id}'")
        engine.execute(f"SET VARIABLE batch_dir = '{d.as_posix()}'")
        engine.execute("BEGIN TRANSACTION")
        try:
            for name, sql in core:
                try:
                    engine.execute(sql)
                except Exception as e:
                    raise RuntimeError(f"batch {batch_id}, core/{name}: {e}") from e
            staged = engine.rows("SELECT count(*) FROM stg_transactions")[0][0]
            loaded = engine.rows(
                "SELECT count(*) FROM fact_transaction WHERE etl_batch_id = ?", [batch_id]
            )[0][0]
            if staged != loaded:
                raise ReconciliationError(
                    f"batch {batch_id}: staged {staged} transactions, loaded {loaded}"
                )
            # The marker commits with the data, so a batch is either loaded and
            # marked or neither, and a re-run skips it rather than loading it twice.
            engine.execute(
                "INSERT INTO etl_batch_log VALUES (?, ?, ?, NULL)", [batch_id, staged, loaded]
            )
            engine.execute("COMMIT")
        except BaseException:
            engine.execute("ROLLBACK")
            raise
        # The snapshot id exists only after the commit, so it is filled in after.
        snapshot = engine.latest_snapshot()
        if snapshot is not None:
            engine.execute(
                "UPDATE etl_batch_log SET snapshot_id = ? WHERE batch_id = ?", [snapshot, batch_id]
            )
        results.append(BatchResult(batch_id, staged, loaded, snapshot))
    build(engine)
    return results


def build(engine: Engine) -> list[str]:
    """Run every technique's build.sql, in technique order. Returns those that ran."""
    ran = []
    for t in techniques():
        sql = t.sql("build")
        if sql is None or (t.requires and t.requires != engine.kind):
            continue
        try:
            engine.execute(sql)
        except Exception as e:
            raise RuntimeError(f"technique {t.number} build.sql: {e}") from e
        ran.append(t.number)
    return ran


def _norm(v) -> str | int:
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, float):
        return str(Decimal(str(v)))
    return v


def query_figures(engine: Engine, sql: str) -> dict[str, str | int]:
    """Run a naive.sql or correct.sql. The contract: two columns, key and value."""
    rows = engine.rows(sql)
    return {str(k): _norm(v) for k, v in rows}


@dataclass
class Demo:
    technique: Technique
    engine: str
    naive: dict[str, str | int] | None
    correct: dict[str, str | int] | None
    truth: dict[str, str | int]
    skipped: str | None = None

    @property
    def correct_matches_truth(self) -> bool:
        return self.correct == self.truth

    @property
    def naive_differs(self) -> bool:
        return self.naive != self.truth


def seed_dir_of(engine: Engine) -> Path:
    return Path(engine.rows("SELECT value FROM lab_meta WHERE key = 'seed_dir'")[0][0])


def demo(engine: Engine, technique: Technique, truth: dict | None = None) -> Demo:
    if truth is None:
        truth = json.loads((seed_dir_of(engine) / "ground_truth.json").read_text())
    expected = truth.get(technique.number, {})
    if technique.requires and technique.requires != engine.kind:
        reason = f"needs the {technique.requires} engine; this warehouse is {engine.kind}"
        return Demo(technique, engine.kind, None, None, expected, skipped=reason)
    return Demo(
        technique,
        engine.kind,
        query_figures(engine, technique.sql("naive")),
        query_figures(engine, technique.sql("correct")),
        expected,
    )
