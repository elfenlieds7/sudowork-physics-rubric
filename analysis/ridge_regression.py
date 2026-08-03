"""Ridge regression · L2 正则化.

在 v5.1 (17 特征) 上加 L2 penalty. 目标: 缓解交互项过拟合 (n=162 k=17 · n/k=9.5 边缘).
如果 Ridge 收紧了系数但 LOPO 反而降, 说明 OLS 在过拟合.
"""
import csv, sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"

BASE = ["concept","reasoning","novelty","visual","modeling","position","is_open",
        "topic_mech","topic_em","textbook_scene_degree","textbook_pattern_degree"]
NEW = ["transfer_cost","is_last_quarter","earlier_load"]
INT = ["mod_x_nov","mod_x_open","con_x_mod"]
V51 = BASE + NEW + INT


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

def fit_ridge(X, y, alpha):
    """Ridge: beta = (X^T X + alpha I)^-1 X^T y (标准化后)"""
    Xb = [[1.0]+row for row in X]
    XT = transpose(Xb)
    XTX = matmul(XT, Xb)
    # 加 alpha I to XTX (skip intercept)
    for i in range(1, len(XTX)):
        XTX[i][i] += alpha
    XTy = matmul(XT, [[v] for v in y])
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
    for r in rows:
        r["mod_x_nov"] = r["modeling"]*r["novelty"]
        r["mod_x_open"] = r["modeling"]*r["is_open"]
        r["con_x_mod"] = r["concept"]*r["modeling"]
    return rows

def make_x(r, feats): return [r[f] for f in feats]

def lopo_ridge(rows, feats, alpha):
    papers = sorted({r["paper"] for r in rows})
    yta, ypa = [], []
    for held in papers:
        train = [r for r in rows if r["paper"] != held]
        test = [r for r in rows if r["paper"] == held]
        beta = fit_ridge([make_x(r, feats) for r in train], [r["y"] for r in train], alpha)
        yp = predict([make_x(r, feats) for r in test], beta)
        yt = [r["y"] for r in test]
        yta.extend(yt); ypa.extend(yp)
    return {"r2": r_squared(yta, ypa), "mae": mae(yta, ypa)}


def main():
    rows = load()

    print(f"{'alpha':>8} {'LOPO R²':>10} {'LOPO MAE':>10}")
    print('-' * 32)
    for alpha in [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]:
        l = lopo_ridge(rows, V51, alpha)
        print(f"{alpha:>8.2f} {l['r2']:>10.4f} {l['mae']:>10.4f}")


if __name__ == "__main__":
    main()
