"""Export v2.4 model LOPO predictions to JSON for browser-side validation tool.

Output: `deliverables/rubric/predictions_v24.json`
  { "meta": { version, n_items, mae_overall, ... },
    "items": { qid: { paper, qtype, pred, main_q } } }
"""
import csv, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_IN = ROOT / "data/labeled/v2_4_labels.csv"
OUT = ROOT / "deliverables/rubric/predictions_v24.json"

FEATS = [
    'context_familiarity', 'info_complexity', 'topic_cross',
    'concept_count', 'depth_ord', 'open_ord',
    'modeling', 'reasoning', 'computation',
    'qt_fill', 'qt_solve',
    'concept_sq', 'mod_x_open', 'con_x_mod', 'depth_x_reason',
]


def load():
    rows = []
    with open(CSV_IN, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            depth_map = {'recall':0,'comprehend':1,'apply':2,'analyze':3}
            open_map = {'closed':0,'semi':1,'open':2}
            row = {
                'qid': r['question_id'],
                'paper': r['paper_id'],
                'y': float(r['score_rate']),
                'qtype': r['question_type'],
                'context_familiarity': int(r['context_familiarity']),
                'info_complexity': int(r['info_complexity']),
                'concept_count': int(r['concept_count']),
                'modeling': int(r['modeling']),
                'reasoning': int(r['reasoning']),
                'computation': int(r['computation']),
                'topic_cross': 1 if r['topic']=='cross' else 0,
                'depth_ord': depth_map[r['knowledge_depth']],
                'open_ord': open_map[r['openness']],
                'qt_fill': 1 if r['question_type']=='fill' else 0,
                'qt_solve': 1 if r['question_type']=='solve' else 0,
            }
            row['concept_sq'] = row['concept_count'] ** 2
            row['mod_x_open'] = row['modeling'] * row['open_ord']
            row['con_x_mod'] = row['concept_count'] * row['modeling']
            row['depth_x_reason'] = row['depth_ord'] * row['reasoning']
            main = row['qid'].split('-')[0]
            row['main_q'] = int(main) if main.isdigit() else None
            rows.append(row)
    return rows


def main():
    rows = load()
    print(f'n = {len(rows)} items')
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])

    preds = np.zeros(len(rows))
    logo = LeaveOneGroupOut()
    for tr, te in logo.split(X, y, groups):
        lasso = Lasso(alpha=0.001, max_iter=50000).fit(X[tr], y[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        preds[te] = (lasso.predict(X[te]) + gbm.predict(X[te])) / 2

    mae = mean_absolute_error(y, preds)
    r2 = r2_score(y, preds)

    # Per-paper MAE
    by_paper = {}
    for p in sorted(set(groups)):
        mask = groups == p
        by_paper[p] = {
            'n': int(mask.sum()),
            'mae': float(mean_absolute_error(y[mask], preds[mask])),
        }

    # Key by composite (paper::qid) because qid is only unique within a paper
    items = {}
    for i, r in enumerate(rows):
        key = f"{r['paper']}::{r['qid']}"
        items[key] = {
            'paper': r['paper'],
            'qid': r['qid'],
            'qtype': r['qtype'],
            'main_q': r['main_q'],
            'pred': round(float(preds[i]), 4),
        }

    out = {
        'meta': {
            'model': 'v2.4 · Lasso + GBM ensemble · LOPO',
            'features': FEATS,
            'n_items': len(rows),
            'mae_overall': round(float(mae), 4),
            'r2_overall': round(float(r2), 4),
            'per_paper': by_paper,
            'generated_by': 'analysis/export_v24_predictions.py',
        },
        'items': items,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {OUT}')
    print(f'MAE = {mae:.4f} · R² = {r2:.4f}')
    print(f'Papers: {list(by_paper.keys())}')


if __name__ == '__main__':
    main()
