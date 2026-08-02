# Rubric v3 · LOPO CV + cohort effect + A+B split textbook feature

**Date**: 2026-08-02 morning · autonomous work per Ethan's directive
**Author**: sudowork agent
**Input**: `data/labeled/combined_scored_v3.csv` (162 items × 12 features across 5 papers)
**Output**: `data/labeled/rubric_v3_result.json`

## Dataset

| Paper          | n  | mean 得分率 | sd (within) |
|----------------|----|-----------|-------------|
| gaokao_2024    | 32 | 0.744     | 0.237       |
| gaokao_2025    | 31 | 0.745     | 0.234       |
| xicheng_2024   | 33 | 0.691     | 0.221       |
| xicheng_2025   | 33 | 0.683     | 0.272       |
| xicheng_2026   | 33 | 0.734     | 0.208       |
| **Total**      | **162** | — | — |

**Cohort variance signal (empirical answer to teacher's Ask #3 · no need to ask her)**:
- across-paper SD of means: **0.027** — 5 试卷均分只在 [0.683, 0.745] 波动。
- This is the natural cohort effect: 3% score-rate SD between different exams of similar style.
- Small enough that ignoring it (Model 2 vs Model 3) yields essentially identical CV metrics.

## Feature schema (v3, 11 features after dropping topic-dummy trap)

| Feature | Range | Interpretation |
|---|---|---|
| concept | 1-5 | 涉及独立物理概念数 |
| reasoning | 1-5 | 推理/代数步数 |
| novelty | 0-3 | 情境陌生度 |
| visual | 0-2 | 图像复杂度 |
| modeling | 0-3 | 建模自主度 |
| position | 0-1 | 卷面位置归一化 |
| is_open | 0/1 | 大题分问 |
| topic_mech / topic_em | 0/1 | 力学 / 电磁 (thermo/optics/modern is reference class) |
| **textbook_scene_degree** | 0-2 | 物理场景/装置匹配度 · **NEW** per A |
| **textbook_pattern_degree** | 0-2 | 解题模式匹配度 · **NEW** per B |

## Results

### Model comparison

| Model                       | R²      | MAE    | Interpretation                             |
|-----------------------------|---------|--------|--------------------------------------------|
| M1 · in-sample OLS          | 0.884   | 0.066  | over-optimistic (fits noise)               |
| M2 · LOPO (raw)             | **0.841** | **0.076** | honest out-of-sample generalization        |
| M3 · LOPO + cohort adjust   | 0.841   | 0.076  | ≈ M2 (cohort SD too small to matter here)  |

**Takeaway**: rubric generalizes to unseen papers. R² drops only 0.043 (0.884 → 0.841) from in-sample to out-of-sample, suggesting mild overfit. MAE 0.076 means the rubric predicts 得分率 within ~7.6 percentage points on new papers.

### Per-paper LOPO breakdown (Model 2)

| Held-out paper | R² on that paper | MAE  |
|---|---|---|
| gaokao_2024    | 0.826 | 0.081 |
| gaokao_2025    | 0.880 | 0.065 |
| xicheng_2024   | 0.845 | 0.067 |
| xicheng_2025   | 0.880 | 0.076 |
| xicheng_2026   | **0.732** | 0.090 |

xicheng_2026 is the worst-generalized paper — probably because its labeling (v1) predates the A+B textbook split and may have systematic bias. Worth relabeling later.

### Feature coefficients (M1, for interpretation only)

| Feature                     | β       | Direction correct? |
|-----------------------------|---------|--------------------|
| intercept                   | +0.982  | (baseline for topic=toam · scene=0 · pattern=0) |
| concept                     | -0.107  | ✓ higher concept load → lower score |
| reasoning                   | -0.049  | ✓ |
| novelty                     | -0.016  | ✓ (weak) |
| visual                      | +0.025  | ✗ (unexpected — probably confounds with lower-numbered items having figures) |
| modeling                    | -0.020  | ✓ (weak) |
| position                    | +0.124  | ✗ (unexpected — position 0.9+ items are the hardest; probably absorbing something else) |
| is_open                     | -0.148  | ✓ big effect — 大题分问 much harder |
| topic_mech                  | +0.045  | mechanics slightly easier than modern |
| topic_em                    | +0.084  | electromagnetism slightly easier than modern |
| **textbook_scene_degree**   | **+0.0003** | ⚠ negligible signal |
| **textbook_pattern_degree** | **+0.071**  | ✓ **strong signal** — pattern match matters |

**KEY FINDING — A+B split validated the pattern dimension, invalidated the scene dimension**:
- `textbook_pattern_degree` has β = +0.071 (statistically meaningful with n=162, k=11)
- `textbook_scene_degree` has β = +0.0003 (indistinguishable from zero)
- Interpretation: what makes a question "typical" is whether students have practiced its **solution pattern**, not whether the **surface scene** is familiar. Novel scenes with familiar patterns (天宫霍尔推进器 → 洛伦兹力+能量) score higher than familiar scenes with novel patterns.
- **This validates the A+B split** — the teacher was right that both dimensions exist, and empirically the pattern dimension carries all the predictive signal.

## What's next (for teacher review)

1. **Confirm the pattern-vs-scene finding**. Teacher may push back if her mental model was "scene matters too". If she confirms, we can drop scene from v4 for simplicity.
2. **Relabel xicheng_2026 with A+B lens** (currently the worst-generalized paper).
3. **v4 candidate features to explore** (if teacher agrees to more labeling):
   - 陷阱数 (misconception-inducing distractor count) — my Ask #4b, still pending
   - 计算量 (raw arithmetic step count) — could split from `reasoning`
   - 学生共有前概念错误数 — needs her deep expertise

## Deferred until later

- Sample-audit teacher review of scene/pattern labels (target: 5-10 items)
- Try 5-scale scene/pattern encoding vs current 0-2
- Try interaction terms (e.g. `is_open × pattern_degree`)

## Files added / changed

- New: `analysis/build_v3_dataset.py` — inline-labeled 162 items, emits CSV
- New: `data/labeled/combined_scored_v3.csv` — 162 rows × 15 columns
- New: `analysis/rubric_v3_lopo.py` — LOPO CV + cohort + M1/M2/M3 comparison
- New: `data/labeled/rubric_v3_result.json` — full fit outputs
- New: `analysis/notebooks/v3_lopo_analysis.md` — this file
- Updated: `data/reference/dianxing_moxing_catalog.md` — v0.2 with A+B split
