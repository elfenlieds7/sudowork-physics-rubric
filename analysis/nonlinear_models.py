"""换模型 · 非线性 · 突破 linear + Ridge 的 0.066 天花板.

Ethan 13:03 建议. 试:
- Random Forest
- Gradient Boosting (sklearn 自带)
- kNN (baseline)

Fit v5.1 (17 特征) 上 · LOPO CV.
"""
import csv, sys
from pathlib import Path
from statistics import mean

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, r2_score

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"

BASE = ["concept","reasoning","novelty","visual","modeling","position","is_open",
        "topic_mech","topic_em","textbook_scene_degree","textbook_pattern_degree"]
NEW = ["transfer_cost","is_last_quarter","earlier_load"]
INT = ["mod_x_nov","mod_x_open","con_x_mod"]
V51 = BASE + NEW + INT


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


def lopo_eval(rows, feats, model_factory):
    """LOPO CV for any sklearn-compatible model"""
    papers = sorted({r["paper"] for r in rows})
    y_true, y_pred = [], []
    for held in papers:
        train = [r for r in rows if r["paper"] != held]
        test = [r for r in rows if r["paper"] == held]
        X_tr = np.array([[r[f] for f in feats] for r in train])
        y_tr = np.array([r["y"] for r in train])
        X_te = np.array([[r[f] for f in feats] for r in test])
        y_te = np.array([r["y"] for r in test])
        model = model_factory()
        model.fit(X_tr, y_tr)
        yp = model.predict(X_te)
        y_true.extend(y_te.tolist())
        y_pred.extend(yp.tolist())
    return {"r2": r2_score(y_true, y_pred), "mae": mean_absolute_error(y_true, y_pred)}


def main():
    rows = load()
    print(f"n = {len(rows)} items, features = {len(V51)} (v5.1)")
    print()
    print(f"{'模型':<45} {'LOPO R²':>10} {'LOPO MAE':>10}")
    print('-' * 68)

    experiments = [
        ("Ridge α=2 (linear baseline)", lambda: Ridge(alpha=2.0)),
        ("Lasso α=0.001", lambda: Lasso(alpha=0.001, max_iter=10000)),
        ("kNN k=5", lambda: KNeighborsRegressor(n_neighbors=5)),
        ("kNN k=10", lambda: KNeighborsRegressor(n_neighbors=10)),
        ("kNN k=15", lambda: KNeighborsRegressor(n_neighbors=15)),
        ("Random Forest 100 trees, depth=5", lambda: RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42, min_samples_leaf=5)),
        ("Random Forest 300 trees, depth=6", lambda: RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42, min_samples_leaf=3)),
        ("Random Forest 500 trees, depth=8", lambda: RandomForestRegressor(n_estimators=500, max_depth=8, random_state=42, min_samples_leaf=2)),
        ("GBM 100 trees, depth=3, lr=0.05", lambda: GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)),
        ("GBM 200 trees, depth=3, lr=0.03", lambda: GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.03, random_state=42)),
        ("GBM 300 trees, depth=4, lr=0.02", lambda: GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.02, random_state=42)),
        ("GBM 500 trees, depth=2, lr=0.01", lambda: GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42)),
        ("SVR linear", lambda: SVR(kernel='linear', C=1.0)),
        ("SVR rbf", lambda: SVR(kernel='rbf', C=1.0, gamma='scale')),
    ]

    for label, factory in experiments:
        try:
            l = lopo_eval(rows, V51, factory)
            print(f"{label:<45} {l['r2']:>10.4f} {l['mae']:>10.4f}")
        except Exception as e:
            print(f"{label:<45} ERROR: {str(e)[:30]}")


if __name__ == "__main__":
    main()
