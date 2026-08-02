"""Pick 20 MCQ items for teacher to label 陷阱数.

Strategy:
- Only 选择题 (is_open=0) — misconception distractors mainly live in MCQ options.
- Sample items where current v3 rubric has LARGEST |residual| — these are the
  items my model can't explain; 陷阱数 might be the missing signal.
- Stratify across 5 papers (4 items each) to preserve breadth.

Emits: analysis/labeling_traps_subset.json — 20 (paper, qid, score_rate,
predicted, residual) records ready for HTML appendix injection.
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_JSON = REPO_ROOT / "analysis" / "labeling_traps_subset.json"

FEATURES = [
    "concept", "reasoning", "novelty", "visual", "modeling",
    "position", "is_open",
    "topic_mech", "topic_em",
    "textbook_scene_degree", "textbook_pattern_degree",
]


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
    beta = matmul(inv(XTX), XTy)
    return [b[0] for b in beta]


def predict(X, beta):
    return [beta[0] + sum(beta[i + 1] * row[i] for i in range(len(row))) for row in X]


def main():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "qid": r["question_id"], "paper": r["paper_id"],
                "y": float(r["score_rate"]),
                "x": [float(r[f]) for f in FEATURES],
                "is_open": int(r["is_open"]),
            })

    beta = fit_ols([r["x"] for r in rows], [r["y"] for r in rows])
    for r in rows:
        r["pred"] = beta[0] + sum(beta[i+1] * r["x"][i] for i in range(len(FEATURES)))
        r["resid"] = r["y"] - r["pred"]

    mcq = [r for r in rows if r["is_open"] == 0]
    print(f"MCQ (is_open=0) items: {len(mcq)}")

    # Stratified: 4 largest-|resid| MCQ per paper
    per_paper = {}
    for r in mcq:
        per_paper.setdefault(r["paper"], []).append(r)

    picked = []
    for p in sorted(per_paper.keys()):
        items = sorted(per_paper[p], key=lambda r: -abs(r["resid"]))[:4]
        picked.extend(items)
        print(f"{p}: picked {[i['qid'] for i in items]}")

    subset = [{
        "paper": r["paper"], "qid": r["qid"],
        "score_rate": round(r["y"], 3),
        "predicted": round(r["pred"], 3),
        "residual": round(r["resid"], 3),
    } for r in picked]

    OUT_JSON.write_text(json.dumps(subset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {len(subset)} items to {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
