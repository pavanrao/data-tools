"""Shared fixtures: one seeded bank, loaded once per session.

The suite runs under --import-mode=importlib, so shared state is a fixture, never
an import (CONVENTIONS rule 6). The default warehouse uses the plain DuckDB
engine, which needs no extension. The DuckLake warehouse is built only if the
extension already loads without a download, so the suite needs no network.
"""

from __future__ import annotations

import json

import pytest
from kimball_lab import runner, seed
from kimball_lab.engine import ducklake_loadable, open_engine

SEED, SCALE = 42, 1


@pytest.fixture(scope="session")
def seed_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("bank")
    seed.write(seed.generate(seed=SEED, scale=SCALE), out)
    return out


@pytest.fixture(scope="session")
def truth(seed_dir):
    return json.loads((seed_dir / "ground_truth.json").read_text())


@pytest.fixture(scope="session")
def manifest(seed_dir):
    return json.loads((seed_dir / "manifest.json").read_text())


@pytest.fixture(scope="session")
def warehouse(seed_dir, tmp_path_factory):
    engine = open_engine(tmp_path_factory.mktemp("wh") / "lab.duckdb", kind="duckdb")
    results = runner.load(engine, seed_dir)
    engine.load_results = results
    yield engine
    engine.close()


@pytest.fixture(scope="session")
def lake(seed_dir, tmp_path_factory):
    reason = ducklake_loadable(install=False)
    if reason is not None:
        pytest.skip(f"ducklake extension not installed locally: {reason}")
    engine = open_engine(
        tmp_path_factory.mktemp("lake") / "lab.ducklake", kind="ducklake", install=False
    )
    engine.load_results = runner.load(engine, seed_dir)
    yield engine
    engine.close()
