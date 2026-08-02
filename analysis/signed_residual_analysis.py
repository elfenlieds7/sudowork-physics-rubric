"""Signed residual 分析 · Ethan 提议的方向.

拆开正负两类看:
- 正残差 (实际 > 预测): 我低估了学生 · 学生比预测做得好 · 为什么?
- 负残差 (实际 < 预测): 我高估了学生 · 学生比预测做得差 · 为什么?

对每一类, 看 top-20 大残差题的共同特征. 反推成因假设.
"""
import csv
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
    return [[sum(A[i][p]*B[p][j] for p in range(k)) for j in range(n)] for i in range(m)]

def inv(M):
    n = len(M); A = [row[:]+[1 if i==j else 0 for j in range(n)] for i,row in enumerate(M)]
    for col in range(n):
        pivot = max(range(col,n), key=lambda r: abs(A[r][col])); A[col],A[pivot] = A[pivot],A[col]
        pv = A[col][col]; A[col] = [x/pv for x in A[col]]
        for r in range(n):
            if r==col: continue
            f = A[r][col]; A[r] = [A[r][c]-f*A[col][c] for c in range(2*n)]
    return [row[n:] for row in A]

def fit_ols(X, y):
    Xb = [[1.0]+row for row in X]
    XT = transpose(Xb); XTX = matmul(XT,Xb); XTy = matmul(XT,[[v] for v in y])
    return [b[0] for b in matmul(inv(XTX), XTy)]


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid":r["question_id"],"paper":r["paper_id"],"y":float(r["score_rate"])}
            for fn in BASE: row[fn] = float(r[fn])
            rows.append(row)
    for r in rows:
        r["transfer_cost"] = max(0.0, r["textbook_pattern_degree"]-r["textbook_scene_degree"])
        r["is_last_quarter"] = 1.0 if r["position"]>0.75 else 0.0
    by_paper = {}
    for r in rows: by_paper.setdefault(r["paper"],[]).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r["position"])
        for i,r in enumerate(s):
            r["earlier_load"] = mean(e["concept"] for e in s[:i]) if i else 0.0
    return rows


def group_by(rows, key_fn, name):
    buckets = {}
    for r in rows:
        buckets.setdefault(key_fn(r), []).append(r)
    print(f"\n{name}")
    print(f"  {'group':<24} {'n':>4} {'负残差数':>10} {'正残差数':>10} {'均负残差':>12} {'均正残差':>12}")
    for k in sorted(buckets.keys(), key=str):
        sub = buckets[k]
        neg = [r["resid"] for r in sub if r["resid"] < 0]
        pos = [r["resid"] for r in sub if r["resid"] > 0]
        neg_mean = mean(neg) if neg else 0
        pos_mean = mean(pos) if pos else 0
        print(f"  {str(k):<24} {len(sub):>4} {len(neg):>10} {len(pos):>10} {neg_mean:>+12.4f} {pos_mean:>+12.4f}")


def main():
    rows = load()
    beta = fit_ols([[r[f] for f in ALL] for r in rows], [r["y"] for r in rows])
    for r in rows:
        r["pred"] = beta[0] + sum(beta[i+1]*r[ALL[i]] for i in range(len(ALL)))
        r["resid"] = r["y"] - r["pred"]

    neg_all = [r for r in rows if r["resid"] < 0]
    pos_all = [r for r in rows if r["resid"] > 0]
    print(f"总: {len(rows)} 道题 · 负残差 {len(neg_all)} · 正残差 {len(pos_all)}")
    print(f"负残差均值 {mean(r['resid'] for r in neg_all):.4f} · 正残差均值 {mean(r['resid'] for r in pos_all):.4f}")

    # Top 20 大负残差 (模型高估 · 学生实际做得差)
    print(f"\n{'='*76}")
    print(f"Top 20 · 模型高估学生 (负残差 · 我预测简单但学生实际难)")
    print(f"{'='*76}")
    print(f"  {'#':<3} {'paper':<15} {'qid':<8} {'实际':>5} {'预测':>5} {'残差':>7} {'open':>4} {'con':>3} {'rea':>3} {'nov':>3} {'mod':>3} {'scn':>3} {'pat':>3}")
    top_neg = sorted(neg_all, key=lambda r: r["resid"])[:20]  # most negative first
    for i, r in enumerate(top_neg, 1):
        print(f"  {i:<3} {r['paper']:<15} {r['qid']:<8} {r['y']:>5.2f} {r['pred']:>5.2f} {r['resid']:>+7.3f} " +
              f"{int(r['is_open']):>4} {int(r['concept']):>3} {int(r['reasoning']):>3} " +
              f"{int(r['novelty']):>3} {int(r['modeling']):>3} {int(r['textbook_scene_degree']):>3} " +
              f"{int(r['textbook_pattern_degree']):>3}")

    # Top 20 大正残差 (模型低估 · 学生实际做得好)
    print(f"\n{'='*76}")
    print(f"Top 20 · 模型低估学生 (正残差 · 我预测难但学生实际做得好)")
    print(f"{'='*76}")
    print(f"  {'#':<3} {'paper':<15} {'qid':<8} {'实际':>5} {'预测':>5} {'残差':>7} {'open':>4} {'con':>3} {'rea':>3} {'nov':>3} {'mod':>3} {'scn':>3} {'pat':>3}")
    top_pos = sorted(pos_all, key=lambda r: -r["resid"])[:20]  # most positive first
    for i, r in enumerate(top_pos, 1):
        print(f"  {i:<3} {r['paper']:<15} {r['qid']:<8} {r['y']:>5.2f} {r['pred']:>5.2f} {r['resid']:>+7.3f} " +
              f"{int(r['is_open']):>4} {int(r['concept']):>3} {int(r['reasoning']):>3} " +
              f"{int(r['novelty']):>3} {int(r['modeling']):>3} {int(r['textbook_scene_degree']):>3} " +
              f"{int(r['textbook_pattern_degree']):>3}")

    # 对比: 平均特征值 (top-20 负 vs top-20 正 vs 全体)
    print(f"\n{'='*76}")
    print(f"特征均值对比: top-20 负残差 vs top-20 正残差 vs 全体")
    print(f"{'='*76}")
    print(f"  {'特征':<28} {'top-负均值':>12} {'top-正均值':>12} {'全体均值':>10} {'差':>7}")
    for f in ALL:
        n_avg = mean(r[f] for r in top_neg)
        p_avg = mean(r[f] for r in top_pos)
        all_avg = mean(r[f] for r in rows)
        diff = n_avg - p_avg
        marker = " ← 显著" if abs(diff) > 0.5 else ""
        print(f"  {f:<28} {n_avg:>+12.3f} {p_avg:>+12.3f} {all_avg:>+10.3f} {diff:>+7.3f}{marker}")

    # 按 sub-group 看 signed residual
    def topic(r):
        if r["topic_mech"]: return "力学"
        if r["topic_em"]: return "电磁"
        return "热光近代"
    group_by(rows, topic, "按话题看正负残差分布")
    group_by(rows, lambda r: "大题分问" if r["is_open"] else "选择题", "按题型看正负残差分布")
    group_by(rows, lambda r: f"scene{int(r['textbook_scene_degree'])}_pat{int(r['textbook_pattern_degree'])}",
             "按 场景×模式 看正负残差分布")
    def pq(r):
        p = r["position"]
        if p < 0.25: return "Q1 前段"
        if p < 0.5: return "Q2"
        if p < 0.75: return "Q3"
        return "Q4 后段"
    group_by(rows, pq, "按位置四分位看正负残差分布")


if __name__ == "__main__":
    main()
