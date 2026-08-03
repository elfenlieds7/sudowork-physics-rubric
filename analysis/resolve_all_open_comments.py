"""Batch resolve 37 open comments on shareone rubric page.

Groups:
1. Ethan owner threads (2 · cross-validation + 末段位置) → resolve with milestone-lock reply
2. Teacher 8-01 / 8-02 threads (5) → contextual acks
3. Teacher 8-03 陷阱数 review threads (30) → uniform ack tied to appendix A / §5.5

All 陷阱数 review labels have been consumed into pre_label_traps.py TRAP_LABELS · v5.2 champion built with them · MAE 0.058 · integrated into v2.html milestone lock (2026-08-03 傍晚).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SHARE_ID = "BzXjsrbu6uQ887Kg"
RESOLVE_JS = r"C:\Users\songym\cursor-projects\document-ai\vendor\shareone-skill\vendor\shareone-skill\scripts\comment_resolve.js"
CREDS = r"C:\Users\songym\.shareone_credentials"

with open(CREDS, encoding='utf-8') as f:
    API_KEY = json.load(f)['api_key']

env = os.environ.copy()
env['SHAREONE_API_KEY'] = API_KEY

TRAP_REVIEW_REPLY = (
    "感谢老师 review · 您在此题的陷阱数评审已合入 v5.2 champion model · "
    "详见 §5.5 · 请刷新页面查看当前状态 (2026-08-03 傍晚 milestone lock)。"
)
TRAP_REVIEW_NOTE = "已合入 v5.2 · MAE 0.058"

CUSTOM = {
    # Ethan 8-01 · cross-validation ask
    "4ec28439-bb0c-4e19-bbb1-68e70473ea5e": {
        "reply": "已切换到 LOPO (Leave-One-Paper-Out) 交叉验证 · 每份卷子都做过 hold-out 测试 · 4 项过拟合验证 (per-paper 一致性 + train vs LOPO gap + 多种子稳定性 + 随机噪声 sanity) 全部通过 · 详见 §二 · 单题 MAE 0.058 · 整卷 1.38 pp.",
        "note": "LOPO CV + 4 项 overfit 检验已 ship",
    },
    # Teacher 8-01 14:54 · 越靠后得分率越低
    "86b2b6a7-d7a7-4cba-8bde-a0d000000000": {
        "reply": "老师给的理想难度结构 (1-14 递增 · 15-16 递增 · 17-20 递增 · 每大题子问递增) 已作为模型用途一 · 每份卷子的模型预测曲线 (§四) 都是按题号排序 · 可以直接对比是否符合理想结构.",
        "note": "已作为模型主要输出用途",
    },
    # Teacher 8-01 15:20 · 非常有必要 (熟悉度 + 模式度)
    "b7938905": {
        "reply": "已 v2 起拆分成 场景相似度 + 模式相似度 两维 · 中间发现 v2 数据看到 '场景无信号' · v4 加迁移成本交叉项后场景系数恢复 · 印证您对 '场景熟悉降低难度' 是真实的判断. 详见 §5.2.",
        "note": "拆维已 ship · 详见 §5.2",
    },
    # Teacher 8-01 15:21 · keyi (4 份 PDF 同样处理)
    "2e7c8254": {
        "reply": "感谢许可 · 高考 2022 · 2023 两份 PDF 已按同样评分表流程处理 · 加入数据集 · 现共 7 份卷子 · 223 道题 · 详见 §3.1.",
        "note": "已处理并合入 v5.1",
    },
    # Teacher 8-01 15:22 · modeling · 参考教材
    "4814fdf1": {
        "reply": "已按老师建议 · 模式相似度打分以 renjiao 教材为基线 · 教材例题习题直接对应 = 2 · 变形 = 1 · 需要跨章或自主建模 = 0. 详见 §3.2 特征说明.",
        "note": "打分标准已锚定教材",
    },
    # Ethan 8-02 11:15 · 末段位置预测
    "cd3cfb39": {
        "reply": "已加 是否卷面末段 (is_last_quarter) 特征 + 前段累积概念载荷 (earlier_load) 特征 · v4 起 ship · 位置特征保留 · 与内容难度共线但可能有正交时间压力贡献 · 详见 §5.4.",
        "note": "末段位置特征已 ship",
    },
    # Teacher 8-02 13:27 · "__" quote · "0" · unclear
    "9f9caf32": {
        "reply": "感谢老师 · 若这条是对某个具体题目的评分 · 相关标签在 8-3 早上您 shareone 完整 review 时已一并合入 v5.2 · 若有其他含义请微信告知.",
        "note": "内容不清 · 8-3 review 已覆盖",
    },
}


def resolve_one(comment_id, reply=None, note=None, dismiss=False):
    args = ["node", RESOLVE_JS, SHARE_ID, comment_id]
    if dismiss:
        args.append("--dismiss")
    if reply:
        args += ["--reply", reply]
    if note:
        args += ["--note", note]
    p = subprocess.run(args, capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def main():
    tmp = Path(r"C:\Users\songym\AppData\Local\Temp\all_open.json")
    if not tmp.exists():
        print(f"missing {tmp} · run fetch first")
        sys.exit(1)
    with open(tmp, encoding='utf-8') as f:
        comments = json.load(f)

    print(f"loaded {len(comments)} top-level open comments")

    n_ok = n_fail = 0
    for c in comments:
        cid = c['id']
        custom = None
        for k, v in CUSTOM.items():
            if cid.startswith(k) or k.startswith(cid[:8]):
                custom = v
                break
        if custom:
            # substantive thread · post agent reply + resolve
            rc, out, err = resolve_one(cid, reply=custom['reply'], note=custom['note'])
            mode = "RESOLVE"
        else:
            # 陷阱数 review · dismiss with note · no notification-spam reply
            rc, out, err = resolve_one(cid, dismiss=True, note=TRAP_REVIEW_NOTE)
            mode = "DISMISS"
        status = "OK" if rc == 0 else "FAIL"
        n_ok += (rc == 0)
        n_fail += (rc != 0)
        print(f"[{status}] {mode} {cid[:8]}  {out[:60]}  {err[:80]}")

    print()
    print(f"resolved/dismissed: {n_ok} · failed: {n_fail} · total: {n_ok+n_fail}")


if __name__ == "__main__":
    main()
