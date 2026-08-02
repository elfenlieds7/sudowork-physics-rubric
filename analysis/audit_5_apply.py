"""只应用杨老师 5 道抽查的确切校准 · 看 LOPO 变化.

她 5 道 (附录 B 序号 → 试卷 · 题号 · 她的场景 · 她的模式):
1. 高考 2024 Q20 (Q20-1): 场景 0 · 模式 0  (我: 0, 2)
2. 高考 2025 Q19-3:       场景 0 · 模式 0  (我: 0, 0 同意 · 无变化)
3. 西城 2024 Q14:          场景 0 · 模式 0  (我: 0, 1)
4. 高考 2025 Q11:          场景 0 · 模式 1  (我: 1, 1)
5. 西城 2025 Q12:          场景 2 · 模式 1  (我: 1, 1)

Total 4 items to change (Q20-1 全维度, Q14 pattern, Q11 scene, Q12 scene)
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

# 5-item audit ground truth
AUDIT = {
    ("gaokao_2024", "20-1"): {"scene": 0, "pattern": 0},  # 霍尔推进器
    # gaokao_2025 Q19-3 already 0/0 · no change
    ("xicheng_2024", "14"): {"scene": 0, "pattern": 0},   # 阿秒光脉冲
    ("gaokao_2025", "11"): {"scene": 0, "pattern": 1},    # 失重实验舱
    ("xicheng_2025", "12"): {"scene": 2, "pattern": 1},   # 缓慢移动
}


def load(apply_audit=False):
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid":r["question_id"],"paper":r["paper_id"],"y":float(r["score_rate"])}
            for fn in BASE: row[fn] = float(r[fn])
            rows.append(row)
    if apply_audit:
        n_changed = 0
        for r in rows:
            key = (r["paper"], r["qid"])
            if key in AUDIT:
                old_s = int(r["textbook_scene_degree"])
                old_p = int(r["textbook_pattern_degree"])
                r["textbook_scene_degree"] = float(AUDIT[key]["scene"])
                r["textbook_pattern_degree"] = float(AUDIT[key]["pattern"])
                if AUDIT[key]["scene"] != old_s or AUDIT[key]["pattern"] != old_p:
                    n_changed += 1
                    print(f"    {r['paper']:<15} Q{r['qid']:<8} scene {old_s}→{AUDIT[key]['scene']}   pattern {old_p}→{AUDIT[key]['pattern']}")
        print(f"  → {n_changed} 道修改")
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
    for label, apply in [("baseline · 未校准", False), ("+ 杨老师 5 道抽查校准 (4 道修改)", True)]:
        print(f"\n{label}")
        rows = load(apply)
        y = [r["y"] for r in rows]
        beta = fit_ols([make_x(r, V4) for r in rows], y)
        yhat = predict([make_x(r, V4) for r in rows], beta)
        l = lopo(rows, V4)
        print(f"  in-sample R² = {r_squared(y, yhat):.4f}   MAE = {mae(y, yhat):.4f}")
        print(f"  LOPO R² = {l['r2']:.4f}   MAE = {l['mae']:.4f}")
        idx_pat = V4.index("textbook_pattern_degree")
        idx_scn = V4.index("textbook_scene_degree")
        idx_tc = V4.index("transfer_cost")
        print(f"  场景系数 = {beta[idx_scn+1]:+.4f}   模式系数 = {beta[idx_pat+1]:+.4f}   迁移成本系数 = {beta[idx_tc+1]:+.4f}")


if __name__ == "__main__":
    main()
