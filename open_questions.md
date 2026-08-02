# Open questions · pending teacher confirmation

Status as of 2026-08-02 morning.

## Resolved (in v3 iteration)

### 1. Sample-audit rubric打分 · PARTIAL · re-open in v3
v1 打分现在被 v3 A+B split 部分废弃 · 需重新 sample-audit for `textbook_scene_degree` and `textbook_pattern_degree` labels (see v3 Q2 below).

### 2. 期末图双柱 · DROPPED (2026-08-01)
Teacher: "蓝橙双柱的图片你不用管." Ignored.

### 3. Permission to process the other 4 PDFs · GRANTED (2026-08-02 08:16 wechat: "1. Yes")
Done. 129 additional items labeled and included in v3 dataset.

### 4a. 典型模型 definition · A+B (2026-08-02 08:17 wechat: "2．A+B")
Teacher confirmed BOTH scene and pattern dimensions are meaningful. Split into 2 features in v3.
**Empirical finding**: pattern β=+0.071 (strong), scene β=+0.0003 (noise). Needs re-confirmation (see v3 Q1).

### 4b. 易混陷阱数 feature · TEACHER SAID YES (v1 shareone comment `b7938905` · "非常有必要")
Teacher confirmed adding 陷阱数 as a rubric feature is worthwhile. **Not yet implemented in v3** — needs her actual labeling for existing 162 items (I can't compute misconception distractors reliably from question text alone).
Deferred to v4 backlog.

### E1. LOPO CV · DONE
`analysis/rubric_v3_lopo.py`. LOPO R² = 0.841 · MAE = 0.076. Reported in v2.html shareone page and Ethan reply (comment `c6b9ee47`).

### E2. Cohort handling · DONE + empirically settled
Model 3 with `score_rate - paper_mean` implemented. Cohort SD across 5 papers = 0.027 (small). M3 ≈ M2 (no measurable difference). Teacher didn't need to answer Ask #3 — data speaks.

## Open (v3 · pending teacher)

### v3 Q1. Confirm "pattern > scene" finding
Does the empirical result (pattern β=+0.071 vs scene β=+0.0003) match teacher's intuition?
- If YES → v4 can drop scene dimension for simplicity
- If NO → likely my scene打分 is systematically off (I labeled 162 items alone using catalog); need sample-audit

### v3 Q2. Sample-audit scene/pattern labels
Ask her to label scene/pattern (0/1/2 each) for 5-10 hand-picked items from 2026 西城 一模 · compare vs my labels · identify systematic bias.
Selection strategy: pick items where scene/pattern differ (e.g. (0,2), (2,0)) — these test the split.

### v3 Q3. Add 陷阱数 as v4 feature · NEEDS HER LABELING
She said this is important (per v1 comment). But: I can't label misconception distractors reliably from question text alone. Would need ~15 min per paper of her time labeling. Frame this as: "if she's willing, ~1 hour of labeling would give us the data to test whether 陷阱数 improves prediction."

### 5. Long-term: dedicated model fine-tune on DGX Spark · OPEN
Direction question only. Not immediate.

## Broader open items (not immediate)

- Automate OCR extraction of hand-written 得分率 from teacher-marked PDFs
- Build the "命题辅助" workflow: given topic + target 得分率, generate candidate problems + predict + iterate
- Turn this into a 教研工具 for her department (long-term goal)

## Notes for next AI joining

- v3 是当前 baseline · out-of-sample R² = 0.841
- If teacher confirms pattern-dominates (v3 Q1), simplify to 10-feature v4 (drop scene)
- If she pushes back, run relabel session and rerun v3 with her labels
- 陷阱数 is confirmed important but blocked on her labeling capacity
- 别问她可以自己算的问题 (Lesson 9)
