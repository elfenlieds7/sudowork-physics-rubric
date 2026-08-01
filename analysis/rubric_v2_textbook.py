"""
Rubric v2 · Add `textbook_model_degree` feature (0/1/2) to see if it captures
signal that v1 missed in residual analysis.

Reads: data/labeled/xicheng_2026_scored_v2.csv
Writes: data/labeled/rubric_v2_result.json

v2 change vs v1:
- 11 features (added textbook_model_degree)
- Same 33 data points
- Still OLS in-sample (LOPO CV waits for 5-paper full dataset, per meta_lessons.md #8)
- Focus: does the new feature explain residual variance from v1?
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "xicheng_2026_scored_v2.csv"
JSON_OUT = REPO_ROOT / "data" / "labeled" / "rubric_v2_result.json"
V1_JSON = REPO_ROOT / "data" / "labeled" / "rubric_v1_result.json"

FEATURES_V2 = ["concept", "reasoning", "novelty", "visual", "modeling",
               "position", "is_open", "topic_mech", "topic_em", "topic_thermo_optics_modern",
               "textbook_model_degree"]  # <-- new
FEATURES_V1 = FEATURES_V2[:-1]  # exclude last


def load_data(csv_path, features):
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"id": r["question_id"], "y": float(r["score_rate"]),
                         "x": [float(r[f]) for f in features]})
    return rows


# ---- OLS ----
def transpose(M): return [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]
def matmul(A, B):
    m, k, n = len(A), len(A[0]), len(B[0])
    return [[sum(A[i][p]*B[p][j] for p in range(k)) for j in range(n)] for i in range(m)]
def inv(M):
    n = len(M); A = [row[:] + [1 if i==j else 0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[pivot] = A[pivot], A[col]
        pv = A[col][col]
        if abs(pv) < 1e-12: raise ValueError("singular")
        A[col] = [x/pv for x in A[col]]
        for r in range(n):
            if r == col: continue
            factor = A[r][col]
            A[r] = [A[r][c] - factor*A[col][c] for c in range(2*n)]
    return [row[n:] for row in A]

def fit_ols(X, y):
    Xb = [[1.0] + row for row in X]
    XT = transpose(Xb)
    XTX = matmul(XT, Xb)
    XTy = matmul(XT, [[v] for v in y])
    beta = matmul(inv(XTX), XTy)
    return [b[0] for b in beta]

def predict(X, beta):
    return [beta[0] + sum(beta[i+1]*row[i] for i in range(len(row))) for row in X]

def r_squared(y, y_hat):
    ybar = mean(y)
    ss_res = sum((yi-yhi)**2 for yi, yhi in zip(y, y_hat))
    ss_tot = sum((yi-ybar)**2 for yi in y)
    return 1 - ss_res/ss_tot


def main():
    # Fit both v1 (10 features) and v2 (11 features) on the same data for direct comparison
    rows_v2 = load_data(CSV_PATH, FEATURES_V2)
    y = [r["y"] for r in rows_v2]
    X_v2 = [r["x"] for r in rows_v2]
    X_v1 = [row[:-1] for row in X_v2]

    beta_v1 = fit_ols(X_v1, y)
    y_hat_v1 = predict(X_v1, beta_v1)
    r2_v1 = r_squared(y, y_hat_v1)
    mae_v1 = mean(abs(yi-yhi) for yi, yhi in zip(y, y_hat_v1))

    beta_v2 = fit_ols(X_v2, y)
    y_hat_v2 = predict(X_v2, beta_v2)
    r2_v2 = r_squared(y, y_hat_v2)
    mae_v2 = mean(abs(yi-yhi) for yi, yhi in zip(y, y_hat_v2))

    n = len(rows_v2)
    print(f"n = {n} data points")
    print(f"\n=== v1 (10 features) ===")
    print(f"R² (in-sample) = {r2_v1:.4f}, MAE = {mae_v1:.4f}, n/(k+1) = {n/11:.2f}")
    print(f"\n=== v2 (11 features, +textbook_model_degree) ===")
    print(f"R² (in-sample) = {r2_v2:.4f}, MAE = {mae_v2:.4f}, n/(k+1) = {n/12:.2f}")
    print(f"\nΔR² = {r2_v2-r2_v1:+.4f}, ΔMAE = {mae_v2-mae_v1:+.4f}")

    print(f"\n=== v2 coefficients ===")
    print(f"  intercept: {beta_v2[0]:+.4f}")
    for name, coef in zip(FEATURES_V2, beta_v2[1:]):
        marker = " <-- NEW" if name == "textbook_model_degree" else ""
        print(f"  {name:<28}: {coef:+.4f}{marker}")

    # Residual change for previously large-residual questions
    print(f"\n=== residuals: v1 vs v2 for previously top-10 largest |v1 residual| ===")
    v1_resid = [(rows_v2[i]["id"], y[i], y_hat_v1[i], y[i]-y_hat_v1[i]) for i in range(n)]
    v1_resid.sort(key=lambda r: -abs(r[3]))
    print(f"{'Q':<6} {'actual':>7} {'v1 pred':>8} {'v1 resid':>9} {'v2 pred':>8} {'v2 resid':>9} {'improved':>10}")
    for qid, ya, yp1, r1 in v1_resid[:10]:
        i = next(i for i in range(n) if rows_v2[i]["id"] == qid)
        yp2 = y_hat_v2[i]; r2 = y - y_hat_v2[i] if False else ya - yp2
        improved = "yes" if abs(r2) < abs(r1) else "no"
        print(f"Q{qid:<5} {ya:>7.2f} {yp1:>8.2f} {r1:>+9.3f} {yp2:>8.2f} {r2:>+9.3f} {improved:>10}")

    # Save result
    result = {
        "n": n,
        "features_v1": FEATURES_V1,
        "features_v2": FEATURES_V2,
        "r2_v1_in_sample": r2_v1,
        "r2_v2_in_sample": r2_v2,
        "delta_r2": r2_v2 - r2_v1,
        "mae_v1": mae_v1,
        "mae_v2": mae_v2,
        "beta_v2": {"intercept": beta_v2[0], **{FEATURES_V2[i]: beta_v2[i+1] for i in range(len(FEATURES_V2))}},
        "predictions": [
            {"id": rows_v2[i]["id"], "actual": y[i],
             "v1_pred": y_hat_v1[i], "v1_resid": y[i]-y_hat_v1[i],
             "v2_pred": y_hat_v2[i], "v2_resid": y[i]-y_hat_v2[i]}
            for i in range(n)
        ],
        "textbook_model_degree_effect": {
            "coefficient": beta_v2[-1],
            "interpretation": "Positive means: higher textbook-familiarity → higher score rate (as expected)"
        },
        "note": ("v2 R² is in-sample only. n/(k+1) = 2.75 is worse than v1's 3.30. "
                 "Real out-of-sample R² likely lower for v2. LOPO CV pending on 5-paper dataset.")
    }
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {JSON_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
