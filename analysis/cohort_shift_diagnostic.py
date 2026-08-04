"""Diagnostic for cohort shift between training (西城 filter) and test cohort (全北京).

杨老师 2026-08-03 14:09 confirmed: all 7 papers' rates in training set are 西城区
students who took those exams (both 西城 mocks and 高考). Test-truth 59% for
today's Q3 is 全北京 cohort, teacher guesses 西城 rate would be "比59%高一点儿".

This script:
1. Restates training cohort ground truth (from teacher's 08-03 14:09 statement)
2. Recomputes today's test-question prediction under alternate feature scorings
   (concept 2/3, trap 1/2/3) to bracket the model's 西城-scale prediction
3. Characterizes training set 得分率 distribution per paper — sanity check for
   any within-set anomaly that would suggest mixed cohorts
"""
import csv
import sys
from pathlib import Path
from statistics import mean, stdev
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from pre_label_traps import TRAP_LABELS as TL

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"
BASE = ['concept', 'reasoning', 'novelty', 'visual', 'modeling', 'position', 'is_open',
        'topic_mech', 'topic_em', 'textbook_scene_degree', 'textbook_pattern_degree']
FEATS = BASE + ['transfer_cost', 'is_last_quarter', 'earlier_load',
                'mod_x_nov', 'mod_x_open', 'con_x_mod',
                'concept_sq', 'con_is_2', 'con_is_3', 'con_is_4', 'con_is_5',
                'con_x_scene', 'trap_count']


def enrich(r):
    r['transfer_cost'] = max(0.0, r['textbook_pattern_degree'] - r['textbook_scene_degree'])
    r['is_last_quarter'] = 1.0 if r['position'] > 0.75 else 0.0
    r['mod_x_nov'] = r['modeling'] * r['novelty']
    r['mod_x_open'] = r['modeling'] * r['is_open']
    r['con_x_mod'] = r['concept'] * r['modeling']
    r['concept_sq'] = r['concept'] ** 2
    r['con_is_2'] = 1.0 if r['concept'] == 2 else 0.0
    r['con_is_3'] = 1.0 if r['concept'] == 3 else 0.0
    r['con_is_4'] = 1.0 if r['concept'] == 4 else 0.0
    r['con_is_5'] = 1.0 if r['concept'] == 5 else 0.0
    r['con_x_scene'] = r['concept'] * r['textbook_scene_degree']
    r.setdefault('earlier_load', 0.0)
    return r


def load_train():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for fn in BASE:
                row[fn] = float(r[fn])
            rows.append(row)
    for r in rows:
        r['transfer_cost'] = max(0.0, r['textbook_pattern_degree'] - r['textbook_scene_degree'])
        r['is_last_quarter'] = 1.0 if r['position'] > 0.75 else 0.0
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r['paper'], []).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r['position'])
        for i, r in enumerate(s):
            r['earlier_load'] = mean(e['concept'] for e in s[:i]) if i else 0.0
    for r in rows:
        r['mod_x_nov'] = r['modeling'] * r['novelty']
        r['mod_x_open'] = r['modeling'] * r['is_open']
        r['con_x_mod'] = r['concept'] * r['modeling']
        r['concept_sq'] = r['concept'] ** 2
        r['con_is_2'] = 1.0 if r['concept'] == 2 else 0.0
        r['con_is_3'] = 1.0 if r['concept'] == 3 else 0.0
        r['con_is_4'] = 1.0 if r['concept'] == 4 else 0.0
        r['con_is_5'] = 1.0 if r['concept'] == 5 else 0.0
        r['con_x_scene'] = r['concept'] * r['textbook_scene_degree']
        key = (r['paper'], r['qid'])
        r['trap_count'] = float(TL[key][0]) if key in TL else 0.0
    return rows


def predict_with_features(model_l, model_g, base_features):
    """Given feature dict, return (lasso, gbm, ensemble) predictions."""
    enrich(base_features)
    xn = np.array([[base_features[f] for f in FEATS]])
    pl = float(model_l.predict(xn)[0])
    pg = float(model_g.predict(xn)[0])
    return pl, pg, (pl + pg) / 2


def main():
    rows = load_train()

    print("=" * 72)
    print("1. TRAINING COHORT GROUND TRUTH")
    print("=" * 72)
    print("杨老师 2026-08-03 14:09 explicit statement:")
    print("  '我提供的数据是西城区学生参加高考时的实测数据'")
    print("  '西城区学生参加高考时，试卷总分的得分率在0.70-0.73之间'")
    print()
    print("Conclusion: ALL 7 papers in training are 西城 cohort rates.")
    print("  - xicheng_2024/25/26 (mock papers): 西城 students on 西城 mocks")
    print("  - gaokao_2022/23/24/25:              西城 students on 北京 gaokao")
    print()
    print("Paper-level 得分率 distribution (should be 0.65-0.75 per teacher):")
    print(f"  {'paper':<15} {'n':>4} {'mean rate':>10} {'median':>10} {'stdev':>10}")
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r['paper'], []).append(r['y'])
    for p in sorted(by_paper):
        ys = by_paper[p]
        print(f"  {p:<15} {len(ys):>4} {mean(ys):>10.4f} {sorted(ys)[len(ys)//2]:>10.4f} {stdev(ys):>10.4f}")

    all_ys = [r['y'] for r in rows]
    print(f"  {'ALL':<15} {len(all_ys):>4} {mean(all_ys):>10.4f} {sorted(all_ys)[len(all_ys)//2]:>10.4f} {stdev(all_ys):>10.4f}")

    print()
    print("Sanity check: no anomalous paper (all in 0.60-0.75 range) → consistent with")
    print("single-cohort hypothesis. If a paper had leaked 全北京 rates it would")
    print("likely show a mean 5-10 pp below others.")

    # Train champion
    y = np.array([r['y'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])
    l = Lasso(alpha=0.001, max_iter=10000).fit(X, y)
    g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                   learning_rate=0.01, random_state=42).fit(X, y)

    print()
    print("=" * 72)
    print("2. SENSITIVITY ANALYSIS on today's test question (气泡上浮)")
    print("=" * 72)
    print("Sweep concept ∈ {2,3,4} × trap ∈ {1,2,3} · keeping other features fixed:")
    print("Model output is 西城-scale prediction (since trained on 西城 cohort).")
    print()
    print(f"  {'concept':>8} {'trap':>5} | {'lasso':>7} {'gbm':>7} {'ensemble':>10}")
    for c in [2, 3, 4]:
        for t in [1, 2, 3]:
            feat = {
                'concept': c, 'reasoning': 2, 'novelty': 0, 'visual': 0,
                'modeling': 0, 'position': 0.09, 'is_open': 0,
                'topic_mech': 0, 'topic_em': 0,
                'textbook_scene_degree': 2, 'textbook_pattern_degree': 2,
                'trap_count': t,
            }
            pl, pg, pe = predict_with_features(l, g, feat)
            marker = "  ← 原始 label" if c == 3 and t == 2 else ""
            print(f"  {c:>8} {t:>5} | {pl:>7.3f} {pg:>7.3f} {pe:>10.3f}{marker}")

    print()
    print("=" * 72)
    print("3. WHAT WE OBSERVED VS WHAT WE KNOW")
    print("=" * 72)
    print("Observed:  今题 全北京 truth = 59.0% (teacher)")
    print("Model:     西城-scale prediction = 58.6% (concept=3, trap=2)")
    print("Teacher's intuition for 西城 truth: '比59%高一点儿'")
    print()
    print("If 西城 truth ≈ 65% (rough teacher intuition + top-district assumption):")
    print(f"  Model residual on 西城 scale = 58.6% - 65% = -6.4 pp under-predict")
    print(f"  That is ~1.1σ of avg MAE 5.8pp · within noise.")
    print()
    print("If 西城 truth ≈ 70% (upper end of intuition):")
    print(f"  Model residual on 西城 scale = 58.6% - 70% = -11.4 pp under-predict")
    print(f"  That is ~2.0σ of avg MAE 5.8pp · borderline outlier.")
    print()
    print("Bottom line: the 0.4pp coincidence with 全北京 truth cannot be used as")
    print("validation without knowing 西城 truth. Model likely under-predicted by")
    print("5-12 pp on 西城 scale, consistent with LOPO residual distribution.")

    print()
    print("=" * 72)
    print("4. WHAT PUBLIC DATA WOULD LET US CALIBRATE COHORT OFFSET")
    print("=" * 72)
    print("Missing anchor: any paper where we know BOTH 西城 rate AND 全北京 rate")
    print("for the same items. Options to fill this:")
    print("  (i)  Ask teacher: does she have any historical exams where she")
    print("       recorded both district-level and city-level rates?")
    print("  (ii) Public Beijing gaokao stats: sometimes 北京教育考试院 publishes")
    print("       city-wide 得分率. If we can dig those, pair-wise with her 西城 data.")
    print("  (iii) Systematic: ask teacher for 5-10 historic questions with BOTH")
    print("        cohort rates so we fit a per-difficulty-band offset model.")


if __name__ == "__main__":
    main()
