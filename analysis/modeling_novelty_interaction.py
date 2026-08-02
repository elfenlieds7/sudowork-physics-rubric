"""基于杨老师 20:58-21:00 洞察 (学生卡步骤 2 建模 · 压轴题难在建模) · 试交互项.

假设: novel 情境 (novelty 高) 且 需要自主建模 (modeling 高) 的题 · 建模难度尤其大
新特征: modeling_novelty_interact = modeling × novelty  (乘积)

比如霍尔推进器: modeling=2 novelty=2 → interact=4 (高建模难度)
气流机翼: modeling=3 novelty=3 → interact=9 (最高)
氘氚核反应: modeling=0 novelty=0 → interact=0 (最低)

Fit v5 = v4 + interact · 看 LOPO 是否改善
"""
import csv
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"

BASE = ["concept","reasoning","novelty","visual","modeling",
        "position","is_open","topic_mech","topic_em",
        "textbook_scene_degree","textbook_pattern_degree"]
NEW = ["transfer_cost","is_last_quarter","earlier_load"]
V4 = BASE + NEW

def transpose(M): return [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]
def matmul(A,B):
    m,k,n = len(A),len(A[0]),len(B[0])
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
def fit_ols(X,y):
    Xb = [[1.0]+row for row in X]
    XT = transpose(Xb); XTX = matmul(XT,Xb); XTy = matmul(XT,[[v] for v in y])
    return [b[0] for b in matmul(inv(XTX), XTy)]
def predict(X, beta):
    return [beta[0]+sum(beta[i+1]*row[i] for i in range(len(row))) for row in X]
def r_squared(y, y_hat):
    ybar = mean(y); ss_res = sum((yi-yhi)**2 for yi,yhi in zip(y,y_hat)); ss_tot = sum((yi-ybar)**2 for yi in y)
    return 1 - ss_res/ss_tot
def mae(y, y_hat): return mean(abs(yi-yhi) for yi,yhi in zip(y,y_hat))


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
    # 新特征
    for r in rows:
        r["mod_x_nov"] = r["modeling"] * r["novelty"]  # 建模 × 新颖 交互
        r["mod_x_open"] = r["modeling"] * r["is_open"]  # 建模 × 大题
        r["nov_x_open"] = r["novelty"] * r["is_open"]  # 新颖 × 大题
        r["mod_x_nov_x_open"] = r["modeling"] * r["novelty"] * r["is_open"]  # 三阶交互
    return rows

def make_x(r, feats): return [r[f] for f in feats]
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

    experiments = [
        ("baseline v4 (14 特征)", V4),
        ("v4 + mod × nov (15)", V4 + ["mod_x_nov"]),
        ("v4 + mod × open (15)", V4 + ["mod_x_open"]),
        ("v4 + nov × open (15)", V4 + ["nov_x_open"]),
        ("v4 + mod × nov × open (15)", V4 + ["mod_x_nov_x_open"]),
        ("v4 + all 4 interactions (18)", V4 + ["mod_x_nov","mod_x_open","nov_x_open","mod_x_nov_x_open"]),
        ("v4 + mod × nov + mod × open (16)", V4 + ["mod_x_nov","mod_x_open"]),
    ]

    print(f"{'实验':<40} {'in-sample R²':>13} {'LOPO R²':>10} {'LOPO MAE':>10}")
    print("-" * 78)
    for label, feats in experiments:
        try:
            beta = fit_ols([make_x(r, feats) for r in rows], y)
            yhat = predict([make_x(r, feats) for r in rows], beta)
            l = lopo(rows, feats)
            print(f"{label:<40} {r_squared(y, yhat):>13.4f} {l['r2']:>10.4f} {l['mae']:>10.4f}")
        except Exception as e:
            print(f"{label:<40} ERROR: {e}")

    # 看最好那个的系数
    print("\n" + "="*78)
    print("v4 + mod × nov + mod × open · 详细系数")
    print("="*78)
    fs = V4 + ["mod_x_nov","mod_x_open"]
    beta = fit_ols([make_x(r, fs) for r in rows], y)
    print(f"  截距: {beta[0]:+.4f}")
    for name, b in zip(fs, beta[1:]):
        marker = " ← NEW" if name in ("mod_x_nov","mod_x_open","nov_x_open","mod_x_nov_x_open") else ""
        print(f"  {name:<28}: {b:+.4f}{marker}")


if __name__ == "__main__":
    main()
