"""v2.4 relabel · 信息呈现 3档→4档 (杨老师 08-12 20:53) + 模块属性 4档→2档 (21:08).

规则 apply 到 223 items.

信息呈现 rule (杨老师 21:01: 信息量大即档4·任一条件即可):
- 档 4: 信息量大 (长文字情境题·复杂装置·多阶段综合大题·任一)
- 档 3: 需将图像/表格信息转换 (v-t·U-I·p-V·波形·电路·作图·曲线)
- 档 2: 有示意图辅助·直接读文字 (常规题+简单示意)
- 档 1: 信息量少·条件明示·无复杂图表 (纯识别类)

模块属性 rule (杨老师 21:08):
- mech/em/thermal → 'in' (模块内)
- cross → 'cross' (跨模块)
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/labeled/v2_3_labels.csv"
OUT_CSV = ROOT / "data/labeled/v2_4_labels.csv"
OUT_JSON = ROOT / "data/labeled/v2_4_info_reasoning.json"


# 档 4 keywords (any → 4)
K4 = [
    # 长文字情境
    '情境题', '长文本', '阿秒', '反物质', '类比', '声波传播', '声呐',
    '光子动量', '广义相对论', '暗物质',
    # 复杂装置
    '加速度计', '电子秤', '电磁弹射微重力', '电磁弹射实验舱', '电磁流量计',
    '离子密度', '电子束冲击', '静电除尘', '储存环', '模式2,3',
    '气流对机翼', '光电效应·电流电压综合',
    '流浪地球', '天宫圆周', '天宫霍尔推进器', '嫦娥六号', '夸父一号',
    '哈勃系数', '宇宙膨胀', '雪如意', 'EAST', '航母阻拦',
    # 综合多阶段
    '多阶段', '综合', '跨模块+函数', '自主建模+α',
    '暗物质', '螺旋星系',
    # 试卷末尾大题 sub (Q19-2/3, Q20-2/3 天然是复杂多信息)
]

# 档 3 keywords (图像转换 · 若未 hit K4)
K3 = [
    # 图像
    '图像', 'v-t图', 'x-t图', 'F-v²', 'U-I', 'U-U/R', 'p-V', 'T²-L', 'f-t',
    'e-t', 'u-t', 'v-r图', 'v-t 图', 'nx-x', '振动图', '波形', 'B(t)',
    # 图/表
    '电路图', '磁感线', '等势面', '等势线', 'i-r 角', '折线', '斜率',
    '作图', '作图+', '曲线', 'q-h',
    # 特殊
    '波形分析', '波动图像', '示意图', '波形+P点', '简谐横波波形', 'v-t',
    '拓扑', '压瘪',  # 等势面复杂多点
    '多点电荷',
]

# 档 1 keywords (纯识别 · 若未 hit K4/K3)
K1 = [
    '识别', '判断', '选择错误', '选错误',
    '偏振', '衍射识别', '干涉识别', '干涉现象识别', '衍射现象识别',
    '核反应方程·识别',
]


def classify_info(notes: str, v23_info: str) -> tuple[int, str]:
    """Return (v24_info, reasoning)."""
    # Priority: K4 > K3 > K1 > default 2
    for k in K4:
        if k in notes:
            return 4, f"档4·信息量大 (匹配'{k}')"
    for k in K3:
        if k in notes:
            return 3, f"档3·需图像/表格转换 (匹配'{k}')"
    for k in K1:
        if k in notes:
            return 1, f"档1·纯识别·条件明示 (匹配'{k}')"
    # Default: use v2.3 old to guide
    # v2.3 old: 0=无图, 1=简单示意, 2=复杂图
    # v2.4 default: 档2 (示意图辅助)
    return 2, f"档2·示意图辅助·直接读文字 (v2.3 old={v23_info}·default)"


def convert_topic(t: str) -> str:
    return 'cross' if t == 'cross' else 'in'


def main():
    with open(SRC, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    reasoning = {}
    for r in rows:
        # 信息呈现
        new_info, why = classify_info(r.get('notes', ''), r['info_complexity'])
        r['info_complexity'] = str(new_info)
        # 模块属性
        r['topic'] = convert_topic(r['topic'])
        reasoning[f"{r['paper_id']}::{r['question_id']}"] = {
            'info_complexity_v24': new_info,
            'topic_v24': r['topic'],
            'reasoning': why,
            'notes': r.get('notes', ''),
        }

    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(reasoning, f, ensure_ascii=False, indent=2)

    # Distribution
    from collections import Counter
    info_new = Counter(r['info_complexity'] for r in rows)
    topic_new = Counter(r['topic'] for r in rows)
    print(f"Total: {len(rows)}")
    print(f"Info complexity v2.4: {dict(sorted(info_new.items()))}")
    print(f"Topic v2.4: {dict(sorted(topic_new.items()))}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
