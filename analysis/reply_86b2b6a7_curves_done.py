"""Reply to comment 86b2b6a7 saying difficulty curves are done in §7."""
import json
import os
import subprocess
from pathlib import Path

SHARE_ID = "BzXjsrbu6uQ887Kg"
PARENT_ID = "86b2b6a7-83e3-46a7-9b55-d44d157b1dcd"

CRED_PATH = Path("C:/Users/songym/.shareone_credentials")
API_KEY = json.loads(CRED_PATH.read_text())["api_key"]
SCRIPT = "C:/Users/songym/cursor-projects/document-ai/vendor/shareone-skill/vendor/shareone-skill/scripts/shareone_api_request.js"

REPLY = """已经兑现了 · 页面新加的 第七部分 "用途示例 · 每份试卷的难度曲线" 就是您要的可视化。

5 张图 (每份试卷一张), 每张里 蓝线是 v4 预测得分率, 红点是学生实际得分率, 按题号 (卷面顺序) 排列。您可以直接看每份试卷是否呈"选择题递增 + 实验题递增 + 大题递增"三段结构。

每份试卷分段均分表 (§7.1) 也放在下面, 一眼看清 预测 vs 实际 的段级误差。

如果这个可视化符合您预期, 您可以标 close 这条评论。如果还需要调整 (比如换颜色 / 加参考线 / 分段背景色), 告诉我一句。"""


def main():
    body = {
        "parent_id": PARENT_ID,
        "quote": "卷面越靠后得分率反而越高",
        "highlighter_data": ('{"startMeta":{"parentTagName":"LI","parentIndex":0,"textOffset":17},'
                             '"endMeta":{"parentTagName":"LI","parentIndex":0,"textOffset":29},'
                             '"text":"卷面越靠后得分率反而越高"}'),
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
    print("stdout:", proc.stdout[:400])
    if proc.returncode != 0:
        print("stderr:", proc.stderr)
        raise SystemExit(1)
    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
