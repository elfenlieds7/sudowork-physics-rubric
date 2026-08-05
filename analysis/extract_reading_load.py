"""Extract per-question character count (阅读量) from 7 试卷 PDFs.

Uses pymupdf to get all text per PDF · then regex-splits by question header
patterns like '1.' '2.' etc. Outputs per (paper, question_id, char_count).

杨老师 23:26 观察: 北京高考控制在 4400 字左右 · 老师命题往往超标 · 文字量
越多难度越大. 加为 rubric 新维度 · 检验独立信号强度.
"""
import re
import sys
from pathlib import Path
import fitz  # pymupdf

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
PDF_DIR = REPO / "data" / "source_pdfs"

PAPERS = {
    "gaokao_2022": "gaokao_2022.pdf",
    "gaokao_2023": "gaokao_2023.pdf",
    "gaokao_2024": "gaokao_2024_physics.pdf",
    "gaokao_2025": "gaokao_2025_physics.pdf",
    "xicheng_2024": "xicheng_2024_yimo.pdf",
    "xicheng_2025": "xicheng_2025_yimo.pdf",
    "xicheng_2026": "xicheng_2026_yimo.pdf",
}


def extract_text(pdf_path):
    doc = fitz.open(str(pdf_path))
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts)


def split_by_questions(text, max_q=25):
    """Split text into per-question chunks by finding question headers.

    Question headers look like: '1.' '2.' at start of line · but not '(1)' '(2)'.
    """
    # First, cut anything before "本部分共14题" or "第一部分" if present
    m = re.search(r'第一部分', text)
    if m:
        text = text[m.start():]
    # Also cut after 答案 · 参考答案 · 解析
    for marker in ['参考答案', '答案与解析', '试题答案', '答案：']:
        m = re.search(marker, text)
        if m:
            text = text[:m.start()]
            break

    # Find all question starts · pattern: newline + digit + period + space, at start of line
    # Match "1." "2." ... "20." at line-start (or after whitespace)
    # Exclude sub-question numbers like "1.1" or "1.2"
    boundaries = []
    for m in re.finditer(r'(?:^|\n)\s*(\d+)[．.\s]', text):
        qnum = int(m.group(1))
        if 1 <= qnum <= max_q:
            boundaries.append((qnum, m.start()))

    # Deduplicate on qnum first-seen; sort by position
    seen = {}
    for qnum, pos in boundaries:
        if qnum not in seen:
            seen[qnum] = pos
    ordered = sorted(seen.items(), key=lambda kv: kv[1])

    chunks = {}
    for i, (qnum, pos) in enumerate(ordered):
        end = ordered[i+1][1] if i + 1 < len(ordered) else len(text)
        chunks[qnum] = text[pos:end]
    return chunks


def count_chars(chunk):
    """Character count excluding whitespace + typical numbering."""
    # Remove whitespace and section headers
    cleaned = re.sub(r'\s+', '', chunk)
    # Remove header line (first "N." pattern)
    return len(cleaned)


def main():
    print(f"{'paper':<15} {'q_num':>5} {'chars':>7}")
    print("-" * 32)
    all_rows = []
    for paper, filename in PAPERS.items():
        pdf_path = PDF_DIR / filename
        if not pdf_path.exists():
            print(f"MISSING: {pdf_path}")
            continue
        text = extract_text(pdf_path)
        chunks = split_by_questions(text)
        for qnum in sorted(chunks):
            n = count_chars(chunks[qnum])
            print(f"{paper:<15} {qnum:>5} {n:>7}")
            all_rows.append({'paper': paper, 'qnum': qnum, 'chars': n})
        total = sum(count_chars(c) for c in chunks.values())
        print(f"{paper} TOTAL: {total} chars")
        print()

    # Save
    import csv
    out = REPO / 'data' / 'labeled' / 'reading_load_per_question.csv'
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['paper', 'qnum', 'chars'])
        w.writeheader()
        w.writerows(all_rows)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
