"""Apply v2.2 mechanical relabel to v2.1 labels.

v2.2 rules (from 08-09 kappa study + 杨老师 14:15/14:20 clarifications):

1. Systematic bias correction (kappa study found smart agent 系统性打高 1 档 · 11/11-12/12):
   - modeling:    -1 shift (floor at 0)
   - reasoning:   -1 shift (floor at 1)
   - computation: -1 shift (floor at 0)

2. Openness rule (杨老师 14:15):
   - Default 'closed' (北京高考物理 > 98% closed)
   - Known exceptions: gaokao_2025 Q19-3, Q20-3 (设计方案 type)
   - All xicheng items: closed (teacher only cited 2026 gaokao Q19)

3. concept_count:
   - Teacher's rule (14:20): merge algebraic variants of same physical law → 1 knowledge point
   - Conservative mechanical: for values ≥ 4, downshift by 1 (assume variant-splitting inflation)
   - Values 1-3 kept as-is (kappa evidence is nuanced · fresh review deferred if needed)
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "labeled" / "v2_1_labels.csv"
OUT = ROOT / "data" / "labeled" / "v2_2_labels.csv"

OPENNESS_EXCEPTIONS = {
    ("gaokao_2025", "Q19-3"): "open",
    ("gaokao_2025", "Q20-3"): "open",
}


def relabel_row(row):
    r = dict(row)
    # 1. Systematic downshift
    r["modeling"] = str(max(0, int(row["modeling"]) - 1))
    r["reasoning"] = str(max(1, int(row["reasoning"]) - 1))
    r["computation"] = str(max(0, int(row["computation"]) - 1))
    # 2. Openness
    key = (row["paper_id"], f'Q{row["question_id"]}')
    r["openness"] = OPENNESS_EXCEPTIONS.get(key, "closed")
    # 3. concept_count conservative shift (only 4+)
    cc = int(row["concept_count"])
    if cc >= 4:
        r["concept_count"] = str(cc - 1)
    return r


def main():
    with open(SRC, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())
    new_rows = [relabel_row(r) for r in rows]

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(new_rows)

    # Diff summary
    from collections import Counter
    for dim in ("modeling", "reasoning", "computation", "concept_count", "openness"):
        old = Counter(r[dim] for r in rows)
        new = Counter(r[dim] for r in new_rows)
        changed = sum(1 for a, b in zip(rows, new_rows) if a[dim] != b[dim])
        print(f"{dim:15} {changed:>3}/223 changed  old={dict(sorted(old.items()))}  new={dict(sorted(new.items()))}")

    print(f"\nWrote: {OUT}")


if __name__ == "__main__":
    main()
