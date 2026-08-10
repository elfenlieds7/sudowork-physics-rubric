"""Build v2.2 calibration csv (20 items) by joining v2_2_labels + blind_idx from v2.1 calibration."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V21_CAL = ROOT / "data" / "labeled" / "v2_calibration_20_items.csv"
V22_LABELS = ROOT / "data" / "labeled" / "v2_2_labels.csv"
OUT = ROOT / "data" / "labeled" / "v2_2_calibration_20_items.csv"


def main():
    with open(V21_CAL, encoding="utf-8") as f:
        cal_rows = list(csv.DictReader(f))
    with open(V22_LABELS, encoding="utf-8") as f:
        v22 = {(r["paper_id"], r["question_id"]): r for r in csv.DictReader(f)}

    out_rows = []
    for r in cal_rows:
        key = (r["paper_id"], r["question_id"])
        if key not in v22:
            print(f"MISSING v2.2 label for {key}")
            continue
        new = dict(v22[key])
        new["blind_idx"] = r["blind_idx"]
        out_rows.append(new)

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cal_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
