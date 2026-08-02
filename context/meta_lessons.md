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

**When you (new AI) find a new lesson, append to this file and commit.**
