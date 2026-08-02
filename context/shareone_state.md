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

### 2. 难度预测 rubric v2 (LOPO scaled up)

- **URL**: https://s.shareone.vip/s/difficulty-rubric-v1-yang  (slug retained from v1 for comment continuity)
- **share_id**: `BzXjsrbu6uQ887Kg`
- **slug**: `difficulty-rubric-v1-yang`  ← misleading, but changing it would fork the comment thread
- **Password**: none (公开)
- **allow_comments**: true
- **Current source**: `deliverables/rubric/v2.html` (deployed 2026-08-02)
- **v2 content**: 162-item dataset (5 papers), LOPO R² = 0.841, MAE = 0.076, A+B split textbook feature. Key finding: `textbook_pattern_degree` β=+0.071 (strong), `textbook_scene_degree` β=+0.0003 (noise).
- **Active comment thread**: 1 open — parent id `4ec28439-bb0c-4e19-bbb1-68e70473ea5e` from `elfenlieds7` (Ethan, `author_role=owner`), asked for LOPO CV commitment. **Resolved 2026-08-02** with agent reply linking v2 deployment.

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
