# sudowork-physics-rubric

Collaboration between **A collaborating physics teacher** (北京八中 物理教研组长 · 40 年教龄 · 命题专家) and **sudowork AI agents** on:

1. **Solving her physics problems** (with proper reflection + diagrams) — proof-of-concept that AI can be a genuine work partner, not just tool
2. **Building a difficulty-prediction rubric** for exam questions — helping her predict question-level 得分率 at command time, to design better-structured tests

## Current state (2026-08-02 early morning)

- **Bungee problem case study (v1→v4)**: 3 reflection iterations after the teacher caught an error; documents the "Type A vs Type B problem type" trap that we later added to `meta_lessons.md`. Deliverable: https://s.shareone.vip/s/bungee-yang-laoshi
- **Rubric v1 (pilot)**: fit on 2026.4 西城一模 (33 questions with hand-annotated score rates from the teacher), R² = 0.886 in-sample, MAE = 0.058, 10 features. Deliverable: https://s.shareone.vip/s/difficulty-rubric-v1-yang
- **Rubric v2 (textbook feature)**: adds `textbook_model_degree` (0/1/2) using the teacher-provided 6-book 人教版 2019 textbook as reference. ΔR² = +0.0034 vs v1 — **not statistically distinguishable at n=33**. See `analysis/notebooks/v2_textbook_feature_analysis.md` for honest interpretation. Feature theoretically sound, waits for 5-paper dataset scale-up for real evaluation.
- **Pending teacher confirmation on**: 4 remaining asks (see `open_questions.md`; #2 dropped by teacher)
- **Pending Ethan-requested methodology**: LOPO cross-validation + cohort effect handling (see `context/meta_lessons.md` #8, requires 5-paper dataset)

## Project structure

```
data/
  source_pdfs/         # 5 exam PDFs (2 高考 + 3 西城一模) · +textbook (gitignored, 80MB)
  source_images/       # Charts + problem images from the teacher (currently empty)
  extracted_pages/     # 44 PNG renderings of exam PDF pages (pymupdf ~150dpi)
  reference/
    textbook_toc.md          # 6-book textbook table of contents (41 chapters, 786 pages)
    dianxing_moxing_catalog.md  # 典型模型 catalog per chapter (v0.1 draft)
    textbook_samples/        # Rendered sample pages for spot-check (gitignored)
  labeled/
    xicheng_2026_scored.csv     # v1: 33 questions × 10 features + score_rate
    xicheng_2026_scored_v2.csv  # v2: same 33 questions × 11 features (+textbook_model_degree)
    rubric_v1_result.json       # OLS fit results v1
    rubric_v2_result.json       # OLS fit results v2 (includes v1 vs v2 comparison)
deliverables/
  bungee_solution/     # 蹦极题 v4 HTML (currently live on shareone)
  rubric/              # Rubric v1 HTML (currently live) · v2 draft coming
analysis/
  rubric_v1_ols.py         # v1 baseline OLS regression
  rubric_v2_textbook.py    # v2 adds textbook_model_degree feature, compares to v1
  notebooks/
    v2_textbook_feature_analysis.md  # honest analysis of v2 results
scripts/
  pdf_to_png.py                # Batch render source_pdfs → extracted_pages
  render_textbook_sample.py    # On-demand sample textbook page renderer (spot-check)
context/
  shareone_state.md    # All shareone URLs, share_ids, comment IDs (no credentials)
  meta_lessons.md      # 8 reasoning traps discovered, methodology commitments
  key_moments.md       # Curated collaboration highlights (personal info scrubbed)
open_questions.md      # Asks pending teacher confirmation (4 open, 1 dropped)
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
