"""v5 · 加两个新特征试信号 (Ethan 提议方向 · signed residual 反推):

A. sub_q_position: 大题子问的位置
   - 0 = 选择题 (is_open=0)
   - 1 = 大题第 1 小问 (通常 setup · 题目已给方向)
   - 2 = 大题第 2 小问
   - 3 = 大题第 3 或更后小问 (通常压轴)

B. compute_load: 数学计算量 (跟推理步数分开)
   - 启发式: MCQ=1, 实验题=2, 大题 setup=2, 大题末尾=3
   - 也 hand-label 一些明显偏离启发式的题

先跑启发式版本看有没有 signal, 有 signal 再手工细化。
"""
import csv
import json
import re
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_JSON = REPO_ROOT / "data" / "labeled" / "rubric_v5_new_features_result.json"

V4_FEATURES = ["concept", "reasoning", "novelty", "visual", "modeling",
               "position", "is_open", "topic_mech", "topic_em",
               "textbook_scene_degree", "textbook_pattern_degree",
               "transfer_cost", "is_last_quarter", "earlier_load"]

NEW_FEATS = ["sub_q_position", "compute_load"]
V5_FEATURES = V4_FEATURES + NEW_FEATS


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


def sub_q_position(qid, is_open):
    """从 qid 抽出大题子问的位置 (0=选择题, 1/2/3=第几小问, 3=末尾)"""
    if not is_open:
        return 0
    # qid 格式: "15-1", "17-2a", "17-2b", "16-a", "20-3", "18-1a", etc.
    parts = qid.split("-")
    if len(parts) < 2:
        return 0  # weird format
    sub = parts[1]
    # 处理 "a" "b" 等字母
    if sub in ("a", "b", "c", "d"):
        pos = ord(sub) - ord("a") + 1  # a=1, b=2, ...
    else:
        # "1", "2", "2a", "2b", "3"
        m = re.match(r"(\d+)", sub)
        if m:
            pos = int(m.group(1))
        else:
            pos = 1
    return min(3, max(1, pos))


def compute_load(qid, is_open, concept, reasoning):
    """启发式 · 数学计算量 (0-3)
    MCQ: 通常 0-1 (选择题偏概念)
    实验题 (15-16): 2 (读数 + 简单代数)
    大题 setup 小问 (17-1, 18-1): 2 (标准套用)
    大题末尾小问 (最后一小问): 3 (复杂代数)
    """
    if not is_open:
        # MCQ: 大部分 concept 主导
        # 若 concept 高 rea 高, 计算多点 (但 MCQ 少)
        return 1 if reasoning >= 3 else 0
    # is_open=1
    parts = qid.split("-")
    if len(parts) < 2:
        return 2
    sub_num = sub_q_position(qid, is_open)
    # 实验题 (Q15, Q16 一般是实验)
    try:
        q_main = int(parts[0])
    except:
        return 2
    if q_main in (15, 16):
        # 实验题 · 一般计算不多但需要读数 + 简单公式
        return 2 if sub_num >= 2 else 1
    if q_main in (17, 18, 19, 20):
        # 大题
        if sub_num == 1:
            return 2  # setup 小问 · 中等计算
        else:
            return 3  # 后小问 · 通常最难 · 计算多
    return 2


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

    # NEW features
    for r in rows:
        r["sub_q_position"] = float(sub_q_position(r["qid"], int(r["is_open"])))
        r["compute_load"] = float(compute_load(r["qid"], int(r["is_open"]), r["concept"], r["reasoning"]))
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
    print(f"n = {len(rows)}")

    # 查看新特征分布
    print("\n新特征分布:")
    from collections import Counter
    print(f"  sub_q_position: {sorted(Counter(int(r['sub_q_position']) for r in rows).items())}")
    print(f"  compute_load:   {sorted(Counter(int(r['compute_load']) for r in rows).items())}")

    y = [r["y"] for r in rows]

    # v4 baseline
    beta_v4 = fit_ols([make_x(r, V4_FEATURES) for r in rows], y)
    yhat_v4 = predict([make_x(r, V4_FEATURES) for r in rows], beta_v4)
    print(f"\nv4 (14 特征):")
    print(f"  in-sample R² = {r_squared(y, yhat_v4):.4f}   MAE = {mae(y, yhat_v4):.4f}")
    l_v4 = lopo(rows, V4_FEATURES)
    print(f"  LOPO R² = {l_v4['r2']:.4f}   MAE = {l_v4['mae']:.4f}")

    # v5 (v4 + 新特征)
    beta_v5 = fit_ols([make_x(r, V5_FEATURES) for r in rows], y)
    yhat_v5 = predict([make_x(r, V5_FEATURES) for r in rows], beta_v5)
    print(f"\nv5 (16 特征 · v4 + sub_q_position + compute_load):")
    print(f"  in-sample R² = {r_squared(y, yhat_v5):.4f}   MAE = {mae(y, yhat_v5):.4f}")
    l_v5 = lopo(rows, V5_FEATURES)
    print(f"  LOPO R² = {l_v5['r2']:.4f}   MAE = {l_v5['mae']:.4f}")

    # 只加 sub_q_position
    v5a_feats = V4_FEATURES + ["sub_q_position"]
    beta_v5a = fit_ols([make_x(r, v5a_feats) for r in rows], y)
    yhat_v5a = predict([make_x(r, v5a_feats) for r in rows], beta_v5a)
    l_v5a = lopo(rows, v5a_feats)
    print(f"\nv5a (15 特征 · v4 + sub_q_position):")
    print(f"  in-sample R² = {r_squared(y, yhat_v5a):.4f}   LOPO R² = {l_v5a['r2']:.4f}   LOPO MAE = {l_v5a['mae']:.4f}")

    # 只加 compute_load
    v5b_feats = V4_FEATURES + ["compute_load"]
    beta_v5b = fit_ols([make_x(r, v5b_feats) for r in rows], y)
    l_v5b = lopo(rows, v5b_feats)
    print(f"\nv5b (15 特征 · v4 + compute_load):")
    print(f"  in-sample R² = {r_squared(y, predict([make_x(r, v5b_feats) for r in rows], beta_v5b)):.4f}   LOPO R² = {l_v5b['r2']:.4f}   LOPO MAE = {l_v5b['mae']:.4f}")

    # v5 系数
    print(f"\nv5 · 新特征系数:")
    for name, b in zip(V5_FEATURES, beta_v5[1:]):
        if name in NEW_FEATS:
            print(f"  {name:<28}: β = {b:+.4f}")

    result = {
        "features_v4": V4_FEATURES,
        "features_v5": V5_FEATURES,
        "v4_lopo_mae": l_v4["mae"], "v4_lopo_r2": l_v4["r2"],
        "v5_lopo_mae": l_v5["mae"], "v5_lopo_r2": l_v5["r2"],
        "v5a_lopo_mae": l_v5a["mae"], "v5a_lopo_r2": l_v5a["r2"],
        "v5b_lopo_mae": l_v5b["mae"], "v5b_lopo_r2": l_v5b["r2"],
        "v5_beta": {"intercept": beta_v5[0], **{V5_FEATURES[i]: beta_v5[i+1] for i in range(len(V5_FEATURES))}},
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
