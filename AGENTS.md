# AGENTS.md · onboarding for AI agents

If you're a new AI joining this project, this file gets you productive fast. Read `README.md` first for high-level context, then this for how-to.

## The 3 people

- **Collaborating teacher** — 北京八中 物理教研组长 · 40 年教龄 · 命题专家。Uses wechat + shareone. **Never asks her to open github or read code.** Her feedback comes via wechat text or (rarely) shareone comment.
- **Ethan (宋一民)** — sudowork founder. Full-context human collaborator. Github: `elfenlieds7`. Pushes AI to be precise, doesn't accept over-generalization, expects meta-reasoning.
- **AI agent (you)** — sudowork系. Coordination + memory + analysis layer. Never a decision-maker; always defer final judgment to Ethan or the teacher.

## The 2 collaboration surfaces (never confuse)

| Surface | Role | Update pattern |
|---|---|---|
| **shareone links** | Read-only + comment for the teacher / external experts | `deliverables/*.html` → shareone via PUT (URL stable, content evolves) |
| **This github repo** | Version-controlled source of truth for AI + Ethan | Normal git workflow (commit, push, PR) |

**Rule**: build deliverables in `deliverables/*/`, deploy to shareone, keep git as canonical source. Shareone is the "publish" step, not the "work" step.

## Standing behaviors expected of you

1. **Solve problem type first, then technique** — see `context/meta_lessons.md` "Type A vs Type B" — do NOT collapse "find constraint" (inequality answer) with "find optimum" (equality answer). This bit us on 蹦极题.
2. **Reflection precision must match error precision** — don't reflect at "big principle" level when the actual error was a specific micro-step. `context/meta_lessons.md` documents 3 iterations of this failure mode.
3. **Match domain reading conventions** — Chinese HS physics has 60+ years of built-in phrasing. "不超过 X" = ≤ X (range, not point). "较大" ≠ maximize. "匹配规律" = constraint (usually inequality). Before answering any problem the teacher sends, apply domain reading mode.
4. **Enable shareone comments by default** — `--allow-comments true` on `upload_page.js`. Failing to do this = surface is broadcast-only, not collaboration. Was forgotten twice; documented in memory.
5. **Read API response schema before displaying** — dump `sorted(response.keys())` first, don't assume field names. (Cost me an "author=?" display bug on shareone comments.)
6. **Communicate what you need clearly** — every message to the teacher should end with EITHER "no ask right now" OR an explicit list of what you need her to confirm/provide.
7. **All deliverables through shareone** — no direct docx sends, no wechat text-dumps of long analysis. Even if the reader is the teacher, prefer a shareone link over a wechat wall-of-text.

## Doing common tasks

### Read a source PDF visually
```bash
python scripts/pdf_to_png.py  # Renders all data/source_pdfs/*.pdf → data/extracted_pages/*.png
```
Then use your image-reading capability to visually inspect (many pages have 手写红字 with 得分率 — text extraction misses these).

### Fit / re-fit rubric
```bash
python analysis/rubric_v1_ols.py  # Baseline OLS, in-sample R²
# TODO: python analysis/rubric_v2_lopo.py  # LOPO cross-validation (see meta_lessons.md commitments)
```

### Deploy an updated HTML to shareone
Currently manual (each iteration this session was done by-hand via `node upload_page.js --share-id <id> <file>`). The `scripts/deploy_shareone.py` (upcoming) will wrap this. Until then:

```bash
# From C:\Users\songym\cursor-projects\document-ai (yes, cross-project — vendor path lives there)
SHAREONE_API_KEY=$(cat ~/.shareone_credentials | python -c "import json,sys; print(json.load(sys.stdin)['api_key'])") \
node vendor/shareone-skill/vendor/shareone-skill/scripts/upload_page.js \
  <path-to-html> --share-id <share_id>
```

### Reply to a shareone comment as agent
```python
# See analysis/reply_shareone_comment.py (extract from scratchpad reply_batch.py pattern)
# Key: POST /api/v1/shares/{ref}/comments with parent_id + quote + highlighter_data + author_role='agent'
```

### Send a wechat message to the teacher
```bash
cd C:/Users/songym/cursor-projects/wechat-skill
PYTHONIOENCODING=utf-8 python scripts/cli.py send -c "<teacher-contact-name>" -t "<message>"
```
Note: message auto-appends "🤖 [此消息由AI助手代发]" watermark. This is desired — the teacher knows she's talking to AI.

## Where things live

- **Source materials** in `data/source_pdfs/` and `data/source_images/`
- **Wechat cache** (external, not committed) `D:\xwechat_files\Saturniid_cf4f\msg\file\2026-08\` — original file location before copy
- **ShareOne credentials** at `C:\Users\songym\.shareone_credentials` (JSON with `api_key`)
- **wechat-skill and shareone-skill** — vendored in `C:\Users\songym\cursor-projects\document-ai\vendor\` (separate project, this repo doesn't own the tools)

## What NOT to do

- Don't commit `.shareone_credentials` or any API keys
- Don't commit raw wechat conversation logs (privacy — teacher's messages)
- Don't make design decisions on behalf of the teacher (she's the命题 expert, not you)
- Don't tell the teacher what shareone URL to click without ALSO explaining what's new / what you need her to look at

## Meta

If you get stuck or confused, read `context/meta_lessons.md` — it contains reasoning traps that already burned time. Don't rediscover them.

If you find a new reasoning trap yourself, append to `context/meta_lessons.md` and commit. That's the accumulating value of this repo.
