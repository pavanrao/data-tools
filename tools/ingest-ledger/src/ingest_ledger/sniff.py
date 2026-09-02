"""Detect what a file actually is, independent of what it is named.

A probe is chosen by suffix, so a file whose extension lies gets handed to the
wrong probe. Some probes are forgiving enough to return *something* -- which is
the worst outcome, because plausible content is what makes a failure silent.

We compare the claimed family against the one in the leading bytes and refuse
to probe a mismatch.
"""

from __future__ import annotations

from pathlib import Path

#: Coarse families. Finer distinctions (xlsx vs docx) live in the probes; here
#: we only need enough to catch a file pretending to be a different kind.
PDF = "pdf"
ZIP = "zip"  # covers OOXML, which is a zip container
XML = "xml"
HTML = "html"
TEXT = "text"

_SUFFIX_FAMILY = {
    ".pdf": PDF,
    ".xlsx": ZIP,
    ".xlsm": ZIP,
    ".docx": ZIP,
    ".zip": ZIP,
    ".xml": XML,
    ".csv": TEXT,
    ".tsv": TEXT,
    ".txt": TEXT,
    ".md": TEXT,
    ".log": TEXT,
}


def actual_family(path: Path) -> str:
    head = path.read_bytes()[:1024]
    if head.startswith(b"%PDF-"):
        return PDF
    if head.startswith(b"PK\x03\x04"):
        return ZIP
    stripped = head.lstrip().lower()
    if stripped.startswith((b"<!doctype html", b"<html")):
        return HTML
    if stripped.startswith(b"<?xml") or stripped.startswith(b"<"):
        return XML
    return TEXT


def mismatch(path: Path) -> str | None:
    """Return a human-readable reason when name and content disagree."""
    claimed = _SUFFIX_FAMILY.get(path.suffix.lower())
    if claimed is None:
        return None
    actual = actual_family(path)
    if claimed == actual:
        return None
    # Text is the fallback bucket; a text-shaped file under a text-ish suffix
    # is not a lie, and XML content under a .txt name is not worth flagging.
    if claimed == TEXT and actual in {TEXT, XML, HTML}:
        return None
    return f"extension claims {claimed}, content is {actual}"
