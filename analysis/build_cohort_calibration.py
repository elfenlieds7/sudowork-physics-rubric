"""Rebuild cohort_calibration.csv from xlsx files 杨老师 provides.

Reads all `YYYY_beijing_gaokao_rates.xlsx` in data/private/ · extracts
(北京, 西城) rate pairs · handles per-year column-layout drift · writes
canonical cohort_calibration.csv used by fit_cohort_offset.py.

Per-year column layout (0-indexed): (qid_col, beijing_col, xicheng_col).
When 杨老师 sends a new year's xlsx, inspect its header row and add here.
"""
import csv
import sys
from pathlib import Path
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

PRIV = Path(__file__).resolve().parent.parent / "data" / "private"

COL_LAYOUT = {
    2023: (0, 1, 2),  # 题目 · 北京市 · 西城整体
    2024: (0, 1, 2),  # 题目 · 北京市 · 西城分类整体
    2025: (0, 2, 3),  # 题目 · 满分值 · 北京市 · 西城分类整体
}


def extract_year(year):
    path = PRIV / f"{year}_beijing_gaokao_rates.xlsx"
    if not path.exists():
        return []
    if year not in COL_LAYOUT:
        print(f"WARN: {year} xlsx present but no column layout defined; skipping.")
        print(f"      Add {year}: (qid_col, bj_col, xc_col) to COL_LAYOUT and retry.")
        return []
    wb = openpyxl.load_workbook(path, data_only=True)
    sh = wb.active
    header = [c.value for c in sh[1]]
    print(f"  {year}: header = {header}")
    qc, bc, xc = COL_LAYOUT[year]
    out = []
    for row in sh.iter_rows(min_row=2, values_only=True):
        if not row or len(row) <= xc or row[qc] is None:
            continue
        qid = str(row[qc]).strip()
        try:
            bj = float(row[bc])
            x = float(row[xc])
        except (TypeError, ValueError):
            continue
        out.append({'paper': f'gaokao_{year}', 'qid': qid, 'bj': bj, 'xc': x})
    return out


def main():
    all_pairs = []
    for year in sorted(COL_LAYOUT.keys()):
        pairs = extract_year(year)
        print(f"  → {len(pairs)} pairs from {year}")
        all_pairs.extend(pairs)

    if not all_pairs:
        print("No pairs extracted. Check xlsx paths in data/private/.")
        return

    out = PRIV / "cohort_calibration.csv"
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['paper_id', 'question_id', 'xicheng_rate', 'beijing_rate', 'offset_pp', 'notes'])
        for p in all_pairs:
            w.writerow([p['paper'], p['qid'], p['xc'], p['bj'],
                        f'{(p["xc"]-p["bj"])*100:+.2f}', ''])
    print(f"\nWrote {len(all_pairs)} pairs to {out.name}")
    print("Next: run `python analysis/fit_cohort_offset.py` to refit models.")


if __name__ == "__main__":
    main()
