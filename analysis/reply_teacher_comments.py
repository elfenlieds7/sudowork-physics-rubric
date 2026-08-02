"""Reply to 杨老师's 4 shareone comments on the rubric v1 page.

Each reply is a comment-back (not resolve — she decides when to close).
Uses parent_id + inherited quote + highlighter_data + author_role='agent'.
"""
import json
import os
import subprocess
from pathlib import Path

SHARE_ID = "BzXjsrbu6uQ887Kg"
CRED_PATH = Path("C:/Users/songym/.shareone_credentials")
API_KEY = json.loads(CRED_PATH.read_text())["api_key"]
SCRIPT = "C:/Users/songym/cursor-projects/document-ai/vendor/shareone-skill/vendor/shareone-skill/scripts/shareone_api_request.js"

# Reply plan · one comment-back per parent · execute-and-comment where done, comment-and-ask where open

REPLIES = [
    # 1 · 卷面靠后得分率反而越高 → "三段递增才是理想难度结构" — 这是 use-case 信号
    {
        "parent_id": "86b2b6a7-83e3-46a7-9b55-d44d157b1dcd",
        "quote": "卷面越靠后得分率反而越高",
        "highlighter_data": ('{"startMeta":{"parentTagName":"LI","parentIndex":0,"textOffset":17},'
                             '"endMeta":{"parentTagName":"LI","parentIndex":0,"textOffset":29},'
                             '"text":"卷面越靠后得分率反而越高"}'),
        "content": (
            "杨老师这条其实是最关键的 use-case 信号 · 我 v2 时没吃透:\n\n"
            "您描述的 [1-14 递增][15-16 递增][17-20 递增, 且每题三小问递增] 三段递增是您理想中命题目标的难度结构。"
            "那 rubric 的核心用途就应该是:\n\n"
            "  **给一份未出版的卷子 · 逐题预测得分率 · 画出\"预测难度 vs 卷面 index\"曲线 · "
            "让您 pre-check 是否符合三段递增, 有 outlier 早发现早调整。**\n\n"
            "v2 页面还没做这个可视化 · v3 会加。同时排查一个 side puzzle: OLS 里 position β=+0.124 (卷面越靠后预测得分率越高), "
            "跟您说的\"三段递增\"方向相反, 我怀疑是因为大题小问的前半段 (17-1, 17-2 setup) 位置高但很简单, "
            "把 position 的信号稀释了。会先算 raw 相关看清楚。\n\n"
            "这条建议先别 close · 等我加完难度曲线可视化, 附截图您再决定。"
        ),
    },
    # 2 · 陷阱数 + 教材经典模型度 → 非常有必要 · 教材经典已在 v2 做了, 陷阱数待您 label
    {
        "parent_id": "b7938905-a74c-43f7-a1ff-d4bd6fbb3ec4",
        "quote": "我要不要加\"易混陷阱数\"和\"教材经典模型度\"两个特征?",
        "highlighter_data": ('{"startMeta":{"parentTagName":"SPAN","parentIndex":5,"textOffset":3},'
                             '"endMeta":{"parentTagName":"SPAN","parentIndex":5,"textOffset":31},'
                             '"text":"我要不要加\\"易混陷阱数\\"和\\"教材经典模型度\\"两个特征?"}'),
        "content": (
            "两条我都记下了 · 完成一半:\n\n"
            "**教材经典模型度** — 已经在 v2 里做了, 且按您 wechat \"A+B\" 的答复拆成了两维: "
            "`textbook_scene_degree` (物理场景/装置) + `textbook_pattern_degree` (解题模式)。"
            "数据出来 pattern β=+0.071 有信号, scene β≈0 无信号 —— 详见 v2.html 里\"关键发现\"那段。"
            "我另在 wechat 里请您 judge 这个结论。\n\n"
            "**易混陷阱数** — 还没做, 因为这个特征我一个人 label 不了 (需要您对每题的常见 misconception distractor 有判断)。"
            "我在想: 是不是可以从 subsample (20 题, ~15 分钟) 开始, 您给每题打一个 0-3 的\"陷阱数\", "
            "我 fit 一遍看是否显著加信号 · 显著再考虑 scale 到全 162 题。\n\n"
            "这条建议先别 close · 陷阱数 subsample 落地后再关。"
        ),
    },
    # 3 · 4 份 PDF 处理 → keyi · 已执行 · comment-back 后可以 close
    {
        "parent_id": "2e7c8254-8e3b-4637-ae53-5da3361e0daf",
        "quote": "其它 4 份 PDF 我可以按同样方法处理吗?",
        "highlighter_data": ('{"startMeta":{"parentTagName":"SPAN","parentIndex":4,"textOffset":4},'
                             '"endMeta":{"parentTagName":"SPAN","parentIndex":4,"textOffset":27},'
                             '"text":"其它 4 份 PDF 我可以按同样方法处理吗?"}'),
        "content": (
            "感谢 · 已经全部处理: 高考 2024/2025 + 西城 2024/2025 · 4 份都进 v2 数据集 · "
            "加上西城 2026 一共 5 papers · 162 items。\n\n"
            "LOPO cross-validation 就是靠这 5 份跑的 · out-of-sample R² = 0.841。\n\n"
            "这条您可以 close 了。"
        ),
    },
    # 4 · modeling → 可以参考教材 · ambiguous, 需澄清
    {
        "parent_id": "4814fdf1-3b80-467c-9d59-d7008d799f30",
        "quote": "modeling",
        "highlighter_data": ('{"startMeta":{"parentTagName":"B","parentIndex":13,"textOffset":22},'
                             '"endMeta":{"parentTagName":"B","parentIndex":13,"textOffset":30},'
                             '"text":"modeling"}'),
        "content": (
            "想请您澄清一下 · 您这里的\"参考教材\"指的是:\n\n"
            "(a) 我 rubric 里的 `modeling` 特征 (0-3 · 表示题目要求学生\"自主建模\"的程度 · 0=完全给出模型, 3=完全自己建), "
            "您觉得它的打分应该以教材例题为参照系 · 教材有的模型算简单 · 教材没有的算难? 还是\n\n"
            "(b) 您指的是我们后来在 wechat 里聊的\"典型模型度\", 那个已经在 v2 里做成了 textbook_scene_degree "
            "+ textbook_pattern_degree, 就是以教材为参照。\n\n"
            "如果是 (a), 我可能需要重新校准 `modeling` 的打分, 因为目前它跟 pattern_degree 可能有共线性; "
            "如果是 (b), 那这条就已经完成了, 您可以 close。\n\n"
            "先不 close · 等您 确认 (a) 或 (b)。"
        ),
    },
]


def post_reply(reply):
    body = {
        "parent_id": reply["parent_id"],
        "quote": reply["quote"],
        "highlighter_data": reply["highlighter_data"],
        "content": reply["content"],
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
    if proc.returncode != 0:
        print(f"FAIL for parent {reply['parent_id'][:8]}:")
        print("stderr:", proc.stderr)
        return None
    return json.loads(proc.stdout)


def main():
    for reply in REPLIES:
        r = post_reply(reply)
        if r:
            print(f"parent {reply['parent_id'][:8]} → new reply id {r['id'][:8]}")
        else:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
