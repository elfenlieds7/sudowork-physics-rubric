"""Export per-question LOPO predictions (champion model) as JS object for v2.html charts."""
import csv, json, sys
from pathlib import Path
from statistics import mean
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.model_selection import LeaveOneGroupOut

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from pre_label_traps import TRAP_LABELS as TL

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"
BASE = ['concept','reasoning','novelty','visual','modeling','position','is_open',
        'topic_mech','topic_em','textbook_scene_degree','textbook_pattern_degree']
FEATS = BASE + ['transfer_cost','is_last_quarter','earlier_load',
                'mod_x_nov','mod_x_open','con_x_mod',
                'concept_sq','con_is_2','con_is_3','con_is_4','con_is_5',
                'con_x_scene','trap_count']


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for fn in BASE: row[fn] = float(r[fn])
            rows.append(row)
    for r in rows:
        r['transfer_cost'] = max(0.0, r['textbook_pattern_degree'] - r['textbook_scene_degree'])
        r['is_last_quarter'] = 1.0 if r['position'] > 0.75 else 0.0
    by_paper = {}
    for r in rows: by_paper.setdefault(r['paper'], []).append(r)
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
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])

    logo = LeaveOneGroupOut()
    preds = np.zeros(len(y))
    for tr, te in logo.split(X, y, groups):
        l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                       learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        preds[te] = (l.predict(X[te]) + g.predict(X[te])) / 2

    # Organize by paper, ordered by position (question order)
    by_paper = {}
    for i, r in enumerate(rows):
        by_paper.setdefault(r['paper'], []).append({
            'qid': r['qid'], 'pos': r['position'],
            'actual': round(float(r['y']), 4),
            'pred': round(float(preds[i]), 4),
        })
    for p in by_paper:
        by_paper[p].sort(key=lambda x: x['pos'])

    # Emit JS-friendly structure
    js = "const CHART_DATA = " + json.dumps(by_paper, ensure_ascii=False, indent=2) + ";"
    out = Path(__file__).resolve().parent.parent / "deliverables" / "rubric" / "chart_data.js"
    with open(out, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f"wrote {out}  ({len(rows)} items across {len(by_paper)} papers)")


if __name__ == "__main__":
    main()
