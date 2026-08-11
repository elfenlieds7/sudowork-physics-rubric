"""v2.3 concept_count relabel · 20 kappa items · using 64 KP + 5 rules.

For each item, I identify the KPs invoked (from 64-KP list), apply
dedup/merge/bridge rules, and count. Reasoning is stored per item for
杨老师 spot-check.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# My v2.3 concept_count labels per item (blind_idx 1-20)
# Each entry: (count, reasoning: list of KP + rule notes)
V23_LABELS = {
    1: (2, "闭合电路欧姆定律(含EMF+内阻) + 实验(测电源电动势和内阻，必做)"),
    2: (3, "机械波产生传播波动图像(声呐) + 光的折射全反射 + 描述运动的物理量(波速频率关系类比)"),
    3: (1, "动能定理(W=ΔEk本身即含'功' 概念，同KP)"),
    4: (2, "开普勒定律 + 机械能守恒(轨道能量)。温度部分是背景陈述，未触发'温度·内能'KP的实质计算"),
    5: (2, "分子动理论 + 温度·内能(轮胎气温→分子平均动能)"),
    6: (4, "弹力(弹簧) + 牛顿第二定律(a=F/m) + 闭合电路欧姆定律(电路灵敏度) + 电阻电阻定律。跨模块dedup后仍4个独立KP"),
    7: (1, "简谐运动(含单摆)。sub-question内单独考察单摆g表达式推导，实验KP由父问Q16主问已计"),
    8: (2, "动能定理(反推力做功W=ΔEk) + 摩擦力(空气阻力属阻力做功的概念)。牛顿定律做工具但未独立触发"),
    9: (2, "牛顿第二定律(F=ma) + 描述运动的物理量(v的分析)。按杨老师 14:56 最简路径规则,不混算动量定理+牛三路径。原v2.3打3已修正"),
    10: (2, "电荷·库仑定律及电场 + 描述电场的物理量(电场强度电势)。近似展开是数学方法，不额外增设KP"),
    11: (3, "仪器操作及读数(选择题干+3选项，实验必做器材) + 实验(仪器题背景) + 电压电流电阻电阻定律(实验目的)。选择题去重后3独立KP"),
    12: (3, "质能方程(相对论质能) + 磁场磁感线安培定则(B(t)) + 法拉第电磁感应定律(储存环推导)"),
    13: (3, "磁场磁感应强度(径向B2) + 描述运动的物理量(圆周运动) + 洛伦兹力(带电粒子圆周)"),
    14: (2, "安培力(F=BIL) + 电压电流电阻(第一级电路)"),
    15: (3, "动量守恒(30度推力+最近距离) + 机械能守恒(能量) + 牛顿第二定律(角动量分解)"),
    16: (4, "洛伦兹力 + 电场力做功与电势能 + 描述电场的物理量(斜率=e/m) + 电场·电场线·等势面(跨模块dedup后4独立)"),
    17: (4, "库仑定律·电荷 + 电压·电流·电阻·电阻定律 + 磁场·磁感线·安培定则·磁感应强度 + 电容器·电容(元件属性图4类元件·选错误)"),
    18: (4, "功·功率 + 动能·动能定理 + 重力势能·弹性势能 + 摩擦力(比较缓慢移动vs恒力的功能关系)"),
    19: (2, "描述电场的物理量(等势面类比等高线) + 力的合成与分解(方法类)。跨模块dedup后2独立"),
    20: (1, "原子核·核反应方程(质量数电荷数守恒同KP)"),
}


def main():
    # Load v2.2 calibration CSV as template
    src = ROOT / "data" / "labeled" / "v2_2_calibration_20_items.csv"
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    # Update concept_count with v2.3
    v23_rows = []
    for r in rows:
        idx = int(r["blind_idx"])
        new_count, _ = V23_LABELS[idx]
        r2 = dict(r)
        r2["concept_count"] = str(new_count)
        v23_rows.append(r2)

    out_csv = ROOT / "data" / "labeled" / "v2_3_calibration_20_items.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(v23_rows)

    # Save reasoning per item for teacher spot-check
    reasoning = {str(i): {"count": c, "reasoning": r} for i, (c, r) in V23_LABELS.items()}
    out_json = ROOT / "data" / "labeled" / "v2_3_calibration_reasoning.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(reasoning, f, ensure_ascii=False, indent=2)

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
