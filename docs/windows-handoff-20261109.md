# Windows 接续说明 · 2026-11-09

本交接用于 `elfenlieds7/sudowork-physics-rubric`。Windows 的 `document-ai/` 是此前协作入口，不是本项目代码的另一份来源。先保护 Windows 已有未提交工作和私密数据，再拉取本仓库；不要用 reset/clean 覆盖另一会话的成果。

## 1. 先看结论与入口

**已完成资料接收、结构核验、研究方案和文档；新决策模型尚未训练。**

| 内容 | 入口 | 实际状态 |
|---|---|---|
| 本项目当前研究计划 | [ShareOne 主页面](https://s.shareone.vip/s/difficulty-rubric-v2-yang)、`deliverables/rubric/v2.html` | v3.4；Decision-1 同类路线、LoRA 监督起点及后续 RLCD 式实验 |
| 通用本地训练架构 | [独立架构页](https://s.shareone.vip/s/ben-di-jue-ce-mo-xing-xun-lian-yu-ai-xie-zuo-jia-gou)、`deliverables/architecture/` | v0.2；图中模块对应组件、API 和待补要求，组合服务未实现 |
| 新七年工作簿接收 | `analysis/intake_gaokao_workbook.py` | 已验证；219 条观测，包含每题实际分值 |
| 数据配置与版本 | `configs/data-intake.v1.json`、`data/reference/data_versions.json` | 公开文件只描述版本、结构、覆盖范围与状态 |
| 研究实验配置 | `configs/decision-model-research.v1.json` | **设计记录，不是可启动训练的配方**；未定项保留 null |
| 旧模型与审计 | `analysis/train_v2_4.py`、`analysis/audit_2026_actuals.py` 等 | 历史代码；不得将其结果当作新模型精度 |
| 私密交接完整性 | `scripts/verify_private_handoff.py` | 可验证清单、大小、SHA-256；可恢复到 Git 忽略路径 |
| 公开数据防漏检查 | `scripts/check_public_data.py` | 检查结构化数据中的实测字段及页面内嵌值；不能替代图片／自由文本检查 |

之前已验证 Jev 原生接口连通及合成题协议。这是工作记录中的人工连通检查，**没有已完成的整卷评测，也没有可交付的 Jev 训练代码**。凭据不进入仓库或交接包。

## 2. 数据版本：不能直接拼接

| 数据 | 覆盖 | 使用限制 |
|---|---|---|
| `gaokao-xicheng-2020-2026-received-20261102-v1` | 七年、219 条；逐年记录数 30/31/30/33/31/32/32；覆盖分值 93/92/94/94/94/91/95 | 部分覆盖；缺失不填零，不据此推断完整 100 分均分 |
| `legacy-rubric-v2.4-223` | 旧版七套高考／模拟卷、223 个设问 | 与新表分别管理，不能简单相加；只作历史对照 |
| 2026 历史核验 | 31 个设问、95 分 | 新表 2026 年为 32 条；例如 15-3 的细分发生变化，先核对映射 |

2020—2022 年新收试卷、答案及原始 Excel 在私密包。仓库已有 2023—2026 年试卷与 2026 年答案；尚未找到 2023—2025 年完整正式答案及评分标准。新收 PDF 暂不作为已审查的公共素材重新发布。

`observed_rates.csv` 字段结构：年份、试卷 ID、群体、规范化小问 ID、来源小问 ID、分值、实测得分率、来源 sheet／行号。得分率单位为 0—1；原文件、逐题记录、关联表、核验审计均保持私密。

新旧题目数字化、小问／父子题映射、评分口径以及题目—成绩连接尚未完成。没有可直接开始 LoRA 的完整训练样本集。

## 3. 哪些在哪台机器

以下是本次实测与已知操作的范围，不代替 Windows 自己的盘点。

| 资料 | GitHub | Mac | Dropbox 私密交接 | Windows | 训练机 |
|---|---|---|---|---|---|
| 代码、配置、页面、覆盖与版本说明 | 已提交并推送 | 已确认 | 无需依赖私密包获取 | 拉取后自行核对提交 | 未核验 checkout |
| 新 Excel、219 条规范化记录、接收审计 | 不含 | 已确认 | 包内逐文件清单与 SHA-256 | **待接收确认** | **UNKNOWN** |
| 2020—2022 新收 PDF 与文件目录 | 不含 | 已确认 | 同上 | 待确认 | UNKNOWN |
| 已发现的旧逐题成绩文件、旧页面完整私密备份 | 当前树不含 | 保留本地 | 同上；旧脚本所需的原路径可恢复 | 待确认 | UNKNOWN |
| 新模型训练检查点、完整 GPU 训练配方 | 未产生 | 未产生 | 无 | 不推断 Windows 是否另有成果 | UNKNOWN |

**本工作线未向训练机传送数据。** 本次根据凭据条目名称尝试 LAN 主机名的只读 SSH 连通核验，名称未能解析，未建立会话。不能据此宣称训练机没有文件，也不能宣称文件已在训练机。地址、账号和完整检查记录只留在私密交接材料。

Mac 还缺：历史 `data/private/2026_validation/2026_teacher_actuals.xlsx` 与 `data/private/cohort_calibration.csv`。不要用新表直接替换这些旧审计输入；Windows 若已保存，应保留版本并补齐来源与校验。本次不伪造这些文件。

## 4. 私密包位置与接收核对

用户选择 Dropbox。相对于账号的 Dropbox 根目录：

```text
sudowork-physics-rubric/private-handoff/2026-11-09/
  README_PRIVATE.md
  manifest.json
  manifest.sha256
  payload/                 # 路径相对于本仓库根目录
```

不创建公开分享链接。Mac 写入同步目录不等于 Windows 已收齐；以接收端 SHA-256 校验为准。清单含每个文件的相对路径、字节数、SHA-256 和 Mac 来源位置；来源绝对路径仅在私密包中。

优先在新的独立 checkout 接收。已有 checkout 拉取前，先备份 Windows 的旧私密副本：本次将历史实测数据取消 Git 跟踪，Git 更新可能移除旧的已跟踪副本。不要因此丢弃 Windows 的独有数据或实验记录。

Windows PowerShell 示例，在仓库根目录执行。若 Dropbox 位于 D 盘，只改 `$physicsBundle` 的根目录：

```powershell
$physicsBundle = Join-Path $env:USERPROFILE 'Dropbox\sudowork-physics-rubric\private-handoff\2026-11-09'
python scripts/verify_private_handoff.py --bundle $physicsBundle
python scripts/verify_private_handoff.py --bundle $physicsBundle --restore-to .
```

恢复工具先核验全部文件，再检查全部目的地：路径必须受 Git 忽略、不得已被 Git 跟踪；已有文件内容不一致时停止，不覆盖。相同文件可以重复接收。先确认拿到了本次新提交及 `.gitignore`，再恢复。

## 5. 怎样运行已完成的部分

Mac 本次核验用 Python 3.14.6、openpyxl 3.1.5；Windows 与 GPU 的 Python／容器版本尚未验证。下面是接续命令，不宣称已在 Windows 执行。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/intake.txt
.\.venv\Scripts\python.exe -m unittest discover -s analysis -p test_intake_gaokao_workbook.py
.\.venv\Scripts\python.exe -m unittest discover -s analysis -p test_private_handoff.py
.\.venv\Scripts\python.exe scripts/check_public_data.py
```

私密包恢复后，重做接收核验（输出继续落在本地忽略目录；终端只打印覆盖摘要）：

```powershell
.\.venv\Scripts\python.exe analysis/intake_gaokao_workbook.py --source 'data/private/gaokao_2020_2026_20261102/20-26年西城.xlsx'
```

若要更新公开覆盖摘要，显式加 `--coverage-summary data/reference/gaokao_2020_2026_coverage.json` 并审阅 diff。与 `configs/data-intake.v1.json` 的年份、219 条以及逐年分值逐项核对。原文件的确切 SHA-256 在私密清单中。

旧模型复现可安装 `requirements/legacy-analysis.txt` 后运行 `analysis/train_v2_4.py`。依赖版本来自 Mac 现状，仅作历史环境记录；本次不重新训练旧模型。旧审计还缺上述单年工作簿与群体校准表，直接运行 `audit_2026_actuals.py` 不会成功。

页面 HTML 可直接浏览。通用架构生成器在 `scripts/build_local_training_page.py`。唯一内容源为 `deliverables/architecture/local-training.data.json`，模块、组件、API 契约及引用统一维护；模板只管样式与交互，HTML 和 Mermaid 图源由生成器产生，勿分别手改。维护说明见同目录 `README.md`。仅修改页面时才需 `requirements/publishing.txt` 与 Chromium；Mermaid JS 支持文件在私密包的 `data/private/handoff_20261109/support/`，也可自行取得同版本资源。示例：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/publishing.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/build_local_training_page.py --mermaid-js data/private/handoff_20261109/support/mermaid.min.js
```

ShareOne 使用其 skill 发布，继续绑定固定的完整 Git 提交；不要改成 main 自动跟随。见 `context/shareone_state.md`。本轮未新增私密分享链接，也不把私密附件上传到 ShareOne。

## 6. Windows 下一步从这里开始

1. **先回报接收基线。** Git 完整提交、私密包校验通过的文件数；盘点 Windows 已有独有文件／代码／实验，先合并事实，不覆盖另一边成果。
2. **完成试题数字化和连接。** 在本地生成包含完整题干、图示、评分要求的记录，按整卷核对小问 ID、分值和真实均值得分率。对 2026 年新旧粒度单独留映射表。
3. **固定划分。** 同年同卷、父子小问和题目变体不跨组。预处理、校准和超参选择只看训练折；2026 年为已审阅的回顾性比较，最终还需新留出／前瞻试卷。
4. **检查实际算力。** 确认 GPU、架构、驱动、容器和内存；按 [NVIDIA 官方 Spark 微调示例](https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/pytorch-fine-tune)选择环境起点，再测试目标模型。Mac 未安装 torch／transformers／PEFT／Datasets／MLflow，没有已验证 GPU 依赖锁。
5. **先建立可核对的同题基线，再写训练。** 自训 Qwen3.5-9B 为自主复现主线，现成开放决策模型用于结构与性能参照；先决策层＋LoRA 监督训练并保留仅训练输出层对照。模型 revision、决策读出、上下文长度、精度、LoRA rank、学习率等在实测后固定；配置中 null 不表示默认值。
6. **RLCD 式实验随后比较。** 先检查领域奖励的正确性与边界行为，再从同一监督起点与同预算继续监督训练比较。负均方误差仅是均值任务的基础对照；它不自动构成 RLCD，也不证明完整概率校准。完整厂商训练配方未知。

## 7. 当前公开数据清理的边界

本次取消跟踪已发现含实测值的旧 CSV／JSON，原文件保留在 Mac 并进入私密包。旧页面图表内嵌的 223 条实测数据已去除，完整旧页面仅在私密包保留；公开页面保留研究结论与汇总指标。含成绩的历史导出脚本改为写入 `data/private/legacy_chart_exports/`。

**旧 Git 提交仍可能含先前已公开的副本；这次没有改写历史。** 固定旧提交的资源也不会因新 main 自动消失。不要向接续者承诺“历史数据已彻底清除”。公开检查脚本用于防止今后再次提交结构化成绩，不能保证所有历史图像或自由文本均已完成审查。

## 8. Windows 接收回执 · 2026-11-10

接收端已核对 Git 完整提交 `aee14007e826ab4cd855af339802ef9cba21a83a`，并完成以下检查：

- 更新前备份 Windows 原有 17 个私密文件，以及本次将取消跟踪的 16 个旧文件；备份均经 SHA-256 校验。现有私密文件更新前后内容一致。
- Dropbox ZIP 整包校验、归档 CRC、清单校验及 32 个数据与支持文件的逐文件 SHA-256 全部通过；32 个文件已恢复到受 Git 忽略的路径，无覆盖冲突。
- 在 Windows 重新解析七年原始工作簿，219 条记录的题号、分值和实测值与恢复 CSV 逐项一致，年度公开覆盖摘要一致。原始 Mac 接收记录保持原样。
- Windows Python 3.13.13、openpyxl 3.1.5 下，13 项测试通过；公开数据检查通过。接收完成时工作树干净。
- Mac 缺少的 `data/private/2026_validation/2026_teacher_actuals.xlsx` 和 `data/private/cohort_calibration.csv` 在 Windows 已确认存在并完整保留；尚未反向同步至 Mac，也未重新运行旧审计。

详细校验与备份位置记录在本地忽略文件 `data/private/handoff_receipts/windows_20261110.json`，公开仓库不包含私密清单或逐题成绩。新模型训练仍未开始，训练机文件与环境状态仍为 UNKNOWN。下一步从小问数字化与映射、固定划分和同题基线开始；不把接收通过当作模型精度或 GPU 环境验证。
