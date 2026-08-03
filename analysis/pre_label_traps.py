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
# UPDATED 2026-08-03 17:00 with teacher's shareone review (v2 · her actual labels)
# 我 systematically 高估 · 30 道 · 我 sum 58 · her sum 34 · avg 差 0.8
# 一致 (0 change): 12 items · 我高估 17 · 我低估 1
TRAP_LABELS = {
    ("gaokao_2024", "8"):    (1, "G误以为对称位置阻力等·上升下落机械能损失误相等 [她: 3→1]"),
    ("gaokao_2024", "6"):    (0, "学生就是不会分析·没陷阱 [她: 2→0]"),
    ("gaokao_2024", "10"):   (1, "G匀速也受摩擦力·力与运动关系 [她: 2→1]"),
    ("gaokao_2024", "2"):    (0, "简单公式套用 [同意]"),
    ("gaokao_2025", "11"):   (1, "G陌生f-t图像信息提取困难 [她: 3→1]"),
    ("gaokao_2025", "6"):    (1, "G受力个数多易漏 [她: 2→1]"),
    ("gaokao_2025", "8"):    (1, "同意 [G类比]"),
    ("gaokao_2025", "10"):   (1, "G距离近则电流为0则F=0 [她: 3→1]"),
    ("xicheng_2024", "14"):  (0, "情境题·同意 [核心动量守恒方向她认为已经1个但也无]"),
    ("xicheng_2024", "8"):   (1, "G学生误 加速度大速度大时间短 [她: 2→1]"),
    ("xicheng_2024", "6"):   (1, "G向心加速度与重力加速度混淆 [她: 2→1]"),
    ("xicheng_2024", "13"):  (2, "同意 [B洛伦兹方向+G速度分解]"),
    ("xicheng_2025", "14"):  (1, "同意 [她: 动量守恒方向陷阱]"),
    ("xicheng_2025", "1"):   (1, "G粒子核电荷数质量数知道但不知道叫什么 [她: 0→1]"),
    ("xicheng_2025", "6"):   (1, "同意"),
    ("xicheng_2025", "12"):  (1, "G缓慢vs恒力受力不同 [她: 3→1]"),
    ("xicheng_2026", "2"):   (0, "无陷阱 [她: 1→0]"),
    ("xicheng_2026", "3"):   (1, "同意·水柱外移气体做功"),
    ("xicheng_2026", "5"):   (1, "同意"),
    ("xicheng_2026", "13"):  (2, "同意"),
    ("xicheng_2026", "15-2"): (0, "实验操作排序·无计算 [她: 2→0]"),
    ("gaokao_2024", "19-2a"): (2, "同意"),
    ("xicheng_2026", "16-2"): (0, "按读数规则直接读·无计算 [她: 2→0]"),
    ("xicheng_2025", "20-2"): (2, "G电场强度E与能量E字母混淆+G非匀强场分析 [她: 3→2]"),
    ("xicheng_2024", "20-2a"): (3, "同意"),
    ("xicheng_2025", "19-2"): (2, "A丢重力+G相对速度对地速度转换 [她: 3→2]"),
    ("gaokao_2025", "20-2"):  (2, "G电场强度E和能量E字母混淆+G非恒力分析 [她: 3→2]"),
    ("xicheng_2024", "15-2a"): (2, "同意"),
    ("gaokao_2024", "16-b"):  (1, "G几何关系无法表示·关系式推导 [她: 2→1]"),
    ("gaokao_2025", "16-3"):  (2, "同意"),
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
