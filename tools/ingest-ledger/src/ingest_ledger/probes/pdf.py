"""PDF probe -- the only module in this package that knows pdfmux exists.

Page-level silent-drop detection is a solved problem: pdfmux re-extracts and
aligns against the source to find pages where text exists but the engine
returned nothing while reporting success. We delegate to it rather than
reimplementing it worse.

What we do *not* delegate is the declared count. pdfmux's verdict comes from
re-extraction, so using it for both sides of the reconciliation would collapse
two independent measurements into one system's opinion of itself. ``declare()``
therefore reads the page tree directly and stays ours.
"""

from __future__ import annotations

from pathlib import Path

from data_tools_core.provenance import UnitKind

from ingest_ledger.models import Declared, Extracted
from ingest_ledger.probes.base import ProbeUnavailable


def _fitz():
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - exercised via extras matrix
        raise ProbeUnavailable("install data-tools-ingest-ledger[pdf]") from exc
    return fitz


class PdfProbe:
    suffixes = (".pdf",)
    name = "pdf"

    def declare(self, path: Path) -> Declared:
        """Page count from the document catalog -- structure only, no text."""
        fitz = _fitz()
        with fitz.open(path) as doc:
            if doc.needs_pass:
                # An encrypted file declares nothing we can verify. Saying "0
                # pages" would let it reconcile as EMPTY and pass silently.
                return Declared(0, UnitKind.PAGE, notes=("encrypted",))
            return Declared(
                units=doc.page_count,
                unit_kind=UnitKind.PAGE,
                unit_ids=tuple(range(1, doc.page_count + 1)),
            )

    def extract(self, path: Path) -> Extracted:
        audited = self._extract_with_pdfmux(path)
        return audited if audited is not None else self._extract_native(path)

    # -- pdfmux adapter -----------------------------------------------------
    # Pinned to pdfmux==1.8.7. If upstream changes this signature, this method
    # is the only thing that breaks.
    #
    # TODO(verify): confirm the verify_extraction() signature against the
    # installed wheel before trusting the audited path in CI; until then the
    # native fallback below is what the tests exercise.

    def _extract_with_pdfmux(self, path: Path) -> Extracted | None:
        try:
            import pdfmux
        except ImportError:
            return None

        declared = self.declare(path)
        cert = pdfmux.verify_extraction(path, engine="pdfmux")
        silent_drops = tuple(getattr(cert, "silent_drops", ()) or ())
        coverage = float(getattr(cert, "coverage", 0.0))

        return Extracted(
            units=max(declared.units - len(silent_drops), 0),
            text=getattr(cert, "text", "") or "",
            missing=silent_drops,
            evidence={
                "auditor": "pdfmux==1.8.7",
                "verdict": str(getattr(cert, "verdict", "")),
                "pdfmux_coverage": coverage,
            },
        )

    # -- native fallback ----------------------------------------------------

    def _extract_native(self, path: Path) -> Extracted:
        """Weaker than pdfmux, but never silent about being weaker.

        Counts a page as recovered only if it yields non-whitespace text. A
        scanned page with no text layer is therefore *missing*, not empty --
        which is exactly the failure the naive pipeline swallows.
        """
        fitz = _fitz()
        recovered: list[str] = []
        missing: list[int] = []
        with fitz.open(path) as doc:
            if doc.needs_pass:
                return Extracted(
                    0,
                    evidence={"auditor": "native-pymupdf"},
                    error="password protected",
                )
            for number, page in enumerate(doc, start=1):
                text = page.get_text().strip()
                if text:
                    recovered.append(text)
                else:
                    missing.append(number)

        return Extracted(
            units=len(recovered),
            text="\n\n".join(recovered),
            missing=tuple(missing),
            evidence={
                "auditor": "native-pymupdf",
                "note": "pdfmux not installed; page-level audit is best-effort",
            },
        )
