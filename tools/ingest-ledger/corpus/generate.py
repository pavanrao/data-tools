#!/usr/bin/env python3
"""Generate the hostile corpus.

Every fixture here is a document that a naive pipeline reads *successfully* and
gets wrong. They are generated rather than committed so the repo stays free of
binaries and so each one's defect is described in code instead of folklore.

    python corpus/generate.py corpus/hostile
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

#: fixture name -> what a naive extractor does wrong with it
DEFECTS = {
    "multi_sheet.xlsx": "data on sheets 2 and 4; naive readers take the active sheet only",
    "textbox_footnote.docx": "body text plus a footnote part that body walkers skip",
    "oversized.xml": "large enough to trip a 512MB cap mid-parse",
    "nested.zip": "an archive inside an archive",
    "bom_mixed.csv": "utf-8 BOM plus a latin-1 byte that breaks strict decoding",
    "liar.pdf": "HTML content behind a .pdf extension",
    "scanned.pdf": "image-only page, no text layer (requires pymupdf)",
    "whitebox.pdf": "text hidden under a white rectangle (requires pymupdf)",
}


def multi_sheet_xlsx(path: Path) -> bool:
    try:
        import openpyxl
    except ImportError:
        return False
    book = openpyxl.Workbook()
    book.active.title = "Cover"
    book["Cover"]["A1"] = "Request for Proposal - cover sheet"
    for name, rows in (("Rates", 12), ("Notes", 0), ("Appendix C", 40)):
        sheet = book.create_sheet(name)
        for i in range(1, rows + 1):
            sheet.cell(row=i, column=1, value=f"{name} line {i}")
            sheet.cell(row=i, column=2, value=i * 100)
    book.save(path)
    return True


def textbox_footnote_docx(path: Path) -> bool:
    def para(text: str) -> str:
        return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"

    document = (
        f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>'
        + "".join(para(f"Body paragraph {i}") for i in range(1, 9))
        + "</w:body></w:document>"
    )
    footnotes = (
        f'<?xml version="1.0" encoding="UTF-8"?><w:footnotes xmlns:w="{W}">'
        + "".join(
            f'<w:footnote w:id="{i}">{para(f"Footnote {i}: the caveat that matters")}</w:footnote>'
            for i in range(1, 4)
        )
        + "</w:footnotes>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/></Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/footnotes.xml", footnotes)
    return True


def oversized_xml(path: Path, *, records: int = 240_000) -> bool:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("<schedule>")
        for i in range(records):
            handle.write(
                f"<item id='{i}'><code>LINE-{i:06d}</code>"
                f"<description>Schedule of values row {i}, padded to make the "
                f"document large enough to matter when parsed eagerly.</description>"
                f"<amount>{i * 37}</amount></item>"
            )
        handle.write("</schedule>")
    return True


def nested_zip(path: Path) -> bool:
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("buried/terms.txt", "\n".join(f"Clause {i}" for i in range(1, 31)))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("readme.txt", "see the inner archive")
        archive.writestr("inner.zip", inner.getvalue())
    return True


def bom_mixed_csv(path: Path) -> bool:
    body = "id,vendor,amount\n1,Acme,100\n2,Caf\xe9 Ltd,250\n3,Zeta,900\n"
    path.write_bytes(b"\xef\xbb\xbf" + body.encode("latin-1"))
    return True


def liar_pdf(path: Path) -> bool:
    path.write_bytes(b"<html><body><h1>Not a PDF</h1><p>Amount due: 4200</p></body></html>")
    return True


def scanned_pdf(path: Path) -> bool:
    try:
        import fitz
    except ImportError:
        return False
    doc = fitz.open()
    for _ in range(3):
        page = doc.new_page()
        # A page whose only content is a raster: extraction yields "".
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 400, 200))
        pix.clear_with(220)
        page.insert_image(fitz.Rect(50, 50, 450, 250), pixmap=pix)
    doc.save(path)
    doc.close()
    return True


def whitebox_pdf(path: Path) -> bool:
    try:
        import fitz
    except ImportError:
        return False
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 120), "Public: contract awarded to vendor A.")
    page.insert_text((72, 160), "SECRET: internal margin is 42 percent.")
    # The desktop-publishing "redaction": cover it, do not remove it.
    page.draw_rect(fitz.Rect(60, 145, 520, 175), color=(1, 1, 1), fill=(1, 1, 1))
    doc.save(path)
    doc.close()
    return True


BUILDERS = {
    "multi_sheet.xlsx": multi_sheet_xlsx,
    "textbox_footnote.docx": textbox_footnote_docx,
    "oversized.xml": oversized_xml,
    "nested.zip": nested_zip,
    "bom_mixed.csv": bom_mixed_csv,
    "liar.pdf": liar_pdf,
    "scanned.pdf": scanned_pdf,
    "whitebox.pdf": whitebox_pdf,
}


def build(out: Path) -> dict[str, bool]:
    out.mkdir(parents=True, exist_ok=True)
    return {name: builder(out / name) for name, builder in BUILDERS.items()}


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else Path(__file__).parent / "hostile"
    for name, built in build(out).items():
        status = "ok" if built else "skipped (optional dependency missing)"
        print(f"{name:<26} {status:<44} {DEFECTS[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
