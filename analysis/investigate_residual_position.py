"""投她第 1 点问题: 残差大的题在试卷位置上是否有规律?
杨老师假设: 前面难题耗时多 → 后面题目实际比预测更难 → 后段负残差 (模型高估)

Test: 对每份试卷, 分位置 quartile 看残差均值 · 也看"整卷前段平均难度" vs "后段残差均值"
"""
import csv
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"

FEATURES = [
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


def main():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "qid": r["question_id"], "paper": r["paper_id"],
                "y": float(r["score_rate"]),
                "x": [float(r[f]) for f in FEATURES],
                "pos": float(r["position"]),
                "concept": float(r["concept"]),
                "reasoning": float(r["reasoning"]),
            })

    beta = fit_ols([r["x"] for r in rows], [r["y"] for r in rows])
    for r in rows:
        r["pred"] = beta[0] + sum(beta[i+1] * r["x"][i] for i in range(len(FEATURES)))
        r["resid"] = r["y"] - r["pred"]

    # A · 按 position quartile 看残差
    print("=" * 60)
    print("A · 按位置 quartile 看残差均值 (每卷内部 quartile · 混所有卷)")
    print("=" * 60)
    quartile_bins = [(0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.01)]
    labels = ["Q1 (0-25%)", "Q2 (25-50%)", "Q3 (50-75%)", "Q4 (75-100%)"]
    for (lo, hi), lbl in zip(quartile_bins, labels):
        subset = [r["resid"] for r in rows if lo <= r["pos"] < hi]
        if subset:
            print(f"  {lbl:<15} n={len(subset):3d}  平均残差={mean(subset):+.4f}  |残差|均值={mean(abs(x) for x in subset):.4f}  SD={pstdev(subset):.4f}")

    # B · 每份试卷单独看 quartile 残差
    print("\n" + "=" * 60)
    print("B · 每份试卷单独看 · 后半段 (position > 0.5) 平均残差")
    print("=" * 60)
    print(f"  杨老师假设: 若前段难则后段 res 偏负 (模型高估)")
    print(f"  {'paper':<18} {'前段均值':>10} {'后段res均值':>12} {'方向':>8}")
    for paper in sorted({r["paper"] for r in rows}):
        pdata = [r for r in rows if r["paper"] == paper]
        first_half_score = mean(r["y"] for r in pdata if r["pos"] <= 0.5)
        second_half_resid = mean(r["resid"] for r in pdata if r["pos"] > 0.5)
        # "前段简单" = first_half_score 高, 那么后段可能有余力 → resid 正
        # "前段难" = first_half_score 低, 后段没时间 → resid 负
        direction = "支持假设" if first_half_score < 0.7 and second_half_resid < 0 else \
                    "反例" if first_half_score < 0.7 and second_half_resid > 0 else \
                    "无强信号"
        print(f"  {paper:<18} {first_half_score:>10.3f} {second_half_resid:>+12.4f} {direction:>10}")

    # C · 直接相关: (卷前段均分) vs (卷后段残差均值) 跨 5 卷
    print("\n" + "=" * 60)
    print("C · 跨试卷 · 前段均分 vs 后段残差均值 (5 数据点相关)")
    print("=" * 60)
    per_paper = {}
    for paper in sorted({r["paper"] for r in rows}):
        pdata = [r for r in rows if r["paper"] == paper]
        per_paper[paper] = {
            "first_half_score": mean(r["y"] for r in pdata if r["pos"] <= 0.5),
            "second_half_resid": mean(r["resid"] for r in pdata if r["pos"] > 0.5),
        }
    xs = [per_paper[p]["first_half_score"] for p in per_paper]
    ys = [per_paper[p]["second_half_resid"] for p in per_paper]
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    deny = (sum((y - my) ** 2 for y in ys)) ** 0.5
    corr = num / (denx * deny) if denx * deny > 0 else 0
    print(f"  Pearson r = {corr:+.3f}  (n=5, 只能定性)")
    if corr > 0.3:
        print(f"  → 前段越简单 → 后段残差越正 (模型低估后段, 也就是学生后段做得比预测好)")
        print(f"    这也侧面支持杨老师假设 (镜像方向): 前段难 → 后段负残差 → 模型高估")
    elif corr < -0.3:
        print(f"  → 前段越简单 → 后段残差越负 (与杨老师假设相反)")
    else:
        print(f"  → 相关性弱, 5 份试卷内没看出前段-后段耦合信号")

    # D · 具体列一下 20 个 top-|residual| 的题的位置分布
    print("\n" + "=" * 60)
    print("D · 20 个 top-|residual| 的题的位置分布 (回她具体问)")
    print("=" * 60)
    top = sorted(rows, key=lambda r: -abs(r["resid"]))[:20]
    pos_bins = {"前段 (0-0.5)": 0, "中段 (0.5-0.75)": 0, "后段 (0.75-1.0)": 0}
    for r in top:
        if r["pos"] < 0.5:
            pos_bins["前段 (0-0.5)"] += 1
        elif r["pos"] < 0.75:
            pos_bins["中段 (0.5-0.75)"] += 1
        else:
            pos_bins["后段 (0.75-1.0)"] += 1
    for k, v in pos_bins.items():
        print(f"  {k}: {v}/20 道")

    # E · 分符号看 top-residual 的位置分布 (正 vs 负)
    print("\n  按符号拆:")
    pos_resid = [r for r in top if r["resid"] > 0]
    neg_resid = [r for r in top if r["resid"] < 0]
    print(f"  正残差 (模型低估, 学生做得比预测好): {len(pos_resid)} 道 · " + \
          f"位置均值 {mean(r['pos'] for r in pos_resid):.3f}")
    print(f"  负残差 (模型高估, 学生做得比预测差): {len(neg_resid)} 道 · " + \
          f"位置均值 {mean(r['pos'] for r in neg_resid):.3f}")


if __name__ == "__main__":
    main()
