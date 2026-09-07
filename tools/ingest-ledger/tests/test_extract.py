"""Supervised extraction: a killed worker must leave a signal, never a fragment."""

from __future__ import annotations

import pytest
from ingest_ledger.extract import _diagnose, run
from ingest_ledger.manifest import walk
from ingest_ledger.models import Status
from ingest_ledger.reconcile import reconcile


def test_memory_cap_turns_an_oom_into_a_failed_status(fixture_path, oom_cap_mb):
    """The podcast's failure: the parse dies, the pipeline reports success.

    Under the cap this must surface as FAILED with a memory diagnosis -- never
    as PARTIAL with whatever happened to be parsed before the kill.

    Skipped where the platform cannot enforce a cap, because there is then no OOM
    to detect. The skip is gated on **what the run actually reported**, not on a
    `sys.platform` guess -- so it stays correct if a future OS gains or loses the
    capability, and the skip reason names the real reason rather than "macOS".
    """
    (entry,) = list(walk(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=oom_cap_mb, timeout_s=120)

    cap = extracted.evidence.get("memory_cap", "unknown")
    if cap != "rlimit_as":
        pytest.skip(f"this platform cannot enforce a memory cap ({cap})")

    row = reconcile(entry, extracted)
    assert row.status is Status.FAILED
    assert "memory" in (row.extracted.error or "").lower()
    assert row.extracted.units == 0


def test_streaming_probe_survives_a_cap_that_kills_an_eager_one(fixture_path):
    """The counterpart: our XML probe streams, so a generous cap is enough.

    Unlike the test above, this one holds on every platform: with a cap it must
    not trip it, and without one it must still read the file correctly. What it
    must never do is fail because the *cap itself* could not be applied.
    """
    (entry,) = list(walk(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=512, timeout_s=180)

    assert extracted.error is None
    assert extracted.units == entry.declared.units


def test_whether_the_memory_cap_was_enforced_is_recorded(fixture_path):
    """The failure this tool exists to prevent, found in the tool itself.

    `RLIMIT_AS` is not settable everywhere -- macOS aliases it to `RLIMIT_RSS`
    and rejects any finite value with EINVAL. The worker used to call
    `setrlimit` unconditionally, so on those platforms it died before opening
    the file and *every* subprocess extraction returned "exit 1: ValueError:
    current limit exceeds maximum limit".

    Two things were wrong with that, and the second is the worse one. The
    extraction path was broken, and the evidence still said `memory_cap_mb: 512`
    as though a cap had been applied. A tool whose whole thesis is "do not report
    a status the probe did not earn" was doing exactly that about itself.

    So the cap is now best-effort and **the outcome is recorded**: either it was
    applied, or the evidence says it could not be (CONVENTIONS rules 2 and 5).
    """
    (entry,) = list(walk(fixture_path("oversized.xml")))
    extracted = run(entry, memory_mb=512, timeout_s=180)

    cap = extracted.evidence.get("memory_cap")
    assert cap is not None, "a run must always say whether its memory cap was applied"
    assert cap == "rlimit_as" or cap.startswith("unenforced:"), cap

    # And an unenforceable cap must never be the reason a run failed.
    assert "current limit exceeds maximum limit" not in (extracted.error or "")


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
