# sudowork-physics-rubric

Collaboration between **A collaborating physics teacher** (北京八中 物理教研组长 · 40 年教龄 · 命题专家) and **sudowork AI agents** on:

1. **Solving her physics problems** (with proper reflection + diagrams) — proof-of-concept that AI can be a genuine work partner, not just tool
2. **Building a difficulty-prediction rubric** for exam questions — helping her predict question-level 得分率 at command time, to design better-structured tests

## Current state (2026-08-02)

- **Bungee problem case study (v1→v4)**: 3 reflection iterations after the teacher caught an error; documents the "Type A vs Type B problem type" trap that we later added to `meta_lessons.md`. Deliverable: https://s.shareone.vip/s/bungee-yang-laoshi
- **Rubric v1 (pilot · superseded)**: fit on 2026.4 西城一模 (33 questions), R² = 0.886 in-sample, 10 features.
- **Rubric v2 (textbook feature · intermediate)**: adds `textbook_model_degree` (0/1/2). ΔR² = +0.0034 vs v1 — not distinguishable at n=33.
- **Rubric v3 · LOPO scale-up · CURRENT** (2026-08-02):
  - **162 items across 5 papers** (高考 2024/2025 + 西城 2024/2025/2026)
  - **LOPO out-of-sample R² = 0.841 · MAE = 0.076** — rubric generalizes to unseen papers
  - **A+B split**: `textbook_scene_degree` and `textbook_pattern_degree` (per teacher's answer). Pattern β=+0.071 (strong signal), scene β=+0.0003 (noise) — solution-pattern familiarity dominates over scene familiarity.
  - Cohort variance empirically small: across-paper mean SD = 0.027 (resolved Ethan-flagged Ask #3 without teacher time)
  - Deliverable: https://s.shareone.vip/s/difficulty-rubric-v1-yang (v2.html deployed, slug retained for comment continuity)
  - Ethan's CV commitment (parent 4ec28439) resolved with reply comment c6b9ee47
- **Pending teacher confirmation on**:
  - Whether pattern-dominates-over-scene finding matches her intuition
  - Sample-audit of 5-10 scene/pattern label choices
  - Whether 陷阱数 (misconception distractor count) is worth adding as v4 feature (Ask #4b, still open)

## Project structure

```
data/
  source_pdfs/         # 5 exam PDFs (2 高考 + 3 西城一模) · +textbook (gitignored, 80MB)
  source_images/       # Charts + problem images from the teacher (currently empty)
  extracted_pages/     # 44 PNG renderings of exam PDF pages (pymupdf ~150dpi)
  reference/
    textbook_toc.md              # 6-book textbook table of contents (41 chapters, 786 pages)
    dianxing_moxing_catalog.md   # 典型模型 catalog · v0.2 with A+B split (scene + pattern)
    textbook_samples/            # Rendered sample pages for spot-check (gitignored)
  labeled/
    xicheng_2026_scored.csv       # v1: 33 questions × 10 features
    xicheng_2026_scored_v2.csv    # v2: same 33 questions × 11 features
    combined_scored_v3.csv        # v3: 162 items × 12 features across 5 papers · CURRENT
    rubric_v1_result.json         # v1 OLS fit
    rubric_v2_result.json         # v2 OLS fit
    rubric_v3_result.json         # v3 LOPO CV + cohort + coefficients · CURRENT
deliverables/
  bungee_solution/     # 蹦极题 v4 HTML (currently live on shareone)
  rubric/              # v1.html (superseded) + v2.html (currently live on shareone)
analysis/
  rubric_v1_ols.py             # v1 baseline OLS regression (33 items)
  rubric_v2_textbook.py        # v2 adds textbook_model_degree feature (33 items)
  build_v3_dataset.py          # v3 inline-labeled 162 items, emits combined CSV
  rubric_v3_lopo.py            # v3 LOPO CV + cohort adjust + M1/M2/M3 comparison
  reply_ethan_cv_comment.py    # one-shot: resolve Ethan's CV comment thread with v3 results
  notebooks/
    v2_textbook_feature_analysis.md  # v2 honest analysis (n=33, not distinguishable)
    v3_lopo_analysis.md              # v3 LOPO + A+B split findings
scripts/
  pdf_to_png.py                # Batch render source_pdfs → extracted_pages
  render_textbook_sample.py    # On-demand sample textbook page renderer (spot-check)
context/
  shareone_state.md    # All shareone URLs, share_ids, comment IDs (no credentials)
  meta_lessons.md      # 9 reasoning traps discovered, methodology commitments
  key_moments.md       # Curated collaboration highlights (personal info scrubbed)
open_questions.md      # Asks pending teacher confirmation (see also v3 notebook for new asks)
```

## Two collaboration surfaces (paired)

- **shareone** (公开链接 + comment 侧栏) — for the teacher to read & feedback. No account needed. She uses wechat mostly.
- **This repo** (github **public**) — source of truth for AI agents (Claude / Gemini / others), engineers, future co-founders. Structured data + code + commit history + AI-onboarding docs. Personal info about the collaborator has been scrubbed; only professional identity is referenced.

Deliverables flow: build in `deliverables/*/`, deploy via `scripts/deploy_shareone.py` (upcoming), shareone URL stays stable.

## Getting started (for a new AI joining this project)

1. Read `AGENTS.md` first — it's specifically for AI onboarding
2. Read `context/meta_lessons.md` — reasoning traps to avoid (these are hard-earned)
3. Read `open_questions.md` — the current pending work
4. Read `context/shareone_state.md` — where things live externally
5. Skim `data/labeled/xicheng_2026_scored_v2.csv` — the current data model (11 features)
6. Skim `analysis/notebooks/v2_textbook_feature_analysis.md` — most recent iteration + its honest interpretation

## For humans

Contact **Ethan (宋一民)** — sudowork founder. Github: `elfenlieds7`.
