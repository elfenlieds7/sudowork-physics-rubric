"""Fit cohort offset model (西城 → 北京市) once teacher provides paired rates.

Input:  data/private/cohort_calibration.csv  (西城_rate + 北京_rate columns filled)
Output: fitted offset model + diagnostics + saved coefficients for re-use

Candidate offset models:
  M0 · Constant:      β_bj = β_xc + c
  M1 · Linear:        β_bj = a + b·β_xc
  M2 · Nonlinear:     β_bj = β_xc + c·(1 - β_xc)   (small offset for hard Qs, big for easy)
  M3 · Difficulty-band: separate c for β_xc ∈ [0, .5], [.5, .8], [.8, 1]

Pick model by cross-validated MAE. Report coefficients and generate a plot
if matplotlib available.
"""
import csv
import sys
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

CAL_PATH = Path(__file__).resolve().parent.parent / "data" / "private" / "cohort_calibration.csv"


def load_pairs():
    if not CAL_PATH.exists():
        print(f"Calibration file not found: {CAL_PATH}")
        print("Waiting for teacher's data (expected tonight 2026-08-04).")
        print(f"Template at: data/private/cohort_calibration_template.csv")
        sys.exit(0)
    pairs = []
    with open(CAL_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            xc = r.get('xicheng_rate', '').strip()
            bj = r.get('beijing_rate', '').strip()
            if xc and bj:
                try:
                    pairs.append({
                        'paper': r['paper_id'],
                        'qid': r['question_id'],
                        'xc': float(xc),
                        'bj': float(bj),
                    })
                except ValueError:
                    pass
    return pairs


def fit_m0_constant(xs, bs):
    """β_bj = β_xc + c · fit c by mean residual."""
    c = float(np.mean(bs - xs))
    pred = xs + c
    mae = float(np.mean(np.abs(pred - bs)))
    return {'model': 'M0 · constant', 'c': c, 'mae': mae, 'pred': pred}


def fit_m1_linear(xs, bs):
    """β_bj = a + b·β_xc · least squares."""
    A = np.column_stack([np.ones(len(xs)), xs])
    coef, *_ = np.linalg.lstsq(A, bs, rcond=None)
    a, b = coef
    pred = a + b * xs
    mae = float(np.mean(np.abs(pred - bs)))
    return {'model': 'M1 · linear', 'a': float(a), 'b': float(b), 'mae': mae, 'pred': pred}


def fit_m2_ceiling(xs, bs):
    """β_bj = β_xc + c(1-β_xc) · fit c."""
    delta = bs - xs
    weight = 1 - xs
    c = float(np.sum(delta * weight) / np.sum(weight ** 2))
    pred = xs + c * (1 - xs)
    mae = float(np.mean(np.abs(pred - bs)))
    return {'model': 'M2 · ceiling', 'c': c, 'mae': mae, 'pred': pred}


def fit_m3_band(xs, bs):
    """Different offset per difficulty band."""
    bands = [(0, 0.5), (0.5, 0.8), (0.8, 1.01)]
    coefs = []
    pred = np.zeros_like(bs)
    for lo, hi in bands:
        mask = (xs >= lo) & (xs < hi)
        if mask.sum() > 0:
            c = float(np.mean(bs[mask] - xs[mask]))
            coefs.append({'band': f'[{lo},{hi})', 'n': int(mask.sum()), 'c': c})
            pred[mask] = xs[mask] + c
        else:
            coefs.append({'band': f'[{lo},{hi})', 'n': 0, 'c': None})
    mae = float(np.mean(np.abs(pred - bs)))
    return {'model': 'M3 · band', 'bands': coefs, 'mae': mae, 'pred': pred}


def loo_mae(fit_fn, xs, bs):
    """Leave-one-out MAE for the fitted model."""
    preds = np.zeros(len(xs))
    for i in range(len(xs)):
        mask = np.arange(len(xs)) != i
        res = fit_fn(xs[mask], bs[mask])
        if 'a' in res and 'b' in res:
            preds[i] = res['a'] + res['b'] * xs[i]
        elif res['model'].startswith('M2'):
            preds[i] = xs[i] + res['c'] * (1 - xs[i])
        elif res['model'].startswith('M3'):
            for band in res['bands']:
                lo, hi = eval(band['band'].replace(',', ','))  # noqa
                # Simpler: just re-classify
            # Fallback: use full-fit band
            bands = [(0, 0.5), (0.5, 0.8), (0.8, 1.01)]
            for lo, hi in bands:
                if lo <= xs[i] < hi:
                    b_res = [b for b in res['bands'] if b['band'] == f'[{lo},{hi})']
                    if b_res and b_res[0]['c'] is not None:
                        preds[i] = xs[i] + b_res[0]['c']
                    else:
                        preds[i] = xs[i]
                    break
        else:
            preds[i] = xs[i] + res['c']
    return float(np.mean(np.abs(preds - bs)))


def main():
    pairs = load_pairs()
    print(f"Loaded {len(pairs)} calibration pairs from {CAL_PATH.name}")
    if len(pairs) < 3:
        print("Need at least 3 pairs to fit any offset model.")
        sys.exit(0)

    xs = np.array([p['xc'] for p in pairs])
    bs = np.array([p['bj'] for p in pairs])

    print()
    print(f"数据集摘要:")
    print(f"  西城 mean = {xs.mean():.4f}  range [{xs.min():.2f}, {xs.max():.2f}]")
    print(f"  北京 mean = {bs.mean():.4f}  range [{bs.min():.2f}, {bs.max():.2f}]")
    print(f"  Delta mean = {(bs-xs).mean():+.4f} = {(bs-xs).mean()*100:+.1f} pp")
    print(f"  Delta stdev = {(bs-xs).std():.4f}")
    print()

    models = []
    for fit in [fit_m0_constant, fit_m1_linear, fit_m2_ceiling, fit_m3_band]:
        res = fit(xs, bs)
        models.append((fit, res))

    print(f"{'Model':<20} {'in-sample MAE':>15} {'LOO MAE':>12}   coefficients")
    print("-" * 76)
    for fit, res in models:
        loo = loo_mae(fit, xs, bs) if len(pairs) >= 5 else float('nan')
        coefs = ''
        if 'c' in res and 'bands' not in res:
            coefs = f"c = {res['c']:+.4f}"
        elif 'a' in res:
            coefs = f"a = {res['a']:+.4f} · b = {res['b']:+.4f}"
        elif 'bands' in res:
            coefs = ' · '.join(
                f"{b['band']}: c={b['c']:+.3f} (n={b['n']})" if b['c'] is not None else f"{b['band']}: empty"
                for b in res['bands']
            )
        print(f"{res['model']:<20} {res['mae']:>15.4f} {loo:>12.4f}   {coefs}")

    # Pick best by LOO MAE (or in-sample if too few pairs)
    if len(pairs) >= 5:
        best = min(models, key=lambda m: loo_mae(m[0], xs, bs))
    else:
        best = min(models, key=lambda m: m[1]['mae'])
    print()
    print(f"BEST MODEL: {best[1]['model']}")
    print(f"Use this to convert future 西城 predictions to 北京市 scale (and inverse).")

    # Diagnostic: residuals per item
    print()
    print("Per-item residuals (sorted by |residual|):")
    print(f"  {'paper':<15} {'qid':<10} {'西城':>7} {'全北京':>7} {'预测':>7} {'残差(pp)':>10}")
    _, best_res = best
    for i in sorted(range(len(pairs)), key=lambda j: abs(best_res['pred'][j] - bs[j]), reverse=True)[:10]:
        p = pairs[i]
        residual = (best_res['pred'][i] - bs[i]) * 100
        print(f"  {p['paper']:<15} {p['qid']:<10} {p['xc']:>7.2f} {p['bj']:>7.2f} "
              f"{best_res['pred'][i]:>7.3f} {residual:>+9.1f}")


if __name__ == "__main__":
    main()
