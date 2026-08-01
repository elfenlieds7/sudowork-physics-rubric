# sudowork-physics-rubric

Collaboration between **A collaborating physics teacher** (北京八中 物理教研组长 · 40 年教龄 · 命题专家) and **sudowork AI agents** on:

1. **Solving her physics problems** (with proper reflection + diagrams) — proof-of-concept that AI can be a genuine work partner, not just tool
2. **Building a difficulty-prediction rubric** for exam questions — helping her predict question-level 得分率 at command time, to design better-structured tests

## Current state (2026-08-01)

- **蹦极题 (bungee)**: worked v1→v4, arrived at correct answer after v2/v3/v4 iterations that the teacher called out — deliverable at https://s.shareone.vip/s/bungee-yang-laoshi (shareone link, no login)
- **Rubric v1 (pilot)**: fit on 2026.4 西城一模 (33 questions with hand-annotated score rates), R² = 0.886 in-sample, MAE = 0.058, 10 features — deliverable at https://s.shareone.vip/s/difficulty-rubric-v1-yang
- **Pending teacher confirmation on**: 5 explicit asks (see `open_questions.md`)
- **Pending Ethan-requested v2 methodology**: LOPO cross-validation + cohort effect handling (see `context/meta_lessons.md` for full commitments)

## Project structure

```
data/
  source_pdfs/       # 5 PDFs the teacher provided (2024/2025 高考 + 2024/2025/2026 西城一模)
  source_images/     # Charts + problem images from the teacher
  extracted_pages/   # 44 PNG renderings of PDF pages (pymupdf, ~150dpi)
  labeled/           # Structured scoring data (json/csv) for machine learning
deliverables/
  bungee_solution/   # 蹦极题 v1-v4 HTML files (v4 is current shareone)
  rubric/            # Rubric v1 HTML (current shareone)
analysis/
  rubric_v1_ols.py   # Baseline linear regression (33 data points, R²=0.886 in-sample)
  # rubric_v2_lopo.py  # (upcoming) LOPO cross-validation + cohort handling
scripts/
  pdf_to_png.py      # Convert source PDFs to PNGs for visual reading
  # deploy_shareone.py # (upcoming) HTML → shareone one-liner
context/
  shareone_state.md  # All shareone URLs, share_ids, comment IDs (no credentials)
  meta_lessons.md    # Reasoning traps discovered, methodology commitments
  key_moments.md     # Curated wechat highlights that shape context
open_questions.md    # Asks pending teacher confirmation
```

## Two collaboration surfaces (paired)

- **shareone** (公开链接 + comment 侧栏) — for the teacher to read & feedback. No account needed. She uses wechat mostly.
- **This repo** (github private) — for AI (Claude / Gemini / others), Ethan, future co-founders. Structured data + code + commit history + AI-onboarding docs.

Deliverables flow: build in `deliverables/*/`, deploy via `scripts/deploy_shareone.py` (upcoming), shareone URL stays stable.

## Getting started (for a new AI joining this project)

1. Read `AGENTS.md` first — it's specifically for AI onboarding
2. Read `context/meta_lessons.md` — reasoning traps to avoid (these are hard-earned)
3. Read `open_questions.md` — the current pending work
4. Read `context/shareone_state.md` — where things live externally
5. Skim `data/labeled/xicheng_2026_scored.json` — the current data model

## For humans

Contact **Ethan (宋一民)** — sudowork founder. Github: `elfenlieds7`.
