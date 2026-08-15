# 项目文件结构 · SSOT

**最后更新**: 2026-08-15 · **当前 canonical 版本**: v2.4

本文档描述本项目所有材料的组织方式 · 覆盖:
- 📂 **GitHub 公开**部分 (本 repo 内 · 可 clone)
- 🔒 **本地敏感数据**部分 (`.gitignore` 排除 · 只在教研组内使用)
- 🌐 **Shareone 页面**部分 (URL 引用 · 不进 repo)

---

## 一 · 顶层结构总览

```
sudowork-physics-rubric/
├── README.md                    # 项目 quick start · GitHub 首页
├── STRUCTURE.md                 # 本文件 · 文件组织说明
├── .gitignore                   # 保密文件排除规则
│
├── deliverables/                # 交付产物 · 面向读者
│   ├── paper/                   # 📄 论文 (v2.4.4)
│   ├── rubric/                  # 📊 主 SSOT (living v2.4)
│   └── archive/                 # 历史快照 (spec / calibration 已并入主 SSOT)
│
├── data/                        # 数据
│   ├── labeled/                 # ✅ 当前 canonical · v2.3/v2.4 labels + teacher gold
│   │   └── archive/             # 历史 label 版本 (v1-v2.2)
│   ├── reference/               # 打分参照资料 (核心知识 · 教材 samples)
│   ├── references/              # 📚 文献参考 (综述文献 + 政策文件)
│   ├── source_pdfs/             # 试卷 PDF 原件 (公开的高考题)
│   ├── extracted_pages/         # PDF 转 PNG (894 页 · 自动生成)
│   └── private/                 # 🔒 保密数据 (git 忽略 · 学生实测得分率原始)
│
├── analysis/                    # Python 脚本 (30+)
│   └── notebooks/               # Jupyter 探索笔记
│
├── context/                     # 内部工作 notes (关键节点 · 教训 · shareone 状态)
│
└── vendor/                      # 第三方依赖 (若有)
```

---

## 二 · 📄 交付产物 (`deliverables/`)

**目的**: 最终对外/对上呈现的产物 · 与 shareone 页面一一对应。

| 目录 / 文件 | 用途 | Shareone URL |
|-------------|------|--------------|
| `paper/v1.html` | **论文 v2.4.4** · 独立发表版 | [sodu-physics-rubric-paper-v1](https://s.shareone.vip/s/sodu-physics-rubric-paper-v1) |
| `rubric/v2.html` | **主 SSOT (living v2.4)** · 项目全景 | [difficulty-rubric-v2-yang](https://s.shareone.vip/s/difficulty-rubric-v2-yang) |
| `archive/spec_2026-08-08_snapshot/` | 原独立 spec 页 (内容已并入主 SSOT 附录 E) | 已 dead |
| `archive/calibration_2026-08-09_snapshot/` | 原独立 kappa study 页 (已并入主 SSOT 附录 F) | 已 dead |
| `archive/bungee_solution/` | 早期探索 · 不再维护 | 无 |

---

## 三 · 数据 (`data/`)

### 3.1 · `data/labeled/` · 打分标签

**当前 canonical** (v2.3 用于 kappa 引用 · v2.4 用于最新训练):

| 文件 | 内容 |
|------|------|
| `v2_4_labels.csv` | ✅ 223 题 · v2.4 rubric 全量 labels · 训练用 |
| `v2_4_info_reasoning.json` | v2.4 relabel reasoning · 信息呈现 4 档 |
| `v2_3_labels.csv` | v2.3 rubric (concept_count 精修) 全量 labels |
| `v2_3_labels_reasoning.json` | v2.3 每题 concept_count reasoning |
| `v2_3_calibration_20_items.csv` | 20 题 kappa 校准子集 · v2.3 |
| `v2_3_calibration_reasoning.json` | 20 题 kappa reasoning · 详细 |
| `teacher_v23_20items_20260811.xlsx` | 🎯 杨老师 v2.3 gold labels · κ 1.00 基准 |
| `archive/` | 历史 labels (v1-v2.2 · 早期探索结果) |

### 3.2 · `data/reference/` · 打分参照资料

评分者 (人类 or AI) 打分时的 canonical 参照。

| 文件 | 内容 |
|------|------|
| `高中物理核心知识点.xlsx` | 🎯 杨老师 64 KP 清单 (v2.3 rubric 基础) |
| `core_knowledge_points_v1.json` | 64 KP 结构化 (脚本 use) |
| `subquestion_points_xicheng.json` | 西城模拟卷小问分值 (Plan 1 训练用) |
| `dianxing_moxing_catalog.md` | 典型模型 catalog |
| `textbook_toc.md` | 教材目录 (人教版 2019) |
| `textbook_samples/` | 教材 sample 页 (可选打分参照) |

### 3.3 · `data/references/` · 文献参考

**注**: 与 `data/reference/` 单复数 · 用途不同 · references 是外部**文献** · reference 是内部**参照**。

| 目录 | 内容 |
|------|------|
| `authoritative/` | 政策文件 3 份 (高考评价体系 · 说明 · 物理课标) |
| `papers/` | 综合难度模型综述 6 篇 (王刚 · 冯小沙 · 冯雪媚 · 余招贤 · 余建刚 · 杨英恺) |

### 3.4 · `data/source_pdfs/` · 试卷原件

7 份高考/西城一模 PDF (公开可获) + 人教版教材 (gitignored · 80MB)。

### 3.5 · `data/extracted_pages/` · 页面 PNG

从 PDF 提取的 894 页 PNG · 供人工/AI 打分参照。**自动生成 · 不用手动维护。**

### 3.6 · `data/private/` · 🔒 保密数据 (**gitignored · 本地 only**)

**⚠️ 本目录内容永不进 GitHub**。用途:

| 文件 | 内容 · 保密原因 |
|------|-----------------|
| `2023_beijing_gaokao_rates.xlsx` | 2023 北京高考学生实测得分率原始数据 · 教研内部 |
| `2024_beijing_gaokao_rates.xlsx` | 2024 北京高考学生实测得分率 |
| `2025_beijing_gaokao_rates.xlsx` | 2025 北京高考学生实测得分率 |
| `cohort_calibration.csv` | 121 对 (西城, 全北京) 配对数据 · 跨样本群 |
| `cohort_calibration_template.csv` | 模板 |
| `README.md` | 保密数据使用说明 |

**接触约束**: 仅杨老师 + sudowork 智能体使用 · 论文只发布模型系数与派生数据 · 有严肃学术使用需求可联系通讯作者协商。

---

## 四 · 🐍 分析脚本 (`analysis/`)

30+ Python 脚本。**当前 canonical** (v2.4 pipeline):

| 类别 | 当前 canonical | 用途 |
|------|----------------|------|
| Relabel | `relabel_v24.py` | 按 v2.4 (信息呈现 4 档 + 模块 2 档) 生成 labels |
| Relabel (concept) | `relabel_v23_full223.py` | 按 v2.3 rubric (64 KP + 7 规则) 生成 concept_count |
| Train | `train_v2_4.py` | Baseline v2.4 训练 (Lasso + GBM) |
| Train (weighted) | `train_v2_4_weighted.py` | ⭐ Plan 1 · 小问分值加权训练 (综合大题 MAE 改善) |
| Train (interaction) | `train_v2_4_interactions.py` | pair-wise interaction 搜索 |
| Kappa | `compute_kappa_v23.py` | κ 计算 · v2.3 vs teacher gold |
| Feature analysis | `feature_analysis_v23.py` | Pearson · Spearman · GBM 重要度 |
| Cohort shift | `build_cohort_calibration.py`, `fit_cohort_offset.py` | 西城 ⇌ 全北京偏移模型 |
| Export | `export_model_to_js.py` | 模型系数 → JS · 用于命题工具 |

**历史/一次性脚本** (仍在 `analysis/` · 未 archive 以免破坏 import): `apply_v22_relabel.py` · `audit_5_apply.py` · `investigate_residual_position.py` · `nonlinear_models.py` · `pattern_recalibrate.py` · `pre_label_traps.py` · `refine_qtype_and_test.py` · `v6_full_traps.py` 等 · 属早期探索或 v1-v2.2 实验 · 保留以供追溯。

---

## 五 · 内部 notes (`context/`)

**不对外的工作记录**:
- `key_moments.md` — 关键节点时间线
- `meta_lessons.md` — 方法学教训
- `shareone_state.md` — shareone 页面状态

`credentials.local.md` (若存在) · gitignored · 保密。

---

## 六 · 🌐 Shareone 页面 (URL only · 不进 repo)

**当前 live · 只 2 个**:

| URL | 用途 | 对应本地 |
|-----|------|----------|
| [difficulty-rubric-v2-yang](https://s.shareone.vip/s/difficulty-rubric-v2-yang) | 主 SSOT (living v2.4) | `deliverables/rubric/v2.html` |
| [sodu-physics-rubric-paper-v1](https://s.shareone.vip/s/sodu-physics-rubric-paper-v1) | 论文 (v2.4.4) | `deliverables/paper/v1.html` |

**已废弃 URL** (tombstoned · HTTP 410):
- `difficulty-rubric-v1-yang` (原主 SSOT · 误删导致 slug tombstone · 迁到 v2-yang)
- `rubric-v2-spec-yang` (内容并入主 SSOT 附录 E)
- `rubric-calibration-v2-yang` (内容并入主 SSOT 附录 F)

---

## 七 · 保密与开源分级 (数据治理)

| 分级 | 例子 | 存放 | 是否公开 |
|------|------|------|----------|
| 🔴 **保密** | 学生实测得分率原始 · 跨样本群配对 · 通讯作者邮箱 | `data/private/` · `context/credentials.local.md` | 仅教研组内 |
| 🟡 **可控公开** | 论文 (含派生指标 · 无学生个人识别) | `deliverables/paper/` · shareone | 学术公开 |
| 🟢 **完全公开** | 评价量表定义 · 模型系数 · 分析脚本 · 综合难度模型综述 | GitHub · shareone 主 SSOT | 任何人可访问 |

**接触约束**: 论文明确说 "原始学生得分率数据受教研内部保密约束不公开发布 · 仅公开模型系数与派生数据 · 有严肃学术使用需求可联系通讯作者协商定制化数据分享方案。"

---

## 八 · 变更历史 (STRUCTURE.md · 简史)

- **2026-08-15**: 初版建立 · 完整重构以下:
  - `deliverables/{rubric_v2,calibration,bungee_solution}/` → `deliverables/archive/`
  - `data/labeled/{rubric_v*_result,combined_scored_v3,v2_1_labels,calibration_20_items,teacher_v2_20items_20260809,v2_2*,reading_load_per_question,xicheng_2026_scored*}` → `data/labeled/archive/`
  - Delete `analysis/__pycache__/`
  - 写此 STRUCTURE.md
