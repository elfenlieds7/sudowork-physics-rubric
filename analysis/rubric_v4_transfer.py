"""v4 · 加 3 个新特征试杨老师的两个假设.

新特征:
- transfer_cost:   max(0, pattern_degree - scene_degree)
                    = "模式熟, 场景陌生" 时的迁移成本 (0-2)
                    杨老师假设: 霍尔推进器方法学过, 但情境陌生 → 高 transfer_cost
- distance_from_end: 1 - position
                    = 距卷面末尾距离, 直接建模压轴题效应
- earlier_load:    卷内位置低于自己的所有题的 concept 均值 (归一化)
                    = 建模她的耗时假设 (前段题概念多 → 时间被吃掉)

也做两个直接验证:
1. 直接对比: (scene=0 pattern=2) 组 vs (scene=2 pattern=2) 组的得分率
   ← 直接测她的迁移成本假设
2. 全局: transfer_cost 高低两组的得分率均值

然后 fit v3 baseline (11 特征) vs v4 (14 特征) LOPO CV, 看 R² 是否上升.
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_JSON = REPO_ROOT / "data" / "labeled" / "rubric_v4_result.json"

BASE_FEATURES = [
    "concept", "reasoning", "novelty", "visual", "modeling",
    "position", "is_open",
    "topic_mech", "topic_em",
    "textbook_scene_degree", "textbook_pattern_degree",
]

NEW_FEATURES = ["transfer_cost", "is_last_quarter", "earlier_load"]

ALL_FEATURES = BASE_FEATURES + NEW_FEATURES


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
        if abs(pv) < 1e-12:
            raise ValueError("singular matrix at col " + str(col))
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


def enrich_features(rows):
    """加 3 个新特征."""
    for r in rows:
        scene = r["textbook_scene_degree"]
        pat = r["textbook_pattern_degree"]
        r["transfer_cost"] = max(0.0, pat - scene)
        # 非线性: 只在卷面后 25% 触发, 捕捉压轴题效应, 避免和 position 线性共线
        r["is_last_quarter"] = 1.0 if r["position"] > 0.75 else 0.0

    # earlier_load 需要按 paper 分组
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["paper"], []).append(r)
    for pdata in by_paper.values():
        pdata_sorted = sorted(pdata, key=lambda r: r["position"])
        for i, r in enumerate(pdata_sorted):
            earlier = pdata_sorted[:i]
            r["earlier_load"] = mean(e["concept"] for e in earlier) if earlier else 0.0


def make_x(r, feat_list):
    return [r[f] for f in feat_list]


def lopo(rows, feat_list):
    papers = sorted({r["paper"] for r in rows})
    y_true_all, y_pred_all = [], []
    per_paper = {}
    for held in papers:
        train = [r for r in rows if r["paper"] != held]
        test = [r for r in rows if r["paper"] == held]
        beta = fit_ols([make_x(r, feat_list) for r in train], [r["y"] for r in train])
        y_pred = predict([make_x(r, feat_list) for r in test], beta)
        y_true = [r["y"] for r in test]
        y_true_all.extend(y_true); y_pred_all.extend(y_pred)
        per_paper[held] = {"n": len(test), "r2": r_squared(y_true, y_pred), "mae": mae(y_true, y_pred)}
    return {"r2": r_squared(y_true_all, y_pred_all), "mae": mae(y_true_all, y_pred_all), "per_paper": per_paper}


def main():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {
                "qid": r["question_id"], "paper": r["paper_id"],
                "y": float(r["score_rate"]),
            }
            for f_name in BASE_FEATURES:
                row[f_name] = float(r[f_name])
            rows.append(row)

    enrich_features(rows)

    # =====================================================
    # A · 直接测她的迁移成本假设
    # =====================================================
    print("=" * 62)
    print("A · 直接测杨老师迁移成本假设 (无模型 · 只看均分)")
    print("=" * 62)

    def group_mean(pred):
        subset = [r for r in rows if pred(r)]
        return (mean(r["y"] for r in subset), len(subset)) if subset else (None, 0)

    # 全部 scene=0 pattern=2 vs scene=2 pattern=2 · 直接对照
    m_no_transfer, n1 = group_mean(lambda r: r["textbook_scene_degree"] == 2 and r["textbook_pattern_degree"] == 2)
    m_transfer, n2 = group_mean(lambda r: r["textbook_scene_degree"] == 0 and r["textbook_pattern_degree"] == 2)
    m_full_novel, n3 = group_mean(lambda r: r["textbook_scene_degree"] == 0 and r["textbook_pattern_degree"] == 0)
    m_all_same, n4 = group_mean(lambda r: r["textbook_scene_degree"] == r["textbook_pattern_degree"])

    print(f"  场景=2 模式=2 (都熟)             n={n1:3d}  均分={m_no_transfer:.3f}" if m_no_transfer else f"  场景=2 模式=2: 空")
    print(f"  场景=0 模式=2 (模式熟场景新)     n={n2:3d}  均分={m_transfer:.3f}   ← 杨老师说的迁移成本组" if m_transfer else "  场景=0 模式=2: 空")
    print(f"  场景=0 模式=0 (都陌生)           n={n3:3d}  均分={m_full_novel:.3f}" if m_full_novel else "  场景=0 模式=0: 空")
    if m_no_transfer and m_transfer:
        gap = m_no_transfer - m_transfer
        print(f"\n  迁移成本效应 (场景熟 - 场景新, 同模式熟): {gap:+.3f} " +
              f"({'支持假设' if gap > 0.02 else '弱信号' if gap > 0 else '反例'})")

    # 按 transfer_cost 分箱
    print(f"\n  按 transfer_cost (0/1/2) 分箱:")
    for tc in [0, 1, 2]:
        subset = [r for r in rows if int(r["transfer_cost"]) == tc]
        if subset:
            print(f"    transfer_cost={tc}  n={len(subset):3d}  均分={mean(r['y'] for r in subset):.3f}")

    # =====================================================
    # B · v3 baseline vs v4 · in-sample + LOPO
    # =====================================================
    print("\n" + "=" * 62)
    print("B · v3 baseline (11 特征) vs v4 (14 特征) LOPO 对比")
    print("=" * 62)

    # v3 baseline
    beta_v3 = fit_ols([make_x(r, BASE_FEATURES) for r in rows], [r["y"] for r in rows])
    yhat_v3 = predict([make_x(r, BASE_FEATURES) for r in rows], beta_v3)
    print(f"  v3 in-sample R² = {r_squared([r['y'] for r in rows], yhat_v3):.4f}   MAE = {mae([r['y'] for r in rows], yhat_v3):.4f}")

    # v4 加 3 特征
    beta_v4 = fit_ols([make_x(r, ALL_FEATURES) for r in rows], [r["y"] for r in rows])
    yhat_v4 = predict([make_x(r, ALL_FEATURES) for r in rows], beta_v4)
    print(f"  v4 in-sample R² = {r_squared([r['y'] for r in rows], yhat_v4):.4f}   MAE = {mae([r['y'] for r in rows], yhat_v4):.4f}")

    # LOPO
    l_v3 = lopo(rows, BASE_FEATURES)
    l_v4 = lopo(rows, ALL_FEATURES)
    print(f"\n  v3 LOPO R² = {l_v3['r2']:.4f}   MAE = {l_v3['mae']:.4f}")
    print(f"  v4 LOPO R² = {l_v4['r2']:.4f}   MAE = {l_v4['mae']:.4f}")
    dr2 = l_v4["r2"] - l_v3["r2"]
    dmae = l_v4["mae"] - l_v3["mae"]
    print(f"\n  ΔR² = {dr2:+.4f}   ΔMAE = {dmae:+.4f}  " +
          f"({'v4 更好' if dr2 > 0.005 else 'v4 略好' if dr2 > 0 else '无改进'})")

    print(f"\n  v4 全数据 OLS · 新特征系数:")
    for name, b in zip(ALL_FEATURES, beta_v4[1:]):
        if name in NEW_FEATURES:
            print(f"    {name:<22}: β = {b:+.4f}")
    print(f"\n  v4 · 场景/模式两维系数变化:")
    for name in ["textbook_scene_degree", "textbook_pattern_degree"]:
        idx3 = BASE_FEATURES.index(name)
        idx4 = ALL_FEATURES.index(name)
        print(f"    {name:<28}  v3 β={beta_v3[idx3+1]:+.4f}  →  v4 β={beta_v4[idx4+1]:+.4f}")

    # 每份 held-out 对比
    print(f"\n  LOPO 每份 held-out 试卷 R²:")
    print(f"  {'paper':<18} {'v3 R²':>8} {'v4 R²':>8} {'Δ':>8}")
    for p in sorted(l_v3["per_paper"].keys()):
        v3r = l_v3["per_paper"][p]["r2"]
        v4r = l_v4["per_paper"][p]["r2"]
        print(f"  {p:<18} {v3r:>8.4f} {v4r:>8.4f} {v4r - v3r:+8.4f}")

    result = {
        "n_rows": len(rows),
        "features_v3": BASE_FEATURES,
        "features_v4": ALL_FEATURES,
        "hypothesis_test": {
            "scene2_pattern2_mean": m_no_transfer,
            "scene0_pattern2_mean": m_transfer,
            "gap": (m_no_transfer - m_transfer) if (m_no_transfer and m_transfer) else None,
            "n_scene2_pattern2": n1,
            "n_scene0_pattern2": n2,
        },
        "v3_in_sample_r2": r_squared([r['y'] for r in rows], yhat_v3),
        "v4_in_sample_r2": r_squared([r['y'] for r in rows], yhat_v4),
        "v3_lopo_r2": l_v3["r2"], "v3_lopo_mae": l_v3["mae"],
        "v4_lopo_r2": l_v4["r2"], "v4_lopo_mae": l_v4["mae"],
        "v4_beta": {"intercept": beta_v4[0], **{ALL_FEATURES[i]: beta_v4[i+1] for i in range(len(ALL_FEATURES))}},
        "v4_per_paper_lopo": l_v4["per_paper"],
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果保存到 {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
