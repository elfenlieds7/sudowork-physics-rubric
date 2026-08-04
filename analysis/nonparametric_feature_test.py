"""Non-parametric feature significance test · 复用冯雪媚 2022 方法学.

For each of our 17 features · run Kruskal-Wallis H (multi-level) or Mann-Whitney U
(binary) against 得分率 to test independent contribution. Then run stepwise linear
regression to see how many survive.

Output: significance table + stepwise selection sequence · usable directly as
Section X.Y in the paper.
"""
import csv
import sys
from pathlib import Path
from statistics import mean
import numpy as np
from scipy.stats import kruskal, mannwhitneyu, spearmanr
from sklearn.linear_model import LinearRegression

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from pre_label_traps import TRAP_LABELS as TL

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"
BASE = ['concept', 'reasoning', 'novelty', 'visual', 'modeling', 'position', 'is_open',
        'topic_mech', 'topic_em', 'textbook_scene_degree', 'textbook_pattern_degree']
FEATS = BASE + ['transfer_cost', 'is_last_quarter', 'earlier_load',
                'mod_x_nov', 'mod_x_open', 'con_x_mod',
                'concept_sq', 'con_is_2', 'con_is_3', 'con_is_4', 'con_is_5',
                'con_x_scene', 'trap_count']

DISPLAY_NAME = {
    'concept': '概念数',
    'reasoning': '推理步数',
    'novelty': '情境新颖度',
    'visual': '视觉复杂度',
    'modeling': '建模自主度',
    'position': '题号位置',
    'is_open': '大题子问',
    'topic_mech': '力学',
    'topic_em': '电磁学',
    'textbook_scene_degree': '场景相似度',
    'textbook_pattern_degree': '模式相似度',
    'transfer_cost': '迁移成本',
    'is_last_quarter': '卷面末段',
    'earlier_load': '前段累积载荷',
    'mod_x_nov': '建模×新颖',
    'mod_x_open': '建模×大题',
    'con_x_mod': '概念×建模',
    'concept_sq': '概念平方',
    'con_is_2': '概念=2',
    'con_is_3': '概念=3',
    'con_is_4': '概念=4',
    'con_is_5': '概念=5',
    'con_x_scene': '概念×场景',
    'trap_count': '陷阱数',
}


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


def nonparametric_test(rows, feat):
    """Return (test_type, statistic, p_value, n_groups)."""
    y = np.array([r['y'] for r in rows])
    x = np.array([r[feat] for r in rows])
    unique = np.unique(x)
    groups = [y[x == v] for v in unique]
    groups = [g for g in groups if len(g) >= 3]  # need at least 3 samples per group
    if len(groups) < 2:
        return ("insufficient", np.nan, np.nan, len(groups))
    if len(groups) == 2:
        stat, p = mannwhitneyu(groups[0], groups[1], alternative='two-sided')
        return ("Mann-Whitney U", stat, p, 2)
    stat, p = kruskal(*groups)
    return (f"Kruskal-Wallis H (k={len(groups)})", stat, p, len(groups))


def spearman_test(rows, feat):
    y = np.array([r['y'] for r in rows])
    x = np.array([r[feat] for r in rows])
    rho, p = spearmanr(x, y)
    return rho, p


def stepwise_forward(rows, features, alpha=0.05, max_features=None):
    """Forward stepwise linear regression. Add best feature per step by F-test p-value."""
    y = np.array([r['y'] for r in rows])
    selected = []
    remaining = list(features)
    history = []
    if max_features is None:
        max_features = len(features)
    while remaining and len(selected) < max_features:
        best_feat = None
        best_r2 = -1
        best_p = 1
        for feat in remaining:
            cand = selected + [feat]
            X = np.column_stack([[r[c] for c in cand] for r in rows]) if False else np.array([[r[c] for c in cand] for r in rows])
            m = LinearRegression().fit(X, y)
            r2 = m.score(X, y)
            if r2 > best_r2:
                best_r2 = r2
                best_feat = feat
        if best_feat is None:
            break
        # F-test: does adding best_feat significantly improve fit?
        n = len(rows)
        k_new = len(selected) + 1
        if selected:
            X_old = np.array([[r[c] for c in selected] for r in rows])
            m_old = LinearRegression().fit(X_old, y)
            r2_old = m_old.score(X_old, y)
        else:
            r2_old = 0.0
        f_stat = ((best_r2 - r2_old) / 1) / ((1 - best_r2) / (n - k_new - 1))
        from scipy.stats import f as f_dist
        p_val = 1 - f_dist.cdf(f_stat, 1, n - k_new - 1) if f_stat > 0 else 1.0
        history.append({
            'step': len(selected) + 1,
            'feat': best_feat,
            'delta_r2': best_r2 - r2_old,
            'cumulative_r2': best_r2,
            'f_stat': f_stat,
            'p_val': p_val,
        })
        if p_val > alpha:
            history[-1]['stopped'] = True
            break
        selected.append(best_feat)
        remaining.remove(best_feat)
    return selected, history


def main():
    rows = load()
    print(f"n = {len(rows)} items · 17-feature base rubric")

    print()
    print("=" * 84)
    print("Step 1 · Non-parametric significance per feature (K-W / M-W-U) + Spearman")
    print("=" * 84)
    print(f"{'特征':<20} {'类型':<28} {'stat':>10} {'p-value':>12} {'ρ':>8} {'signif':>8}")
    print("-" * 96)
    results = []
    for feat in FEATS:
        test, stat, p, k = nonparametric_test(rows, feat)
        rho, prho = spearman_test(rows, feat)
        sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else '-'))
        results.append({'feat': feat, 'p': p, 'rho': rho, 'sig': sig})
        display = DISPLAY_NAME.get(feat, feat)
        print(f"{display:<20} {test:<28} {stat if stat==stat else 0:>10.3f} "
              f"{p if p==p else 1:>12.2e} {rho:>+8.3f} {sig:>8}")

    n_sig = sum(1 for r in results if r['p'] < 0.05)
    n_sig01 = sum(1 for r in results if r['p'] < 0.01)
    n_sig001 = sum(1 for r in results if r['p'] < 0.001)
    print(f"\n显著性汇总: p<0.05: {n_sig}/17 · p<0.01: {n_sig01}/17 · p<0.001: {n_sig001}/17")

    print()
    print("=" * 84)
    print("Step 2 · 前向逐步回归 (Stepwise Forward · α=0.05)")
    print("=" * 84)
    selected, history = stepwise_forward(rows, FEATS, alpha=0.05)
    print(f"{'step':>4} {'feat':<20} {'ΔR²':>8} {'累积 R²':>10} {'F':>8} {'p-value':>12}")
    for h in history:
        stopped = ' ← 停止 (未通过 α)' if h.get('stopped') else ''
        print(f"{h['step']:>4} {DISPLAY_NAME.get(h['feat'], h['feat']):<20} "
              f"{h['delta_r2']:>8.4f} {h['cumulative_r2']:>10.4f} "
              f"{h['f_stat']:>8.2f} {h['p_val']:>12.2e}{stopped}")
    print(f"\n最终入选 {len(selected)} 个特征 (17 里保留 {len(selected)} · 淘汰 {17-len(selected)})")
    if selected:
        print(f"  入选顺序: " + " → ".join(DISPLAY_NAME.get(f, f) for f in selected))

    print()
    print("=" * 84)
    print("Step 3 · 与冯雪媚 2022 结果对比")
    print("=" * 84)
    print("冯雪媚 2022 (广西合格性 · 108 单选题) 5 维保留 · R²=0.74")
    print(f"我们 (西城 高考 · 223 题) {len(selected)} 维保留 · 逐步回归 R²={history[-1]['cumulative_r2'] if history else 0:.4f}")
    print()
    print("说明: 我们的 R² 天花板不代表最优模型 · 只是线性模型的实力.")
    print("Champion (Lasso+GBM 集成 · LOPO) 单题 MAE = 0.057 · 对应 R² ≈ 0.89.")
    print("逐步回归主要用于: (a) 验证多维独立信号 · (b) 论文中论证特征必要性 · (c) 对照文献方法.")


def overfit_check_stepwise(rows):
    """Compare in-sample R² to LOPO R² for stepwise-selected features.

    Two flavors:
    - Naive (pre-selected features · LOPO): may still be inflated because feature
      selection was done on full data
    - Nested (stepwise per fold · LOPO): honest — feature selection redone in each
      training fold
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import LeaveOneGroupOut

    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    logo = LeaveOneGroupOut()

    print()
    print("=" * 84)
    print("Step 4 · Overfit check on stepwise-regression R²=0.91")
    print("=" * 84)

    # ---- 4a: naive LOPO with pre-selected 6 features ----
    print("\n4a · Naive LOPO (pre-selected 6 features · feature list frozen on full data):")
    selected, _ = stepwise_forward(rows, FEATS, alpha=0.05)
    print(f"  预选特征: {selected}")
    ys_all, yp_all = [], []
    per_paper_r2 = {}
    for tr, te in logo.split(rows, y, groups):
        Xtr = np.array([[rows[i][c] for c in selected] for i in tr])
        Xte = np.array([[rows[i][c] for c in selected] for i in te])
        m = LinearRegression().fit(Xtr, y[tr])
        yp = m.predict(Xte)
        ys_all.extend(y[te].tolist())
        yp_all.extend(yp.tolist())
        held = groups[te[0]]
        per_paper_r2[held] = float(np.corrcoef(y[te], yp)[0, 1] ** 2) if len(te) > 1 else np.nan
    ys_all = np.array(ys_all)
    yp_all = np.array(yp_all)
    lopo_mae = float(np.mean(np.abs(ys_all - yp_all)))
    lopo_r2 = float(1 - np.sum((ys_all - yp_all) ** 2) / np.sum((ys_all - ys_all.mean()) ** 2))
    print(f"  LOPO MAE = {lopo_mae:.4f}")
    print(f"  LOPO R²  = {lopo_r2:.4f}")
    print(f"  In-sample R² (前面报的) = 0.9076")
    print(f"  Gap (in-sample - LOPO) = {0.9076 - lopo_r2:+.4f}")
    print(f"  Per-paper LOPO R²:")
    for p in sorted(per_paper_r2):
        print(f"    {p:<15} R² = {per_paper_r2[p]:.4f}")
    sd = np.std(list(per_paper_r2.values()))
    print(f"  Per-paper R² SD = {sd:.4f}  (低 = 一致 · 高 = 某卷 leak)")

    # ---- 4b: nested LOPO (stepwise per fold) ----
    print("\n4b · Nested LOPO (stepwise 重新在每 fold 训练集上跑 · 无 feature-selection leak):")
    ys_all, yp_all = [], []
    fold_selections = {}
    for tr, te in logo.split(rows, y, groups):
        held = groups[te[0]]
        tr_rows = [rows[i] for i in tr]
        fold_selected, _ = stepwise_forward(tr_rows, FEATS, alpha=0.05, max_features=6)
        fold_selections[held] = fold_selected
        Xtr = np.array([[rows[i][c] for c in fold_selected] for i in tr])
        Xte = np.array([[rows[i][c] for c in fold_selected] for i in te])
        m = LinearRegression().fit(Xtr, y[tr])
        yp = m.predict(Xte)
        ys_all.extend(y[te].tolist())
        yp_all.extend(yp.tolist())
    ys_all = np.array(ys_all)
    yp_all = np.array(yp_all)
    nested_mae = float(np.mean(np.abs(ys_all - yp_all)))
    nested_r2 = float(1 - np.sum((ys_all - yp_all) ** 2) / np.sum((ys_all - ys_all.mean()) ** 2))
    print(f"  Nested LOPO MAE = {nested_mae:.4f}")
    print(f"  Nested LOPO R²  = {nested_r2:.4f}")
    print()
    print(f"  Per-fold stepwise selections (顺序 · 前 6):")
    for p in sorted(fold_selections):
        print(f"    {p:<15}: {' → '.join(DISPLAY_NAME.get(f, f) for f in fold_selections[p][:6])}")

    # ---- 4c: random-feature sanity check ----
    print("\n4c · Random-noise sanity check:")
    np.random.seed(999)
    rand_feat = np.random.randn(len(rows))
    for r_, v in zip(rows, rand_feat):
        r_['_random'] = float(v)
    feats_with_noise = FEATS + ['_random']
    DISPLAY_NAME['_random'] = '随机噪声'
    ys_all, yp_all = [], []
    n_selected_noise = 0
    for tr, te in logo.split(rows, y, groups):
        tr_rows = [rows[i] for i in tr]
        fold_selected, _ = stepwise_forward(tr_rows, feats_with_noise, alpha=0.05, max_features=6)
        if '_random' in fold_selected:
            n_selected_noise += 1
        Xtr = np.array([[rows[i][c] for c in fold_selected] for i in tr])
        Xte = np.array([[rows[i][c] for c in fold_selected] for i in te])
        m = LinearRegression().fit(Xtr, y[tr])
        yp = m.predict(Xte)
        ys_all.extend(y[te].tolist())
        yp_all.extend(yp.tolist())
    ys_all = np.array(ys_all)
    yp_all = np.array(yp_all)
    noise_r2 = float(1 - np.sum((ys_all - yp_all) ** 2) / np.sum((ys_all - ys_all.mean()) ** 2))
    print(f"  加随机特征后 nested LOPO R² = {noise_r2:.4f}")
    print(f"  vs 无随机特征 nested LOPO R² = {nested_r2:.4f}")
    print(f"  差 = {noise_r2 - nested_r2:+.4f}  (近 0 = ok)")
    print(f"  随机特征在 7 次 fold 里被 stepwise 选中的次数 = {n_selected_noise} / 7  (低 = ok)")

    print()
    print("=" * 84)
    print("综合判断")
    print("=" * 84)
    gap = 0.9076 - nested_r2
    if gap < 0.05:
        judge = "健康 · 无严重过拟合"
    elif gap < 0.10:
        judge = "轻度过拟合 · 但仍可信"
    else:
        judge = "过拟合警告 · 报告 nested LOPO R² 更诚实"
    print(f"  In-sample R² = 0.9076")
    print(f"  Naive LOPO R² = {lopo_r2:.4f} (feature list frozen)")
    print(f"  Nested LOPO R² = {nested_r2:.4f} (feature list per-fold)")
    print(f"  最保守估计 (nested LOPO R²) = {nested_r2:.4f}")
    print(f"  过拟合 gap = {gap:+.4f}")
    print(f"  判断: {judge}")


if __name__ == "__main__":
    main()
    print()
    print("### 追加过拟合检验 (Ethan 08-05 提醒) ###")
    print()
    rows = load()
    overfit_check_stepwise(rows)
