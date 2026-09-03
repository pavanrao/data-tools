"""Shared contracts for the data-tools collection.

Deliberately dependency-free. Anything that needs a third-party package belongs
in the tool that needs it, not here.
"""

from data_tools_core.provenance import Provenance, UnitKind

__all__ = ["Provenance", "UnitKind"]
