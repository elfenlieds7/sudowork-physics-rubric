"""Select 20 items for v2.1 inter-rater calibration study.

Strategy: stratified by concept_count (1-5, 4 items each) · topic diverse ·
mix of question_type · shuffled for blind rating.
"""
import csv
import sys
from pathlib import Path
import random
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

CSV = Path(__file__).resolve().parent.parent / "data" / "labeled" / "v2_1_labels.csv"
OUT = Path(__file__).resolve().parent.parent / "data" / "labeled" / "v2_calibration_20_items.csv"

random.seed(20260808)


def main():
    rows = []
    with open(CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)

    by_concept = defaultdict(list)
    for r in rows:
        by_concept[int(r['concept_count'])].append(r)

    print("Concept dist in v2.1 pool:")
    for c in sorted(by_concept):
        n = len(by_concept[c])
        n_mech = sum(1 for r in by_concept[c] if r['topic']=='mech')
        n_em = sum(1 for r in by_concept[c] if r['topic']=='em')
        n_therm = sum(1 for r in by_concept[c] if r['topic']=='thermal')
        n_cross = sum(1 for r in by_concept[c] if r['topic']=='cross')
        print(f"  concept={c}: n={n} · mech={n_mech} em={n_em} therm={n_therm} cross={n_cross}")

    # Adaptive sampling: v2.1 no concept=5 items · take 5 per concept from 1-4
    plan = {1: 5, 2: 5, 3: 5, 4: 5}  # total 20
    selected = []
    for c, want in plan.items():
        pool = by_concept[c]
        if not pool:
            continue
        # Prefer topic diversity
        buckets = {
            'mech': [r for r in pool if r['topic']=='mech'],
            'em':   [r for r in pool if r['topic']=='em'],
            'therm':[r for r in pool if r['topic']=='thermal'],
            'cross':[r for r in pool if r['topic']=='cross'],
        }
        picks = []
        for b in buckets.values():
            if b:
                sample_n = min(len(b), 1)
                picks.extend(random.sample(b, sample_n))
        # Fill remainder
        remaining = [r for r in pool if r not in picks]
        random.shuffle(remaining)
        picks.extend(remaining[:want - len(picks)])
        picks = picks[:want]
        selected.extend(picks)

    # Shuffle final order (blind for teacher)
    random.shuffle(selected)

    print(f"\nSelected {len(selected)} items · shuffled for blind rating:\n")
    print(f"{'idx':>3} {'paper':<15} {'qid':<8} {'concept':>7} {'topic':<8} {'qt':<6}")
    for i, r in enumerate(selected, 1):
        print(f"{i:>3} {r['paper_id']:<15} {r['question_id']:<8} {r['concept_count']:>7} {r['topic']:<8} {r['question_type']:<6}")

    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ['blind_idx'])
        w.writeheader()
        for i, r in enumerate(selected, 1):
            row = dict(r)
            row['blind_idx'] = i
            w.writerow(row)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
