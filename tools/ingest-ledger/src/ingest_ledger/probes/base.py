"""The probe protocol.

A probe knows one format. It must be able to answer "how many units are in
here?" without extracting content -- that is the independence the reconciler
depends on.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ingest_ledger.models import Declared, Extracted


class ProbeUnavailable(RuntimeError):
    """Raised when a probe's optional dependency is not installed."""


@runtime_checkable
class Probe(Protocol):
    #: Lowercased suffixes this probe claims, e.g. ``(".xlsx", ".xlsm")``.
    suffixes: tuple[str, ...]
    #: Short stable identifier recorded in the ledger as evidence.
    name: str

    def declare(self, path: Path) -> Declared:
        """Count units from structure alone. Must not extract content."""
        ...

    def extract(self, path: Path) -> Extracted:
        """Recover content, reporting which declared units did not come back."""
        ...
