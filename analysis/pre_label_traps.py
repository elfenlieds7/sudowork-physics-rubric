"""我 (agent) pre-label 30 道 subset 陷阱数 · 用杨老师 18:13 定义:
陷阱数 = 触发学生常见失分点 (A-G) 的个数.

A 竖直方向丢重力
B 矢量忽略方向 (正负号)
C 温度热量混淆
D 忽视功的正负
E 忽视有效数字
F 算术错误 (比例/单位/代入)
G 其他 (概念混淆/公式适用/几何抽象)

Pre-labels 目的: 让杨老师 review + 微调, 比空白让她打分快.
测试目标: 加陷阱数进模型后单题 MAE 是否降到 6% 以下.
"""

# key: (paper, qid) · value: (trap_count, comment)
TRAP_LABELS = {
    ("gaokao_2024", "8"):    (3, "A重力+B阻力方向随速度+D阻力功正负"),
    ("gaokao_2024", "6"):    (2, "B感应电流方向+G瞬间vs稳态"),
    ("gaokao_2024", "10"):   (2, "B摩擦力方向+G物vs带谁快"),
    ("gaokao_2024", "2"):    (0, "简单公式套用"),
    ("gaokao_2025", "11"):   (3, "A重力+B方向+G超重失重"),
    ("gaokao_2025", "6"):    (2, "B各力方向+G受力个数易漏"),
    ("gaokao_2025", "8"):    (1, "G等高线电场类比"),
    ("gaokao_2025", "10"):   (3, "B感应方向+D功正负+G电磁感应"),
    ("xicheng_2024", "14"):  (0, "情境题·简单套用"),
    ("xicheng_2024", "8"):   (2, "D等势面功+G电势能变化"),
    ("xicheng_2024", "6"):   (2, "G向心力+G与自转比较"),
    ("xicheng_2024", "13"):  (2, "B洛伦兹力方向+G速度分解"),
    ("xicheng_2025", "14"):  (1, "B光对物体方向"),
    ("xicheng_2025", "1"):   (0, "核反应方程·纯识别"),
    ("xicheng_2025", "6"):   (1, "G识别哪些物理量与倾角无关"),
    ("xicheng_2025", "12"):  (3, "A重力+B力方向+D功正负"),
    ("xicheng_2026", "2"):   (1, "简单MCQ·猜1个陷阱"),
    ("xicheng_2026", "3"):   (1, "简单MCQ"),
    ("xicheng_2026", "5"):   (1, "简单MCQ"),
    ("xicheng_2026", "13"):  (2, "较难MCQ·2陷阱猜"),
    ("xicheng_2026", "15-2"): (2, "G电学计算+F代数"),
    ("gaokao_2024", "19-2a"): (2, "A引力势能符号+F代数"),
    ("xicheng_2026", "16-2"): (2, "G实验计算+F代数"),
    ("xicheng_2025", "20-2"): (3, "B方向+G几何抽象+F代数"),
    ("xicheng_2024", "20-2a"): (3, "D功正负+G非弹性碰撞+F代数"),
    ("xicheng_2025", "19-2"): (3, "A重力+D功正负+G反冲建模"),
    ("gaokao_2025", "20-2"):  (3, "B向心力方向+G对数几何+F代数"),
    ("xicheng_2024", "15-2a"): (2, "E有效数字+F公式代入"),
    ("gaokao_2024", "16-b"):  (2, "G关系式推导+F代数"),
    ("gaokao_2025", "16-3"):  (2, "E有效数字+F计算"),
}


def main():
    import csv, sys
    from pathlib import Path
    sys.stdout.reconfigure(encoding="utf-8")
    from statistics import mean
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.linear_model import Lasso
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import LeaveOneGroupOut

    CSV_PATH = Path("data/labeled/combined_scored_v3.csv")
    BASE = ['concept','reasoning','novelty','visual','modeling','position','is_open',
            'topic_mech','topic_em','textbook_scene_degree','textbook_pattern_degree']

    rows = []
    with open(CSV_PATH, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            row = {'qid':r['question_id'],'paper':r['paper_id'],'y':float(r['score_rate'])}
            for fn in BASE: row[fn] = float(r[fn])
            rows.append(row)

    for r in rows:
        r['transfer_cost'] = max(0.0, r['textbook_pattern_degree']-r['textbook_scene_degree'])
        r['is_last_quarter'] = 1.0 if r['position']>0.75 else 0.0
    by_paper = {}
    for r in rows: by_paper.setdefault(r['paper'],[]).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r['position'])
        for i,r in enumerate(s):
            r['earlier_load'] = mean(e['concept'] for e in s[:i]) if i else 0.0
    for r in rows:
        r['mod_x_nov'] = r['modeling']*r['novelty']
        r['mod_x_open'] = r['modeling']*r['is_open']
        r['con_x_mod'] = r['concept']*r['modeling']
        # Add trap_count · default 0 (unknown), overwritten for 30 subset
        key = (r['paper'], r['qid'])
        r['trap_count'] = float(TRAP_LABELS.get(key, (0, ""))[0])

    n_labeled = sum(1 for r in rows if r['trap_count'] > 0 or (r['paper'], r['qid']) in TRAP_LABELS)
    print(f"标记了 {n_labeled} 道题的陷阱数 · 其余 {len(rows)-n_labeled} 道默认 0")

    # Correlation with concept
    trap_vals = [r['trap_count'] for r in rows if (r['paper'], r['qid']) in TRAP_LABELS]
    concept_vals = [r['concept'] for r in rows if (r['paper'], r['qid']) in TRAP_LABELS]
    mt = mean(trap_vals); mc = mean(concept_vals)
    num = sum((t-mt)*(c-mc) for t,c in zip(trap_vals, concept_vals))
    dent = (sum((t-mt)**2 for t in trap_vals))**0.5
    denc = (sum((c-mc)**2 for c in concept_vals))**0.5
    corr = num/(dent*denc) if dent*denc>0 else 0
    print(f"陷阱数 与 概念数 相关系数 r = {corr:+.3f}  (基于 30 道 pre-label)")

    V51 = BASE + ['transfer_cost','is_last_quarter','earlier_load','mod_x_nov','mod_x_open','con_x_mod']

    y = np.array([r['y'] for r in rows])
    groups = [r['paper'] for r in rows]
    logo = LeaveOneGroupOut()

    def lopo_ensemble(feats):
        X = np.array([[r[f] for f in feats] for r in rows])
        y_true, yl, yg = [], [], []
        for tr, te in logo.split(X, y, groups):
            l = Lasso(alpha=0.001, max_iter=10000).fit(X[tr], y[tr])
            g = GradientBoostingRegressor(n_estimators=500, max_depth=2, learning_rate=0.01, random_state=42).fit(X[tr], y[tr])
            y_true.extend(y[te].tolist())
            yl.extend(l.predict(X[te]).tolist())
            yg.extend(g.predict(X[te]).tolist())
        yt = np.array(y_true); yl = np.array(yl); yg = np.array(yg)
        return {
            'Lasso': mean_absolute_error(yt, yl),
            'GBM': mean_absolute_error(yt, yg),
            'AVG': mean_absolute_error(yt, (yl+yg)/2),
        }

    # 测 3 个 hypothesis
    print()
    print(f"{'实验':<52} {'Lasso':>8} {'GBM':>8} {'AVG':>8}")
    print("-" * 78)

    # baseline (no trap)
    r = lopo_ensemble(V51)
    print(f"{'baseline v5.1 (无陷阱数)':<52} {r['Lasso']:>8.4f} {r['GBM']:>8.4f} {r['AVG']:>8.4f}")

    # Independent · 陷阱数作为独立特征
    r = lopo_ensemble(V51 + ['trap_count'])
    print(f"{'独立版: 陷阱数 as 独立特征':<52} {r['Lasso']:>8.4f} {r['GBM']:>8.4f} {r['AVG']:>8.4f}")

    # Merged · 陷阱数与概念数合并 = 加到 concept
    for r_ in rows:
        r_['concept_merged'] = r_['concept'] + r_['trap_count']
    V51_merged = ['concept_merged' if f=='concept' else f for f in V51]
    r = lopo_ensemble(V51_merged)
    print(f"{'合并版: concept + trap_count 合成 1 个':<52} {r['Lasso']:>8.4f} {r['GBM']:>8.4f} {r['AVG']:>8.4f}")

    # Replace · 陷阱数直接替换概念数
    V51_replace = ['trap_count' if f=='concept' else f for f in V51]
    r = lopo_ensemble(V51_replace)
    print(f"{'替换版: 只用陷阱数替代概念数':<52} {r['Lasso']:>8.4f} {r['GBM']:>8.4f} {r['AVG']:>8.4f}")

    # v5.1 + concept nonlinearity + trap_count (最佳配置)
    for r_ in rows:
        r_['concept_sq'] = r_['concept']**2
        r_['con_is_2'] = 1.0 if r_['concept'] == 2 else 0.0
        r_['con_is_3'] = 1.0 if r_['concept'] == 3 else 0.0
        r_['con_is_4'] = 1.0 if r_['concept'] == 4 else 0.0
        r_['con_is_5'] = 1.0 if r_['concept'] == 5 else 0.0
        r_['con_x_scene'] = r_['concept']*r_['textbook_scene_degree']
    V51_full = V51 + ['concept_sq','con_is_2','con_is_3','con_is_4','con_is_5','con_x_scene']
    r = lopo_ensemble(V51_full)
    print(f"{'v5.1 + concept nonlin (无 trap)':<52} {r['Lasso']:>8.4f} {r['GBM']:>8.4f} {r['AVG']:>8.4f}")
    r = lopo_ensemble(V51_full + ['trap_count'])
    print(f"{'v5.1 + concept nonlin + trap_count':<52} {r['Lasso']:>8.4f} {r['GBM']:>8.4f} {r['AVG']:>8.4f}")


if __name__ == "__main__":
    main()
