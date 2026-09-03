"""The ``dt`` meta-CLI: uses the collection as a whole.

Tools are discovered through the ``data_tools.tools`` entry-point group, so
``dt`` knows about exactly the tools that are installed — nothing is hardcoded
and no tool is imported until it is actually invoked.
"""

from __future__ import annotations

import sys
from importlib.metadata import entry_points


def discover() -> dict[str, object]:
    """Map tool name -> entry point, for every installed data-tools tool."""
    return {ep.name: ep for ep in entry_points(group="data_tools.tools")}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    tools = discover()

    if not argv or argv[0] in {"ls", "-h", "--help"}:
        if not tools:
            print("no data-tools tools installed; try `uv sync` at the repo root")
            return 1
        print("installed tools:\n")
        for name, ep in sorted(tools.items()):
            summary = (ep.load().__doc__ or "").strip().splitlines()
            print(f"  {name:<20} {summary[0] if summary else ''}")
        print("\nrun one with:  dt <tool> [args...]")
        return 0

    name, *rest = argv
    if name not in tools:
        print(f"unknown tool {name!r}; `dt ls` lists what is installed", file=sys.stderr)
        return 2

    # Hand off argv as though the tool's own console script had been invoked.
    sys.argv = [name, *rest]
    return int(tools[name].load()() or 0)
