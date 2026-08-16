"""Compare 2022-2026 北京高考物理试题 · 整卷预测/实测得分率 + 各维度均值 + 特点。"""
import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.model_selection import LeaveOneGroupOut

ROOT = Path(__file__).resolve().parent.parent

# Q_TOTAL per paper (each year's structure varies slightly)
Q_TOTAL_BY_PAPER = {
    'gaokao_2022': {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12},
    'gaokao_2023': {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12},
    'gaokao_2024': {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12},
    'gaokao_2025': {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12},
    'gaokao_2026': {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12},
}
MCQ_POINTS = 3

FEATS = [
    'context_familiarity', 'info_complexity', 'topic_cross',
    'concept_count', 'depth_ord', 'open_ord',
    'modeling', 'reasoning', 'computation',
    'qt_fill', 'qt_solve',
    'concept_sq', 'mod_x_open', 'con_x_mod', 'depth_x_reason',
]


def build_row(r):
    depth_map = {'recall':0,'comprehend':1,'apply':2,'analyze':3}
    open_map = {'closed':0,'semi':1,'open':2}
    row = {
        'qid': r['question_id'],
        'paper': r['paper_id'],
        'y': float(r['score_rate']) if r['score_rate'] else None,
        'question_type': r['question_type'],
        'topic': r['topic'],
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
    return row


def load_all():
    rows = []
    with open(ROOT / 'data/labeled/v2_4_labels.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['paper_id'].startswith('gaokao_'):
                rows.append(build_row(r))
    with open(ROOT / 'data/labeled/gaokao_2026_v24_labels.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(build_row(r))
    return rows


def q_weight(qid, paper, qtype):
    if qtype == 'mcq':
        return MCQ_POINTS
    main = qid.split('-')[0]
    try:
        main_int = int(main)
    except ValueError:
        return 3
    total = Q_TOTAL_BY_PAPER.get(paper, {}).get(main_int, 3)
    # Count sub-questions with same main-number in this paper
    return None, main_int, total  # will compute after grouping


def main():
    all_rows = load_all()
    # Get predictions for 2026 by training on 2022-2025 + xicheng (i.e., non-2026)
    # For 2022-2025, use LOPO predictions
    print('Computing predictions...')

    # Load full training set (including xicheng for consistency with paper)
    all_train = []
    with open(ROOT / 'data/labeled/v2_4_labels.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            all_train.append(build_row(r))

    train_2026_input = np.array([[r[f] for f in FEATS] for r in all_train])
    y_train = np.array([r['y'] for r in all_train])
    groups = np.array([r['paper'] for r in all_train])

    # LOPO for 2022-2025
    preds_by_key = {}
    logo = LeaveOneGroupOut()
    for tr, te in logo.split(train_2026_input, y_train, groups):
        te_paper = all_train[te[0]]['paper']
        if not te_paper.startswith('gaokao_'):
            continue
        lasso = Lasso(alpha=0.001, max_iter=50000).fit(train_2026_input[tr], y_train[tr])
        gbm = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(train_2026_input[tr], y_train[tr])
        pred = (lasso.predict(train_2026_input[te]) + gbm.predict(train_2026_input[te])) / 2
        for i, idx in enumerate(te):
            preds_by_key[(all_train[idx]['paper'], all_train[idx]['qid'])] = np.clip(pred[i], 0.02, 0.99)

    # 2026 prediction: train on all
    test_2026 = [r for r in all_rows if r['paper']=='gaokao_2026']
    X_2026 = np.array([[r[f] for f in FEATS] for r in test_2026])
    lasso_all = Lasso(alpha=0.001, max_iter=50000).fit(train_2026_input, y_train)
    gbm_all = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(train_2026_input, y_train)
    pred_2026 = np.clip((lasso_all.predict(X_2026) + gbm_all.predict(X_2026)) / 2, 0.02, 0.99)
    for i, r in enumerate(test_2026):
        preds_by_key[(r['paper'], r['qid'])] = pred_2026[i]

    # Group by year
    years = ['gaokao_2022', 'gaokao_2023', 'gaokao_2024', 'gaokao_2025', 'gaokao_2026']

    # Print overall summary
    print()
    print('=' * 90)
    print('五年北京高考物理 · 整卷难度对比 (100 分卷)')
    print('=' * 90)
    print(f"{'Year':10}   {'实测均分':>8}  {'预测均分':>8}  {'实测MAE':>8}  {'MCQ均分':>8}  {'解答均分':>8}  {'最难题':>6}")
    print('-' * 90)

    year_stats = {}
    for year in years:
        year_rows = [r for r in all_rows if r['paper']==year]
        if not year_rows:
            continue

        # Compute paper-total actual + pred
        # For each row compute weight (points fraction)
        # Group by main_q to know sub_count
        from collections import defaultdict
        subs_by_main = defaultdict(list)
        for r in year_rows:
            if r['question_type'] != 'mcq':
                try:
                    main = int(r['qid'].split('-')[0])
                    subs_by_main[main].append(r)
                except ValueError:
                    pass

        weights = []
        actuals = []
        preds = []
        for r in year_rows:
            if r['question_type'] == 'mcq':
                w = MCQ_POINTS
            else:
                try:
                    main = int(r['qid'].split('-')[0])
                    total = Q_TOTAL_BY_PAPER[year].get(main, 3)
                    n_subs = len(subs_by_main[main])
                    w = total / n_subs if n_subs > 0 else total
                except ValueError:
                    w = 3
            weights.append(w)
            actuals.append(r['y'])
            preds.append(preds_by_key.get((r['paper'], r['qid']), None))

        weights = np.array(weights)
        actuals_arr = np.array([a if a is not None else np.nan for a in actuals])
        preds_arr = np.array([p if p is not None else np.nan for p in preds])

        # Paper total (out of 100)
        pred_total = np.average(preds_arr, weights=weights) * 100
        if not np.isnan(actuals_arr).all():
            actual_total = np.average(actuals_arr, weights=weights) * 100
            mae = np.abs(actual_total - pred_total)
        else:
            actual_total = None
            mae = None

        # MCQ vs 解答
        mcq_mask = np.array([r['question_type']=='mcq' for r in year_rows])
        solve_mask = np.array([r['question_type']=='solve' for r in year_rows])
        mcq_total = preds_arr[mcq_mask].mean() * 42 if mcq_mask.any() else None
        solve_avg = preds_arr[solve_mask].mean() * 100 if solve_mask.any() else None
        hardest = preds_arr.min() * 100

        print(f"{year:10}   {actual_total if actual_total else 'N/A':>7}{'  ' if actual_total is None else 'pp'}  "
              f"{pred_total:>6.1f}pp  {'N/A' if mae is None else f'{mae:>6.1f}pp':>8}  "
              f"{mcq_total:>6.1f}pp  {solve_avg:>6.1f}pp  {hardest:>5.1f}pp")

        year_stats[year] = {
            'pred_total': pred_total,
            'actual_total': actual_total,
            'mcq_total': mcq_total,
            'solve_avg': solve_avg,
            'hardest': hardest,
        }

    # Feature averages per year
    print()
    print('=' * 90)
    print('各维度均值 · 5 年趋势')
    print('=' * 90)
    dim_names = ['context_familiarity', 'info_complexity', 'concept_count', 'topic_cross',
                 'depth_ord', 'open_ord', 'modeling', 'reasoning', 'computation']
    dim_labels = {
        'context_familiarity': '情境陌生度',
        'info_complexity': '信息呈现',
        'concept_count': '核心知识数',
        'topic_cross': '跨模块比例',
        'depth_ord': '知识深度',
        'open_ord': '开放度',
        'modeling': '建模复杂',
        'reasoning': '推理链',
        'computation': '运算复杂',
    }
    print(f"{'Year':10}", end='')
    for d in dim_names:
        print(f"  {dim_labels[d]:>7}", end='')
    print()
    print('-' * 100)
    for year in years:
        year_rows = [r for r in all_rows if r['paper']==year]
        if not year_rows:
            continue
        print(f"{year:10}", end='')
        for d in dim_names:
            vals = [r[d] for r in year_rows]
            print(f"  {np.mean(vals):>7.2f}", end='')
        print()

    # Focus on 2026 特点
    print()
    print('=' * 90)
    print('2026 vs 前 4 年均值 · 变化')
    print('=' * 90)
    prev = [r for r in all_rows if r['paper'].startswith('gaokao_') and r['paper']!='gaokao_2026']
    curr = [r for r in all_rows if r['paper']=='gaokao_2026']
    print(f"{'维度':>15}  {'2022-2025 均':>12}  {'2026':>8}  {'变化':>8}")
    print('-' * 60)
    for d in dim_names:
        pv = np.mean([r[d] for r in prev])
        cv = np.mean([r[d] for r in curr])
        delta = cv - pv
        arrow = '↑' if delta > 0.05 else ('↓' if delta < -0.05 else '·')
        print(f"{dim_labels[d]:>15}  {pv:>12.2f}  {cv:>8.2f}  {arrow} {delta:+.2f}")

    # Save comparison CSV
    OUT = ROOT / "data/labeled/5year_comparison.csv"
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['year', 'pred_total_pp', 'actual_total_pp', 'mcq_total_pp', 'solve_avg_pp', 'hardest_pp'])
        for year in years:
            s = year_stats.get(year, {})
            w.writerow([year, f"{s.get('pred_total', 0):.1f}",
                        s.get('actual_total', ''),
                        f"{s.get('mcq_total', 0):.1f}" if s.get('mcq_total') else '',
                        f"{s.get('solve_avg', 0):.1f}" if s.get('solve_avg') else '',
                        f"{s.get('hardest', 0):.1f}" if s.get('hardest') else ''])
    print()
    print(f'Comparison saved: {OUT}')


if __name__ == '__main__':
    main()
