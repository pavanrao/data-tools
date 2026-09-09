"""Allow `python -m sqlite_mcp` when the scripts directory is not on PATH."""

from .cli import main

raise SystemExit(main())
