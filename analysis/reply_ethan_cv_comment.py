"""One-shot: reply to Ethan's CV comment on the rubric shareone page with v2 results.

Parent comment id: 4ec28439-bb0c-4e19-bbb1-68e70473ea5e (author: elfenliedsp/owner)
Share id: BzXjsrbu6uQ887Kg
"""
import json
import os
import subprocess
from pathlib import Path

SHARE_ID = "BzXjsrbu6uQ887Kg"
PARENT_ID = "4ec28439-bb0c-4e19-bbb1-68e70473ea5e"

CRED_PATH = Path("C:/Users/songym/.shareone_credentials")
API_KEY = json.loads(CRED_PATH.read_text())["api_key"]
SCRIPT = "C:/Users/songym/cursor-projects/document-ai/vendor/shareone-skill/vendor/shareone-skill/scripts/shareone_api_request.js"

REPLY = """v2 交付 · resolve 你这条:

**LOPO CV 已跑 · 5 papers · 162 items · 11 features**
- **LOPO out-of-sample R² = 0.841** · MAE = 0.076
- vs in-sample R² = 0.884 · **只掉 0.04** · rubric 结构本身稳
- 每份 held-out paper 的 R² 都在 0.73-0.88 之间 · 无 catastrophic fail

**Cohort 处理 · 你猜对了 (b) 是对的方向, 但数据表明这里 factor out 不出啥**
- 5 份卷子均分范围 [0.683, 0.745] · across-paper SD 只有 **0.027**
- M2 (raw score_rate) vs M3 (score_rate - paper_mean, 你说的 option b) · **R² 和 MAE 完全一致**
- 说明这 5 份试卷已经很同质, cohort 效应本来就小 · adjust 或不 adjust 在数据里没区别

也就是 Ask #3 (三年同题波动多少) 我不用问杨老师了 · Lesson 9 已经加到 meta_lessons.md 里 · 谢谢提醒。

**Bonus finding · A+B split validated · pattern 是信号, scene 是噪声**
杨老师 8:17 wechat 回 "2. A+B", 我把 v1 的 textbook_model_degree 拆成了两维:
- textbook_scene_degree β = **+0.0003** (系数接近 0 · 场景是否典型对得分率无独立影响)
- textbook_pattern_degree β = **+0.071** (强信号 · pattern 每高一档得分率提高 7pp)

说明学生做不出的不是"场景没见过", 而是"解题模式没练过"。天宫霍尔推进器 (scene=0 pattern=2 · 0.76) > 声波类比光线 (scene=0 pattern=0 · 0.50) 就是这个 pattern。

**详细内容全在 v2.html 里 (this page 现在已经指向 v2)** · repo commit 稍后跟上。

Resolve 建议: 你标 resolve 这条 · 后续 A+B pattern finding 如果杨老师 push back, 我另开新 thread。"""


def main():
    body = {
        "parent_id": PARENT_ID,
        "quote": "cross-validation",
        "highlighter_data": ('{"startMeta":{"parentTagName":"DIV","parentIndex":14,"textOffset":177},'
                             '"endMeta":{"parentTagName":"DIV","parentIndex":14,"textOffset":193},'
                             '"text":"cross-validation"}'),
        "content": REPLY,
        "author_role": "agent",
    }
    payload = json.dumps(body, ensure_ascii=False)
    tmp = Path("C:/Users/songym/cursor-projects/sudowork-physics-rubric/scratch_reply_body.json")
    tmp.write_text(payload, encoding="utf-8")

    env = os.environ.copy()
    env["SHAREONE_API_KEY"] = API_KEY
    proc = subprocess.run(
        ["node", SCRIPT, f"/api/v1/shares/{SHARE_ID}/comments",
         "--method", "POST", "--data-file", str(tmp)],
        capture_output=True, text=True, env=env, encoding="utf-8",
    )
    print("stdout:", proc.stdout)
    if proc.returncode != 0:
        print("stderr:", proc.stderr)
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
