"""v5 探索 · 3 个实验:

A. Ablation: 依次删掉 concept / modeling / novelty · 看场景系数是否复活
   目的: 验证 v4 的因果解释 "场景独立信号被吸走了" 是不是对的
   期望: 如果去掉 concept 或 modeling, 场景系数应该上升
        (即 concept / modeling 打分时确实吸了 陌生场景 的信号)

B. Scene × Pattern 全 dummy: 用 dummy variables 编码 (scene, pattern) 9 个组合
   目的: 看看是不是只有 (0, 2) 组是异常低 · 还是所有 4 个非对角组都有信号
   期望: (0, 2) β 大负 (28pp 差是我们观察到的极端组)

C. 时间压力交互项: earlier_load × is_last_quarter · 直接测杨老师第 1 点假设
   期望: 交互系数负 (前段难 × 后段位置 → 得分率进一步下降)
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_JSON = REPO_ROOT / "data" / "labeled" / "rubric_v5_result.json"

V3_FEATURES = [
    "concept", "reasoning", "novelty", "visual", "modeling",
    "position", "is_open",
    "topic_mech", "topic_em",
    "textbook_scene_degree", "textbook_pattern_degree",
]


def transpose(M):
    return [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]


def matmul(A, B):
    m, k, n = len(A), len(A[0]), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)] for i in range(m)]


def inv(M):
    n = len(M)
    A = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[pivot] = A[pivot], A[col]
        pv = A[col][col]
        if abs(pv) < 1e-12:
            raise ValueError("singular at " + str(col))
        A[col] = [x / pv for x in A[col]]
        for r in range(n):
            if r == col:
                continue
            factor = A[r][col]
            A[r] = [A[r][c] - factor * A[col][c] for c in range(2 * n)]
    return [row[n:] for row in A]


def fit_ols(X, y):
    Xb = [[1.0] + row for row in X]
    XT = transpose(Xb)
    XTX = matmul(XT, Xb)
    XTy = matmul(XT, [[v] for v in y])
    return [b[0] for b in matmul(inv(XTX), XTy)]


def predict(X, beta):
    return [beta[0] + sum(beta[i + 1] * row[i] for i in range(len(row))) for row in X]


def r_squared(y, y_hat):
    ybar = mean(y)
    ss_res = sum((yi - yhi) ** 2 for yi, yhi in zip(y, y_hat))
    ss_tot = sum((yi - ybar) ** 2 for yi in y)
    return 1 - ss_res / ss_tot


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for f_name in V3_FEATURES:
                row[f_name] = float(r[f_name])
            row["position"] = float(r["position"])
            row["is_last_quarter"] = 1.0 if row["position"] > 0.75 else 0.0
            rows.append(row)

    # earlier_load
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["paper"], []).append(r)
    for pdata in by_paper.values():
        pdata_sorted = sorted(pdata, key=lambda r: r["position"])
        for i, r in enumerate(pdata_sorted):
            earlier = pdata_sorted[:i]
            r["earlier_load"] = mean(e["concept"] for e in earlier) if earlier else 0.0
    return rows


def make_x(r, feat_list):
    return [r[f] for f in feat_list]


def coef_for(rows, feats, name):
    beta = fit_ols([make_x(r, feats) for r in rows], [r["y"] for r in rows])
    if name in feats:
        return beta[feats.index(name) + 1]
    return None


# ============ Experiment A · Ablation ============
def experiment_a(rows):
    print("=" * 62)
    print("A · Ablation · 依次删掉 concept / modeling / novelty 特征")
    print("    看 场景相似度 系数是否复活")
    print("=" * 62)
    print(f"  {'model':<45} {'场景 β':>10} {'模式 β':>10}")

    for label, drop_list in [
        ("v3 baseline (11 features)", []),
        ("v3 - concept", ["concept"]),
        ("v3 - reasoning", ["reasoning"]),
        ("v3 - novelty", ["novelty"]),
        ("v3 - modeling", ["modeling"]),
        ("v3 - concept - modeling", ["concept", "modeling"]),
        ("v3 - concept - modeling - novelty", ["concept", "modeling", "novelty"]),
        ("v3 - concept - modeling - novelty - reasoning", ["concept", "modeling", "novelty", "reasoning"]),
    ]:
        feats = [f for f in V3_FEATURES if f not in drop_list]
        try:
            scene_b = coef_for(rows, feats, "textbook_scene_degree")
            pat_b = coef_for(rows, feats, "textbook_pattern_degree")
            print(f"  {label:<45} {scene_b:>+10.4f} {pat_b:>+10.4f}")
        except Exception as e:
            print(f"  {label:<45} ERROR: {e}")


# ============ Experiment B · Scene x Pattern 全 dummy ============
def experiment_b(rows):
    print("\n" + "=" * 62)
    print("B · Scene × Pattern 全 dummy · 看 9 组每组均分")
    print("=" * 62)
    print(f"  {'scene':>6} {'pattern':>8} {'n':>6} {'mean_y':>8}")
    for s in [0, 1, 2]:
        for p in [0, 1, 2]:
            sub = [r for r in rows if r["textbook_scene_degree"] == s and r["textbook_pattern_degree"] == p]
            if sub:
                print(f"  {s:>6} {p:>8} {len(sub):>6} {mean(r['y'] for r in sub):>8.3f}")
            else:
                print(f"  {s:>6} {p:>8} {0:>6} {'—':>8}")


# ============ Experiment C · 时间压力交互项 ============
def experiment_c(rows):
    print("\n" + "=" * 62)
    print("C · 时间压力交互项 · earlier_load × is_last_quarter")
    print("    杨老师假设: 前段难 & 位置靠后 → 得分率进一步下降")
    print("=" * 62)
    for r in rows:
        r["load_x_late"] = r["earlier_load"] * r["is_last_quarter"]

    v4_feats = V3_FEATURES + ["is_last_quarter", "earlier_load"]
    v5c_feats = v4_feats + ["load_x_late"]

    beta_v4 = fit_ols([make_x(r, v4_feats) for r in rows], [r["y"] for r in rows])
    beta_v5c = fit_ols([make_x(r, v5c_feats) for r in rows], [r["y"] for r in rows])

    print(f"  v4 (无交互项):")
    print(f"    earlier_load     β = {beta_v4[v4_feats.index('earlier_load')+1]:+.4f}")
    print(f"    is_last_quarter  β = {beta_v4[v4_feats.index('is_last_quarter')+1]:+.4f}")
    print(f"  v5c (加 load × late 交互项):")
    print(f"    earlier_load        β = {beta_v5c[v5c_feats.index('earlier_load')+1]:+.4f}")
    print(f"    is_last_quarter     β = {beta_v5c[v5c_feats.index('is_last_quarter')+1]:+.4f}")
    print(f"    load × late 交互    β = {beta_v5c[v5c_feats.index('load_x_late')+1]:+.4f}")

    # R² comparison
    yhat_v4 = predict([make_x(r, v4_feats) for r in rows], beta_v4)
    yhat_v5c = predict([make_x(r, v5c_feats) for r in rows], beta_v5c)
    print(f"  in-sample R² · v4 = {r_squared([r['y'] for r in rows], yhat_v4):.4f}")
    print(f"  in-sample R² · v5c = {r_squared([r['y'] for r in rows], yhat_v5c):.4f}")

    # 直接看: 后段位置 · 前段 concept 高 vs 前段 concept 低 的均分对比
    print(f"\n  直接验证 (无模型): 后段题 (position>0.75) 按 前段 concept load 分组")
    late = [r for r in rows if r["is_last_quarter"] == 1]
    late_sorted = sorted(late, key=lambda r: r["earlier_load"])
    n = len(late_sorted)
    lo = late_sorted[:n // 2]
    hi = late_sorted[n // 2:]
    print(f"    后段 · 前段 concept 低 · n={len(lo)} · 均分={mean(r['y'] for r in lo):.3f}")
    print(f"    后段 · 前段 concept 高 · n={len(hi)} · 均分={mean(r['y'] for r in hi):.3f}")


def main():
    rows = load()
    experiment_a(rows)
    experiment_b(rows)
    experiment_c(rows)


if __name__ == "__main__":
    main()
