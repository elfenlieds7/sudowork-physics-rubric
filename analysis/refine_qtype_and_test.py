"""Refine 题型 label for Q15/16 (实验题 · 有填空 + 解答小问) · retrain · LOPO + overfit.

杨老师 23:38: "填空题并不少 · 高考试卷和模拟试卷中的实验题即 15、16 题, 很多小问都是
填空题, 这里面需要识别有些也是选择题, 比如给出几个选项让填在空里. 纯的填空题难度要
比选择题大, 得分率往往会低一些."

现状: 训练集 Q15/16 (48 道) 全部 is_open = 1 · 与 Q17-20 解答题同粒度.

Heuristic v1 (this script):
- Q15/16-1 · Q15/16-2: 填空 → is_open = 0.5
- Q15/16-3 及以后: 解答 → is_open = 1 (保持)
- Q17-20 所有小问: 解答 → is_open = 1 (保持)
- Q1-14: 选择 → is_open = 0 (保持)

比较: v5.6 baseline vs v6.1 (refined is_open) LOPO MAE. 若降 · commit;
若升 · 说明启发式不够 · 报告等杨老师 hand-label.
"""
import csv
import re
import sys
from pathlib import Path
from statistics import mean
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from pre_label_traps import TRAP_LABELS as TL

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "data" / "labeled" / "combined_scored_v3.csv"

BASE = ['concept', 'reasoning', 'novelty', 'visual', 'modeling', 'position', 'is_open',
        'topic_mech', 'topic_em', 'textbook_scene_degree', 'textbook_pattern_degree']
FEATS = BASE + ['transfer_cost', 'is_last_quarter', 'earlier_load',
                'mod_x_nov', 'mod_x_open', 'con_x_mod',
                'concept_sq', 'con_is_2', 'con_is_3', 'con_is_4', 'con_is_5',
                'con_x_scene', 'trap_count']


def sub_index(qid):
    """Extract sub-question index from qid like '15-2a' or '16-3' -> 2 or 3."""
    m = re.match(r'\d+-(\d+)', qid)
    return int(m.group(1)) if m else None


def load_and_optionally_refine(refine=False):
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for fn in BASE:
                row[fn] = float(r[fn])
            # Refine is_open for Q15/16
            if refine:
                mq = re.match(r'(\d+)', row['qid'])
                if mq and int(mq.group(1)) in (15, 16):
                    si = sub_index(row['qid'])
                    # Also consider 16-a / 16-b (letter sub-indices) as sub 1-2 approximation
                    if si is not None and si <= 2:
                        row['is_open'] = 0.5
                    elif re.search(r'-[ab]$', row['qid']):
                        row['is_open'] = 0.5
                    # else keep as 1
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


def lopo(rows, feats):
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in feats] for r in rows])
    logo = LeaveOneGroupOut()
    yts, yps = [], []
    per_paper_mae = {}
    for tr, te in logo.split(X, y, groups):
        l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                      learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        yp = (l.predict(X[te]) + g.predict(X[te])) / 2
        yts.extend(y[te].tolist())
        yps.extend(yp.tolist())
        per_paper_mae[groups[te[0]]] = mean_absolute_error(y[te], yp)
    return mean_absolute_error(yts, yps), r2_score(yts, yps), per_paper_mae


def check_relabeled_items(rows_baseline, rows_refined):
    """Where did we relabel · and what's the pred change?"""
    changed = []
    for a, b in zip(rows_baseline, rows_refined):
        if a['is_open'] != b['is_open']:
            changed.append((a['paper'], a['qid'], a['is_open'], b['is_open'], a['y']))
    return changed


def main():
    baseline = load_and_optionally_refine(refine=False)
    refined = load_and_optionally_refine(refine=True)
    changed = check_relabeled_items(baseline, refined)
    print(f"Relabeled items: {len(changed)}")
    print(f"{'paper':<15} {'qid':<10} {'old':>4} {'new':>4} {'y_true':>7}")
    for row in changed[:15]:
        print(f"  {row[0]:<13} Q{row[1]:<8} {row[2]:>4} {row[3]:>4} {row[4]:>7.2f}")
    if len(changed) > 15:
        print(f"  ... 加 {len(changed)-15} 条")

    print()
    print("=" * 60)
    print("LOPO 比较")
    print("=" * 60)
    b_mae, b_r2, b_pp = lopo(baseline, FEATS)
    r_mae, r_r2, r_pp = lopo(refined, FEATS)
    print(f"Baseline (Q15/16 全部 is_open=1): MAE {b_mae:.4f} · R² {b_r2:.4f}")
    print(f"Refined  (Q15/16-1,-2 = 0.5)   : MAE {r_mae:.4f} · R² {r_r2:.4f}")
    delta = r_mae - b_mae
    if delta < 0:
        print(f"\n✅ Refined 降低 MAE by {-delta*10000:.1f} bps · 填空 vs 解答 区分有独立信号")
    else:
        print(f"\n⚠️ Refined 升高 MAE by {delta*10000:.1f} bps · 启发式仍不够")

    print()
    print(f"Per-paper LOPO MAE:")
    print(f"  {'paper':<15} {'baseline':>10} {'refined':>10} {'diff':>8}")
    for p in sorted(b_pp):
        d = r_pp[p] - b_pp[p]
        print(f"  {p:<15} {b_pp[p]:>10.4f} {r_pp[p]:>10.4f} {d:>+8.4f}")


if __name__ == "__main__":
    main()
