"""The reconciliation contract.

The whole tool is an argument that these two counts must come from independent
code paths. ``Declared`` is computed by reading structure only -- page trees,
sheet names, archive indexes -- and never by extracting content. ``Extracted``
is whatever the extractor actually recovered. Their disagreement is the signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from data_tools_core.provenance import UnitKind


class Status(StrEnum):
    COMPLETE = "complete"  # every declared unit accounted for
    PARTIAL = "partial"  # some units recovered, some silently missing
    FAILED = "failed"  # extraction raised, timed out, or was killed
    UNSUPPORTED = "unsupported"  # no probe claims this format -- an honest gap
    EMPTY = "empty"  # file declares zero units (may be legitimate)


@dataclass(frozen=True, slots=True)
class Declared:
    """What the file says it contains, read from structure alone."""

    units: int
    unit_kind: UnitKind
    #: Identifiers of the declared units, when cheap to enumerate. Lets the
    #: reconciler report *which* units went missing, not just how many.
    unit_ids: tuple[str | int, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Extracted:
    """What the extractor actually recovered."""

    units: int
    text: str = ""
    missing: tuple[str | int, ...] = ()
    #: Which probe ran and what it observed. Never let a status be unexplained.
    evidence: dict[str, object] = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True, slots=True)
class FileReconciliation:
    """One row of the report."""

    path: Path
    sha256: str
    declared: Declared | None
    extracted: Extracted | None
    status: Status
    coverage: float
    container_path: tuple[str, ...] = ()
    #: Why this file could not be probed, when it could not be.
    note: str | None = None

    @property
    def quarantined(self) -> bool:
        return self.status in {Status.PARTIAL, Status.FAILED, Status.UNSUPPORTED}
