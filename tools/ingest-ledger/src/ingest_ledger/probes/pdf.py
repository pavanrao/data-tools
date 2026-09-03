"""PDF probe -- the only module in this package that knows pdfmux exists.

pdfmux answers a question we do not want to reimplement: *fidelity* -- given
this source and this extractor output, which pages held text that the engine
dropped while reporting success? We extract, hand it our per-page output, and
record its verdict.

It is not, however, the same question this tool asks. pdfmux compares extracted
text against the source text layer, so a scanned page with no text layer at all
reconciles as PASS at coverage 1.00: nothing was dropped, because there was
nothing to drop. Measured against the page count, that same file yielded zero
content -- which is exactly the gap a downstream index would inherit silently.

So we ask about *yield* and pdfmux answers about *fidelity*, and a page is
missing if either says so. Its verdict is evidence in the ledger, never the
status itself.
"""

from __future__ import annotations

from pathlib import Path

from data_tools_core.provenance import UnitKind

from ingest_ledger.models import Declared, Extracted
from ingest_ledger.probes.base import ProbeUnavailable

#: Pinned; see pyproject `[pdf]` extra. Confined entirely to this module.
PDFMUX_PIN = "pdfmux==1.8.7"


def _pymupdf():
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - exercised via extras matrix
        raise ProbeUnavailable("install data-tools-ingest-ledger[pdf]") from exc
    return pymupdf


class PdfProbe:
    suffixes = (".pdf",)
    name = "pdf"

    def declare(self, path: Path) -> Declared:
        """Page count from the document catalog -- structure only, no text."""
        pymupdf = _pymupdf()
        with pymupdf.open(path) as doc:
            if doc.needs_pass:
                # An encrypted file declares nothing we can verify. Reporting
                # "0 pages" would let it reconcile as EMPTY and pass silently.
                return Declared(0, UnitKind.PAGE, notes=("encrypted",))
            return Declared(
                units=doc.page_count,
                unit_kind=UnitKind.PAGE,
                unit_ids=tuple(range(1, doc.page_count + 1)),
            )

    def extract(self, path: Path) -> Extracted:
        pages, error = self._pages(path)
        if error is not None:
            return Extracted(0, evidence={"auditor": "native-pymupdf"}, error=error)

        # Yield: a page that produced no text did not survive ingestion,
        # whatever the reason -- no text layer, failed OCR, or a dropped page.
        zero_yield = tuple(n for n, text in enumerate(pages, start=1) if not text.strip())
        evidence: dict[str, object] = {"auditor": "native-pymupdf", "zero_yield_pages": zero_yield}

        # Fidelity: pdfmux compares our output against the source text layer.
        fidelity = self._audit(path, pages)
        evidence.update(fidelity)
        dropped = tuple(fidelity.get("pdfmux_silent_drops", ()))

        missing = tuple(sorted(set(zero_yield) | set(dropped)))
        recovered = [text for text in pages if text.strip()]

        return Extracted(
            units=max(len(pages) - len(missing), 0),
            text="\n\n".join(recovered),
            missing=missing,
            evidence=evidence,
        )

    # -- extraction (ours) --------------------------------------------------

    def _pages(self, path: Path) -> tuple[list[str], str | None]:
        pymupdf = _pymupdf()
        with pymupdf.open(path) as doc:
            if doc.needs_pass:
                return [], "password protected"
            return [page.get_text() for page in doc], None

    # -- pdfmux adapter -----------------------------------------------------
    # Signature verified against pdfmux 1.8.7:
    #   verify_extraction(source_pdf, extracted, *, engine=..., fmt=...,
    #                     source_pages=...) -> CertificationManifest
    # `extracted` is required -- pdfmux audits an extraction, it does not
    # perform one. Passing a page-indexed dict gets page_aligned=True.

    def _audit(self, path: Path, pages: list[str]) -> dict[str, object]:
        try:
            import pdfmux
        except ImportError:
            return {"fidelity_audit": "unavailable", "note": f"install {PDFMUX_PIN}"}

        try:
            cert = pdfmux.verify_extraction(
                path,
                {number: text for number, text in enumerate(pages, start=1)},
                engine="ingest-ledger",
            )
        except Exception as exc:  # noqa: BLE001 - an auditor must never end the run
            return {"fidelity_audit": f"error: {type(exc).__name__}: {exc}"}

        return {
            "fidelity_audit": PDFMUX_PIN,
            "pdfmux_verdict": cert.verdict,
            "pdfmux_coverage": round(cert.coverage, 4),
            "pdfmux_silent_drops": tuple(cert.silent_drops),
            "pdfmux_low_confidence_pages": tuple(cert.low_confidence_pages),
        }
