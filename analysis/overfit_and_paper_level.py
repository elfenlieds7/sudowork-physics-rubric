"""Overfit sanity checks + paper-level MAE for current champion model.

Champion: v5.1 + concept nonlin + 30 trap labels · Lasso+GBM ensemble · MAE 0.0578

Checks:
1. Per-paper LOPO consistency (are any papers unusually good/bad?)
2. Train MAE vs LOPO MAE gap (overfit indicator)
3. Multi-seed variance (model stability)
4. Random-feature sanity (should not improve MAE)
5. Paper-level (weighted total) 得分率 prediction accuracy
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
sys.path.insert(0, str(Path(__file__).parent))
from pre_label_traps import TRAP_LABELS as TL

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"
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


def per_paper_weights(paper_rows):
    from collections import Counter
    main_counts = Counter()
    for r in paper_rows:
        if r['is_open'] == 1:
            main = r['qid'].split('-')[0]
            main_counts[main] += 1
    weights = []
    for r in paper_rows:
        if r['is_open'] == 0:
            weights.append(3.0)
        else:
            main = r['qid'].split('-')[0]
            try:
                total = {15: 8, 16: 10, 17: 9, 18: 9, 19: 10, 20: 12}.get(int(main), 3)
            except:
                total = 3
            n_subs = main_counts[main]
            weights.append(total / n_subs)
    return weights


def main():
    rows = load()
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in FEATS] for r in rows])
    logo = LeaveOneGroupOut()

    # =============================================================
    print("=" * 72)
    print("1. Per-paper LOPO consistency + train vs LOPO gap")
    print("=" * 72)
    per_paper = {}
    train_maes = []
    for tr, te in logo.split(X, y, groups):
        held = groups[te[0]]
        l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                       learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        yp_tr = (l.predict(X[tr]) + g.predict(X[tr])) / 2
        train_maes.append(mean_absolute_error(y[tr], yp_tr))
        yp_te = (l.predict(X[te]) + g.predict(X[te])) / 2
        per_paper[held] = {
            'lopo_mae': mean_absolute_error(y[te], yp_te),
            'lopo_r2': r2_score(y[te], yp_te),
            'n': len(te),
        }
    print(f"{'paper':<20} {'n':>4} {'LOPO_MAE':>10} {'LOPO_R2':>10}")
    for p in sorted(per_paper.keys()):
        d = per_paper[p]
        print(f"  {p:<18} {d['n']:>4} {d['lopo_mae']:>10.4f} {d['lopo_r2']:>10.4f}")
    lopo_maes = [d['lopo_mae'] for d in per_paper.values()]
    print(f"\n  LOPO MAE 均值 = {mean(lopo_maes):.4f} · SD across papers = {stdev(lopo_maes):.4f}")
    print(f"  Train MAE (LOPO 训练集内平均) = {mean(train_maes):.4f}")
    print(f"  Overfit gap (LOPO test - Train) = {mean(lopo_maes) - mean(train_maes):+.4f}")
    print(f"  (小 gap = ok · 大 gap = 过拟合)")

    # =============================================================
    print()
    print("=" * 72)
    print("2. Multi-seed GBM · 训练 stability (10 seeds)")
    print("=" * 72)
    seed_results = []
    for seed in [42, 1, 7, 100, 2024, 3, 17, 99, 84, 1234]:
        yt_all, yp_all = [], []
        for tr, te in logo.split(X, y, groups):
            m = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                           learning_rate=0.01, random_state=seed).fit(X[tr], y[tr])
            yt_all.extend(y[te].tolist())
            yp_all.extend(m.predict(X[te]).tolist())
        seed_results.append(mean_absolute_error(yt_all, yp_all))
        print(f"  seed={seed}: MAE = {seed_results[-1]:.4f}")
    print(f"\n  GBM 多 seed 均值 = {mean(seed_results):.4f} · SD = {stdev(seed_results):.4f}")
    print(f"  范围 [{min(seed_results):.4f}, {max(seed_results):.4f}]  (小 SD = ok)")

    # =============================================================
    print()
    print("=" * 72)
    print("3. 整卷加权得分率预测精度 · 用杨老师给的分值权重")
    print("=" * 72)
    y_pred_all = np.zeros(len(y))
    for tr, te in logo.split(X, y, groups):
        l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                       learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        y_pred_all[te] = (l.predict(X[te]) + g.predict(X[te])) / 2

    print(f"  {'paper':<20} {'实际总':>10} {'预测总':>10} {'误差(pp)':>10}")
    total_errors = []
    for paper in sorted(set(groups)):
        idx = [i for i, g in enumerate(groups) if g == paper]
        prows = [rows[i] for i in idx]
        weights = per_paper_weights(prows)
        tot_w = sum(weights)
        actual = sum(w * rows[idx[j]]['y'] for j, w in enumerate(weights)) / tot_w
        pred = sum(w * y_pred_all[idx[j]] for j, w in enumerate(weights)) / tot_w
        err = pred - actual
        total_errors.append(abs(err))
        print(f"  {paper:<20} {actual:>10.4f} {pred:>10.4f} {err*100:>+9.2f}")
    print(f"\n  整卷 MAE 平均 = {mean(total_errors)*100:.2f} 个百分点")
    print(f"  整卷 MAE 中位数 = {sorted(total_errors)[len(total_errors)//2]*100:.2f} 个百分点")
    print(f"  整卷 MAE 最大 = {max(total_errors)*100:.2f} 个百分点")
    print(f"  之前 (无 trap · v5.1 ensemble): 整卷 MAE = 1.40 pp")

    # =============================================================
    print()
    print("=" * 72)
    print("4. Sanity check · 加 1 个随机噪声特征 · MAE 应该几乎不变")
    print("=" * 72)
    np.random.seed(999)
    random_feat = np.random.randn(len(rows))
    X_r = np.column_stack([X, random_feat])
    yt_all, yp_all = [], []
    for tr, te in logo.split(X_r, y, groups):
        l = Lasso(alpha=0.001, max_iter=10000).fit(X_r[tr], y[tr])
        g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                       learning_rate=0.01, random_state=42).fit(X_r[tr], y[tr])
        yt_all.extend(y[te].tolist())
        yp_all.extend(((l.predict(X_r[te]) + g.predict(X_r[te])) / 2).tolist())
    random_mae = mean_absolute_error(yt_all, yp_all)
    print(f"  加 1 个随机噪声特征后: MAE = {random_mae:.4f}")
    print(f"  原 MAE (未加): 0.0578")
    print(f"  差 = {random_mae - 0.0578:+.4f}")
    print(f"  (近 0 = ok · 大幅改善 = 说明原模型 fit noise · overfit)")


if __name__ == "__main__":
    main()
