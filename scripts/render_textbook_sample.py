"""Render selected textbook pages for visual spot-check of the 典型模型 catalog.

Only renders specific pages (not full 786-page book) to keep disk usage sane.
Output: data/reference/textbook_samples/<tag>_p<NN>.png (gitignored)
"""
import fitz
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXTBOOK_PATH = REPO_ROOT / "data" / "source_pdfs" / "renjiao_2019_textbook_6books.pdf"
OUT_DIR = REPO_ROOT / "data" / "reference" / "textbook_samples"

# Sample pages per chapter (start-of-chapter + 例题 pages if known)
# Refer to data/reference/textbook_toc.md for chapter start pages
SAMPLES = [
    # (page_number, tag) — page number is 1-indexed in the PDF
    (61, "必修1_ch3_相互作用力_start"),
    (87, "必修1_ch4_运动和力_start"),
    (161, "必修2_ch6_圆周运动_start"),
    (212, "必修2_ch8_机械能守恒_start"),
    (356, "必修3_ch13_电磁感应_start"),
    (427, "选修1_ch2_机械振动_start"),
    (457, "选修1_ch3_机械波_start"),
    (549, "选修2_ch2_电磁感应_start"),
    (748, "选修3_ch5_原子核_start"),
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not TEXTBOOK_PATH.exists():
        print(f"MISSING: {TEXTBOOK_PATH}")
        print("Re-obtain textbook PDF from teacher wechat (see open_questions.md #4).")
        return
    doc = fitz.open(str(TEXTBOOK_PATH))
    mat = fitz.Matrix(1.7, 1.7)  # ~150 DPI
    for page_no, tag in SAMPLES:
        if page_no > len(doc):
            print(f"skip {tag} (page {page_no} exceeds {len(doc)})")
            continue
        page = doc[page_no - 1]
        pix = page.get_pixmap(matrix=mat)
        out = OUT_DIR / f"p{page_no:03d}_{tag}.png"
        pix.save(str(out))
        print(f"  {tag:<40} p{page_no} -> {out.name}")
    doc.close()
    print(f"\n{len(SAMPLES)} sample pages rendered to {OUT_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
