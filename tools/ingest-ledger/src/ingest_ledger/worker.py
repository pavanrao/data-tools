"""Extraction subprocess.

Run as ``python -m ingest_ledger.worker <path>``; prints one JSON object.

Extraction happens here, in its own process under its own resource limits, so
that the failure mode the podcast describes -- the OOM killer taking the parse
while the pipeline reports success -- becomes an exit code the parent can see.
"""

from __future__ import annotations

import json
import resource
import sys
from pathlib import Path


def _apply_limits(memory_mb: int) -> None:
    limit = memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def main(argv: list[str]) -> int:
    path = Path(argv[0])
    _apply_limits(int(argv[1]))

    from ingest_ledger.probes import for_path

    probe = for_path(path)
    if probe is None:
        json.dump({"error": "no probe"}, sys.stdout)
        return 3

    result = probe.extract(path)
    json.dump(
        {
            "units": result.units,
            "text": result.text,
            "missing": list(result.missing),
            "evidence": result.evidence,
            "error": result.error,
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
