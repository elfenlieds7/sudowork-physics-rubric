# ShareOne state · 2026-11-02

## 2026-11-02 · 计划 v3.2：恢复复现主线与奖励设计说明

- 用户明确原目标是复现微软Decision-1路线；主页面突出以公开技术为参照的自主Qwen决策模型主线，现成模型保留作性能对照与结构参考。
- LoRA监督起点之后明确安排同模型RLCD式实验，与同预算监督继续训练比较。已有可用决策模型时可另做直接强化学习小对照；先监督不是LoRA或RLCD的定义要求。
- 新增 `#reward-design`，说明基础均值奖励、概率标签边界、泛化和稳定性；奖励公式尚未定稿。微软完整配方未知，不能把自己的RLCD式实验称为精确复现。
- 本轮开始时主页面绑定 `a199700aa9d0012e54dfb837e8e0592cc4568f24`，下载内容与本地完全相同。七年资料、219条记录及结构核验状态不变；没有启动模型训练。
- 显示文件名随版本改为“物理试题得分率预测_研究进展与下一阶段计划_v3.2.html”，发布继续固定新Git提交，保留原链接与访问设置。

## 2026-11-02 · 计划 v3.1 与七年数据接收

- 主链接、分享ID保持：`difficulty-rubric-v2-yang` / `TJPUMgC3WpqM8XPX`；Git源文件仍为 `deliverables/rubric/v2.html`。
- 显示文件名改为“物理试题得分率预测_研究进展与下一阶段计划_v3.1.html”；固定提交的远端源绑定保留。
- 新增 `#training-basics`：全参／LoRA与监督训练／RLCD两个维度、中文交互示意、决策层＋LoRA首轮方案与全参决策条件。
- 新增 `#data-intake`：七年219条观测、逐年覆盖分值、资料状态；不含逐题成绩。
- 结构核验完成，题目数字化、同题比较和训练均未完成。2026年新表32条与旧核验31设问须先对齐，不覆盖历史误差结果。
- 新表及接收审计位于本地忽略目录 `data/private/gaokao_2020_2026_20261102/`。2020—2022年试卷与答案在其 `source_pdfs/`；全部未进入公开Git。
- 2023—2026年试卷、2026年参考答案已有；2023—2025年正式参考答案与评分标准当前未在仓库找到。
- 本轮开始下载的源内容与 `95112aa61430e56229fb2065f98b8c9aa6424c11` 完全一致，未发现未处理评论。历史正文逐字保留，发布时只更新本分享的固定提交绑定。
- 用户授权随项目推进同步更新本链接。按下方流程先提交Git，再绑定新完整提交并回读核验；维持访问和评论设置。

下方为上次发布记录及沿用的发布流程。

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

页内 `#anchor` 点击由源文件的 window 捕获阶段监听器处理：先阻止默认跳转，展开历史区并在当前文档滚动。ShareOne 的 document 捕获阶段链接桥会将锚点按 HTTP 链接交给外层导航；仅在冒泡阶段 preventDefault 已经太晚。验收必须确认外层 URL 仍为原 `/s/` 链接，不能只检查目标内容可见。

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
