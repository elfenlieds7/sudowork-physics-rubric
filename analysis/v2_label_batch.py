"""Apply v2.1 batch scores to specific (paper, qid) items. Idempotent."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

CSV = Path(__file__).resolve().parent.parent / "data" / "labeled" / "v2_1_labels.csv"

BATCH = {
    # === gaokao_2025 (31 items) ===
    ("gaokao_2025", "1"):     dict(context_familiarity=1, info_complexity=1, topic="thermal", concept_count=2, knowledge_depth="analyze",   openness="closed", modeling=1, reasoning=3, computation=0, question_type="mcq",  notes="古代点火器·压缩空气+热+力"),
    ("gaokao_2025", "2"):     dict(context_familiarity=0, info_complexity=0, topic="thermal", concept_count=1, knowledge_depth="recall",    openness="closed", modeling=0, reasoning=1, computation=0, question_type="mcq",  notes="光的衍射现象识别"),
    ("gaokao_2025", "3"):     dict(context_familiarity=0, info_complexity=2, topic="em",      concept_count=1, knowledge_depth="analyze",   openness="closed", modeling=1, reasoning=3, computation=0, question_type="mcq",  notes="金属圆环感应电流·不能产生的判断"),
    ("gaokao_2025", "4"):     dict(context_familiarity=0, info_complexity=1, topic="em",      concept_count=2, knowledge_depth="apply",     openness="closed", modeling=0, reasoning=3, computation=1, question_type="mcq",  notes="交流发电机线圈·e-t关系判断"),
    ("gaokao_2025", "5"):     dict(context_familiarity=0, info_complexity=2, topic="mech",    concept_count=2, knowledge_depth="analyze",   openness="closed", modeling=0, reasoning=3, computation=0, question_type="mcq",  notes="简谐运动S振动·波形+P点判断"),
    ("gaokao_2025", "6"):     dict(context_familiarity=1, info_complexity=1, topic="mech",    concept_count=2, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=4, computation=1, question_type="mcq",  notes="长方体AB叠放斜面·B受力个数分析"),
    ("gaokao_2025", "7"):     dict(context_familiarity=1, info_complexity=1, topic="mech",    concept_count=2, knowledge_depth="analyze",   openness="closed", modeling=1, reasoning=3, computation=0, question_type="mcq",  notes="嫦娥六号·椭圆轨道+圆轨道·万有引力"),
    ("gaokao_2025", "8"):     dict(context_familiarity=1, info_complexity=2, topic="cross",   concept_count=2, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=3, computation=0, question_type="mcq",  notes="小山坡等高线·力学+电场类比(跨模块)"),
    ("gaokao_2025", "9"):     dict(context_familiarity=1, info_complexity=1, topic="em",      concept_count=3, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=4, computation=1, question_type="mcq",  notes="自感线圈+电容器+3灯泡·稳态分析"),
    ("gaokao_2025", "10"):    dict(context_familiarity=1, info_complexity=1, topic="em",      concept_count=3, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=4, computation=0, question_type="mcq",  notes="磁铁+弹簧+闭合线圈电磁感应+能量"),
    ("gaokao_2025", "11"):    dict(context_familiarity=2, info_complexity=2, topic="mech",    concept_count=3, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=4, computation=0, question_type="mcq",  notes="电磁弹射实验舱·f-t图·失重+多阶段"),
    ("gaokao_2025", "12"):    dict(context_familiarity=2, info_complexity=1, topic="cross",   concept_count=3, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=4, computation=1, question_type="mcq",  notes="电磁流量计·U0与Q关系(跨模块)"),
    ("gaokao_2025", "13"):    dict(context_familiarity=2, info_complexity=0, topic="thermal", concept_count=3, knowledge_depth="analyze",   openness="closed", modeling=1, reasoning=4, computation=0, question_type="mcq",  notes="反物质·反氢+湮灭+聚变"),
    ("gaokao_2025", "14"):    dict(context_familiarity=2, info_complexity=1, topic="thermal", concept_count=2, knowledge_depth="analyze",   openness="closed", modeling=2, reasoning=3, computation=0, question_type="mcq",  notes="声波·姑苏城声线传播情境"),
    ("gaokao_2025", "15-1"):  dict(context_familiarity=0, info_complexity=1, topic="cross",   concept_count=1, knowledge_depth="comprehend",openness="closed",modeling=0, reasoning=1, computation=0, question_type="fill", notes="实验操作·三选一多概念判断"),
    ("gaokao_2025", "15-2a"): dict(context_familiarity=0, info_complexity=1, topic="thermal", concept_count=1, knowledge_depth="comprehend",openness="closed",modeling=0, reasoning=1, computation=0, question_type="fill", notes="双缝干涉·双缝A或B判断"),
    ("gaokao_2025", "15-2b"): dict(context_familiarity=0, info_complexity=2, topic="thermal", concept_count=1, knowledge_depth="apply",     openness="semi", modeling=0, reasoning=1, computation=1, question_type="fill", notes="双缝干涉·手轮读数"),
    ("gaokao_2025", "15-3"):  dict(context_familiarity=1, info_complexity=1, topic="em",      concept_count=2, knowledge_depth="analyze",   openness="semi", modeling=1, reasoning=3, computation=0, question_type="fill", notes="电流表故障·多用电表检测·断路位置"),
    ("gaokao_2025", "16-1"):  dict(context_familiarity=0, info_complexity=1, topic="mech",    concept_count=1, knowledge_depth="comprehend",openness="closed",modeling=0, reasoning=1, computation=0, question_type="fill", notes="打点计时器·操作步骤排序"),
    ("gaokao_2025", "16-2"):  dict(context_familiarity=0, info_complexity=1, topic="mech",    concept_count=1, knowledge_depth="comprehend",openness="closed",modeling=0, reasoning=2, computation=0, question_type="fill", notes="纸带左端还是右端与小车相连"),
    ("gaokao_2025", "16-3"):  dict(context_familiarity=0, info_complexity=2, topic="mech",    concept_count=2, knowledge_depth="apply",     openness="semi", modeling=1, reasoning=2, computation=2, question_type="fill", notes="打B点速度v·中值速度"),
    ("gaokao_2025", "16-4"):  dict(context_familiarity=1, info_complexity=2, topic="mech",    concept_count=2, knowledge_depth="apply",     openness="semi", modeling=1, reasoning=3, computation=2, question_type="fill", notes="圆盘计时·加速度+向心加速度"),
    ("gaokao_2025", "17-1"):  dict(context_familiarity=0, info_complexity=0, topic="mech",    concept_count=1, knowledge_depth="apply",     openness="semi", modeling=0, reasoning=2, computation=1, question_type="solve",notes="物体上抛炸裂·初速v0"),
    ("gaokao_2025", "17-2"):  dict(context_familiarity=0, info_complexity=0, topic="mech",    concept_count=2, knowledge_depth="apply",     openness="semi", modeling=1, reasoning=2, computation=2, question_type="solve",notes="炸裂后B速度vB·动量守恒"),
    ("gaokao_2025", "17-3"):  dict(context_familiarity=0, info_complexity=0, topic="mech",    concept_count=2, knowledge_depth="apply",     openness="semi", modeling=1, reasoning=3, computation=2, question_type="solve",notes="A B落地距离d·平抛+竖直"),
    ("gaokao_2025", "19-1"):  dict(context_familiarity=0, info_complexity=1, topic="mech",    concept_count=1, knowledge_depth="apply",     openness="semi", modeling=1, reasoning=2, computation=2, question_type="solve",notes="飞机加速跑道·牵引功W(动能定理)"),
    ("gaokao_2025", "19-2"):  dict(context_familiarity=1, info_complexity=1, topic="mech",    concept_count=2, knowledge_depth="analyze",   openness="semi", modeling=2, reasoning=3, computation=2, question_type="solve",notes="飞机决策距离d·L,a1,a2约束"),
    ("gaokao_2025", "19-3"):  dict(context_familiarity=2, info_complexity=1, topic="mech",    concept_count=3, knowledge_depth="analyze",   openness="open", modeling=3, reasoning=5, computation=3, question_type="solve",notes="气流对机翼力F∝u^α·自主建模+α"),
    ("gaokao_2025", "20-1"):  dict(context_familiarity=1, info_complexity=1, topic="em",      concept_count=1, knowledge_depth="apply",     openness="semi", modeling=1, reasoning=2, computation=1, question_type="solve",notes="圆筒+金属线·电荷Q到达A功W"),
    ("gaokao_2025", "20-2"):  dict(context_familiarity=2, info_complexity=1, topic="em",      concept_count=3, knowledge_depth="analyze",   openness="semi", modeling=3, reasoning=5, computation=3, question_type="solve",notes="圆筒粒子E1E2E3能量差比较(非匀强+对数积分)"),
    ("gaokao_2025", "20-3"):  dict(context_familiarity=2, info_complexity=1, topic="cross",   concept_count=4, knowledge_depth="analyze",   openness="open", modeling=3, reasoning=5, computation=3, question_type="solve",notes="静电除尘·基态氢电离所需E(玻尔原子+电场)"),
}


def main():
    rows = []
    with open(CSV, encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            rows.append(r)

    idx = {h: i for i, h in enumerate(header)}
    updated = 0
    for r in rows:
        key = (r[idx['paper_id']], r[idx['question_id']])
        if key in BATCH:
            d = BATCH[key]
            for k, v in d.items():
                if k in idx:
                    r[idx[k]] = str(v)
            updated += 1

    with open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

    print(f'updated {updated} items in this batch')

if __name__ == "__main__":
    main()
