"""v6 · 合并 v4 迁移成本 + v5c 时间压力交互项 · 跑 LOPO 看总体提升.

v6 特征 (15 个):
- 11 个 v3 baseline
- transfer_cost = max(0, pattern - scene)      [v4]
- is_last_quarter                              [v4]
- earlier_load                                 [v4]
- load_x_late = earlier_load × is_last_quarter [v5c]  ← 直接测杨老师第 1 点
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_JSON = REPO_ROOT / "data" / "labeled" / "rubric_v6_result.json"

BASE = ["concept", "reasoning", "novelty", "visual", "modeling",
        "position", "is_open", "topic_mech", "topic_em",
        "textbook_scene_degree", "textbook_pattern_degree"]

NEW = ["transfer_cost", "is_last_quarter", "earlier_load", "load_x_late"]

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


def predict(X, beta):
    return [beta[0] + sum(beta[i + 1] * row[i] for i in range(len(row))) for row in X]


def r_squared(y, y_hat):
    ybar = mean(y)
    ss_res = sum((yi - yhi) ** 2 for yi, yhi in zip(y, y_hat))
    ss_tot = sum((yi - ybar) ** 2 for yi in y)
    return 1 - ss_res / ss_tot


def mae(y, y_hat):
    return mean(abs(yi - yhi) for yi, yhi in zip(y, y_hat))


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for f_name in BASE:
                row[f_name] = float(r[f_name])
            row["position"] = float(r["position"])
            rows.append(row)

    # engineered
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

    for r in rows:
        r["load_x_late"] = r["earlier_load"] * r["is_last_quarter"]
    return rows


def make_x(r, feats):
    return [r[f] for f in feats]


def lopo(rows, feats):
    papers = sorted({r["paper"] for r in rows})
    yta, ypa = [], []
    per = {}
    for held in papers:
        train = [r for r in rows if r["paper"] != held]
        test = [r for r in rows if r["paper"] == held]
        beta = fit_ols([make_x(r, feats) for r in train], [r["y"] for r in train])
        yp = predict([make_x(r, feats) for r in test], beta)
        yt = [r["y"] for r in test]
        yta.extend(yt); ypa.extend(yp)
        per[held] = {"n": len(test), "r2": r_squared(yt, yp), "mae": mae(yt, yp)}
    return {"r2": r_squared(yta, ypa), "mae": mae(yta, ypa), "per_paper": per}


def main():
    rows = load()
    print(f"n = {len(rows)}, features = {len(ALL)}")
    print()

    y = [r["y"] for r in rows]

    for label, feats in [
        ("v3 (11 特征)", BASE),
        ("v4 (14 特征 · 加 transfer_cost + is_last_quarter + earlier_load)", BASE + NEW[:3]),
        ("v6 (15 特征 · v4 + load × late 交互项)", ALL),
    ]:
        beta = fit_ols([make_x(r, feats) for r in rows], y)
        yhat = predict([make_x(r, feats) for r in rows], beta)
        l = lopo(rows, feats)
        print(f"{label}")
        print(f"  in-sample R² = {r_squared(y, yhat):.4f}   MAE = {mae(y, yhat):.4f}")
        print(f"  LOPO R²      = {l['r2']:.4f}   MAE = {l['mae']:.4f}")
        print()

    # v6 系数 detail
    beta_v6 = fit_ols([make_x(r, ALL) for r in rows], y)
    print("v6 全部系数:")
    print(f"  {'feature':<28} {'β':>10}")
    print(f"  {'intercept':<28} {beta_v6[0]:>+10.4f}")
    for name, b in zip(ALL, beta_v6[1:]):
        marker = " ← NEW" if name in NEW else ""
        print(f"  {name:<28} {b:>+10.4f}{marker}")

    # v6 每份 held-out
    print(f"\nv6 · 每份 held-out 试卷 LOPO:")
    l_v6 = lopo(rows, ALL)
    print(f"  {'paper':<18} {'R²':>8} {'MAE':>8}")
    for p in sorted(l_v6["per_paper"].keys()):
        d = l_v6["per_paper"][p]
        print(f"  {p:<18} {d['r2']:>8.4f} {d['mae']:>8.4f}")

    # save
    result = {
        "features": ALL,
        "v6_in_sample_r2": r_squared(y, predict([make_x(r, ALL) for r in rows], beta_v6)),
        "v6_lopo_r2": l_v6["r2"],
        "v6_lopo_mae": l_v6["mae"],
        "v6_beta": {"intercept": beta_v6[0], **{ALL[i]: beta_v6[i+1] for i in range(len(ALL))}},
        "v6_per_paper": l_v6["per_paper"],
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
