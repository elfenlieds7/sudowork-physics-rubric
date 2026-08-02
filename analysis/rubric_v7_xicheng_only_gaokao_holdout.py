"""场景三 pilot · 只用西城 3 届模拟卷训 v4 · hold out 高考 2 届, 测泛化.

对应杨老师 docx 场景三 (高考数据验证) + Ethan 提到的"跨区域" 顾虑.

实验:
A. 只用 3 份西城模拟卷训 v4 · 预测 2 份高考 · 报告 naive R² / MAE
B. 在每份高考 hold-out 里 · 用 k 道题的实际数据 fit 一个 cohort adjustment 常数 · 预测剩下的
   k = 3, 5, 8, 全卷平均 · 看小样本校准能否显著提升精度
   这个直接测杨老师 17:19 语音的 vision: "上传几份该区试卷 → 重新定位该区得分率"
C. 对比 baseline (完整 5 卷 v4 训练) 的 gaokao 预测精度, 看跨区域惩罚有多大

Features: v4 的 14 特征 (BASE 11 + transfer_cost + is_last_quarter + earlier_load)
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_JSON = REPO_ROOT / "data" / "labeled" / "rubric_v7_transfer_result.json"

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


def make_x(r, feats):
    return [r[f] for f in feats]


def main():
    rows = load()

    xicheng_papers = ["xicheng_2024", "xicheng_2025", "xicheng_2026"]
    gaokao_papers = ["gaokao_2024", "gaokao_2025"]

    xicheng_data = [r for r in rows if r["paper"] in xicheng_papers]
    gaokao_data = [r for r in rows if r["paper"] in gaokao_papers]

    print("=" * 66)
    print("A · 只用 3 份西城模拟卷训 v4 · 预测 2 份高考")
    print("=" * 66)
    print(f"训练: {len(xicheng_data)} 道 (西城 3 届) · 测试: {len(gaokao_data)} 道 (高考 2 届)")
    print()

    y_train = [r["y"] for r in xicheng_data]
    X_train = [make_x(r, ALL) for r in xicheng_data]
    beta = fit_ols(X_train, y_train)

    y_test = [r["y"] for r in gaokao_data]
    X_test = [make_x(r, ALL) for r in gaokao_data]
    y_pred_naive = predict(X_test, beta)

    for r, p in zip(gaokao_data, y_pred_naive):
        r["pred_naive"] = p

    r2_naive = r_squared(y_test, y_pred_naive)
    mae_naive = mae(y_test, y_pred_naive)
    print(f"Naive 预测 (无校准):")
    print(f"  高考整体 · R² = {r2_naive:.4f}  MAE = {mae_naive:.4f}")

    # Per-paper
    for p in gaokao_papers:
        sub = [r for r in gaokao_data if r["paper"] == p]
        yt = [r["y"] for r in sub]
        yp = [r["pred_naive"] for r in sub]
        m_pred = mean(yp)
        m_true = mean(yt)
        print(f"  {p}: R² = {r_squared(yt, yp):.4f}  MAE = {mae(yt, yp):.4f}  " +
              f"整卷均分 (实际) = {m_true:.3f}  (预测) = {m_pred:.3f}  (偏差) {m_pred - m_true:+.3f}")

    print()
    print("=" * 66)
    print("B · 从每份高考里挑 k 道题 fit cohort constant · 预测剩下的")
    print("   直接测: 上传 k 份该区数据 → 校准 baseline 的 vision")
    print("=" * 66)

    # 对每份高考 · 每种 k · 用 first-k 道题 fit shift, 预测剩下的
    # 更 realistic: 随机挑 k 道; 但样本量小, 用 first-k 简化
    results_B = {}
    for k in [3, 5, 8, "all"]:
        y_true_all = []
        y_pred_cal_all = []
        for p in gaokao_papers:
            sub = sorted([r for r in gaokao_data if r["paper"] == p], key=lambda r: r["position"])
            if k == "all":
                calib = sub
                test = sub
            else:
                calib = sub[:k]  # 前 k 道
                test = sub[k:]  # 剩下的
            if not test:
                continue

            # cohort shift = mean(actual - naive_pred) on calib set
            shifts = [r["y"] - r["pred_naive"] for r in calib]
            shift = mean(shifts)

            for r in test:
                y_true_all.append(r["y"])
                y_pred_cal_all.append(r["pred_naive"] + shift)

        if y_true_all:
            r2_cal = r_squared(y_true_all, y_pred_cal_all)
            mae_cal = mae(y_true_all, y_pred_cal_all)
            results_B[str(k)] = {"r2": r2_cal, "mae": mae_cal, "n_test": len(y_true_all)}
            print(f"  k = {k:<5}  hold-out 里 fit {k if k != 'all' else '全部'} 道 " +
                  f"→ 预测剩下 {len(y_true_all)} 道 · R² = {r2_cal:.4f}  MAE = {mae_cal:.4f}")

    print()
    print("=" * 66)
    print("C · Baseline · 完整 5 卷训 v4 · LOPO gaokao 部分")
    print("=" * 66)

    # 完整训 5 卷 · LOPO gaokao 2 份
    for held in gaokao_papers:
        train_full = [r for r in rows if r["paper"] != held]
        test_full = [r for r in rows if r["paper"] == held]
        beta_full = fit_ols([make_x(r, ALL) for r in train_full], [r["y"] for r in train_full])
        yp = predict([make_x(r, ALL) for r in test_full], beta_full)
        yt = [r["y"] for r in test_full]
        print(f"  {held}: R² = {r_squared(yt, yp):.4f}  MAE = {mae(yt, yp):.4f}  " +
              f"(用其他 4 卷含另一份高考)")

    # Save
    result = {
        "experiment": "cross-region transfer pilot",
        "train": "3 xicheng papers only",
        "test": "2 gaokao papers held out",
        "A_naive": {"r2": r2_naive, "mae": mae_naive},
        "B_calibrated": results_B,
        "beta_xicheng_only": {"intercept": beta[0], **{ALL[i]: beta[i+1] for i in range(len(ALL))}},
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果保存到 {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
