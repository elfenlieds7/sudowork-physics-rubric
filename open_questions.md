# Open questions · pending teacher confirmation

Status as of 2026-08-01 · she's cooking dinner, will resume tomorrow.

## Pending from her (5 asks in rubric v1 page)

Referenced in the deliverable at https://s.shareone.vip/s/difficulty-rubric-v1-yang (red-bordered "ASK" boxes).

### 1. Rubric 打分校准 · OPEN

Are the 10-dimension scores I assigned to the 33 questions in `data/labeled/xicheng_2026_scored.json` reasonable? Especially `concept` / `reasoning` / `modeling` dimensions where teacher intuition matters. Ask her to sample 3-5 questions and eyeball.

### 2. 期末图双柱含义 · DROPPED (2026-08-01 22:45)

Teacher said: "蓝橙双柱的图片你不用管，请忽略这张图片内容。"
No action needed. Chart data not added to rubric.

### 3. Permission to process the other 4 PDFs · OPEN

Currently only 2026.4 一模 (33 datapoints) processed. Other 4:
- 2024/2025 gaokao physics
- 2024/2025 西城 一模

Processing gets us to ~150 datapoints — enough for LOPO cross-validation. Should be OK, just want her go-ahead.

### 4. Add 2 new rubric features · PARTIALLY RESOLVED (2026-08-01 22:40-22:45)

Rubric residual analysis (in the shareone page) suggests two missing features:
- **易混陷阱数** (number of confusable-concept traps a question has) — STILL OPEN, needs teacher intuition
- **教材经典模型度** (how much the question mirrors a textbook prototype) — **Teacher provided 6-book 人教版 2019 教材 (80MB PDF) as reference**. Guidance: "教材中的例题和习题的情景是学生比较熟悉的情景。可以根据教材确定典型模型。"

Textbook is at `data/source_pdfs/renjiao_2019_textbook_6books.pdf` (git-ignored due to size; re-obtain from teacher wechat if needed).

Next step for me: extract 例题/练习 catalog per chapter, define "典型模型" set, score existing 33 questions on this feature. See task #17.

Still need her to clarify (pending 1 question):
- "典型模型" = specific 物理场景/装置 (弹簧-滑块 · 单摆 · RL 电路 · 电磁感应导轨), OR 教材训练过的解题模式 (能量守恒解决碰撞 · 图像法解运动)? Different granularity.

### 5. Long-term: dedicated model fine-tune on DGX Spark · OPEN

Ethan mentioned they have local DGX Spark that can run Qwen 35B post-training. If rubric methodology stabilizes with R² > 0.6 out-of-sample, we could fine-tune a dedicated difficulty-prediction model. Not for now; direction question only.

## Pending from Ethan (this-session commitments)

Ethan's shareone comment (2026-08-01) on rubric page has 2 methodology asks:

### E1. Leave-One-Paper-Out (LOPO) cross-validation · COMMITTED

Replace random 5-fold with LOPO. Report LOPO R² as honest main metric + random 5-fold as upper bound.

**Blocker**: needs data from all 5 PDFs (currently only 2026 一模 processed). Depends on ask #3 above.

**Deliverable**: `analysis/rubric_v2_lopo.py` + updated shareone page + new comment reply that resolves Ethan's comment.

### E2. Cohort effect (年份 differences) handling · COMMITTED

Two things:
- **Must ask the teacher**: "同一学校 / 同一教材, 3 年一模成绩是否 comparable? 每一届学生水平变化多大?"
- **Model change**: predict `score_rate - paper_mean` instead of raw `score_rate` — factor out per-paper cohort baseline (Option (b) from methodology reply).

**Deliverable**: same as E1 + include cohort handling in v2 script + wechat message to the teacher asking the cohort question.

## What I'll do when the teacher comes back tomorrow (proposed sequence)

1. Wait for her to open the shareone rubric link and either comment / wechat back on the 5 asks
2. Based on her answers, kick off `analysis/rubric_v2_lopo.py` implementation
3. When v2 is done, deploy new HTML to same shareone URL (URL stable)
4. Reply to Ethan's shareone comment with v2 results → he can resolve
5. Send the teacher a "v2 ready" wechat with 1-2 explicit new asks (if any)

## Broader open items (not immediate)

- Automate the "hand-written 得分率 extraction from PDFs" (OCR pipeline) so future papers she sends are auto-parsed
- Build the "命题辅助" side: given a topic + target difficulty, generate 3-5 problem candidates + predict difficulty + cross-AI test
- Turn this into a proper教研工具 for her department (long-term)
