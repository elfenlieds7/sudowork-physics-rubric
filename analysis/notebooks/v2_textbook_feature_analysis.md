# Rubric v2 · textbook_model_degree 特征分析

**Date**: 2026-08-01 深夜 · autonomous work (teacher already sleeping)
**Author**: sudowork agent
**Input**: `data/labeled/xicheng_2026_scored_v2.csv` (33 questions with new column)
**Reference**: `data/reference/dianxing_moxing_catalog.md` (v0.1 draft catalog)
**Output**: `data/labeled/rubric_v2_result.json`

## What I did

1. **Drafted 典型模型 catalog v0.1** from prior HS physics knowledge + TOC alignment (`data/reference/dianxing_moxing_catalog.md`)
2. **Sample-rendered 9 textbook chapter opener pages** for spot-check (`data/reference/textbook_samples/`, gitignored). Confirmed my catalog aligns with actual chapter content on 机械振动 chapter (and by inference, others).
3. **Scored 33 questions** on new feature `textbook_model_degree` (0=novel, 1=variation, 2=direct textbook prototype)
4. **Refit OLS v1 vs v2** on same 33 data points

## Result

| Metric | v1 (10 features) | v2 (11 features) | Δ |
|---|---|---|---|
| R² (in-sample) | 0.8860 | 0.8894 | **+0.0034** |
| MAE | 0.0584 | 0.0571 | -0.0013 |
| n/(k+1) | 3.00 | 2.75 | worse |
| `textbook_model_degree` β | — | +0.0361 | direction ✓ |

## Honest interpretation

**The signal is not statistically distinguishable at n=33**. Reasons:

1. **Sample size too small**: 33 obs can't reliably distinguish 10-feature from 11-feature OLS. Adding a feature almost always increases in-sample R² by ~ε regardless of true signal.
2. **Multicollinearity**: `textbook_model_degree` likely correlates with existing features (`novelty` is its rough inverse; `concept` and `modeling` also proxy for "textbook standard vs novel"). New feature doesn't add orthogonal signal.
3. **Coarse encoding (0/1/2)**: might be lossy; could try 0-5 or continuous score, but that adds subjectivity.

**Residual improvement**: 7 of top-10 previously-large residuals shrank. Direction is right, but effect is small. This is consistent with "modest true signal, obscured by noise at small n".

## What this means for v3

**Not** "drop the feature" — the direction is right and the theoretical basis (teacher-provided textbook as reference) is sound. Just wait for scale:

1. Process the other 4 PDFs (need teacher permission per Ask #3, but she implicitly OK'd by sending them) → ~150 data points
2. Then LOPO cross-validation can compare v1 vs v2 out-of-sample. At n=150, ΔR² of ~0.01 becomes distinguishable from noise.
3. If v2 out-of-sample R² > v1 → keep feature. Else drop.

## Pending on teacher (won't advance without her)

- **Textbook model definition** (Ask #4 clarify): should "典型模型" be concrete物理场景/装置 or 教材训练的解题模式? My v0.1 catalog uses BOTH mixed, which may hurt accuracy. Cleaner definition → better feature.
- **Sample-audit my scoring**: for 5-10 of the 33 questions, does her domain judgment of "textbook_model_degree" match mine? Cheap way to catch systematic bias in my scoring.

## Deferred until 5-paper dataset

- LOPO cross-validation
- Cohort effect handling (predict `score_rate - paper_mean`)
- Feature importance via permutation
- Trying alternate encodings (5-scale, continuous, one-hot per model)

## Files added / changed in this iteration

- New: `data/reference/dianxing_moxing_catalog.md` (v0.1 catalog)
- New: `data/labeled/xicheng_2026_scored_v2.csv` (33 rows × 12 cols, adds `textbook_model_degree`)
- New: `analysis/rubric_v2_textbook.py` (OLS comparison v1 vs v2)
- New: `analysis/notebooks/v2_textbook_feature_analysis.md` (this file)
- New: `scripts/render_textbook_sample.py` (utility, on-demand rendering)
- New: `data/labeled/rubric_v2_result.json` (fit results, both v1 and v2)
- Updated: `.gitignore` (ignore rendered textbook pages)
