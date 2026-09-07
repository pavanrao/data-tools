"""Compare chunking strategies on one corpus, and recommend one.

Chunkers return *spans*, not strings, so every chunk is addressable back into the
document it came from -- which is what makes character-level Precision Omega and
IoU computable at all. See this tool's README for the research behind that
choice, the decisions taken, and what is not yet built.
"""

from chunking_lab.chunkers import from_spec
from chunking_lab.invariant import InvariantViolation, check, coverage
from chunking_lab.spans import Chunking, Span

__all__ = [
    "Chunking",
    "InvariantViolation",
    "Span",
    "check",
    "coverage",
    "from_spec",
]
