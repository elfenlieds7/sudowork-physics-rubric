"""Export champion model (Lasso + GBM ensemble) to JS-consumable JSON.

Champion = Lasso(alpha=0.001) + GradientBoostingRegressor(500 trees · depth 2 · lr 0.01)
· etwork trained on all 223 items with 24 features.

Output: `deliverables/rubric/model_champion.js` — a single file with:
  window.RUBRIC_MODEL = {
    features: [...24 feature names in order...],
    lasso: { intercept: float, coef: [24 floats] },
    gbm: {
      init: float,
      learning_rate: float,
      trees: [ {threshold, feature, left, right, value}, ... ]
    },
    m3_band: {
      simple:   { lo, hi, offset_pp },
      medium:   { lo, hi, offset_pp },
      hard:     { lo, hi, offset_pp },
    }
  };

Then a companion JS predictor reads this and returns:
  { xicheng_pred, beijing_pred, band }
"""
import csv
import json
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
OUT_PATH = Path(__file__).resolve().parent.parent / "deliverables" / "rubric" / "model_champion.js"

BASE = ['concept', 'reasoning', 'novelty', 'visual', 'modeling', 'position', 'is_open',
        'topic_mech', 'topic_em', 'textbook_scene_degree', 'textbook_pattern_degree']
FEATS = BASE + ['transfer_cost', 'is_last_quarter', 'earlier_load',
                'mod_x_nov', 'mod_x_open', 'con_x_mod',
                'concept_sq', 'con_is_2', 'con_is_3', 'con_is_4', 'con_is_5',
                'con_x_scene', 'trap_count']


def load():
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


def tree_to_json(tree):
    """Extract a sklearn DecisionTreeRegressor into a flat node array.

    Each node: { left, right, feature, threshold, value }
    Node index 0 is root · leaves have left=right=-1 and value populated.
    """
    T = tree.tree_
    nodes = []
    for i in range(T.node_count):
        left = int(T.children_left[i])
        right = int(T.children_right[i])
        feature = int(T.feature[i])
        threshold = float(T.threshold[i])
        value = float(T.value[i, 0, 0])
        nodes.append({
            'left': left,
            'right': right,
            'feature': feature,
            'threshold': threshold,
            'value': value,
        })
    return nodes


def main():
    rows = load()
    y = np.array([r['y'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])
    print(f"训练集: {len(rows)} 题 · {len(FEATS)} 特征")

    # Train Lasso
    lasso = Lasso(alpha=0.001, max_iter=10000).fit(X, y)
    lasso_json = {
        'intercept': float(lasso.intercept_),
        'coef': [float(c) for c in lasso.coef_],
    }
    # Show non-zero coefs
    nz = [(FEATS[i], c) for i, c in enumerate(lasso.coef_) if abs(c) > 1e-6]
    print(f"\nLasso 非零系数 ({len(nz)} / {len(FEATS)}):")
    for name, c in sorted(nz, key=lambda x: abs(x[1]), reverse=True)[:10]:
        print(f"  {name:<25} {c:+.4f}")

    # Train GBM
    gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                     learning_rate=0.01, random_state=42).fit(X, y)
    # Extract initial constant + all trees
    init_pred = float(gbm.init_.constant_[0][0])
    trees = []
    for est in gbm.estimators_:
        tree = est[0]
        trees.append(tree_to_json(tree))
    print(f"\nGBM: init={init_pred:.4f} · {len(trees)} 棵树 · 每棵最多 4 节点 (depth 2)")
    total_nodes = sum(len(t) for t in trees)
    print(f"总节点数 = {total_nodes}  (预估 JSON ~{total_nodes * 30 // 1024} KB)")

    # M3 band offsets (from earlier cohort fit)
    m3 = {
        'simple':  {'lo': 0.8,  'hi': 1.01, 'offset_pp': -5.6},
        'medium':  {'lo': 0.5,  'hi': 0.8,  'offset_pp': -8.2},
        'hard':    {'lo': 0.0,  'hi': 0.5,  'offset_pp': -6.7},
    }

    model = {
        'version': 'v5.6',
        'created': '2026-08-05',
        'features': FEATS,
        'lasso': lasso_json,
        'gbm': {
            'init': init_pred,
            'learning_rate': 0.01,
            'trees': trees,
        },
        'm3_band': m3,
    }

    # Write as JS file (window.RUBRIC_MODEL = ...)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write("// Auto-generated · do not edit · run analysis/export_model_to_js.py\n")
        f.write("// Champion model: Lasso + GBM ensemble · 223 items × 24 features · LOPO MAE 0.057\n")
        f.write("window.RUBRIC_MODEL = ")
        json.dump(model, f, ensure_ascii=False)
        f.write(";\n")
    kb = OUT_PATH.stat().st_size // 1024
    print(f"\n写入: {OUT_PATH.name}  ({kb} KB)")

    # Sanity check: Python vs would-be JS prediction on first 3 items
    print()
    print("Sanity check (Python-side):")
    print(f"  {'qid':<16} {'y_true':>8} {'Lasso':>8} {'GBM':>8} {'Ensemble':>10}")
    l_pred = lasso.predict(X)
    g_pred = gbm.predict(X)
    for i in [0, 50, 100, 150, 200]:
        avg = (l_pred[i] + g_pred[i]) / 2
        r = rows[i]
        print(f"  {r['paper'][:8]}.{r['qid']:<7} {r['y']:>8.3f} {l_pred[i]:>8.3f} {g_pred[i]:>8.3f} {avg:>10.3f}")


if __name__ == "__main__":
    main()
