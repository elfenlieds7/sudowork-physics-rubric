# sudowork-physics-rubric

Collaboration between **A collaborating physics teacher** (北京市西城区教育研修学院 · 40 年教龄 · 命题专家) and **sudowork AI agents** on:

1. **Solving her physics problems** (with proper reflection + diagrams) — proof-of-concept that AI can be a genuine work partner, not just tool
2. **Building a difficulty-prediction rubric** for exam questions — 命题时预测题目 得分率 · design better-structured tests

📂 **文件组织**: 见 [STRUCTURE.md](STRUCTURE.md) · 完整覆盖 GitHub 公开数据 + 本地敏感数据 + Shareone 页面。

## Current state (2026-08-15 · v2.4)

**当前 canonical**: 客观难度模型 v2.4 · 10 维评价量表 · 8 条计数规则 · 223 题全量 labels。

- **Kappa 达到 1.00** (v2.3 · 20 题校准 · 与杨老师 gold labels 完全一致) — 迭代 6 轮 · 8 条规则收敛
- **v2.4 baseline**: 整卷 MAE 1.96pp · 单题 MAE 8.5pp
- **Plan 1 加权训练** (小问分值加权): 综合大题 MAE 10.26 → 10.05 pp (-0.21 改善)
- **论文 v2.4.4** · 目标期刊: 物理教师/物理教学

**核心交付物** (只 2 个 canonical page):

| Shareone URL | 用途 | 本地路径 |
|--------------|------|----------|
| [difficulty-rubric-v2-yang](https://s.shareone.vip/s/difficulty-rubric-v2-yang) | 主 SSOT (living v2.4) | `deliverables/rubric/v2.html` |
| [sodu-physics-rubric-paper-v1](https://s.shareone.vip/s/sodu-physics-rubric-paper-v1) | 论文 (v2.4.4) | `deliverables/paper/v1.html` |

## Two collaboration surfaces (paired)

- **shareone** (公开链接 + comment 侧栏) — 杨老师 review + wechat feedback
- **This repo** (github **public**) — AI agents / 工程 / 未来 co-founders 的 source of truth。敏感学生数据 gitignored · 只公开评价量表定义 · 模型系数 · 分析脚本

## Getting started (for a new AI joining this project)

1. 读 [STRUCTURE.md](STRUCTURE.md) — 完整文件组织
2. 读 `context/meta_lessons.md` — 方法学教训 (hard-earned)
3. 读 `context/shareone_state.md` — shareone 页面状态
4. 打开 shareone 主 SSOT 通读 v2.4 rubric + 附录 D/E/F (evolution / spec / kappa)
5. 打开论文 v2.4.4 熟悉最新 pipeline + 结果结构
6. 看 `analysis/train_v2_4_weighted.py` — 当前 canonical 训练脚本 (Plan 1 加权)

## Historical context (superseded)

早期 pilot (v1 · 33 题 · R²=0.886) 与 LOPO scale-up (v3 · 162 题) 属于探索阶段 · 已被 v2.3/v2.4 rubric 取代。历史 spec/calibration 独立页面已并入主 SSOT 附录 (见 STRUCTURE.md · 二)。

## For humans

Contact **Ethan (宋一民)** — sudowork founder · Github: `elfenlieds7`。学术使用需求 (含定制化数据分享) 可联系通讯作者协商。
