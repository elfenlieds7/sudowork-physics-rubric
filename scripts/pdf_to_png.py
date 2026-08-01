"""Render all PDFs in data/source_pdfs/ to PNGs in data/extracted_pages/.

Requires pymupdf (pip install pymupdf).

Usage:
    python scripts/pdf_to_png.py
"""
import fitz  # pymupdf
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "data" / "source_pdfs"
OUT_DIR = REPO_ROOT / "data" / "extracted_pages"

# Rendering matrix — 1.7 ≈ 150 DPI, good balance of quality vs file size for visual reading
RENDER_MATRIX = fitz.Matrix(1.7, 1.7)


def render_pdf(pdf_path: Path, out_dir: Path) -> int:
    """Render a PDF's pages to <tag>_pNN.png files. Returns page count."""
    tag = pdf_path.stem
    doc = fitz.open(str(pdf_path))
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=RENDER_MATRIX)
        (out_dir / f"{tag}_p{i:02d}.png").write_bytes(pix.tobytes("png"))
    n = len(doc)
    doc.close()
    return n


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {SOURCE_DIR}"); return
    print(f"Rendering {len(pdfs)} PDFs to {OUT_DIR}\n")
    total = 0
    for pdf in pdfs:
        n = render_pdf(pdf, OUT_DIR)
        total += n
        print(f"  {pdf.name:<50} -> {n:>3} pages")
    print(f"\n{len(pdfs)} PDFs · {total} pages · done.")


if __name__ == "__main__":
    main()
