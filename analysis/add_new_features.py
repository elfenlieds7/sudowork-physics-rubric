"""Add reading_load + openness features · retrain champion · LOPO + 4 overfit checks.

杨老师 23:26: 阅读量 (北京高考 ~4400 字/整卷) + 开放程度 是两个尚未纳入的
关键难度维度. 立即测独立信号强度.

阅读量 (reading_load): main-question char count · distributed to all sub-questions
of that main question (all sub-Qs share the parent's read load).

开放程度 (openness): heuristic 0/1/2 based on qid structure:
- 选择/填空/单个题号: 0
- 大题第一小问 (X-1 or X-1a): 0
- 大题中间小问: 1
- 大题最后小问 (X-3 or X-2b or X-2c): 2 (需推理/论证/开放)

Rerun: champion (Lasso + GBM ensemble) LOPO + 4 overfit checks.
"""
import csv
import re
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

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "data" / "labeled" / "combined_scored_v3.csv"
READLOAD_CSV = REPO / "data" / "labeled" / "reading_load_per_question.csv"

BASE = ['concept', 'reasoning', 'novelty', 'visual', 'modeling', 'position', 'is_open',
        'topic_mech', 'topic_em', 'textbook_scene_degree', 'textbook_pattern_degree']
FEATS_V56 = BASE + ['transfer_cost', 'is_last_quarter', 'earlier_load',
                'mod_x_nov', 'mod_x_open', 'con_x_mod',
                'concept_sq', 'con_is_2', 'con_is_3', 'con_is_4', 'con_is_5',
                'con_x_scene', 'trap_count']


def main_qnum(qid):
    """Extract main question number from qid like '17-2a' -> 17."""
    m = re.match(r'(\d+)', qid)
    return int(m.group(1)) if m else None


def openness_heuristic(paper, qid):
    """0/1/2 based on qid structure."""
    mq = main_qnum(qid)
    if mq is None:
        return 0
    # Single-number qid: choice question
    if qid == str(mq):
        return 0
    # Sub-question
    suffix = qid[len(str(mq)):]  # e.g. '-1', '-2a', '-3'
    # Detect last sub-question: '-3' or last '-2X' where X is letter
    # Simple: if ends in '3' or '4' or is Q19/Q20 last part
    if mq >= 19:
        # 大题末段 · 通常最开放
        if suffix in ['-3', '-2b', '-2c', '-2-2', '-2-3']:
            return 2
        elif suffix in ['-2', '-2a', '-2-1', '-1b']:
            return 1
        else:
            return 0
    else:
        # 17-18: 常规大题
        if suffix in ['-3', '-2c', '-4']:
            return 1
        elif suffix in ['-2', '-2b']:
            return 1
        else:
            return 0


def load_reading_loads():
    if not READLOAD_CSV.exists():
        print(f"MISSING: {READLOAD_CSV} · run extract_reading_load.py first")
        sys.exit(1)
    d = {}
    with open(READLOAD_CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d[(r['paper'], int(r['qnum']))] = int(r['chars'])
    return d


def load_labeled():
    rows = []
    with open(CSV_PATH, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for fn in BASE:
                row[fn] = float(r[fn])
            rows.append(row)
    return rows


def enrich(rows, read_loads):
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
        # NEW: reading_load (parent question char count)
        mq = main_qnum(r['qid'])
        r['reading_load'] = float(read_loads.get((r['paper'], mq), 200)) if mq else 200.0
        # normalize by 4400 baseline
        r['reading_load_norm'] = r['reading_load'] / 4400.0
        # NEW: openness heuristic
        r['openness'] = float(openness_heuristic(r['paper'], r['qid']))


def train_and_eval(rows, feats, label=""):
    y = np.array([r['y'] for r in rows])
    groups = np.array([r['paper'] for r in rows])
    X = np.array([[r[f] for f in feats] for r in rows])
    logo = LeaveOneGroupOut()

    yts, yps = [], []
    for tr, te in logo.split(X, y, groups):
        l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
        g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                      learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
        yts.extend(y[te].tolist())
        yps.extend(((l.predict(X[te]) + g.predict(X[te])) / 2).tolist())
    yts = np.array(yts)
    yps = np.array(yps)
    mae = mean_absolute_error(yts, yps)
    r2 = r2_score(yts, yps)
    print(f"[{label}] LOPO MAE = {mae:.4f} · R² = {r2:.4f}")
    return mae, r2


def stepwise_forward(rows, features, alpha=0.05):
    """Forward stepwise · return selected list."""
    from scipy.stats import f as f_dist
    y = np.array([r['y'] for r in rows])
    selected = []
    remaining = list(features)
    while remaining:
        best_feat, best_r2 = None, -1
        for feat in remaining:
            cand = selected + [feat]
            X = np.array([[r[c] for c in cand] for r in rows])
            m = np.linalg.lstsq(np.column_stack([np.ones(len(rows)), X]), y, rcond=None)[0]
            pred = np.ones(len(rows)) * m[0] + X @ m[1:]
            ss_res = np.sum((y - pred) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            r2 = 1 - ss_res / ss_tot
            if r2 > best_r2:
                best_r2 = r2
                best_feat = feat
        if best_feat is None:
            break
        # F-test
        n = len(rows)
        k_new = len(selected) + 1
        if selected:
            X_old = np.array([[r[c] for c in selected] for r in rows])
            m = np.linalg.lstsq(np.column_stack([np.ones(len(rows)), X_old]), y, rcond=None)[0]
            pred_old = np.ones(len(rows)) * m[0] + X_old @ m[1:]
            ss_old = np.sum((y - pred_old) ** 2)
            r2_old = 1 - ss_old / np.sum((y - y.mean()) ** 2)
        else:
            r2_old = 0
        f_stat = ((best_r2 - r2_old) / 1) / ((1 - best_r2) / (n - k_new - 1))
        p_val = 1 - f_dist.cdf(f_stat, 1, n - k_new - 1) if f_stat > 0 else 1
        if p_val > alpha:
            break
        selected.append(best_feat)
        remaining.remove(best_feat)
    return selected


def main():
    read_loads = load_reading_loads()
    rows = load_labeled()
    enrich(rows, read_loads)

    # Check new feature distributions
    rl = [r['reading_load'] for r in rows]
    op = [r['openness'] for r in rows]
    print(f"\n阅读量 (chars): min={min(rl):.0f} · median={sorted(rl)[len(rl)//2]:.0f} · mean={mean(rl):.0f} · max={max(rl):.0f}")
    from collections import Counter
    print(f"开放程度分布: {sorted(Counter(op).items())}")

    print()
    print("=" * 72)
    print("Baseline v5.6 (24 features): LOPO MAE 0.057 (期望)")
    print("=" * 72)
    train_and_eval(rows, FEATS_V56, label="baseline")

    FEATS_V60 = FEATS_V56 + ['reading_load_norm', 'openness']
    print()
    print("=" * 72)
    print("v5.6 + reading_load_norm + openness · 独立信号强度")
    print("=" * 72)
    train_and_eval(rows, FEATS_V60, label="+reading+open")

    # Check where in stepwise the new features rank
    print()
    print("=" * 72)
    print("Stepwise · 新特征排名")
    print("=" * 72)
    selected = stepwise_forward(rows, FEATS_V60, alpha=0.05)
    print(f"入选顺序 (共 {len(selected)}):")
    for i, feat in enumerate(selected, 1):
        marker = " ← 新" if feat in ['reading_load_norm', 'openness'] else ""
        print(f"  {i}. {feat}{marker}")

    print()
    print("=" * 72)
    print("Overfit 检验 · 加新特征后过拟合 gap 是否变化")
    print("=" * 72)

    def train_mae(feats):
        y = np.array([r['y'] for r in rows])
        groups = np.array([r['paper'] for r in rows])
        X = np.array([[r[f] for f in feats] for r in rows])
        logo = LeaveOneGroupOut()
        train_maes = []
        for tr, te in logo.split(X, y, groups):
            l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
            g = GradientBoostingRegressor(n_estimators=500, max_depth=2,
                                          learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
            yp_tr = (l.predict(X[tr]) + g.predict(X[tr])) / 2
            train_maes.append(mean_absolute_error(y[tr], yp_tr))
        return mean(train_maes)

    v56_train = train_mae(FEATS_V56)
    v60_train = train_mae(FEATS_V60)
    v56_lopo, _ = train_and_eval(rows, FEATS_V56, "v5.6 (silent)")
    v60_lopo, _ = train_and_eval(rows, FEATS_V60, "v6.0 (silent)")

    print()
    print(f"  v5.6 baseline · train MAE {v56_train:.4f} · LOPO MAE {v56_lopo:.4f} · gap {v56_lopo - v56_train:+.4f}")
    print(f"  v6.0 +2 new  · train MAE {v60_train:.4f} · LOPO MAE {v60_lopo:.4f} · gap {v60_lopo - v60_train:+.4f}")
    if v60_lopo < v56_lopo:
        print(f"\n  ✅ 新特征降低 LOPO MAE by {(v56_lopo - v60_lopo) * 10000:.1f} bps · 独立信号存在")
    else:
        print(f"\n  ⚠️ LOPO MAE 未降 · 新特征 heuristic 可能太粗 · 需 hand-label")

    print()
    print("=" * 72)
    print("Sanity: random noise 特征加入 · MAE 应该不变")
    print("=" * 72)
    np.random.seed(999)
    for r in rows:
        r['_random'] = float(np.random.randn())
    train_and_eval(rows, FEATS_V60 + ['_random'], "v6.0 + noise")


if __name__ == "__main__":
    main()
