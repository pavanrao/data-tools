"""Judgement, tested as pure logic over hand-built outcomes."""

from __future__ import annotations

from discover_probe.probe import PathOutcome, build_checks


def check(checks, name):
    return next(c for c in checks if c.name == name)


def ok(**kwargs):
    return PathOutcome(status="ok", **kwargs)


def test_eras_disagreeing_about_capabilities_is_a_note_not_a_failure():
    # The SDK's own server does exactly this, correctly: change notification
    # works through subscriptions/listen in the modern era only.
    modern = ok(capabilities={"tools": {"list_changed": True}})
    legacy = ok(capabilities={"tools": {"list_changed": False}})

    result = check(build_checks(modern, legacy), "capabilities-by-era")

    assert result.verdict == "note"
    assert "list_changed" in result.evidence


def test_identical_capabilities_in_both_eras_pass():
    caps = {"tools": {"list_changed": False}}

    assert (
        check(
            build_checks(ok(capabilities=caps), ok(capabilities=caps)), "capabilities-by-era"
        ).verdict
        == "pass"
    )


def test_a_listing_that_errors_fails_the_claim_and_names_which():
    modern = ok(
        capabilities={"tools": {}, "prompts": {}},
        listings={"tools": "2", "prompts": "error: MCPError: boom"},
    )

    result = check(build_checks(modern, PathOutcome(status="rejected", error="x")), "claims-modern")

    assert result.verdict == "fail"
    assert "prompts error" in result.evidence


def test_an_empty_listing_is_honest_not_a_false_claim():
    modern = ok(capabilities={"resources": {}}, listings={"resources": "0"})

    assert (
        check(build_checks(modern, PathOutcome(status="rejected")), "claims-modern").verdict
        == "pass"
    )


def test_claims_for_a_path_that_never_connected_are_skipped_not_failed():
    result = check(
        build_checks(PathOutcome(status="unreachable", error="x"), ok()), "claims-modern"
    )

    assert result.verdict == "skip"


def test_advertising_logging_is_noted_as_deprecated_naming_the_era():
    legacy = ok(capabilities={"logging": {}})

    result = check(build_checks(PathOutcome(status="rejected"), legacy), "deprecated-logging")

    assert result.verdict == "note"
    assert "legacy" in result.evidence


def test_no_logging_capability_passes_the_deprecation_check():
    assert check(build_checks(ok(), ok()), "deprecated-logging").verdict == "pass"


def test_an_absent_capability_and_an_empty_one_are_the_same_thing():
    # Found probing sqlite-mcp: one era omits `experimental`, the other sends {}.
    # Reporting that as a difference would put noise on every server's report.
    modern = ok(capabilities={"tools": {}})
    legacy = ok(capabilities={"tools": {}, "experimental": {}})

    assert check(build_checks(modern, legacy), "capabilities-by-era").verdict == "pass"
