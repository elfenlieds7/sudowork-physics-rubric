"""残差诊断 · 找 v4 系统性预测不准的题类 · 目标: 从当前 MAE 0.073 拉到 0.05.

拆分维度:
1. 按 concept level (1-5) · 看 mean |residual| 是否随概念难度变化
2. 按 topic (mech/em/toam)
3. 按 is_open (选择题 vs 大题子问)
4. 按 场景 × 模式 9 组
5. 按 position 四分位
6. 按 novelty · modeling · visual 分档
7. 按每份试卷分组

对每类计算 mean residual (bias · 是否系统性) + mean |residual| (spread · 是否分布散)

Also: top-30 大残差题 · 手工挑 pattern.
"""
import csv
import json
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"

BASE = ["concept", "reasoning", "novelty", "visual", "modeling",
        "position", "is_open", "topic_mech", "topic_em",
        "textbook_scene_degree", "textbook_pattern_degree"]

NEW = ["transfer_cost", "is_last_quarter", "earlier_load"]

ALL = BASE + NEW


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


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for f_name in BASE:
                row[f_name] = float(r[f_name])
            row["position"] = float(r["position"])
            rows.append(row)

    for r in rows:
        s = r["textbook_scene_degree"]
        p = r["textbook_pattern_degree"]
        r["transfer_cost"] = max(0.0, p - s)
        r["is_last_quarter"] = 1.0 if r["position"] > 0.75 else 0.0

    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["paper"], []).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r["position"])
        for i, r in enumerate(s):
            r["earlier_load"] = mean(e["concept"] for e in s[:i]) if i else 0.0

    return rows


def group_stats(rows, key_fn, label):
    """key_fn(r) → bucket label"""
    buckets = {}
    for r in rows:
        buckets.setdefault(key_fn(r), []).append(r)
    print(f"\n{label}")
    print(f"  {'group':<20} {'n':>4} {'mean_resid':>12} {'mean|resid|':>13} {'mean_y':>8} {'mean_pred':>10}")
    for k in sorted(buckets.keys(), key=str):
        sub = buckets[k]
        mr = mean(r["resid"] for r in sub)
        mar = mean(abs(r["resid"]) for r in sub)
        my = mean(r["y"] for r in sub)
        mp = mean(r["pred"] for r in sub)
        print(f"  {str(k):<20} {len(sub):>4} {mr:>+12.4f} {mar:>13.4f} {my:>8.3f} {mp:>10.3f}")


def main():
    rows = load()

    beta = fit_ols([[r[f] for f in ALL] for r in rows], [r["y"] for r in rows])
    for r in rows:
        r["pred"] = beta[0] + sum(beta[i+1] * r[ALL[i]] for i in range(len(ALL)))
        r["resid"] = r["y"] - r["pred"]

    print(f"n = {len(rows)}, features = {len(ALL)}")
    overall_mar = mean(abs(r["resid"]) for r in rows)
    print(f"整体 MAE = {overall_mar:.4f}")
    print(f"目标: MAE ≤ 0.050  (需要削减 {(overall_mar - 0.05) / overall_mar * 100:.0f}% 误差)")

    # 1. concept level
    group_stats(rows, lambda r: f"concept={int(r['concept'])}", "1. 按概念数分组")
    # 2. topic
    def topic(r):
        if r["topic_mech"]: return "力学"
        if r["topic_em"]: return "电磁"
        return "热光近代"
    group_stats(rows, topic, "2. 按话题分组")
    # 3. is_open
    group_stats(rows, lambda r: "大题分问" if r["is_open"] else "选择题", "3. 按题型分组")
    # 4. 场景 × 模式 9 组
    group_stats(rows, lambda r: f"scene{int(r['textbook_scene_degree'])}_pat{int(r['textbook_pattern_degree'])}",
                "4. 按 场景×模式 分组")
    # 5. position quartile
    def pq(r):
        p = r["position"]
        if p < 0.25: return "Q1 前段"
        if p < 0.5: return "Q2"
        if p < 0.75: return "Q3"
        return "Q4 后段"
    group_stats(rows, pq, "5. 按位置四分位分组")
    # 6. novelty
    group_stats(rows, lambda r: f"novelty={int(r['novelty'])}", "6. 按情境新颖度分组")
    # 7. modeling
    group_stats(rows, lambda r: f"modeling={int(r['modeling'])}", "7. 按建模自主度分组")
    # 8. paper
    group_stats(rows, lambda r: r["paper"], "8. 按试卷分组")

    # top 30 |residual|
    print(f"\n\n=== Top 30 大 |residual| 题目 ===")
    print(f"  {'#':<3} {'paper':<15} {'qid':<8} {'actual':>7} {'pred':>7} {'resid':>8} {'open':>4} {'topic':>4} {'scn':>3} {'pat':>3} {'con':>3} {'rea':>3}")
    top = sorted(rows, key=lambda r: -abs(r["resid"]))[:30]
    for i, r in enumerate(top, 1):
        t = "mech" if r["topic_mech"] else ("em" if r["topic_em"] else "toam")
        print(f"  {i:<3} {r['paper']:<15} {r['qid']:<8} {r['y']:>7.2f} {r['pred']:>7.2f} {r['resid']:>+8.3f} "
              f"{int(r['is_open']):>4} {t:>4} {int(r['textbook_scene_degree']):>3} "
              f"{int(r['textbook_pattern_degree']):>3} {int(r['concept']):>3} {int(r['reasoning']):>3}")

    # 相关系数: 各特征绝对值 vs |resid|
    print(f"\n\n=== |residual| 和各特征的相关系数 (哪个特征值高 · |残差| 也高) ===")
    print(f"  正相关意味着 特征越大 我预测越不准 · 该特征可能 under-modeled")
    ar = [abs(r["resid"]) for r in rows]
    mar_ = mean(ar)
    for f_name in ALL:
        xs = [r[f_name] for r in rows]
        mx = mean(xs)
        num = sum((x - mx) * (a - mar_) for x, a in zip(xs, ar))
        denx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
        dena = (sum((a - mar_) ** 2 for a in ar)) ** 0.5
        corr = num / (denx * dena) if denx * dena > 0 else 0
        print(f"  {f_name:<28}  corr = {corr:+.3f}")


if __name__ == "__main__":
    main()
