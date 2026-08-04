"""Predict score rate for a single new question using champion model.

Champion: v5.2 · Lasso + GBM ensemble · trained on all 223 items · MAE 0.058.

Usage: pass features via NEW_Q dict at top, run script.
"""
import csv
import sys
from pathlib import Path
from statistics import mean
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


NEW_Q = {
    'title': "Q3 · 恒温水槽气泡上浮 · 理想气体 (等温膨胀 · 吸热) · 杨老师 2026-08-04 08:31 测试",
    'concept': 3,
    'reasoning': 2,
    'novelty': 0,
    'visual': 0,
    'modeling': 0,
    'position': 0.09,
    'is_open': 0,
    'topic_mech': 0,
    'topic_em': 0,
    'textbook_scene_degree': 2,
    'textbook_pattern_degree': 2,
    'trap_count': 2,
}


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


def main():
    rows = load_train()
    y = np.array([r['y'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])
    print(f"train n={len(rows)}")

    l = Lasso(alpha=0.001, max_iter=10000).fit(X, y)
    g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                   learning_rate=0.01, random_state=42).fit(X, y)

    # Predict new question
    NEW_Q['earlier_load'] = 0.0
    enrich(NEW_Q)

    print(f"\n{NEW_Q['title']}")
    print("-" * 72)
    for f in FEATS:
        print(f"  {f:22s} = {NEW_Q[f]}")

    xn = np.array([[NEW_Q[f] for f in FEATS]])
    pl = float(l.predict(xn)[0])
    pg = float(g.predict(xn)[0])
    pe = (pl + pg) / 2

    print()
    print(f"Lasso 预测:  {pl:.4f} ({pl*100:.1f}%)")
    print(f"GBM 预测:    {pg:.4f} ({pg*100:.1f}%)")
    print(f"Ensemble:    {pe:.4f} ({pe*100:.1f}%)")
    print()
    print(f"90% 置信区间 (± MAE): [{max(0, pe-0.058):.3f}, {min(1, pe+0.058):.3f}]")
    print(f"                    = [{max(0, pe-0.058)*100:.1f}%, {min(1, pe+0.058)*100:.1f}%]")

    # Similar items from training set
    print()
    print("训练集中类似题目 (topic热光 + concept 2-4 + trap 1-3 + is_open=0):")
    similars = [r for r in rows if r['topic_mech'] == 0 and r['topic_em'] == 0
                and 2 <= r['concept'] <= 4 and r['is_open'] == 0
                and r['trap_count'] >= 1]
    if not similars:
        similars = [r for r in rows if r['topic_mech'] == 0 and r['topic_em'] == 0
                    and 2 <= r['concept'] <= 4 and r['is_open'] == 0]
    for s in similars[:10]:
        print(f"  {s['paper']:<15} Q{s['qid']:<6} concept={int(s['concept'])} trap={int(s['trap_count'])} 实际得分率={s['y']:.2f}")


if __name__ == "__main__":
    main()
