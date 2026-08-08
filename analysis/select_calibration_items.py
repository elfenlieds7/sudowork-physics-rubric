"""Select 20 items for inter-rater calibration study.

Strategy: stratified by concept (1-5, 4 items each) · topic diverse · mix of
MCQ / 大题小问 / 实验 · shuffled so she doesn't see my grouping.
"""
import csv
import sys
from pathlib import Path
import random
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"

random.seed(20260808)  # deterministic


def main():
    rows = []
    with open(CSV_PATH, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)

    # Group by concept
    by_concept = defaultdict(list)
    for r in rows:
        by_concept[int(r['concept'])].append(r)

    print("Concept dist in full 223-item pool:")
    for c in sorted(by_concept):
        n = len(by_concept[c])
        n_mech = sum(1 for r in by_concept[c] if r['topic_mech']=='1')
        n_em = sum(1 for r in by_concept[c] if r['topic_em']=='1')
        n_therm = sum(1 for r in by_concept[c] if r['topic_mech']=='0' and r['topic_em']=='0')
        n_open = sum(1 for r in by_concept[c] if r['is_open']=='1')
        print(f"  concept={c}: n={n} · mech={n_mech} em={n_em} therm={n_therm} · open={n_open}")

    # Sample 4 per concept, prefer topic diversity + MCQ/大题 mix
    selected = []
    for c in [1, 2, 3, 4, 5]:
        pool = by_concept[c]
        if not pool:
            continue
        want = 4
        # Prefer topic diversity
        mech = [r for r in pool if r['topic_mech']=='1']
        em = [r for r in pool if r['topic_em']=='1']
        therm = [r for r in pool if r['topic_mech']=='0' and r['topic_em']=='0']

        # Take 1-2 from each topic if available, then fill randomly
        picks = []
        for bucket in [mech, em, therm]:
            if bucket:
                sample_n = min(len(bucket), max(1, want // 3))
                picks.extend(random.sample(bucket, sample_n))
        # Fill remainder
        remaining = [r for r in pool if r not in picks]
        random.shuffle(remaining)
        picks.extend(remaining[:want - len(picks)])
        picks = picks[:want]

        selected.extend(picks)

    # Shuffle final order (blind for teacher)
    random.shuffle(selected)

    print(f"\nSelected {len(selected)} items · shuffled for blind rating:\n")
    print(f"{'idx':>3} {'paper':<15} {'qid':<8} {'concept':>7} {'reason':>7} {'novel':>5} {'model':>5} {'open':>4} {'topic':<8} {'sc/pt':<6}")
    for i, r in enumerate(selected, 1):
        topic = 'mech' if r['topic_mech']=='1' else ('em' if r['topic_em']=='1' else 'therm')
        print(f"{i:>3} {r['paper_id']:<15} Q{r['question_id']:<7} {r['concept']:>7} {r['reasoning']:>7} {r['novelty']:>5} {r['modeling']:>5} {r['is_open']:>4} {topic:<8} {r['textbook_scene_degree']}/{r['textbook_pattern_degree']}")

    # Save for next-step packet building
    out = Path(__file__).resolve().parent.parent / "data" / "labeled" / "calibration_20_items.csv"
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ['blind_idx'])
        w.writeheader()
        for i, r in enumerate(selected, 1):
            row = dict(r)
            row['blind_idx'] = i
            w.writerow(row)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
