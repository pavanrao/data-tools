"""Era classification, tested as pure logic.

A server that never answered is not a server that said no. Conflating the two is
the error this module exists to avoid.
"""

from __future__ import annotations

import pytest
from discover_probe.probe import classify_era


@pytest.mark.parametrize(
    ("discover", "handshake", "era"),
    [
        ("ok", "ok", "both"),
        ("ok", "rejected", "modern-only"),
        ("ok", "unreachable", "modern-only"),
        ("rejected", "ok", "legacy-only"),
        ("unreachable", "ok", "legacy-only"),
        ("rejected", "rejected", "neither"),
        ("rejected", "unreachable", "neither"),
        ("unreachable", "unreachable", "unreachable"),
    ],
)
def test_era_follows_from_what_each_path_actually_did(discover, handshake, era):
    assert classify_era(discover, handshake) == era
