"""Allow `python -m kimball_lab` when the scripts directory is not on PATH."""

from .cli import main

raise SystemExit(main())
