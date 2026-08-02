# Meta-lessons · reasoning traps discovered in this project

These are hard-earned. If you're a new AI joining this project, read all of them. They cost real time and teacher-facing credibility to discover. Don't rediscover.

---

## Lesson 1 · Type A vs Type B problem identification (from 蹦极题)

**Trap**: Chinese physics problems can look identical at the surface but require different answer types:
- **Type A** ("求约束/规律" · "满足什么条件" · "匹配规律"): answer is a **constraint / inequality** defining feasible region
- **Type B** ("最合适设计" · "最大 X · 最小 Y"): answer is a **boundary equality** — the specific optimum

**Boundary/极限 thinking is the CORRECT tool for Type B**. It's WRONG for Type A. When misapplied to Type A, you'll produce a specific-value answer where the correct answer is a range.

**The specific 蹦极 error**: (2a) asked "L, k, m 满足怎样的匹配规律?" — Type A, correct answer `kL ≤ 4mg`. I answered `kL = 4mg` (boundary equality, which is the answer to Type B). Because (2b) actually IS Type B and I was thinking ahead to (2b) while answering (2a).

**How to avoid**: before answering, explicitly ask yourself: "is this sub-question asking for constraint or optimum?" Constraint → inequality. Optimum → equality. Never bleed information between adjacent sub-questions.

---

## Lesson 2 · Reflection precision must match error precision (recursive · meta)

**Trap**: when an error is discovered, LLMs tend to reflect at "big principle" level ("LLM has X bias", "training convention leads to Y") rather than "specific micro-step" level ("I confused problem type at step 3"). Big-principle reflections FEEL deep but give no actionable anchor for future debugging.

**The specific meta-error**:
- v2 reflection: "LLM has closed-form-answer bias" — treated the technique as culprit; but boundary thinking itself is fine
- v3 reflection: "didn't do domain context switch" — vague label, no fix path
- v4 reflection: "mis-identified problem type as Type B" — specific, actionable, memorable

Ethan pushed 3 times before I arrived at v4. Each push was "more precise, less big-principle".

**How to avoid**: after any error reflection, ask "if this reflection is right, what would fix it? Is the fix at the same level of granularity as the error?" If reflection is at meta-level ("bias toward X") but error was at micro-level ("wrong choice at step 3"), reflection is too coarse. Zoom in.

---

## Lesson 3 · Apply domain reading conventions

**Trap**: LLMs default to general problem-solving mode, don't switch to domain-specific reading conventions when signaled to.

**The specific evidence**:
- 中国高考物理 has ~60 years of built-in phrasing conventions:
  - "**不超过 X**" = ≤ X (strict range, not point)
  - "**较大**" = sufficient / adequate — NOT "maximize"
  - "**匹配规律**" = constraint relationship (usually inequality)
  - "**首要保证 X · 在此前提下 Y**" = X hard constraint + Y soft preference (layered)
- I knew nothing (or rather, I "knew" these but didn't invoke them)
- Ethan gave me the domain signal ("the teacher is 命题 expert + 教研组长") but I didn't switch reading mode

**How to avoid**: when reading material authored by a known domain expert, explicitly ask "what reading conventions apply here?" before answering. This is a meta-check, cheap.

---

## Lesson 4 · Reflection over-generalizes toward "big principles"

(Interleaved with lesson 2; documenting as its own item because Ethan called it out separately.)

When LLM reflects on an error, there's a strong pull toward saying "LLMs have X bias" or "training does Y". These are often true statements but they lose the specificity of the error and provide no fix hook.

**Better reflections look like**: "I did A at step X because I skipped meta-check Y." Not "LLMs have bias A".

---

## Lesson 5 · Boundary/极限思维 is a valid tool, not a bias

**Not a lesson about a mistake, but a corrective**:

When reflecting on the 蹦极 error, I initially blamed "boundary thinking" as a bias. Ethan pointed out: boundary thinking is a **correct technique** for optimization problems. The error wasn't using boundary thinking; it was applying it to the wrong problem type.

**Applies more broadly**: when a technique produces a wrong answer, ask "was the technique wrong, or was the classification of the problem wrong?" Usually the latter.

---

## Lesson 6 · Enable shareone comments by default (execution lesson)

**Trap**: creating a shareone page for collaboration but forgetting `--allow-comments true`. Result: page is broadcast-only, no comment sidebar, feedback bottlenecked to wechat.

**Reminded by Ethan 2 times this session** (bungee page + rubric page). Both required post-hoc `update_share_settings.js --allow-comments true`.

**Fix**: for any `deliverables/*/` page targeted at the teacher or external experts, always pass `--allow-comments true` on `upload_page.js`. Also see `document-ai` memory `feedback_shareone_defaults.md`.

---

## Lesson 7 · Read API response schema before displaying (execution lesson)

**Trap**: guessing at API response field names ("author_name" is a natural guess) without dumping the actual schema first. Result: display code shows "author=?" and looks like a bug.

**Actual schema for shareone comment**:
- `user`: `{"username": "elfenliedsp"}` ← author name is here
- `author_role`: role
- `user_id`: uuid
- Does NOT have `author_name`

**Fix**: for any new API response, before writing display code, run `print(sorted(response.keys()))` and pick correct field names. Cost < 5 sec, saves debugging.

---

## Lesson 8 · Data-scale-appropriate methodology (from Ethan's cross-validation comment)

**Trap**: reporting in-sample R² (0.886 with 33 data points × 10 features) without acknowledging severe overfit risk.

**Rule**: 
- **k features vs n data points**: rule of thumb 10 obs / feature minimum for stable OLS
- Any R² > 0.5 on n/k < 5 is suspect — needs cross-validation to be honest
- **For this project specifically**: max data we'll ever have is ~150 points (5 papers × ~30 questions), which is still small. Use LOPO cross-validation (Leave-One-Paper-Out) as the honest metric — it simulates "predict a new paper's difficulty" which is the real use case.

**Related commitment**: `analysis/rubric_v2_lopo.py` (upcoming) will use LOPO CV. Also explore cohort effect: predict `score_rate - paper_mean` instead of raw to factor out per-paper baseline difficulty differences.

---

## Lesson 9 · Don't ask questions you can compute from data

**Trap**: framing "what's the answer to X?" as an ask to a human collaborator, when X is empirically computable from data you already have (or are about to have).

**The specific evidence (2026-08-02 morning kickoff)**:
- I asked the teacher Ask #3: "2024/2025/2026 三届一模 · 同一题难度 · 学生得分率波动多少?" — intended to inform cohort-effect modeling
- Ethan (immediately): "3 你是不是可以自己算呀, 你能自己算的就不要问了。顺便也告诉他一下免得他浪费时间"
- The empirical cohort variance IS what I wanted the teacher's intuition to estimate. Once I have 3 years of exam data (which I will, per Ask #1 permission granted), the variance is literally in the data.
- Asking the teacher wastes her time AND gives a less precise answer than data will.

**How to avoid**: before including a question in an ask-list to a human, ask yourself: "if I had the data, could I compute this directly?" If yes, don't ask — compute after data comes in.

**Related to Lesson 8**: sample-size limits are important, but so is data-adequacy: don't add human effort as substitute for computable analysis.

---

## Lesson 10 · counter-intuitive 结论发布前先留 label-quality-audit 空间

**Trap**: 数据出了一个 counter-intuitive 结论 (e.g. "特征 X 系数为 0 · 没信号"), 直接作为结论发布, 没先自问"这可能是 label bias 吗"。领域专家一戳就穿。

**The specific evidence (2026-08-02)**:
- v3 数据: `textbook_scene_degree` β = +0.0003 · 我发布结论"场景没独立信号 · 只有模式重要"
- 杨老师 11:24 wechat 直接反驳: "不太符合我的直觉。同样设问下, 场景熟 → 学生快速理解情境 → 剩时间做分析推理; 场景陌生 → 认知负担高。霍尔推进器方法学过, 但难以迁移到陌生情景"
- 我 12:00 加了 `transfer_cost = max(0, pattern - scene)` 交叉特征 · **场景系数直接从 +0.0003 → +0.026**
- 也就是 v3 的"场景没信号"是 label 偏差 (我给 concept / modeling / novelty 打分时已经把陌生场景的罚分吸掉了 · 场景 独立信号被抢走), 不是真实的物理

**Why it happened**:
- 全 162 道题的 label 都是我一个人打的
- 打 concept · reasoning · modeling · novelty 时, 我看到"陌生场景"会 mentally 加分 (概念多、建模自主 、情境新颖)
- 这些特征跟 scene 相关性高 · 造成 scene 独立信号被"吸走"的 collinearity artifact
- 直接的可观测数据: 场景=0 pattern=2 组 n=2, 均分 0.585 vs 场景=2 pattern=2 组 n=73, 均分 0.866 · 差 28pp · 明明信号强
- 但线性模型 "on the margin, after all other features" 就检测不到

**How to avoid**:
1. **发布 counter-intuitive 结论前, 先自问**: "这个特征的 raw group means 直接看有信号吗? 如果 raw 有 · 但系数为 0 · 是不是 collinearity?"
2. **对于每一个 headline 结论**, 明确一句 "以下前提: 假设我的 label 正确。若 label 有偏, 该结论可能反转。"
3. **主动准备 audit list**: 让领域专家抽查若干题的 label, 让他反证 label 偏差, 你才好知道结论是否 robust
4. **优先测简单 group means**, 再看模型系数。系数是有条件的; means 是无条件的。

**Related to**: Lesson 2 (反思精度) — 这次也是反思到最后才找到 label bias · 之前一直在讨论"是不是模型不对 / 是不是特征不够"。反思应该从 label 开始, 不是从模型开始。

---

## Lesson 11 · 给非技术领域专家的沟通必须严格纯中文 · 每次发消息前扫一遍

**Trap**: 用英文技术词写中文消息 · 感觉"效率高" (英文短), 但对非技术领域专家 (老师 · 医生 · 律师 · 教练 …) 造成阅读摩擦, 严重时对方直接说"看不懂"。

**具体证据 (2026-08-02 与杨老师协作)**:
- 11:07 杨老师首次提出: "请用中文叙述，以便让我更好理解你的意思"
- 11:11 我承诺 "以后微信也全中文"
- 之后 Ethan 又提醒 3 次 · 我依然习惯性夹英文: LOPO / MAE / clarify / label / MCQ / novelty / count vs severity / phase 1 / workload / concrete plan
- 18:15 杨老师直接说 "这句话我不明白什么意思？请用中文说明，我需要做什么？"
- 这条 wechat 里我夹了 3 个英文短语她全没看懂 · 卡住她 · 让她无法开始 label

**原因分析 (为什么我总漏)**:
- 训练里技术圈默认中英夹用 · 神经默认走这条 path
- 有些概念中文长 (Leave-One-Paper-Out cross-validation vs LOPO), 我"图省事" —— 但这是我省事, 对方多费脑
- 我 review outbound 时没显式扫描英文 token

**如何避免 (每次给她发前必须做的)**:
1. **发前 grep 一遍自己的消息**, 找拉丁字母组成的词 · 逐个替换成中文 (数学符号如 R²、β、MAE 可保留 · 但首次用后加中文注释)
2. **技术术语中文对照表** (给这个 project 用):
   - LOPO / cross-validation → 留一试卷交叉验证
   - in-sample / out-of-sample → 训练集内 / 训练集外
   - MAE → 平均误差 (首次) / 后续可用简写
   - R² → 决定系数 (首次)
   - β / coefficient → 系数
   - overfit → 过拟合
   - feature → 特征
   - label / labeling → 打分 / 标注
   - novelty (rubric feature name) → 情境新颖度
   - MCQ → 选择题
   - clarify (verb) → 澄清 / 讲清楚
   - subsample / subset → 抽样 / 小样本
   - phase 1 / phase 2 → 第一阶段 / 第二阶段
   - workload → 工作量
   - pilot → 试跑 / 试验
   - baseline → 基线
   - threshold → 阈值
   - concrete plan → 具体方案
   - solo → 独立 / 一个人
   - blocker → 卡点
   - counter-intuitive → 反直觉
3. **不确定某词是否她认识时**, 首次用后括号加中文注释 · 比如 "MAE (平均绝对误差)"
4. **她一说"看不懂"就立刻承认 + 重写**, 不 defend

**Related to**: 已有的沟通原则 (Ethan 之前给的规则: 停下来必须说原因; comment-back 必须 wechat 通知)

---

## Recap in one line each

1. Type A (constraint) vs Type B (optimum) — never bleed
2. Reflection precision = error precision
3. Apply domain reading conventions when domain-signaled
4. Don't over-generalize reflections into "LLM has bias X"
5. Techniques aren't wrong; problem-type classification is what's wrong
6. Enable shareone comments by default
7. Dump API schema before assuming field names
8. Small data + many features = must cross-validate
9. Don't ask questions you can compute from data
10. Counter-intuitive 结论发布前先做 label-quality-audit · raw group means 先看
11. 给非技术领域专家的沟通必须严格纯中文 · 发送前 grep 一次自己消息里的英文 token · 每次

**When you (new AI) find a new lesson, append to this file and commit.**
