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


def apply_limits(memory_mb: int) -> str:
    """Cap the address space, best-effort, and report what actually happened.

    Not every platform can do this. macOS aliases ``RLIMIT_AS`` to ``RLIMIT_RSS``
    and rejects any finite value with EINVAL -- ``setrlimit`` there raises
    ``ValueError: current limit exceeds maximum limit`` even when the current hard
    limit is infinite, and even when re-setting a limit to the value it already
    has. Nothing about the requested size is wrong; the resource is simply not
    capable.

    This used to raise, which killed the worker before it opened the file and
    made *every* subprocess extraction fail on those platforms. Swallowing it
    silently would be worse: the ledger would record ``memory_cap_mb: 512`` for a
    run that had no cap at all, which is precisely the unearned status this tool
    exists to catch. So the cap is best-effort and the outcome is returned, to be
    recorded alongside the extraction (CONVENTIONS rules 2 and 5).

    Returns ``"rlimit_as"`` when the cap is in force, or ``"unenforced: <why>"``
    when the platform refused it.
    """
    limit = memory_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    except (ValueError, OSError) as exc:
        return f"unenforced: {type(exc).__name__}: {exc}"
    return "rlimit_as"


def main(argv: list[str]) -> int:
    path = Path(argv[0])
    memory_cap = apply_limits(int(argv[1]))

    from ingest_ledger.probes import for_path

    probe = for_path(path)
    if probe is None:
        json.dump({"error": "no probe", "memory_cap": memory_cap}, sys.stdout)
        return 3

    result = probe.extract(path)
    json.dump(
        {
            "units": result.units,
            "text": result.text,
            "missing": list(result.missing),
            "evidence": {**result.evidence, "memory_cap": memory_cap},
            "error": result.error,
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
