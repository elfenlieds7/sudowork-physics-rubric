"""Predict 2026 gaokao physics difficulty using v2.4 model (trained on all 7 papers).

Output: predicted 得分率 per question + 整卷加权预测 + per-question comparison.
"""
import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN_CSV = ROOT / "data/labeled/v2_4_labels.csv"
TEST_CSV = ROOT / "data/labeled/gaokao_2026_v24_labels.csv"

# 2026 卷面结构 (per test paper)
Q_TOTAL_2026 = {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12}
MCQ_POINTS = 3

FEATS = [
    'context_familiarity', 'info_complexity', 'topic_cross',
    'concept_count', 'depth_ord', 'open_ord',
    'modeling', 'reasoning', 'computation',
    'qt_fill', 'qt_solve',
    'concept_sq', 'mod_x_open', 'con_x_mod', 'depth_x_reason',
]


def build_row(r, y=None):
    depth_map = {'recall':0,'comprehend':1,'apply':2,'analyze':3}
    open_map = {'closed':0,'semi':1,'open':2}
    row = {
        'qid': r['question_id'],
        'paper': r['paper_id'],
        'y': y if y is not None else (float(r['score_rate']) if r['score_rate'] else None),
        'context_familiarity': int(r['context_familiarity']),
        'info_complexity': int(r['info_complexity']),
        'concept_count': int(r['concept_count']),
        'modeling': int(r['modeling']),
        'reasoning': int(r['reasoning']),
        'computation': int(r['computation']),
        'topic_cross': 1 if r['topic']=='cross' else 0,
        'question_type': r['question_type'],
        'depth_ord': depth_map[r['knowledge_depth']],
        'open_ord': open_map[r['openness']],
        'qt_fill': 1 if r['question_type']=='fill' else 0,
        'qt_solve': 1 if r['question_type']=='solve' else 0,
        'notes': r.get('notes', ''),
    }
    row['concept_sq'] = row['concept_count'] ** 2
    row['mod_x_open'] = row['modeling'] * row['open_ord']
    row['con_x_mod'] = row['concept_count'] * row['modeling']
    row['depth_x_reason'] = row['depth_ord'] * row['reasoning']
    return row


def load(csv_path):
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(build_row(r))
    return rows


def q_weight_2026(qid, qtype):
    """Return weight for 2026 question (Plan 1: 总分 / sub-count · MCQ=3)."""
    if qtype == 'mcq':
        return MCQ_POINTS
    main = qid.split('-')[0]
    try:
        main_int = int(main)
    except ValueError:
        return 3
    total = Q_TOTAL_2026.get(main_int, 3)
    # Sub-count for 2026 (hardcoded from test csv)
    sub_counts_2026 = {15: 3, 16: 4, 17: 3, 18: 3, 19: 3, 20: 3}
    n_subs = sub_counts_2026.get(main_int, 1)
    return total / n_subs if n_subs > 0 else total


def main():
    train_rows = load(TRAIN_CSV)
    test_rows = load(TEST_CSV)
    print(f'Training: {len(train_rows)} items from 7 papers')
    print(f'Predicting: {len(test_rows)} items in 2026')
    print()

    y_train = np.array([r['y'] for r in train_rows])
    X_train = np.array([[r[f] for f in FEATS] for r in train_rows])
    X_test = np.array([[r[f] for f in FEATS] for r in test_rows])

    # Train on all 223 training items
    lasso = Lasso(alpha=0.001, max_iter=50000).fit(X_train, y_train)
    gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01,
                                     random_state=42).fit(X_train, y_train)
    preds = (lasso.predict(X_test) + gbm.predict(X_test)) / 2
    preds = np.clip(preds, 0.02, 0.99)

    # Per-question predictions
    print('=' * 80)
    print('单题预测 · 2026 高考物理')
    print('=' * 80)
    print(f"{'qid':10} {'类型':6} {'预测得分率':>10} {'情境':>4} {'信息':>4} {'概念':>4} {'开放':>4} {'跨模':>4} {'notes'}")
    print('-' * 100)
    for i, r in enumerate(test_rows):
        pred = preds[i]
        print(f"{r['qid']:10} {r['question_type']:6} {pred*100:>9.1f}% "
              f"{r['context_familiarity']:>4} {r['info_complexity']:>4} {r['concept_count']:>4} "
              f"{r['open_ord']:>4} {r['topic_cross']:>4} {r['notes'][:40]}")

    print()
    print('=' * 80)
    print('整卷加权预测 (Plan 1 · 分值 weight)')
    print('=' * 80)
    weights = np.array([q_weight_2026(r['qid'], r['question_type']) for r in test_rows])
    weighted_pred = np.average(preds, weights=weights)
    total_weight = weights.sum()
    print(f'整卷分值合计: {total_weight:.1f} 分 (应 = 100)')
    print(f'整卷加权预测得分率: {weighted_pred*100:.2f}% (即预测均分 {weighted_pred*100:.1f})')

    # Segments
    mcq_mask = np.array([r['question_type']=='mcq' for r in test_rows])
    fill_mask = np.array([r['question_type']=='fill' for r in test_rows])
    solve_mask = np.array([r['question_type']=='solve' for r in test_rows])
    print()
    print(f'MCQ (Q1-14 · 42 分): 预测平均得分率 = {preds[mcq_mask].mean()*100:.2f}% · 预测均分 {preds[mcq_mask].sum() * MCQ_POINTS:.1f} / 42')
    print(f'填空题 (Q15 · Q16 · 18 分): 预测平均得分率 = {preds[fill_mask].mean()*100:.2f}%')
    print(f'解答题 (Q17-20 · 40 分): 预测平均得分率 = {preds[solve_mask].mean()*100:.2f}%')

    # Difficulty buckets
    easy = (preds >= 0.8).sum()
    medium = ((preds >= 0.6) & (preds < 0.8)).sum()
    hard = ((preds >= 0.4) & (preds < 0.6)).sum()
    very_hard = (preds < 0.4).sum()
    print()
    print(f'难度分布:')
    print(f'  容易 (≥80%): {easy} 题')
    print(f'  中等 (60-80%): {medium} 题')
    print(f'  较难 (40-60%): {hard} 题')
    print(f'  很难 (<40%): {very_hard} 题')

    # Print hardest 5
    print()
    print(f'最难 5 题:')
    idx_sorted = np.argsort(preds)
    for i in idx_sorted[:5]:
        r = test_rows[i]
        print(f"  {r['qid']:8} {preds[i]*100:>5.1f}%  {r['notes'][:70]}")

    # Save predictions
    OUT = ROOT / "data/labeled/gaokao_2026_predictions.csv"
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['paper_id', 'question_id', 'predicted_score_rate', 'question_type', 'context_familiarity', 'concept_count', 'modeling', 'reasoning', 'topic', 'openness', 'notes'])
        for i, r in enumerate(test_rows):
            w.writerow([r['paper'], r['qid'], f'{preds[i]:.4f}', r['question_type'],
                        r['context_familiarity'], r['concept_count'], r['modeling'], r['reasoning'],
                        'cross' if r['topic_cross'] else 'in',
                        ['closed','semi','open'][r['open_ord']], r['notes']])
    print()
    print(f'Predictions saved: {OUT}')

    return preds, test_rows, weighted_pred


if __name__ == '__main__':
    main()
