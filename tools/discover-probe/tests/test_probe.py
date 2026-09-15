"""Probing real servers over a real wire. Model-free and network-free."""

from __future__ import annotations

import anyio
from discover_probe.probe import probe


def run(opener, **kwargs):
    return anyio.run(lambda: probe(opener, target="test", **kwargs))


def check(report, name):
    return next(c for c in report.checks if c.name == name)


def test_a_server_that_speaks_both_eras_is_classified_both(both_eras):
    report = run(both_eras)

    assert report.era == "both"
    assert check(report, "discover").verdict == "pass"
    assert "2026-07-28" in check(report, "discover").evidence
    assert check(report, "handshake").verdict == "pass"


def test_rejecting_discover_makes_a_server_legacy_only_and_says_why(legacy_only):
    report = run(legacy_only)

    assert report.era == "legacy-only"
    # The server answered and said no. That must stay distinct from silence, or
    # the era verdict is built on a guess.
    assert report.discover.status == "rejected"
    assert check(report, "discover").verdict == "fail"
    assert check(report, "discover").evidence.startswith("rejected:")
    assert "-32601" in check(report, "discover").evidence
    assert check(report, "handshake").verdict == "pass"


def test_advertised_listings_are_actually_called_not_just_believed(both_eras):
    report = run(both_eras)

    lists = check(report, "claims-modern")
    assert lists.verdict == "pass"
    assert "tools 1" in lists.evidence


def test_a_refused_connection_is_unreachable_not_a_verdict_about_the_protocol(
    refuses_to_connect,
):
    report = run(refuses_to_connect)

    assert report.era == "unreachable"
    assert report.discover.status == "unreachable"
    assert "nothing listening" in check(report, "discover").evidence


def test_a_server_that_goes_silent_times_out_instead_of_hanging_the_probe(never_answers):
    report = run(never_answers, timeout=0.5)

    assert report.era == "unreachable"
    assert "timed out" in check(report, "discover").evidence


def test_a_cold_start_that_times_out_discover_is_retried_once(cold_start):
    report = run(cold_start, timeout=0.5)

    assert report.discover.status == "ok"
    assert report.era == "both"
    # The retry is disclosed, not hidden: a reader can see the first attempt failed.
    assert "retried" in check(report, "discover").evidence


def test_a_server_that_really_never_answers_discover_stays_unreachable(hangs_on_discover):
    # The retry must not launder real silence into a pass.
    report = run(hangs_on_discover, timeout=0.5)

    assert report.discover.status == "unreachable"
    assert report.era == "legacy-only"
    assert "both attempts" in check(report, "discover").evidence
