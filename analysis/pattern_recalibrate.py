"""杨老师 21:39 抽查校准 · 系统性修正 pattern 打分.

她的规则 (推断出的):
- pattern=2 只有当 scene=2 (直接套用, 无需迁移) · 场景 novel 或变形时应该更低
- 5 道抽查里: 2 道我 pattern=2 但她给 0 (都是 scene=0 pat=2 的迁移类)
- 1 道我 pattern=1 但她给 0 (阿秒光脉冲, 也是 scene=0)

修正策略:
- 对 (scene=0, pattern=2) 组: pattern → 0  (完全靠类比 · 无 pattern 信号)
- 对 (scene=1, pattern=2) 组: pattern → 1  (需要小改造, 不是直接套)
- 对 (scene=0, pattern=1) 组: 保留 1 或降到 0? 她 阿秒光脉冲 (scene=0 pat=1) 给了 0, 说明可能全降到 0
  但样本只 1 道, 先只降 1 → 试保留和降两版

试 2 个策略:
- A: 只降 (scene=0,pat=2)→0 + (scene=1,pat=2)→1  (最保守, 30 道受影响)
- B: A 之上加 (scene=0,pat=1)→0  (更激进, 15 道额外受影响)

Fit 一遍看 LOPO 是否降 MAE / 场景 · 模式 系数是否更强
"""
import csv, json
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


def recalibrate_pattern(rows, strategy):
    """回填修正后的 pattern · 重新算 transfer_cost."""
    changed = 0
    for r in rows:
        s = int(r["textbook_scene_degree"])
        p = int(r["textbook_pattern_degree"])
        new_p = p
        if strategy == "A":
            # (scene=0 pat=2) → 0 · (scene=1 pat=2) → 1
            if s == 0 and p == 2: new_p = 0
            elif s == 1 and p == 2: new_p = 1
        elif strategy == "B":
            # A + (scene=0 pat=1) → 0
            if s == 0 and p == 2: new_p = 0
            elif s == 1 and p == 2: new_p = 1
            elif s == 0 and p == 1: new_p = 0
        if new_p != p:
            changed += 1
        r["textbook_pattern_degree"] = float(new_p)
        r["transfer_cost"] = max(0.0, r["textbook_pattern_degree"] - r["textbook_scene_degree"])
    return changed


def main():
    y_orig = None
    for strategy in ["原样 (baseline)", "A", "B"]:
        rows = load()
        y = [r["y"] for r in rows]
        if strategy != "原样 (baseline)":
            n_changed = recalibrate_pattern(rows, strategy)
        else:
            n_changed = 0

        beta = fit_ols([make_x(r, V4) for r in rows], y)
        yhat = predict([make_x(r, V4) for r in rows], beta)
        l = lopo(rows, V4)

        print(f"\n{strategy} · 修改 {n_changed} 道题的 pattern")
        print(f"  in-sample R² = {r_squared(y, yhat):.4f}   MAE = {mae(y, yhat):.4f}")
        print(f"  LOPO R² = {l['r2']:.4f}   MAE = {l['mae']:.4f}")
        idx_pat = V4.index("textbook_pattern_degree")
        idx_scn = V4.index("textbook_scene_degree")
        idx_tc = V4.index("transfer_cost")
        print(f"  场景系数 = {beta[idx_scn+1]:+.4f}")
        print(f"  模式系数 = {beta[idx_pat+1]:+.4f}")
        print(f"  迁移成本系数 = {beta[idx_tc+1]:+.4f}")


if __name__ == "__main__":
    main()
