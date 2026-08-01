"""
Baseline difficulty prediction: rubric features -> score rate, fit linear regression.

Data: 2026.4 西城高三物理一模 · 33 sub-questions with hand-annotated score rates
(from the teacher's red-ink markup on the paper).

Reads: data/labeled/xicheng_2026_scored.csv
Writes: data/labeled/rubric_v1_result.json

Features (rubric v0.1):
- concept: 涉及独立物理概念数 (1-5)
- reasoning: 推理/代数步数 (1=recall/plug-in, 5=multi-step derivation)
- novelty: 情境陌生度 (0=textbook, 3=novel/current-events)
- visual: 图像/表格数 (0-3)
- modeling: 建模自主度 (0=given, 3=self-derive)
- position: 题号在卷面位置 (0.0-1.0)
- is_open: 是否大题分问 (0/1)
- topic_mech: 是否力学 (0/1)
- topic_em: 是否电磁 (0/1)
- topic_thermo_optics_modern: 是否 热/光/近代 (0/1)

Baseline: OLS linear regression, R² in-sample only (severely overfit at n/k=3.3).
See context/meta_lessons.md #8 for why we can't trust this — v2 will use LOPO CV.
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "xicheng_2026_scored.csv"
JSON_OUT = REPO_ROOT / "data" / "labeled" / "rubric_v1_result.json"

FEATURES = ["concept", "reasoning", "novelty", "visual", "modeling",
            "position", "is_open", "topic_mech", "topic_em", "topic_thermo_optics_modern"]


# ---- Load ----
def load_data(csv_path: Path):
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"id": r["question_id"], "y": float(r["score_rate"]),
                         "x": [float(r[f]) for f in FEATURES]})
    return rows


# ---- OLS multiple linear regression (pure python, no numpy dep) ----
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
            raise ValueError("singular matrix")
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
    beta = matmul(inv(XTX), XTy)
    return [b[0] for b in beta]  # [intercept, b1, ..., bk]


def predict(X, beta):
    return [beta[0] + sum(beta[i + 1] * row[i] for i in range(len(row))) for row in X]


def r_squared(y, y_hat):
    ybar = mean(y)
    ss_res = sum((yi - yhi) ** 2 for yi, yhi in zip(y, y_hat))
    ss_tot = sum((yi - ybar) ** 2 for yi in y)
    return 1 - ss_res / ss_tot


# ---- Run ----
def main():
    rows = load_data(CSV_PATH)
    y = [r["y"] for r in rows]
    X = [r["x"] for r in rows]
    beta = fit_ols(X, y)
    y_hat = predict(X, beta)
    r2 = r_squared(y, y_hat)
    mae = mean(abs(yi - yhi) for yi, yhi in zip(y, y_hat))

    print(f"n = {len(rows)} data points, k = {len(FEATURES)} features + intercept")
    print(f"\nR² (in-sample, NOT CV) = {r2:.4f}")
    print(f"MAE = {mae:.4f}")
    print(f"\nWARNING: n/k ratio = {len(rows) / (len(FEATURES)+1):.1f} — high overfit risk. "
          "v2 will use LOPO CV. See context/meta_lessons.md #8.")

    print("\nCoefficients:")
    print(f"  intercept: {beta[0]:+.4f}")
    for name, coef in zip(FEATURES, beta[1:]):
        print(f"  {name:<28}: {coef:+.4f}")

    print("\nTop 10 largest |residuals|:")
    resid = sorted([(rows[i]["id"], y[i], y_hat[i], y[i] - y_hat[i]) for i in range(len(rows))],
                   key=lambda x: -abs(x[3]))
    for qid, ya, yp, r in resid[:10]:
        tag = "under-est (harder)" if r < 0 else "over-est (easier)"
        print(f"  Q{qid:<6} actual={ya:.2f} pred={yp:.2f} resid={r:+.3f}  [{tag}]")

    result = {
        "n": len(rows),
        "features": FEATURES,
        "r2_in_sample": r2,
        "mae": mae,
        "n_over_k_plus_1": len(rows) / (len(FEATURES) + 1),
        "beta": {"intercept": beta[0], **{FEATURES[i]: beta[i+1] for i in range(len(FEATURES))}},
        "predictions": [{"id": rows[i]["id"], "actual": y[i], "pred": y_hat[i], "resid": y[i] - y_hat[i]}
                        for i in range(len(rows))],
    }
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {JSON_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
