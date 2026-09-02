from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "corpus"))

import generate  # noqa: E402


def _small_oversized_xml(path: Path) -> bool:
    """Same defect, fewer records -- big enough to blow a small cap, quick to write."""
    return generate.oversized_xml(path, records=40_000)


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
