# ShareOne state · 2026-10-29

## 当前主 SSOT

- **URL**: https://s.shareone.vip/s/difficulty-rubric-v2-yang
- **源文件**: `deliverables/rubric/v2.html`，文件名沿用，当前内容为计划 v3.0。
- **当前计划**：因旧模型单题精度不足，开展语义决策模型同题评测与领域适配；新模型精度尚未验证。
- **历史区**：`#legacy-archive` 保留完整旧页面，`#validation-2026` 保留 G.10 实测核验。
- **本轮更新前评论数**：0。更新原分享，保留评论、访问范围、密码、水印及其他设置。
- **本轮开始时绑定**：`https://raw.githubusercontent.com/elfenlieds7/sudowork-physics-rubric/99a59e861ba3afab8cb35b7558c3a585380568f1/deliverables/rubric/v2.html`。
- **版本方式**：固定 Git commit；不要默默改成 main 分支 URL。

### 后续更新流程

1. 修改并核验上述 Git 源文件，提交、推送到 `elfenlieds7/sudowork-physics-rubric`。
2. 按当前安装的 ShareOne skill 检查凭据。设置 `SHAREONE_BASE_URL=https://s.shareone.vip`，运行该 skill 的 `scripts/upload_page.js --share-id difficulty-rubric-v2-yang --remote-url <新完整提交的 raw URL>`。
3. 不加 `--force-new`，不解绑源，不改 slug；省略未要求修改的设置参数。
4. 下载原分享，核对源 URL、完整内容与提交产物一致，并检查原链接、评论和交互。

页面仍固定到旧提交时，单独 Git push 不会使 ShareOne 换版。以发布脚本返回的实际分享 URL 和下载核验为准。凭据不得写进本文件或仓库。

页内 `#anchor` 点击由源文件脚本处理：阻止默认跳转，展开历史区并在当前文档滚动。线上嵌入文档的默认链接目标可能指向顶层窗口，普通锚点会离开 ShareOne 评论外壳；验收必须确认外层 URL 仍为原 `/s/` 链接，不能只检查目标内容可见。

## 其他页面与方法边界

- 论文 `https://s.shareone.vip/s/sodu-physics-rubric-paper-v1` 仍为历史稿，本轮未重写。
- 蹦极题 `https://s.shareone.vip/s/bungee-yang-laoshi` 独立保留，本轮未改动。
- 旧 `difficulty-rubric-v1-yang` 已废弃，不得作为当前主链接。下方旧记录仅供追溯。
- Jev 为固定的厂商模型，目前不提供客户微调；sudorouter 原生 `/v1/systemone` 为推理接入。已验证 Jev 1.14 的合成题调用，完整试卷评测尚未完成。
- 直接评测、本地输出校准、训练开放模型分别记录。RLCD 式训练与监督训练分开，不把 RLCR 论文的代码路线写成已确认的 Decision-1／Clef 配方。
- 原始成绩保留在 `data/private/`，不进入公开页面或云端请求；只在本地连接预测和实测。2026 年已审阅数据属于回顾性核验。

---

## 历史记录 · 2026-08-01（下方链接和操作示例不作为当前流程）

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
