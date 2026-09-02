"""Run extraction under supervision.

The point of the subprocess is not speed -- it is that a killed extraction
leaves a signal. In-process, an OOM takes the whole run down or, worse, the
extractor catches it and returns a fragment. Out of process, we get an exit
code, and a fragment becomes a measurable shortfall against the manifest.
"""

from __future__ import annotations

import json
import subprocess
import sys

from ingest_ledger.manifest import ManifestEntry
from ingest_ledger.models import Extracted

DEFAULT_MEMORY_MB = 512
DEFAULT_TIMEOUT_S = 120


def run(
    entry: ManifestEntry,
    *,
    memory_mb: int = DEFAULT_MEMORY_MB,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> Extracted:
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-m", "ingest_ledger.worker", str(entry.path), str(memory_mb)],
        capture_output=True,
        timeout=None,
        check=False,
        **_timeout_kwargs(timeout_s),
    )

    if proc.returncode != 0:
        return Extracted(
            0,
            evidence={"exit_code": proc.returncode, "memory_cap_mb": memory_mb},
            error=_diagnose(proc.returncode, proc.stderr.decode(errors="replace")),
        )

    payload = json.loads(proc.stdout)
    return Extracted(
        units=payload["units"],
        text=payload["text"],
        missing=tuple(payload["missing"]),
        evidence={**payload["evidence"], "memory_cap_mb": memory_mb},
        error=payload["error"],
    )


def _timeout_kwargs(timeout_s: int) -> dict[str, object]:
    return {"timeout": timeout_s}


def _diagnose(code: int, stderr: str) -> str:
    """Turn an exit code into something a human can act on."""
    if code == -9:
        return "killed (SIGKILL) - likely out of memory"
    if "MemoryError" in stderr:
        return "MemoryError - exceeded the configured cap"
    tail = stderr.strip().splitlines()[-1:] or ["no stderr"]
    return f"exit {code}: {tail[0]}"
