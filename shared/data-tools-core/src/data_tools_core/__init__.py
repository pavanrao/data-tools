"""Shared contracts for the data-tools collection.

Deliberately dependency-free. Anything that needs a third-party package belongs
in the tool that needs it, not here.

The one nuance is :mod:`data_tools_core.llm`, the optional model layer. It is
not imported here and imports its backend lazily, so ``import data_tools_core``
never pulls in a model stack. Reach for it explicitly — ``from
data_tools_core.llm import ChatProvider`` — and install it with the ``llm``
extra.
"""

from data_tools_core.provenance import Provenance, UnitKind

__all__ = ["Provenance", "UnitKind"]
