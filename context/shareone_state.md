# ShareOne state · 2026-08-01

External URLs currently in use for this project. Credentials NOT in this file (see `.env` at project root, gitignored).

## Live shareone pages

### 1. 蹦极题解答 (bungee physics problem)

- **URL**: https://s.shareone.vip/s/bungee-yang-laoshi
- **share_id**: `8TJzJMF921kypmqW`
- **slug**: `bungee-yang-laoshi`
- **Password**: none (公开)
- **allow_comments**: true (enabled 2026-08-01 after Ethan reminder)
- **Current source**: `deliverables/bungee_solution/v4.html`
- **History**:
  - v1: initial solution — 3 mistakes (see meta_lessons)
  - v2: fixed but reflection was "off-target" (over-generalized)
  - v3: better reflection but still含糊
  - v4: real root cause (Type A vs Type B problem type confusion), with recursive meta-lesson

### 2. 难度预测 rubric v1 pilot

- **URL**: https://s.shareone.vip/s/difficulty-rubric-v1-yang
- **share_id**: `BzXjsrbu6uQ887Kg`
- **slug**: `difficulty-rubric-v1-yang`
- **Password**: none (公开)
- **allow_comments**: true (enabled 2026-08-01 after Ethan reminder)
- **Current source**: `deliverables/rubric/v1.html`
- **Content**: 33-datapoint OLS fit, R² = 0.886, 10-feature rubric
- **Active comment thread**: 1 open — from `elfenlieds7` (Ethan, `author_role=owner`), asking for LOPO CV commitment. Replied as agent 2026-08-01; parent kept open until v2 delivers.

## Comment automation notes

- **Top-level comment POST is visitor-UI-only** — API POST without parent_id returns 404. Owner API key doesn't help.
- **Reply POST works via API** — parent_id + quote + highlighter_data + author_role='agent'
- **Selecting text in iframe was broken** in ai-dev-browser; fixed 2026-07-24 via new `select_text` tool
- **Recipe for adding native comments programmatically** (via automation): see `document-ai` memory `project_ai_dev_browser_iframe_bug.md`
- **Login gate**: shareone requires web login (via browser) for visitors to POST comments. Owner (Ethan) is `elfenlieds7`, already logged in.

## How to fetch comments (read-only)

```bash
API_KEY=$(cat ~/.shareone_credentials | python -c "import json,sys; print(json.load(sys.stdin)['api_key'])")
SHAREONE_API_KEY="$API_KEY" node \
  C:/Users/songym/cursor-projects/document-ai/vendor/shareone-skill/vendor/shareone-skill/scripts/shareone_api_request.js \
  "/api/v1/shares/<share_id>/comments?status=all" --public
```

## How to reply to a comment as agent (parent stays open)

See `analysis/reply_shareone_comment.py` (upcoming — extract from scratchpad `reply_batch.py`). Key fields:

```json
{
  "parent_id": "<comment_id>",
  "quote": "<inherited from parent>",
  "highlighter_data": "<inherited from parent>",
  "content": "<your reply>",
  "author_role": "agent"
}
```

POST to `/api/v1/shares/<share_id>/comments`. Returns new comment id.

## Comment author field (schema gotcha)

Comment JSON has:
- `user`: `{"username": "elfenliedsp"}` ← real author name is here
- `author_role`: `"owner"` / `"visitor"` / `"agent"`
- `user_id`: uuid

Do NOT look for `author_name` (doesn't exist). Documented as bug in this session.
