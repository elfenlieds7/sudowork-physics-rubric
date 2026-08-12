"""v2.3 feature importance + correlation analysis · 回答杨老师 08-12 09:58:
哪些维度与得分率相关性不大 · 可能层级设计不合理。
"""
import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.inspection import permutation_importance
from sklearn.model_selection import LeaveOneGroupOut, cross_val_score

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data/labeled/v2_3_labels.csv"


def load():
    rows = []
    with open(CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            row = {
                'paper': r['paper_id'],
                'y': float(r['score_rate']),
                'context_familiarity': int(r['context_familiarity']),
                'info_complexity': int(r['info_complexity']),
                'concept_count': int(r['concept_count']),
                'modeling': int(r['modeling']),
                'reasoning': int(r['reasoning']),
                'computation': int(r['computation']),
            }
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
            rows.append(row)
    return rows


FEATURES = [
    ('context_familiarity', '情境特征'),
    ('info_complexity', '信息呈现'),
    ('topic_mech', '模块-力学'),
    ('topic_em', '模块-电磁'),
    ('topic_thermal', '模块-热光原'),
    ('topic_cross', '模块-跨模块'),
    ('concept_count', '核心知识数(v2.3)'),
    ('depth_ord', '知识深度'),
    ('open_ord', '设问开放度'),
    ('modeling', '建模复杂度'),
    ('reasoning', '推理链长度'),
    ('computation', '运算难度'),
    ('qt_fill', '题型-填空'),
    ('qt_solve', '题型-解答'),
]


def main():
    rows = load()
    n = len(rows)
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])

    print(f'v2.3 · 14 features vs 得分率 · n={n}')
    print('=' * 105)
    print(f'{"维度":22} {"Pearson r":>12} {"p":>10} {"Spearman ρ":>13} {"p":>10} {"GBM 重要度":>12} {"Lasso β":>12}')
    print('=' * 105)

    # Full feature matrix
    X = np.array([[r[f] for f, _ in FEATURES] for r in rows])
    lasso = Lasso(alpha=0.001, max_iter=10000).fit(X, y)
    gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(X, y)
    perm = permutation_importance(gbm, X, y, n_repeats=30, random_state=42, n_jobs=-1)

    results = []
    for i, (f, name) in enumerate(FEATURES):
        x = X[:, i]
        pear_r, pear_p = pearsonr(x, y)
        spear_r, spear_p = spearmanr(x, y)
        gbm_imp = perm.importances_mean[i]
        lasso_beta = lasso.coef_[i]
        results.append({
            'name': name, 'key': f,
            'pearson': pear_r, 'p_pear': pear_p,
            'spearman': spear_r, 'p_spear': spear_p,
            'gbm_imp': gbm_imp, 'lasso_beta': lasso_beta,
        })
        print(f'{name:22} {pear_r:>12.3f} {pear_p:>10.4f} {spear_r:>13.3f} {spear_p:>10.4f} {gbm_imp:>12.4f} {lasso_beta:>12.4f}')

    print()
    print('=' * 105)
    print('信号弱 · 建议 review 的维度 (|Pearson| < 0.15 或 |Spearman| < 0.15 或 GBM 重要度 < 0.001):')
    print('=' * 105)
    for r in results:
        weak = (abs(r['pearson']) < 0.15) or (abs(r['spearman']) < 0.15) or (r['gbm_imp'] < 0.001)
        if weak:
            reasons = []
            if abs(r['pearson']) < 0.15: reasons.append(f"Pearson|{r['pearson']:.3f}|<0.15")
            if abs(r['spearman']) < 0.15: reasons.append(f"Spearman|{r['spearman']:.3f}|<0.15")
            if r['gbm_imp'] < 0.001: reasons.append(f"GBM|{r['gbm_imp']:.4f}|<0.001")
            print(f'  · {r["name"]}: {" · ".join(reasons)}')

    print()
    print('=' * 105)
    print('信号强的 top 5 (可信度 gate 判定):')
    print('=' * 105)
    top5 = sorted(results, key=lambda r: -abs(r['pearson']))[:5]
    for r in top5:
        print(f'  · {r["name"]}: Pearson {r["pearson"]:.3f} · Spearman {r["spearman"]:.3f} · GBM 重要度 {r["gbm_imp"]:.4f}')


if __name__ == '__main__':
    main()
