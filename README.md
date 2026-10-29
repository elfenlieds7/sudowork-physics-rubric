# 物理试题得分率预测

与合作教师共同研究：根据完整试题、评分要求与目标学生群体，预测每个小问的预期得分率，辅助命题。

## 当前阶段 · 2026-10-29

**计划 v3.0：旧模型的单题精度尚未达到使用要求，进入语义决策模型评测与领域适配阶段。**

- 2026 年逐题核验覆盖 31 个设问、95 分。调整版的分值加权平均绝对误差为 **18.54 个百分点**，解答题已观测部分为 **26.31 个百分点**。整卷误差相抵不能替代单题准确。
- 主线：VLM 忠实数字化 → 完整题目 JSON 与图示记录 → 决策模型 → 本地实测成绩核验。不预先限定旧模型的 15 个特征。
- 候选：Jev 商业参考基线、Clef-Flash 9B、H2O-Lightning-4B、自训 Qwen3.5-9B；旧 Lasso + GBM 保留为冻结对照。
- Jev 官方不提供客户微调。直接评测、本地输出校准、开放模型训练分开报告；监督训练与 RLCD 式实验也分开记录。
- 按整年／整卷划分，禁止小问跨组；2026 年已有核验属于回顾性分析。最终还需未参与调试的试卷或前瞻考试验证。
- **已验证的是 Jev 原生接口连通与合成题协议，完整精度比较和新模型训练尚未完成。**

## 两个主要页面

| ShareOne URL | 用途 | 源文件 |
|---|---|---|
| [difficulty-rubric-v2-yang](https://s.shareone.vip/s/difficulty-rubric-v2-yang) | 主 SSOT：计划 v3.0，含完整历史区 | `deliverables/rubric/v2.html` |
| [sodu-physics-rubric-paper-v1](https://s.shareone.vip/s/sodu-physics-rubric-paper-v1) | 历史论文稿 v2.4.4，本轮未重写 | `deliverables/paper/v1.html` |

Git 仓库管理源文件与历史；ShareOne 提供阅读和评论。主 SSOT 保持原链接，绑定 GitHub 固定提交。更新源文件并提交、推送后，需将原分享的 `remote_url` 更新到新提交；不得另建分享或默默改成跟随分支。见 [页面状态](context/shareone_state.md)。

## 数据与保密

仓库为公开仓库。原始成绩与题目—成绩连接表保留在 gitignored 的 `data/private/`，不提交、不嵌入公开页面、不发给云端模型。发送公开试卷前检查是否附有手写成绩等内部标注。

旧训练集为 7 套试卷、223 个设问，混合高考与模拟卷；它不等于已整理完毕的 2020—2026 年西城高考样本。下一阶段先核对各年题目与实测统计。高考与高三期末的备考阶段不同，分别验证。

## 新加入项目时先读

1. 本文件与 ShareOne 主 SSOT 上方的当前计划。
2. [STRUCTURE.md](STRUCTURE.md)：文件组织，旧量表与训练脚本保留供复现。
3. [context/shareone_state.md](context/shareone_state.md)：当前链接、源文件与更新流程。
4. [context/meta_lessons.md](context/meta_lessons.md)：已发生的方法学问题。
5. `analysis/audit_2026_actuals.py` 及主页面历史附录 G.10：2026 年实测核验口径。

旧量表的评分一致性、早期交叉验证与论文结果属于历史探索，不再作为当前单题预测已可用的依据。

联系 Ethan（宋一民），GitHub：`elfenlieds7`。学术使用与定制数据分享需联系协商。
