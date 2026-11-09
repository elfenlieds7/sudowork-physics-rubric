# 物理试题得分率预测

与合作教师共同研究：根据完整试题、评分要求与目标学生群体，预测每个小问的预期得分率，辅助命题。

## Windows 接续入口

先读 [2026-11-09 交接说明](docs/windows-handoff-20261109.md)：已完成内容、下一步、运行命令、依赖和数据位置。私密数据由 Dropbox 交接，使用 `scripts/verify_private_handoff.py` 核对并恢复；新模型训练尚未开始。

## 当前阶段 · 2026-11-09

**计划 v3.4：Windows 接续资料、代码与依赖已整理；保持 Decision-1 同类路线复现、LoRA 监督起点及后续 RLCD 式实验。七年统计已接收，新模型尚未训练；逐题实测数据改由私密包交接。**

- 2026 年逐题核验覆盖 31 个设问、95 分。调整版的分值加权平均绝对误差为 **18.54 个百分点**，解答题已观测部分为 **26.31 个百分点**。整卷误差相抵不能替代单题准确。
- 主线：VLM 忠实数字化 → 完整题目 JSON 与图示记录 → 决策模型 → 本地实测成绩核验。不预先限定旧模型的 15 个特征。
- 候选：Jev 商业参考基线、Clef-Flash 9B、H2O-Lightning-4B、自训 Qwen3.5-9B；旧 Lasso + GBM 保留为冻结对照。
- Jev 官方不提供客户微调。直接评测、本地输出校准、开放模型训练分开报告；监督训练与 RLCD 式实验也分开记录。
- 新表覆盖 2020—2026 年，219 条观测记录，各条附实际分值。结构、重复题号、父子重复计数与年度分值汇总已核验；题目数字化和小问映射尚未完成。覆盖范围见 `data/reference/gaokao_2020_2026_coverage.json`，该文件不含实测得分率。
- 首轮以决策层＋LoRA监督适配为主，保留仅训练输出层的对照。RLCD式实验随后独立比较；部分解冻或全参微调按留出试卷收益、数据覆盖和实机资源决定。参数更新范围与学习目标是两个维度。
- 以微软公开的Qwen3.5-9B、单次前向决策和概率输出为技术参照，自训Qwen为自主复现主线，现成模型提供结构参考与性能对照。RLCD式实验为明确研究阶段，并与同预算监督继续训练比较；微软完整训练框架、奖励与配方尚未获得，不宣称精确复现。通用决策能力与物理适配分别验证，通用训练数据配方仍待落实。
- 任务奖励需要自行定义和验证。负均方误差只能作为均值预测的基础对照；它不自动证明完整概率校准或RLCD增益。只用训练年份实测计算训练奖励，最终测试成绩不参与更新。
- 按整年／整卷划分，禁止小问跨组；2026 年已有核验属于回顾性分析。最终还需未参与调试的试卷或前瞻考试验证。
- **已验证的是 Jev 原生接口连通与合成题协议，完整精度比较和新模型训练尚未完成。**

## 项目页面与通用架构

| ShareOne URL | 用途 | 源文件 |
|---|---|---|
| [difficulty-rubric-v2-yang](https://s.shareone.vip/s/difficulty-rubric-v2-yang) | 主 SSOT：计划 v3.4，含完整历史区 | `deliverables/rubric/v2.html` |
| [sodu-physics-rubric-paper-v1](https://s.shareone.vip/s/sodu-physics-rubric-paper-v1) | 历史论文稿 v2.4.4，本轮未重写 | `deliverables/paper/v1.html` |
| [本地决策模型训练与 AI 协作架构](https://s.shareone.vip/s/ben-di-jue-ce-mo-xing-xun-lian-yu-ai-xie-zuo-jia-gou) | 通用独立架构 v0.1，组件、接口和信息边界；服务待实现 | `deliverables/architecture/local-training.html` |

Git 仓库管理源文件与历史；ShareOne 提供阅读和评论。主 SSOT 保持原链接，绑定 GitHub 固定提交。更新源文件并提交、推送后，需将原分享的 `remote_url` 更新到新提交；不得另建分享或默默改成跟随分支。见 [页面状态](context/shareone_state.md)。

## 数据与保密

仓库为公开仓库。原始成绩与题目—成绩连接表保留在 gitignored 的 `data/private/`，以及本次已取消 Git 跟踪的旧数据路径，不提交、不嵌入公开页面、不发给云端模型。发送公开试卷前检查是否附有手写成绩等内部标注。

旧训练集为 7 套试卷、223 个设问，混合高考与模拟卷；与新收到的七年219条高考统计分别管理，不能直接相加。新表各年覆盖91—95分，未列得分率保持缺失；不填零，不推断完整100分均分。2026年新表32条与历史31个设问的粒度不同，先映射再比较。高考与高三期末的备考阶段不同，分别验证。

2020—2022年试卷与参考答案已接收，在本地私密目录归档；仓库已有2023—2026年试卷和2026年答案。当前尚未找到2023—2025年正式参考答案与评分标准。发送试卷给云端模型前仍需检查手写成绩、批注和附件。

### 本地数据接收核验

```bash
python analysis/intake_gaokao_workbook.py --source /absolute/path/to/workbook.xlsx
python -m unittest discover -s analysis -p test_intake_gaokao_workbook.py
```

脚本按原表实际字段核验，规范化题号并保留来源行；所有含成绩的输出强制写入 `data/private/`。如需更新公开覆盖摘要，另加 `--coverage-summary data/reference/gaokao_2020_2026_coverage.json`。原表版本以哈希固定，后续更换资料使用新的私密接收目录。

## 新加入项目时先读

1. 本文件与 ShareOne 主 SSOT 上方的当前计划。
2. [STRUCTURE.md](STRUCTURE.md)：文件组织，旧量表与训练脚本保留供复现。
3. [context/shareone_state.md](context/shareone_state.md)：当前链接、源文件与更新流程。
4. [context/meta_lessons.md](context/meta_lessons.md)：已发生的方法学问题。
5. `analysis/audit_2026_actuals.py` 及主页面历史附录 G.10：2026 年实测核验口径。

旧量表的评分一致性、早期交叉验证与论文结果属于历史探索，不再作为当前单题预测已可用的依据。

联系 Ethan（宋一民），GitHub：`elfenlieds7`。学术使用与定制数据分享需联系协商。

### 公开文件检查

提交前运行 `python scripts/check_public_data.py`；检查暂存内容使用 `--staged`。旧页面曾内嵌的逐题实测值和旧训练成绩文件已从当前公开树移出，原件在私密包；旧 Git 历史未改写。
