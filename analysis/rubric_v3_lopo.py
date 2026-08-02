"""
Rubric v3 · LOPO cross-validation + cohort effect modeling · A+B split textbook feature.

Data: data/labeled/combined_scored_v3.csv (162 items across 5 papers).
Features (12): concept, reasoning, novelty, visual, modeling, position, is_open,
    topic_mech, topic_em, topic_thermo_optics_modern,
    textbook_scene_degree, textbook_pattern_degree.  [split per teacher's A+B answer]
Target: score_rate  ·  Group: paper_id

Three models fit for comparison:
  M1 (baseline): predict score_rate directly, in-sample OLS
  M2 (LOPO): same features, Leave-One-Paper-Out cross-validation
  M3 (LOPO + cohort): predict (score_rate - paper_mean), then re-add paper mean

Also reports empirical cohort variance (answers what we were going to ask teacher Ask #3).

Reads: data/labeled/combined_scored_v3.csv
Writes: data/labeled/rubric_v3_result.json
"""
import csv
import json
import statistics
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
JSON_OUT = REPO_ROOT / "data" / "labeled" / "rubric_v3_result.json"

FEATURES = [
    "concept", "reasoning", "novelty", "visual", "modeling",
    "position", "is_open",
    "topic_mech", "topic_em",   # topic_thermo_optics_modern is implicit reference (dummy-var trap)
    "textbook_scene_degree", "textbook_pattern_degree",
]


# ---- Load ----
def load_data(csv_path: Path):
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "id": r["question_id"],
                "paper": r["paper_id"],
                "y": float(r["score_rate"]),
                "x": [float(r[f]) for f in FEATURES],
            })
    return rows


# ---- OLS pure python ----
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
    return [b[0] for b in beta]


def predict(X, beta):
    return [beta[0] + sum(beta[i + 1] * row[i] for i in range(len(row))) for row in X]


def r_squared(y, y_hat):
    ybar = mean(y)
    ss_res = sum((yi - yhi) ** 2 for yi, yhi in zip(y, y_hat))
    ss_tot = sum((yi - ybar) ** 2 for yi in y)
    return 1 - ss_res / ss_tot


def mae(y, y_hat):
    return mean(abs(yi - yhi) for yi, yhi in zip(y, y_hat))


# ---- Model 1: in-sample OLS baseline ----
def m1_in_sample(rows):
    y = [r["y"] for r in rows]
    X = [r["x"] for r in rows]
    beta = fit_ols(X, y)
    y_hat = predict(X, beta)
    return {"r2": r_squared(y, y_hat), "mae": mae(y, y_hat), "beta": beta}


# ---- Model 2: LOPO CV (raw score_rate) ----
def m2_lopo(rows):
    papers = sorted({r["paper"] for r in rows})
    y_true_all, y_pred_all = [], []
    per_paper = {}
    for held_out in papers:
        train = [r for r in rows if r["paper"] != held_out]
        test = [r for r in rows if r["paper"] == held_out]
        beta = fit_ols([r["x"] for r in train], [r["y"] for r in train])
        y_pred = predict([r["x"] for r in test], beta)
        y_true = [r["y"] for r in test]
        y_true_all.extend(y_true); y_pred_all.extend(y_pred)
        per_paper[held_out] = {
            "n_test": len(test),
            "r2": r_squared(y_true, y_pred) if len(test) >= 2 else None,
            "mae": mae(y_true, y_pred),
        }
    return {"r2": r_squared(y_true_all, y_pred_all),
            "mae": mae(y_true_all, y_pred_all),
            "per_paper": per_paper}


# ---- Model 3: LOPO CV + cohort adjustment ----
# Predict residual-from-paper-mean; then add back the paper mean at inference.
# For held-out paper, we don't KNOW its true mean at inference time — use average-of-training-means.
def m3_lopo_cohort(rows):
    papers = sorted({r["paper"] for r in rows})
    paper_means = {p: mean([r["y"] for r in rows if r["paper"] == p]) for p in papers}
    y_true_all, y_pred_all = [], []
    per_paper = {}
    for held_out in papers:
        train = [r for r in rows if r["paper"] != held_out]
        test = [r for r in rows if r["paper"] == held_out]

        # target = deviation from own paper's mean
        y_train_dev = [r["y"] - paper_means[r["paper"]] for r in train]
        beta = fit_ols([r["x"] for r in train], y_train_dev)

        # prediction: predicted deviation + best-guess paper mean for held-out.
        # Best guess without seeing held-out data: mean of training-paper means.
        train_mean_of_means = mean(paper_means[p] for p in papers if p != held_out)
        dev_pred = predict([r["x"] for r in test], beta)
        y_pred = [d + train_mean_of_means for d in dev_pred]
        y_true = [r["y"] for r in test]
        y_true_all.extend(y_true); y_pred_all.extend(y_pred)
        per_paper[held_out] = {
            "n_test": len(test),
            "true_paper_mean": paper_means[held_out],
            "predicted_paper_mean": train_mean_of_means,
            "r2": r_squared(y_true, y_pred) if len(test) >= 2 else None,
            "mae": mae(y_true, y_pred),
        }
    return {"r2": r_squared(y_true_all, y_pred_all),
            "mae": mae(y_true_all, y_pred_all),
            "per_paper": per_paper,
            "paper_means": paper_means}


# ---- Empirical cohort variance (was going to ask teacher Ask #3) ----
def cohort_variance(rows):
    papers = sorted({r["paper"] for r in rows})
    per_paper_mean = {p: mean([r["y"] for r in rows if r["paper"] == p]) for p in papers}
    per_paper_sd = {p: statistics.pstdev([r["y"] for r in rows if r["paper"] == p]) for p in papers}
    across_paper_mean = mean(per_paper_mean.values())
    across_paper_sd = statistics.pstdev(list(per_paper_mean.values()))
    return {
        "per_paper_mean": per_paper_mean,
        "per_paper_sd_within": per_paper_sd,
        "across_paper_mean_of_means": across_paper_mean,
        "across_paper_sd_of_means": across_paper_sd,
        "interpretation": (
            f"5 试卷均分范围 ~ [{min(per_paper_mean.values()):.3f}, "
            f"{max(per_paper_mean.values()):.3f}]. 均分 sd across papers = "
            f"{across_paper_sd:.3f} — 这就是 cohort variance 的经验估计"
        ),
    }


# ---- Run ----
def main():
    rows = load_data(CSV_PATH)
    print(f"Loaded {len(rows)} items across {len({r['paper'] for r in rows})} papers.")
    print(f"Features: {len(FEATURES)}. n/k = {len(rows)/(len(FEATURES)+1):.1f}\n")

    print("=" * 60)
    print("Empirical cohort variance (empirical answer to teacher Ask #3)")
    print("=" * 60)
    cv = cohort_variance(rows)
    print(f"{'paper':<18} {'mean':>7} {'sd_within':>10} {'n':>4}")
    for p, m in sorted(cv["per_paper_mean"].items()):
        n = sum(1 for r in rows if r["paper"] == p)
        print(f"{p:<18} {m:>7.3f} {cv['per_paper_sd_within'][p]:>10.3f} {n:>4}")
    print(f"\n across-paper mean of means: {cv['across_paper_mean_of_means']:.3f}")
    print(f" across-paper SD of means:   {cv['across_paper_sd_of_means']:.3f}  ← cohort variance signal")
    print(f" {cv['interpretation']}\n")

    print("=" * 60)
    print("Model 1 · in-sample OLS baseline (over-optimistic)")
    print("=" * 60)
    m1 = m1_in_sample(rows)
    print(f"R² = {m1['r2']:.4f} · MAE = {m1['mae']:.4f}")
    print()

    print("=" * 60)
    print("Model 2 · LOPO CV (predict raw score_rate)")
    print("=" * 60)
    m2 = m2_lopo(rows)
    print(f"pooled R² = {m2['r2']:.4f} · MAE = {m2['mae']:.4f}")
    print(f"{'held_out_paper':<18} {'r2':>7} {'mae':>7} {'n':>4}")
    for p, s in m2["per_paper"].items():
        r2s = f"{s['r2']:>7.3f}" if s["r2"] is not None else "     — "
        print(f"{p:<18} {r2s} {s['mae']:>7.3f} {s['n_test']:>4}")
    print()

    print("=" * 60)
    print("Model 3 · LOPO CV + cohort adjustment (predict residual-from-paper-mean)")
    print("=" * 60)
    m3 = m3_lopo_cohort(rows)
    print(f"pooled R² = {m3['r2']:.4f} · MAE = {m3['mae']:.4f}")
    print(f"{'held_out':<18} {'true_μ':>8} {'pred_μ':>8} {'r2':>7} {'mae':>7} {'n':>4}")
    for p, s in m3["per_paper"].items():
        r2s = f"{s['r2']:>7.3f}" if s["r2"] is not None else "     — "
        print(f"{p:<18} {s['true_paper_mean']:>8.3f} {s['predicted_paper_mean']:>8.3f} "
              f"{r2s} {s['mae']:>7.3f} {s['n_test']:>4}")

    print()
    print("=" * 60)
    print("Model 1 coefficients (for interpretation)")
    print("=" * 60)
    print(f"  intercept: {m1['beta'][0]:+.4f}")
    for name, coef in zip(FEATURES, m1["beta"][1:]):
        print(f"  {name:<28}: {coef:+.4f}")

    # Save
    result = {
        "n_rows": len(rows),
        "n_papers": len({r["paper"] for r in rows}),
        "features": FEATURES,
        "cohort_variance": cv,
        "m1_in_sample": {"r2": m1["r2"], "mae": m1["mae"],
                         "beta": {"intercept": m1["beta"][0],
                                  **{FEATURES[i]: m1["beta"][i+1] for i in range(len(FEATURES))}}},
        "m2_lopo_raw": {"r2_pooled": m2["r2"], "mae_pooled": m2["mae"], "per_paper": m2["per_paper"]},
        "m3_lopo_cohort": {"r2_pooled": m3["r2"], "mae_pooled": m3["mae"], "per_paper": m3["per_paper"]},
    }
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {JSON_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
