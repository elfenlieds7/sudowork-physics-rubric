"""v6 · 全 223 道陷阱数 (30 老师 label + 193 我 heuristic) · 试多个模型 + 交互项.

Heuristic 遵循老师严格版原则:
- 每题识别 1-2 个核心真会错的地方, 不 stack multiple
- 默认低 (0-1), 只在明确复杂时给 2-3
- 陷阱不是刻意设计, 是知识关联性

Based on 老师 30 items patterns:
- concept 1-2 · 通常 0-1
- concept 3 · 通常 1
- concept 4-5 · 通常 1-2
- 大题最后小问 (modeling 高 + is_open) · 通常 2-3
- 唯一 3 只出现在极难题 (小行星 · 涉及 3 层错误)
"""
import csv, sys
from pathlib import Path
from statistics import mean

sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# Import teacher's actual 30 labels
sys.path.insert(0, str(Path(__file__).parent))
from pre_label_traps import TRAP_LABELS as TEACHER_LABELS

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"
BASE = ['concept','reasoning','novelty','visual','modeling','position','is_open',
        'topic_mech','topic_em','textbook_scene_degree','textbook_pattern_degree']


def heuristic_trap(r):
    """遵循老师严格版原则给未 label 的 193 items 一个 heuristic trap_count."""
    concept = r['concept']
    is_open = r['is_open']
    modeling = r['modeling']
    novelty = r['novelty']
    reasoning = r['reasoning']

    # Base from concept · 匹配她的观察
    if concept <= 1:
        base = 0
    elif concept == 2:
        base = 0 if is_open == 0 else 1  # MCQ 简单 · 大题稍有陷阱
    elif concept == 3:
        base = 1
    else:  # concept >= 4
        base = 1 if is_open == 0 else 2

    # 大题最后小问 · modeling 高 · 可能更多陷阱
    if is_open and modeling >= 3 and reasoning >= 4:
        base = min(3, base + 1)

    # 简单情境题 · 只是套公式 · 减
    if is_open == 0 and reasoning <= 1 and modeling <= 0:
        base = 0

    return float(min(3, max(0, base)))


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid":r["question_id"],"paper":r["paper_id"],"y":float(r["score_rate"])}
            for fn in BASE: row[fn] = float(r[fn])
            rows.append(row)
    for r in rows:
        r["transfer_cost"] = max(0.0, r["textbook_pattern_degree"]-r["textbook_scene_degree"])
        r["is_last_quarter"] = 1.0 if r["position"] > 0.75 else 0.0
    by_paper = {}
    for r in rows: by_paper.setdefault(r["paper"],[]).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r["position"])
        for i,r in enumerate(s):
            r["earlier_load"] = mean(e["concept"] for e in s[:i]) if i else 0.0
    for r in rows:
        r["mod_x_nov"] = r["modeling"]*r["novelty"]
        r["mod_x_open"] = r["modeling"]*r["is_open"]
        r["con_x_mod"] = r["concept"]*r["modeling"]
        # 陷阱数 · 30 用老师 · 193 用 heuristic
        key = (r['paper'], r['qid'])
        if key in TEACHER_LABELS:
            r['trap_count'] = float(TEACHER_LABELS[key][0])
            r['trap_source'] = 'teacher'
        else:
            r['trap_count'] = heuristic_trap(r)
            r['trap_source'] = 'heuristic'
        # concept nonlinearities
        r['concept_sq'] = r['concept']**2
        r['con_is_2'] = 1.0 if r['concept'] == 2 else 0.0
        r['con_is_3'] = 1.0 if r['concept'] == 3 else 0.0
        r['con_is_4'] = 1.0 if r['concept'] == 4 else 0.0
        r['con_is_5'] = 1.0 if r['concept'] == 5 else 0.0
        r['con_x_scene'] = r['concept']*r['textbook_scene_degree']
        # trap 交互
        r['trap_x_concept'] = r['trap_count'] * r['concept']
        r['trap_x_open'] = r['trap_count'] * r['is_open']
    return rows


def main():
    rows = load()
    teacher_n = sum(1 for r in rows if r['trap_source'] == 'teacher')
    heuristic_n = sum(1 for r in rows if r['trap_source'] == 'heuristic')
    print(f"陷阱数分布: teacher={teacher_n} · heuristic={heuristic_n} · total={len(rows)}")
    # 分布
    from collections import Counter
    dist = Counter(int(r['trap_count']) for r in rows)
    print(f"trap_count 分布: {sorted(dist.items())}")
    # avg by source
    t_avg = mean(r['trap_count'] for r in rows if r['trap_source']=='teacher')
    h_avg = mean(r['trap_count'] for r in rows if r['trap_source']=='heuristic')
    print(f"平均 trap: teacher={t_avg:.2f} · heuristic={h_avg:.2f}")

    y = np.array([r['y'] for r in rows])
    groups = [r['paper'] for r in rows]
    logo = LeaveOneGroupOut()

    def lopo_multi(feats):
        X = np.array([[r[f] for f in feats] for r in rows])
        y_true, preds = [], {'Ridge':[],'Lasso':[],'GBM':[],'XGB':[],'LGB':[]}
        for tr, te in logo.split(X, y, groups):
            models = {
                'Ridge': Ridge(alpha=2.0),
                'Lasso': Lasso(alpha=0.001, max_iter=10000),
                'GBM': GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42),
                'XGB': XGBRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42, verbosity=0),
                'LGB': LGBMRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42, verbose=-1),
            }
            y_true.extend(y[te].tolist())
            for name, m in models.items():
                m.fit(X[tr], y[tr])
                preds[name].extend(m.predict(X[te]).tolist())
        yt = np.array(y_true)
        results = {name: (r2_score(yt, np.array(p)), mean_absolute_error(yt, np.array(p))) for name, p in preds.items()}
        # Ensemble avg (Lasso + GBM)
        avg = (np.array(preds['Lasso']) + np.array(preds['GBM']))/2
        results['LassoGBM_avg'] = (r2_score(yt, avg), mean_absolute_error(yt, avg))
        # All ensemble
        all_avg = np.mean([np.array(preds[n]) for n in preds], axis=0)
        results['ALL_avg'] = (r2_score(yt, all_avg), mean_absolute_error(yt, all_avg))
        return results

    V51 = BASE + ['transfer_cost','is_last_quarter','earlier_load','mod_x_nov','mod_x_open','con_x_mod']
    V51_nonlin = V51 + ['concept_sq','con_is_2','con_is_3','con_is_4','con_is_5','con_x_scene']

    experiments = [
        ('baseline v5.1 (no trap)', V51),
        ('v5.1 + trap (full 223)', V51 + ['trap_count']),
        ('v5.1 + trap + trap_x_concept', V51 + ['trap_count','trap_x_concept']),
        ('v5.1 + trap + trap_x_open', V51 + ['trap_count','trap_x_open']),
        ('v5.1 + trap + both interactions', V51 + ['trap_count','trap_x_concept','trap_x_open']),
        ('v5.1 + nonlin + trap', V51_nonlin + ['trap_count']),
        ('v5.1 + nonlin + trap + both int', V51_nonlin + ['trap_count','trap_x_concept','trap_x_open']),
    ]

    print()
    print(f"{'实验':<45} {'Ridge':>7} {'Lasso':>7} {'GBM':>7} {'XGB':>7} {'LGB':>7} {'LasGBM':>7} {'ALL':>7}")
    print('-' * 100)
    for label, feats in experiments:
        r = lopo_multi(feats)
        print(f"{label:<45} " + ' '.join(f"{r[m][1]:>7.4f}" for m in ['Ridge','Lasso','GBM','XGB','LGB','LassoGBM_avg','ALL_avg']))


if __name__ == "__main__":
    main()
