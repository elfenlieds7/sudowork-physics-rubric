"""v2.4 + Plan 1 · 训练时用分值 weight (Q-total / sub-count 等分 default).

杨老师 2026-08-14 建议 B: 训练加分值 weight · 看综合大题预测是否改善。
"""
import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from statistics import mean, stdev
from collections import Counter
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data/labeled/v2_4_labels.csv"

Q_TOTAL = {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12}
MCQ_POINTS = 3


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
                'concept_count': int(r['concept_count']),
                'modeling': int(r['modeling']),
                'reasoning': int(r['reasoning']),
                'computation': int(r['computation']),
                'topic_cross': 1 if r['topic']=='cross' else 0,
                'question_type': r['question_type'],
            }
            depth_map = {'recall':0,'comprehend':1,'apply':2,'analyze':3}
            row['depth_ord'] = depth_map[r['knowledge_depth']]
            open_map = {'closed':0,'semi':1,'open':2}
            row['open_ord'] = open_map[r['openness']]
            row['qt_fill'] = 1 if r['question_type']=='fill' else 0
            row['qt_solve'] = 1 if r['question_type']=='solve' else 0
            row['concept_sq'] = row['concept_count'] ** 2
            row['mod_x_open'] = row['modeling'] * row['open_ord']
            row['con_x_mod'] = row['concept_count'] * row['modeling']
            row['depth_x_reason'] = row['depth_ord'] * row['reasoning']
            rows.append(row)
    return rows


FEATS = [
    'context_familiarity', 'info_complexity', 'topic_cross',
    'concept_count', 'depth_ord', 'open_ord',
    'modeling', 'reasoning', 'computation',
    'qt_fill', 'qt_solve',
    'concept_sq', 'mod_x_open', 'con_x_mod', 'depth_x_reason',
]


def compute_weights(rows):
    """Plan 1: Q-total / sub-count for 解答题, MCQ = 3."""
    # Group by paper·main-Q
    from collections import defaultdict
    main_counts = defaultdict(int)
    for r in rows:
        if r['question_type'] != 'mcq':
            main = r['qid'].split('-')[0]
            try:
                main_int = int(main)
                main_counts[(r['paper'], main_int)] += 1
            except ValueError:
                pass
    weights = np.zeros(len(rows))
    for i, r in enumerate(rows):
        if r['question_type'] == 'mcq':
            weights[i] = MCQ_POINTS
        else:
            main = r['qid'].split('-')[0]
            try:
                main_int = int(main)
                total = Q_TOTAL.get(main_int, 3)
                n_subs = main_counts[(r['paper'], main_int)]
                weights[i] = total / n_subs if n_subs > 0 else total
            except ValueError:
                weights[i] = 3
    return weights


def train_and_eval(rows, weighted=False):
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])
    w = compute_weights(rows) if weighted else None
    logo = LeaveOneGroupOut()

    yt_all, yp_all, w_all, idx_all = [], [], [], []
    for tr, te in logo.split(X, y, groups):
        if weighted:
            lasso = Lasso(alpha=0.001, max_iter=50000).fit(X[tr], y[tr], sample_weight=w[tr])
            gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(X[tr], y[tr], sample_weight=w[tr])
        else:
            lasso = Lasso(alpha=0.001, max_iter=50000).fit(X[tr], y[tr])
            gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        pred = (lasso.predict(X[te]) + gbm.predict(X[te])) / 2
        yt_all.extend(y[te].tolist())
        yp_all.extend(pred.tolist())
        if weighted:
            w_all.extend(w[te].tolist())
        idx_all.extend(te.tolist())

    yt = np.array(yt_all)
    yp = np.array(yp_all)

    # Unweighted MAE (每 sub-question 等权)
    mae_unw = mean_absolute_error(yt, yp)

    # Weighted MAE (用分值 weight)
    if weighted or True:
        w_eval = np.array(w_all) if weighted else compute_weights([rows[i] for i in idx_all])
        mae_w = np.average(np.abs(yt - yp), weights=w_eval)
    else:
        mae_w = None

    r2 = r2_score(yt, yp)

    # Break down by question type
    # 综合大题 (Q19/Q20) vs simple
    is_综合 = np.array([1 if int(rows[i]['qid'].split('-')[0]) in (19, 20) else 0 for i in idx_all if rows[i]['qid'].split('-')[0].isdigit()])
    idx_综合 = [i for i, row_i in enumerate(idx_all) if rows[row_i]['qid'].split('-')[0].isdigit() and int(rows[row_i]['qid'].split('-')[0]) in (19, 20)]
    idx_simple = [i for i, row_i in enumerate(idx_all) if rows[row_i]['qid'].split('-')[0].isdigit() and int(rows[row_i]['qid'].split('-')[0]) not in (19, 20)]

    yt_zh = yt[idx_综合]
    yp_zh = yp[idx_综合]
    mae_zh = mean_absolute_error(yt_zh, yp_zh) if len(idx_综合) > 0 else None

    yt_sm = yt[idx_simple]
    yp_sm = yp[idx_simple]
    mae_sm = mean_absolute_error(yt_sm, yp_sm) if len(idx_simple) > 0 else None

    return {
        'mae_unweighted': mae_unw,
        'mae_weighted': mae_w,
        'r2': r2,
        'mae_综合大题_Q19_20': mae_zh,
        'n_综合': len(idx_综合),
        'mae_简单题': mae_sm,
        'n_simple': len(idx_simple),
    }


def main():
    rows = load()
    print(f'n = {len(rows)}')

    print()
    print('=' * 80)
    print('Baseline (无分值 weight · 每小问等权训练)')
    print('=' * 80)
    res_base = train_and_eval(rows, weighted=False)
    for k, v in res_base.items():
        if isinstance(v, float):
            print(f'  {k:30}: {v:.4f}')
        else:
            print(f'  {k:30}: {v}')

    print()
    print('=' * 80)
    print('Plan 1 · 分值 weight (Q-total / sub-count 等分 default)')
    print('=' * 80)
    res_w = train_and_eval(rows, weighted=True)
    for k, v in res_w.items():
        if isinstance(v, float):
            print(f'  {k:30}: {v:.4f}')
        else:
            print(f'  {k:30}: {v}')

    print()
    print('=' * 80)
    print('Delta · Plan 1 相对 Baseline')
    print('=' * 80)
    print(f'  综合大题 (Q19/20) MAE: {res_base["mae_综合大题_Q19_20"]:.4f} → {res_w["mae_综合大题_Q19_20"]:.4f} ({(res_w["mae_综合大题_Q19_20"]-res_base["mae_综合大题_Q19_20"])*100:+.2f} pp)')
    print(f'  简单题 MAE:            {res_base["mae_简单题"]:.4f} → {res_w["mae_简单题"]:.4f} ({(res_w["mae_简单题"]-res_base["mae_简单题"])*100:+.2f} pp)')
    print(f'  Unweighted MAE:        {res_base["mae_unweighted"]:.4f} → {res_w["mae_unweighted"]:.4f} ({(res_w["mae_unweighted"]-res_base["mae_unweighted"])*100:+.2f} pp)')
    print(f'  Weighted MAE (分值):    {res_base["mae_weighted"]:.4f} → {res_w["mae_weighted"]:.4f} ({(res_w["mae_weighted"]-res_base["mae_weighted"])*100:+.2f} pp)')


if __name__ == '__main__':
    main()
