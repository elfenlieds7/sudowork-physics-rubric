"""Ethan 20:15 shareone comment cd3cfb39: 位置和难度共线, 需要统计解耦.

试 3 种处理:
A. 完全去掉 position 特征 (假设内容特征已抓住所有难度信号, position 只是 nuisance)
B. Residualize position: pos_resid = position - E[position | concept, reasoning, is_open, ...]
   这样 position 只剩下"控制内容后的意外位置" · 语义清晰
C. Keep raw position (v4 现状)
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"

V4_BASE = ["concept", "reasoning", "novelty", "visual", "modeling",
           "position", "is_open", "topic_mech", "topic_em",
           "textbook_scene_degree", "textbook_pattern_degree",
           "transfer_cost", "is_last_quarter", "earlier_load"]

# 用于回归 position 的内容特征 (排除 position 本身和它派生的 is_last_quarter/earlier_load)
CONTENT_FEATS = ["concept", "reasoning", "novelty", "visual", "modeling",
                 "is_open", "topic_mech", "topic_em",
                 "textbook_scene_degree", "textbook_pattern_degree",
                 "transfer_cost"]


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

def predict(X, beta):
    return [beta[0]+sum(beta[i+1]*row[i] for i in range(len(row))) for row in X]

def r_squared(y, y_hat):
    ybar = mean(y); ss_res = sum((yi-yhi)**2 for yi,yhi in zip(y,y_hat)); ss_tot = sum((yi-ybar)**2 for yi in y)
    return 1 - ss_res/ss_tot

def mae(y, y_hat):
    return mean(abs(yi-yhi) for yi,yhi in zip(y,y_hat))


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for f_name in ["concept","reasoning","novelty","visual","modeling",
                           "position","is_open","topic_mech","topic_em",
                           "textbook_scene_degree","textbook_pattern_degree"]:
                row[f_name] = float(r[f_name])
            rows.append(row)
    for r in rows:
        r["transfer_cost"] = max(0.0, r["textbook_pattern_degree"]-r["textbook_scene_degree"])
        r["is_last_quarter"] = 1.0 if r["position"] > 0.75 else 0.0
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["paper"],[]).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r["position"])
        for i,r in enumerate(s):
            r["earlier_load"] = mean(e["concept"] for e in s[:i]) if i else 0.0
    return rows


def make_x(r, feats):
    return [r[f] for f in feats]

def lopo(rows, feats):
    papers = sorted({r["paper"] for r in rows})
    yta, ypa = [], []
    for held in papers:
        train = [r for r in rows if r["paper"] != held]
        test = [r for r in rows if r["paper"] == held]
        beta = fit_ols([make_x(r, feats) for r in train], [r["y"] for r in train])
        yp = predict([make_x(r, feats) for r in test], beta)
        yt = [r["y"] for r in test]
        yta.extend(yt); ypa.extend(yp)
    return {"r2": r_squared(yta, ypa), "mae": mae(yta, ypa)}


def main():
    rows = load()
    y = [r["y"] for r in rows]

    # ============================================
    # 先看 position 和 content 的相关性
    # ============================================
    print("=" * 70)
    print("position 与内容特征的相关性 (Ethan 说的 共线)")
    print("=" * 70)
    ps = [r["position"] for r in rows]
    p_mean = mean(ps)
    for f in CONTENT_FEATS:
        xs = [r[f] for r in rows]
        mx = mean(xs)
        num = sum((x-mx)*(p-p_mean) for x,p in zip(xs, ps))
        denx = (sum((x-mx)**2 for x in xs))**0.5
        denp = (sum((p-p_mean)**2 for p in ps))**0.5
        corr = num/(denx*denp) if denx*denp>0 else 0
        marker = " ← 显著" if abs(corr) > 0.4 else ""
        print(f"  {f:<28} · corr with position = {corr:+.3f}{marker}")

    # ============================================
    # 实验 A · 去掉 position 特征
    # ============================================
    print("\n" + "=" * 70)
    print("A · 从 v4 里去掉 position (但保留 is_last_quarter · earlier_load)")
    print("=" * 70)
    A_feats = [f for f in V4_BASE if f != "position"]
    l_A = lopo(rows, A_feats)
    beta_A = fit_ols([make_x(r, A_feats) for r in rows], y)
    yhat_A = predict([make_x(r, A_feats) for r in rows], beta_A)
    print(f"  in-sample R² = {r_squared(y, yhat_A):.4f}   MAE = {mae(y, yhat_A):.4f}")
    print(f"  LOPO R² = {l_A['r2']:.4f}   MAE = {l_A['mae']:.4f}")

    # ============================================
    # 实验 B · Residualize position (跑 position ~ content 回归 · 用残差替换)
    # ============================================
    print("\n" + "=" * 70)
    print("B · Residualize position: pos_resid = position - E[position | 内容]")
    print("=" * 70)
    # fit position ~ content features
    X_content = [make_x(r, CONTENT_FEATS) for r in rows]
    beta_pos = fit_ols(X_content, ps)
    p_pred = predict(X_content, beta_pos)
    for r, p_p in zip(rows, p_pred):
        r["position_residual"] = r["position"] - p_p
    # 看残差范围
    pos_resids = [r["position_residual"] for r in rows]
    print(f"  position ~ content 回归 R² = {r_squared(ps, p_pred):.4f}")
    print(f"  position_residual 范围 = [{min(pos_resids):.3f}, {max(pos_resids):.3f}], SD = {(sum((x-mean(pos_resids))**2 for x in pos_resids)/len(pos_resids))**0.5:.3f}")
    # 用 position_residual 替换 position 在 v4 里
    B_feats = [f if f != "position" else "position_residual" for f in V4_BASE]
    l_B = lopo(rows, B_feats)
    beta_B = fit_ols([make_x(r, B_feats) for r in rows], y)
    yhat_B = predict([make_x(r, B_feats) for r in rows], beta_B)
    print(f"  in-sample R² = {r_squared(y, yhat_B):.4f}   MAE = {mae(y, yhat_B):.4f}")
    print(f"  LOPO R² = {l_B['r2']:.4f}   MAE = {l_B['mae']:.4f}")
    print(f"  position_residual 系数 β = {beta_B[B_feats.index('position_residual')+1]:+.4f}")

    # ============================================
    # 实验 C · v4 raw position (baseline)
    # ============================================
    print("\n" + "=" * 70)
    print("C · v4 现状 (raw position)")
    print("=" * 70)
    l_C = lopo(rows, V4_BASE)
    beta_C = fit_ols([make_x(r, V4_BASE) for r in rows], y)
    print(f"  in-sample R² = {r_squared(y, predict([make_x(r, V4_BASE) for r in rows], beta_C)):.4f}   MAE = {mae(y, predict([make_x(r, V4_BASE) for r in rows], beta_C)):.4f}")
    print(f"  LOPO R² = {l_C['r2']:.4f}   MAE = {l_C['mae']:.4f}")
    print(f"  position 系数 β = {beta_C[V4_BASE.index('position')+1]:+.4f}")

    # ============================================
    # Summary
    # ============================================
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"  {'模型':<36} {'LOPO R²':>10} {'LOPO MAE':>10}")
    print(f"  {'A · 去掉 position':<36} {l_A['r2']:>10.4f} {l_A['mae']:>10.4f}")
    print(f"  {'B · Residualize position':<36} {l_B['r2']:>10.4f} {l_B['mae']:>10.4f}")
    print(f"  {'C · v4 raw position (baseline)':<36} {l_C['r2']:>10.4f} {l_C['mae']:>10.4f}")


if __name__ == "__main__":
    main()
