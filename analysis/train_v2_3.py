"""Train v2.3 model on new 10-dim rubric labels · report LOPO MAE + 4 overfit checks.

v2.3 dimensions (10):
- Categorical: topic (mech/em/thermal/cross · one-hot 3 dummies) ·
  knowledge_depth (recall/comprehend/apply/analyze · ordinal 0-3) ·
  openness (closed/semi/open · ordinal 0-2) ·
  question_type (mcq/fill/solve · one-hot 2 dummies)
- Numeric: context_familiarity 0-2 · info_complexity 0-2 · concept_count 1-5 ·
  modeling 0-3 · reasoning 1-5 · computation 0-3
"""
import csv
import sys
from pathlib import Path
from statistics import mean, stdev
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut

sys.stdout.reconfigure(encoding="utf-8")

CSV = Path(__file__).resolve().parent.parent / "data" / "labeled" / "v2_3_labels.csv"


def load():
    rows = []
    with open(CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            row = {
                'qid': r['question_id'],
                'paper': r['paper_id'],
                'y': float(r['score_rate']),
                'context_familiarity': int(r['context_familiarity']),
                'info_complexity': int(r['info_complexity']),
                'topic': r['topic'],
                'concept_count': int(r['concept_count']),
                'knowledge_depth': r['knowledge_depth'],
                'openness': r['openness'],
                'modeling': int(r['modeling']),
                'reasoning': int(r['reasoning']),
                'computation': int(r['computation']),
                'question_type': r['question_type'],
            }
            # Encode categoricals
            row['topic_mech']    = 1 if r['topic'] == 'mech'    else 0
            row['topic_em']      = 1 if r['topic'] == 'em'      else 0
            row['topic_thermal'] = 1 if r['topic'] == 'thermal' else 0
            row['topic_cross']   = 1 if r['topic'] == 'cross'   else 0
            depth_map = {'recall': 0, 'comprehend': 1, 'apply': 2, 'analyze': 3}
            row['depth_ord'] = depth_map[r['knowledge_depth']]
            open_map = {'closed': 0, 'semi': 1, 'open': 2}
            row['open_ord'] = open_map[r['openness']]
            row['qt_mcq']   = 1 if r['question_type'] == 'mcq'   else 0
            row['qt_fill']  = 1 if r['question_type'] == 'fill'  else 0
            row['qt_solve'] = 1 if r['question_type'] == 'solve' else 0
            # Derived interactions (kept from v1 that were signal)
            row['concept_sq'] = row['concept_count'] ** 2
            row['mod_x_open'] = row['modeling'] * row['open_ord']
            row['con_x_mod'] = row['concept_count'] * row['modeling']
            row['depth_x_reason'] = row['depth_ord'] * row['reasoning']
            rows.append(row)
    return rows


FEATS_BASE = [
    'context_familiarity', 'info_complexity',
    'topic_mech', 'topic_em', 'topic_thermal', 'topic_cross',
    'concept_count', 'depth_ord', 'open_ord',
    'modeling', 'reasoning', 'computation',
    'qt_fill', 'qt_solve',  # mcq is baseline
]

FEATS_ENRICHED = FEATS_BASE + [
    'concept_sq', 'mod_x_open', 'con_x_mod', 'depth_x_reason'
]


def train_lopo(rows, feats, seed=42):
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in feats] for r in rows])
    logo = LeaveOneGroupOut()

    y_true_all, y_lasso, y_gbm = [], [], []
    for tr, te in logo.split(X, y, groups):
        lasso = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                         learning_rate=0.01, random_state=seed).fit(X[tr], y[tr])
        y_true_all.extend(y[te].tolist())
        y_lasso.extend(lasso.predict(X[te]).tolist())
        y_gbm.extend(gbm.predict(X[te]).tolist())

    yt = np.array(y_true_all)
    yl = np.array(y_lasso)
    yg = np.array(y_gbm)
    ye = (yl + yg) / 2

    return {
        'lasso_mae': mean_absolute_error(yt, yl),
        'lasso_r2':  r2_score(yt, yl),
        'gbm_mae':   mean_absolute_error(yt, yg),
        'gbm_r2':    r2_score(yt, yg),
        'ens_mae':   mean_absolute_error(yt, ye),
        'ens_r2':    r2_score(yt, ye),
    }


def overfit_checks(rows, feats):
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in feats] for r in rows])
    logo = LeaveOneGroupOut()

    per_paper = {}
    train_maes = []
    y_pred_all = np.zeros(len(y))
    for tr, te in logo.split(X, y, groups):
        held = groups[te[0]]
        lasso = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                         learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        yp_tr = (lasso.predict(X[tr]) + gbm.predict(X[tr])) / 2
        train_maes.append(mean_absolute_error(y[tr], yp_tr))
        yp_te = (lasso.predict(X[te]) + gbm.predict(X[te])) / 2
        y_pred_all[te] = yp_te
        per_paper[held] = {
            'lopo_mae': mean_absolute_error(y[te], yp_te),
            'lopo_r2': r2_score(y[te], yp_te),
            'n': len(te),
        }

    # Multi-seed
    seed_results = []
    for seed in [42, 1, 7, 100, 2024, 3, 17, 99, 84, 1234]:
        yt_all, yp_all = [], []
        for tr, te in logo.split(X, y, groups):
            gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                             learning_rate=0.01, random_state=seed).fit(X[tr], y[tr])
            yt_all.extend(y[te].tolist())
            yp_all.extend(gbm.predict(X[te]).tolist())
        seed_results.append(mean_absolute_error(yt_all, yp_all))

    # Random feature sanity
    np.random.seed(999)
    X_r = np.column_stack([X, np.random.randn(len(rows))])
    yt_all, yp_all = [], []
    for tr, te in logo.split(X_r, y, groups):
        lasso = Lasso(alpha=0.001, max_iter=10000).fit(X_r[tr], y[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                         learning_rate=0.01, random_state=42).fit(X_r[tr], y[tr])
        yt_all.extend(y[te].tolist())
        yp_all.extend(((lasso.predict(X_r[te]) + gbm.predict(X_r[te])) / 2).tolist())
    random_mae = mean_absolute_error(yt_all, yp_all)

    return {
        'per_paper': per_paper,
        'train_mae_mean': mean(train_maes),
        'lopo_mae_mean': mean(d['lopo_mae'] for d in per_paper.values()),
        'lopo_mae_stdev': stdev(d['lopo_mae'] for d in per_paper.values()),
        'seed_mae_mean': mean(seed_results),
        'seed_mae_stdev': stdev(seed_results),
        'random_feat_mae': random_mae,
    }


def paper_level(rows, feats):
    from collections import Counter
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in feats] for r in rows])
    logo = LeaveOneGroupOut()

    y_pred_all = np.zeros(len(y))
    for tr, te in logo.split(X, y, groups):
        lasso = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                         learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        y_pred_all[te] = (lasso.predict(X[te]) + gbm.predict(X[te])) / 2

    def paper_weights(paper_rows):
        main_counts = Counter()
        for r in paper_rows:
            if r['qt_solve'] == 1 or r['qt_fill'] == 1:
                main = r['qid'].split('-')[0]
                main_counts[main] += 1
        weights = []
        for r in paper_rows:
            if r['qt_mcq'] == 1:
                weights.append(3.0)
            else:
                main = r['qid'].split('-')[0]
                try:
                    total = {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12}.get(int(main), 3)
                except ValueError:
                    total = 3
                n_subs = main_counts[main]
                weights.append(total / n_subs)
        return weights

    total_errors = []
    per_paper_totals = {}
    for paper in sorted(set(groups)):
        idx = [i for i, g in enumerate(groups) if g == paper]
        prows = [rows[i] for i in idx]
        weights = paper_weights(prows)
        tot_w = sum(weights)
        actual = sum(w * rows[idx[j]]['y'] for j, w in enumerate(weights)) / tot_w
        pred = sum(w * y_pred_all[idx[j]] for j, w in enumerate(weights)) / tot_w
        err = pred - actual
        total_errors.append(abs(err))
        per_paper_totals[paper] = (actual, pred, err)

    return {
        'per_paper_totals': per_paper_totals,
        'total_mae_pp': mean(total_errors) * 100,
        'total_median_pp': sorted(total_errors)[len(total_errors)//2] * 100,
        'total_max_pp': max(total_errors) * 100,
    }


def main():
    rows = load()
    print(f'n = {len(rows)}')

    print()
    print('=' * 72)
    print(f'V2.3 · BASE features ({len(FEATS_BASE)}) · LOPO CV')
    print('=' * 72)
    res_base = train_lopo(rows, FEATS_BASE)
    for k, v in res_base.items():
        print(f'  {k:12s}: {v:.4f}')

    print()
    print('=' * 72)
    print(f'V2.3 · ENRICHED features ({len(FEATS_ENRICHED)}) · LOPO CV')
    print('=' * 72)
    res_enr = train_lopo(rows, FEATS_ENRICHED)
    for k, v in res_enr.items():
        print(f'  {k:12s}: {v:.4f}')

    # Use enriched for detailed checks
    print()
    print('=' * 72)
    print('V2.3 · OVERFIT CHECKS (enriched features)')
    print('=' * 72)
    checks = overfit_checks(rows, FEATS_ENRICHED)
    print(f'  Per-paper LOPO MAE:  mean={checks["lopo_mae_mean"]:.4f} · stdev={checks["lopo_mae_stdev"]:.4f}')
    print(f'  Train MAE (in-set):  mean={checks["train_mae_mean"]:.4f}')
    print(f'  Overfit gap:         {checks["lopo_mae_mean"] - checks["train_mae_mean"]:+.4f}')
    print(f'  Multi-seed MAE:      mean={checks["seed_mae_mean"]:.4f} · stdev={checks["seed_mae_stdev"]:.4f}')
    print(f'  Random-feat MAE:     {checks["random_feat_mae"]:.4f}  (v.s. base ens MAE)')
    print()
    print('  Per-paper detail:')
    for p, d in sorted(checks['per_paper'].items()):
        print(f'    {p:<15} n={d["n"]:3d} · LOPO MAE={d["lopo_mae"]:.4f} · R²={d["lopo_r2"]:.4f}')

    print()
    print('=' * 72)
    print('V2.3 · PAPER-LEVEL WEIGHTED MAE')
    print('=' * 72)
    pl = paper_level(rows, FEATS_ENRICHED)
    for p, (actual, pred, err) in pl['per_paper_totals'].items():
        print(f'  {p:<15} actual={actual:.4f} · pred={pred:.4f} · err={err*100:+.2f} pp')
    print(f'  Total (integrated) MAE:    {pl["total_mae_pp"]:.2f} pp')
    print(f'  Total median:              {pl["total_median_pp"]:.2f} pp')
    print(f'  Total max:                 {pl["total_max_pp"]:.2f} pp')

    print()
    print('=' * 72)
    print('SUMMARY · v1 vs v2.3')
    print('=' * 72)
    print(f'  v1 (17 dims + trap + position): single-item MAE = 0.0570, paper MAE = 1.53 pp')
    print(f'  v2.3 (14 dims features, 10 打分维度, no trap/position): single MAE = {res_enr["ens_mae"]:.4f}, paper MAE = {pl["total_mae_pp"]:.2f} pp')


if __name__ == "__main__":
    main()
