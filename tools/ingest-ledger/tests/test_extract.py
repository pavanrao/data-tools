"""Supervised extraction: a killed worker must leave a signal, never a fragment."""

from __future__ import annotations

import pytest
from conftest import OOM_CAP_MB
from ingest_ledger.extract import _diagnose, run
from ingest_ledger.manifest import walk
from ingest_ledger.models import Status
from ingest_ledger.reconcile import reconcile


def test_memory_cap_turns_an_oom_into_a_failed_status(fixture_path):
    """The podcast's failure: the parse dies, the pipeline reports success.

    Under the cap this must surface as FAILED with a memory diagnosis -- never
    as PARTIAL with whatever happened to be parsed before the kill.
    """
    (entry,) = list(walk(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=OOM_CAP_MB, timeout_s=120)
    row = reconcile(entry, extracted)

    assert row.status is Status.FAILED
    assert "memory" in (row.extracted.error or "").lower()
    assert row.extracted.units == 0


def test_streaming_probe_survives_a_cap_that_kills_an_eager_one(fixture_path):
    """The counterpart: our XML probe streams, so a generous cap is enough."""
    (entry,) = list(walk(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=512, timeout_s=180)

    assert extracted.error is None
    assert extracted.units == entry.declared.units


def test_timeout_is_reported_as_a_timeout(fixture_path):
    (entry,) = list(walk(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=512, timeout_s=0)
    assert "timed out" in (extracted.error or "")


def test_limits_are_recorded_as_evidence(fixture_path):
    (entry,) = list(walk(fixture_path("bom_mixed.csv")))
    extracted = run(entry, memory_mb=256, timeout_s=30)
    assert extracted.evidence["memory_cap_mb"] == 256
    assert extracted.evidence["timeout_s"] == 30


@pytest.mark.parametrize(
    ("code", "stderr", "expected"),
    [
        (-9, "", "out of memory"),
        (137, "", "out of memory"),
        (1, "MemoryError: boom", "memory cap"),
        (1, "ProbeUnavailable: install extras", "dependency not installed"),
        (2, "ValueError: nope", "exit 2"),
    ],
)
def test_exit_codes_become_actionable_diagnoses(code, stderr, expected):
    assert expected in _diagnose(code, stderr)
