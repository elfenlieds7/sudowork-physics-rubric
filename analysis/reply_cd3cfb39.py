"""Reply to Ethan's shareone comment cd3cfb39 about position/difficulty coupling."""
import json, os, subprocess
from pathlib import Path

SHARE_ID = "BzXjsrbu6uQ887Kg"
PARENT_ID = "cd3cfb39"

CRED = Path("C:/Users/songym/.shareone_credentials")
API_KEY = json.loads(CRED.read_text())["api_key"]
SCRIPT = "C:/Users/songym/cursor-projects/document-ai/vendor/shareone-skill/vendor/shareone-skill/scripts/shareone_api_request.js"

REPLY = """跑数据验证了 · 完全对:

- position ~ 内容特征回归 R² = 0.912 · 位置 91% 方差被内容特征解释, 几乎冗余
- 最强共线: is_open r=+0.853 (大题全在后段), novelty +0.522, modeling +0.458

3 个处理方案 LOPO 对比:
- 去掉 position: R² 0.8589 · MAE 0.0725  ← 最好
- Residualize (回归内容后取残差): R² 0.8570 · MAE 0.0730 (跟原样一致 · OLS 数学上 partial effect 不变)
- v4 原样保留: R² 0.8570 · MAE 0.0730

**采纳 · v4 revised = 13 特征 (去掉 position)**. 提升幅度 +0.002 R² / -0.0005 MAE, 数字小但方向对.

也印证了您的判断: 一旦其他内容特征做齐, 位置本身没有独立信号, 只是命题者按难度递增排题的自然结果.

网页 §9.5 已经加了这个分析. 这条您方便时 close 都行."""


def main():
    # First fetch the full parent id
    proc = subprocess.run(["node", SCRIPT, f"/api/v1/shares/{SHARE_ID}/comments?status=all", "--public"],
                          capture_output=True, text=True,
                          env={**os.environ, "SHAREONE_API_KEY": API_KEY}, encoding="utf-8")
    all_comments = json.loads(proc.stdout)
    parent = None
    for c in all_comments:
        if c["id"].startswith(PARENT_ID):
            parent = c
            break
    if not parent:
        print(f"Could not find parent {PARENT_ID}")
        return

    body = {
        "parent_id": parent["id"],
        "quote": parent["quote"],
        "highlighter_data": parent["highlighter_data"],
        "content": REPLY,
        "author_role": "agent",
    }
    payload = json.dumps(body, ensure_ascii=False)
    tmp = Path("C:/Users/songym/cursor-projects/sudowork-physics-rubric/scratch_reply_body.json")
    tmp.write_text(payload, encoding="utf-8")

    proc = subprocess.run(["node", SCRIPT, f"/api/v1/shares/{SHARE_ID}/comments",
                           "--method", "POST", "--data-file", str(tmp)],
                          capture_output=True, text=True,
                          env={**os.environ, "SHAREONE_API_KEY": API_KEY}, encoding="utf-8")
    print(proc.stdout[:400])
    if proc.returncode != 0:
        print("STDERR:", proc.stderr)
    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
