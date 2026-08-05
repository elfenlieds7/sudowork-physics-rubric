"""Verify JS predictor output matches Python champion within numeric tolerance.

Approach: use Node.js to run the JS predictor on 20 test items · compare
against Python champion predictions. Any drift larger than 0.001 is a bug.
"""
import csv
import json
import subprocess
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
MODEL_JS = Path(__file__).resolve().parent.parent / "deliverables" / "rubric" / "model_champion.js"

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


def main():
    rows = load()
    y = np.array([r['y'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])
    lasso = Lasso(alpha=0.001, max_iter=10000).fit(X, y)
    gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                     learning_rate=0.01, random_state=42).fit(X, y)

    # Pick 10 test items covering range of difficulty
    test_idx = [0, 25, 50, 75, 100, 125, 150, 175, 200, 222]

    # Build JS test harness
    js_code = f"""
const model = require('{MODEL_JS.as_posix()}'.replace(/^.*[/]/, './'));
// Node requires we re-add the window global if the file writes to window
"""

    # Actually the model file writes to `window` · in Node we need to fake it
    node_harness = """
global.window = {};
"""
    node_harness += MODEL_JS.read_text(encoding='utf-8').replace(
        'window.RUBRIC_MODEL', 'global.window.RUBRIC_MODEL')
    node_harness += """
const M = global.window.RUBRIC_MODEL;

function predictLasso(featVec) {
  let s = M.lasso.intercept;
  for (let i = 0; i < featVec.length; i++) s += featVec[i] * M.lasso.coef[i];
  return s;
}
function predictOneTree(nodes, featVec) {
  let idx = 0;
  while (nodes[idx].left !== -1) {
    const n = nodes[idx];
    if (featVec[n.feature] <= n.threshold) idx = n.left; else idx = n.right;
  }
  return nodes[idx].value;
}
function predictGBM(featVec) {
  let s = M.gbm.init;
  for (const tree of M.gbm.trees) s += M.gbm.learning_rate * predictOneTree(tree, featVec);
  return s;
}

const testItems = TESTITEMSJSON;
const out = [];
for (const item of testItems) {
  const fv = M.features.map(name => item[name]);
  const lasso = predictLasso(fv);
  const gbm = predictGBM(fv);
  out.push({lasso, gbm, avg: (lasso + gbm) / 2});
}
console.log(JSON.stringify(out));
"""

    # Build test items JSON
    test_items = []
    for i in test_idx:
        r = rows[i]
        test_items.append({f: r[f] for f in FEATS})
    node_harness = node_harness.replace('TESTITEMSJSON', json.dumps(test_items))

    # Run node
    tmp = Path(__file__).resolve().parent / '_verify_tmp.js'
    tmp.write_text(node_harness, encoding='utf-8')
    result = subprocess.run(['node', str(tmp)], capture_output=True, text=True, encoding='utf-8')
    tmp.unlink()
    if result.returncode != 0:
        print(f"Node error: {result.stderr}")
        return
    js_preds = json.loads(result.stdout.strip())

    # Python predictions
    l_py = lasso.predict(X[test_idx])
    g_py = gbm.predict(X[test_idx])

    # Compare
    print(f"{'#':>3} {'paper.qid':<20} {'y_true':>7} {'lasso_py':>9} {'lasso_js':>9} {'Δlasso':>8} {'gbm_py':>8} {'gbm_js':>8} {'Δgbm':>8}")
    print("-" * 96)
    max_l_diff = 0
    max_g_diff = 0
    for k, i in enumerate(test_idx):
        r = rows[i]
        l_p = l_py[k]
        g_p = g_py[k]
        l_j = js_preds[k]['lasso']
        g_j = js_preds[k]['gbm']
        l_d = abs(l_p - l_j)
        g_d = abs(g_p - g_j)
        max_l_diff = max(max_l_diff, l_d)
        max_g_diff = max(max_g_diff, g_d)
        print(f"{k:>3} {r['paper'][:12]}.{r['qid']:<7} {r['y']:>7.3f} {l_p:>9.5f} {l_j:>9.5f} {l_d:>8.2e} {g_p:>8.4f} {g_j:>8.4f} {g_d:>8.2e}")

    print()
    print(f"Max Lasso 差 = {max_l_diff:.2e}")
    print(f"Max GBM   差 = {max_g_diff:.2e}")
    if max_l_diff < 1e-4 and max_g_diff < 1e-4:
        print(f"\n✅ JS 预测与 Python champion 数值一致 (差 < 1e-4)")
    else:
        print(f"\n⚠️  差异超出预期 · 检查 JS predictor / model export 逻辑")


if __name__ == "__main__":
    main()
