"""v2.4 · Lasso 加所有 pair-wise interactions · 找有信号的 · 看 MAE 改善。
杨老师 22:09 建议: 14 维保持 orthogonal · 合成放 model 层 (feature engineering) 。
"""
import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from itertools import combinations
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso, LassoCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASE_FEATS = [
    ('context_familiarity', '情境'),
    ('info_complexity', '信息呈现'),
    ('topic_cross', '跨模块'),
    ('concept_count', '核心知识'),
    ('depth_ord', '知识深度'),
    ('open_ord', '开放度'),
    ('modeling', '建模'),
    ('reasoning', '推理'),
    ('computation', '运算'),
    ('qt_fill', '填空'),
    ('qt_solve', '解答'),
]


def load():
    rows = []
    with open(ROOT / 'data/labeled/v2_4_labels.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            row = {'paper': r['paper_id'], 'y': float(r['score_rate'])}
            row['context_familiarity'] = int(r['context_familiarity'])
            row['info_complexity'] = int(r['info_complexity'])
            row['topic_cross'] = 1 if r['topic'] == 'cross' else 0
            row['concept_count'] = int(r['concept_count'])
            depth_map = {'recall':0,'comprehend':1,'apply':2,'analyze':3}
            row['depth_ord'] = depth_map[r['knowledge_depth']]
            open_map = {'closed':0,'semi':1,'open':2}
            row['open_ord'] = open_map[r['openness']]
            row['modeling'] = int(r['modeling'])
            row['reasoning'] = int(r['reasoning'])
            row['computation'] = int(r['computation'])
            row['qt_fill'] = 1 if r['question_type']=='fill' else 0
            row['qt_solve'] = 1 if r['question_type']=='solve' else 0
            rows.append(row)
    return rows


def build_features(rows, include_interactions=True):
    keys = [f for f, _ in BASE_FEATS]
    n = len(rows)
    X_base = np.array([[r[f] for f in keys] for r in rows])
    if not include_interactions:
        return X_base, keys[:]
    # Pair-wise interactions
    inter_names = []
    inter_cols = []
    for i, j in combinations(range(len(keys)), 2):
        inter_names.append(f'{keys[i]}×{keys[j]}')
        inter_cols.append(X_base[:, i] * X_base[:, j])
    X_full = np.column_stack([X_base] + inter_cols)
    all_names = keys + inter_names
    return X_full, all_names


def train_lopo(rows, X, alpha=0.001):
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    logo = LeaveOneGroupOut()
    scaler = StandardScaler()
    y_all, yl_all, yg_all = [], [], []
    for tr, te in logo.split(X, y, groups):
        Xtr = scaler.fit_transform(X[tr])
        Xte = scaler.transform(X[te])
        lasso = Lasso(alpha=alpha, max_iter=50000).fit(Xtr, y[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(Xtr, y[tr])
        y_all.extend(y[te].tolist())
        yl_all.extend(lasso.predict(Xte).tolist())
        yg_all.extend(gbm.predict(Xte).tolist())
    y_all = np.array(y_all)
    yl = np.array(yl_all)
    yg = np.array(yg_all)
    ye = (yl + yg) / 2
    return {
        'lasso_mae': mean_absolute_error(y_all, yl),
        'gbm_mae': mean_absolute_error(y_all, yg),
        'ens_mae': mean_absolute_error(y_all, ye),
        'ens_r2': r2_score(y_all, ye),
    }


def find_signal_interactions(rows):
    """Fit Lasso on all pair-wise · find non-zero coefficients."""
    y = np.array([r['y'] for r in rows])
    X_full, names = build_features(rows, include_interactions=True)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_full)
    # LassoCV to find optimal alpha
    lasso_cv = LassoCV(cv=5, max_iter=50000).fit(Xs, y)
    print(f'LassoCV chose alpha={lasso_cv.alpha_:.5f}')
    # Refit final
    coef = lasso_cv.coef_
    kept = [(names[i], coef[i]) for i in range(len(names)) if coef[i] != 0]
    kept.sort(key=lambda x: -abs(x[1]))
    return kept, coef


def main():
    rows = load()
    print(f'n = {len(rows)}')
    print()
    print('=' * 80)
    print('Baseline v2.4 (no interactions · 11 base features)')
    print('=' * 80)
    X_base, _ = build_features(rows, include_interactions=False)
    res_base = train_lopo(rows, X_base)
    for k, v in res_base.items():
        print(f'  {k:12}: {v:.4f}')
    print()
    print('=' * 80)
    print('v2.4 + all pair-wise interactions (11 base + 55 interactions = 66 features)')
    print('=' * 80)
    X_full, names = build_features(rows, include_interactions=True)
    print(f'  Total features: {len(names)}')
    for alpha in [0.001, 0.002, 0.005, 0.01]:
        res = train_lopo(rows, X_full, alpha=alpha)
        print(f'  alpha={alpha:.4f} · ens_mae={res["ens_mae"]:.4f} · ens_r2={res["ens_r2"]:.4f}')
    print()
    print('=' * 80)
    print('Non-zero interactions (Lasso 全数据 · LassoCV 选 alpha)')
    print('=' * 80)
    kept, _ = find_signal_interactions(rows)
    print(f'共保留 {len(kept)} 项 (含 base + interaction)')
    print()
    print('Top 20 by |coefficient|:')
    for name, coef in kept[:20]:
        mark = '💡 交互' if '×' in name else '  base'
        print(f'  {mark} {name:45} {coef:+.4f}')


if __name__ == '__main__':
    main()
