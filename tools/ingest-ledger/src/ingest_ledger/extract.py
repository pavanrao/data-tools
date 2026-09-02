"""Run extraction under supervision.

The point of the subprocess is not speed -- it is that a killed extraction
leaves a signal. In-process, an OOM either takes the whole run down or, worse,
the extractor catches it and returns a fragment that looks like success. Out of
process we get an exit code, and a fragment becomes a measurable shortfall
against the manifest.
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
    limits = {"memory_cap_mb": memory_mb, "timeout_s": timeout_s}
    argv = [sys.executable, "-m", "ingest_ledger.worker", str(entry.path), str(memory_mb)]

    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            argv, capture_output=True, timeout=timeout_s, check=False
        )
    except subprocess.TimeoutExpired:
        return Extracted(
            0,
            evidence={**limits, "auditor": "subprocess"},
            error=f"timed out after {timeout_s}s",
        )

    if proc.returncode != 0:
        return Extracted(
            0,
            evidence={**limits, "auditor": "subprocess", "exit_code": proc.returncode},
            error=_diagnose(proc.returncode, proc.stderr.decode(errors="replace")),
        )

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        # A worker that exits 0 with unreadable output is still a failure --
        # treating it as empty would be the silent behaviour we exist to stop.
        return Extracted(
            0,
            evidence={**limits, "auditor": "subprocess"},
            error="worker produced unreadable output",
        )

    return Extracted(
        units=payload["units"],
        text=payload["text"],
        missing=tuple(payload["missing"]),
        evidence={**payload["evidence"], **limits},
        error=payload["error"],
    )


def _diagnose(code: int, stderr: str) -> str:
    """Turn an exit code into something a human can act on."""
    if code in (-9, 137):
        return "killed (SIGKILL) - out of memory"
    if "MemoryError" in stderr:
        return "MemoryError - exceeded the configured memory cap"
    if "ProbeUnavailable" in stderr:
        return "probe dependency not installed"
    tail = [line for line in stderr.strip().splitlines() if line.strip()]
    return f"exit {code}: {tail[-1] if tail else 'no stderr'}"
