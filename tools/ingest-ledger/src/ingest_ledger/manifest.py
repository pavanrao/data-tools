"""Walk the input and declare what is in it -- before anything tries to read it.

Archives are expanded recursively so that a zip inside a zip is not a blind
spot. Every entry gets a content hash, so a later run can tell "this file
changed" from "this file finally extracted".
"""

from __future__ import annotations

import tempfile
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from data_tools_core.provenance import hash_file

from ingest_ledger.models import Declared
from ingest_ledger.probes import ProbeUnavailable, for_path
from ingest_ledger.sniff import mismatch

#: Refuse to follow an archive nested deeper than this. A zip bomb is a silent
#: failure of a different kind.
MAX_ARCHIVE_DEPTH = 4


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    path: Path
    sha256: str
    container_path: tuple[str, ...]
    declared: Declared | None
    probe: str | None
    note: str | None = None


def walk(
    root: Path,
    *,
    workdir: Path | None = None,
    _containers: tuple[str, ...] = (),
) -> Iterator[ManifestEntry]:
    """Yield one entry per leaf file, descending into archives.

    ``workdir`` is where archive members are unpacked. Pass one that outlives
    the iteration if anything downstream needs to re-open an entry: without it
    members are unpacked into a temporary directory that is removed as soon as
    the walk finishes, leaving those paths dangling.
    """
    paths = sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else [root]
    for path in paths:
        if zipfile.is_zipfile(path):
            yield from _walk_archive(path, _containers, workdir)
        else:
            yield _describe(path, _containers)


def _walk_archive(
    path: Path, containers: tuple[str, ...], workdir: Path | None
) -> Iterator[ManifestEntry]:
    if len(containers) >= MAX_ARCHIVE_DEPTH:
        yield ManifestEntry(
            path,
            hash_file(path),
            containers,
            None,
            None,
            note=f"archive nesting exceeds depth {MAX_ARCHIVE_DEPTH}",
        )
        return

    # An OOXML file is a zip. Let its own probe claim it rather than exploding
    # it into XML parts nobody asked for.
    if for_path(path) is not None:
        yield _describe(path, containers)
        return

    inner = containers + (path.name,)
    if workdir is not None:
        target = workdir / "!".join(inner)
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(target)
        yield from walk(target, workdir=workdir, _containers=inner)
        return

    with tempfile.TemporaryDirectory(prefix="ingest-ledger-") as tmp:
        with zipfile.ZipFile(path) as archive:
            archive.extractall(tmp)
        yield from walk(Path(tmp), workdir=None, _containers=inner)


def _describe(path: Path, containers: tuple[str, ...]) -> ManifestEntry:
    # A file whose name disagrees with its bytes is never handed to a probe.
    # Some probes are forgiving enough to return plausible content from the
    # wrong format, and plausible is exactly what makes a failure silent.
    if reason := mismatch(path):
        return ManifestEntry(path, hash_file(path), containers, None, None, note=reason)

    probe = for_path(path)
    if probe is None:
        return ManifestEntry(
            path, hash_file(path), containers, None, None, note="no probe claims this format"
        )
    try:
        declared = probe.declare(path)
    except ProbeUnavailable as exc:
        return ManifestEntry(
            path, hash_file(path), containers, None, probe.name, note=f"probe unavailable: {exc}"
        )
    except Exception as exc:  # noqa: BLE001 - a probe that dies must not end the walk
        return ManifestEntry(
            path,
            hash_file(path),
            containers,
            None,
            probe.name,
            note=f"declare failed: {type(exc).__name__}: {exc}",
        )
    return ManifestEntry(path, hash_file(path), containers, declared, probe.name)
