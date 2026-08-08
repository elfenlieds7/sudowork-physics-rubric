"""v2.1 labeling workspace — build empty CSV with 223 rows × 10 dims.

Dimensions (v2.1):
1. 情境特征 (0=熟悉/1=半陌生/2=完全陌生)
2. 信息呈现 (0=无图/1=简单示意/2=复杂图信息)
3. 模块属性 (力学/电磁学/热学光学原子物理/跨模块综合)
4. 知识点数 (1-5)
5. 知识深度 (记忆识别/基础理解/常规应用/综合分析)
6. 设问开放度 (封闭/半开放/完全开放)
7. 建模复杂度 (0=无需/1=简单/2=中等/3=复杂)
8. 推理链长度 (1-5)
9. 运算难度 (0=无/1=简单/2=中等/3=复杂)
10. 题型因素 (选择题/填空题/解答题)
"""
import csv
from pathlib import Path

V1_CSV = Path(__file__).resolve().parent.parent / "data" / "labeled" / "combined_scored_v3.csv"
V2_CSV = Path(__file__).resolve().parent.parent / "data" / "labeled" / "v2_1_labels.csv"

DIMS = [
    'context_familiarity',    # 情境特征 · 0/1/2
    'info_complexity',        # 信息呈现 · 0/1/2
    'topic',                  # 模块属性 · mech/em/thermal/cross
    'concept_count',          # 知识点数 · 1-5
    'knowledge_depth',        # 知识深度 · recall/comprehend/apply/analyze
    'openness',               # 设问开放度 · closed/semi/open
    'modeling',               # 建模复杂度 · 0-3
    'reasoning',              # 推理链长度 · 1-5
    'computation',            # 运算难度 · 0-3
    'question_type',          # 题型因素 · mcq/fill/solve
]

def main():
    v1_rows = []
    with open(V1_CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            v1_rows.append(r)

    with open(V2_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['paper_id', 'question_id', 'score_rate'] + DIMS + ['notes'])
        for r in v1_rows:
            w.writerow([r['paper_id'], r['question_id'], r['score_rate']] + [''] * len(DIMS) + [''])

    print(f'wrote {V2_CSV} · {len(v1_rows)} rows · empty v2.1 dims')

if __name__ == "__main__":
    main()
