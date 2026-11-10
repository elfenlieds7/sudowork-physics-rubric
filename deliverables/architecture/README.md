# 通用架构：一份内容源，多个生成视图

唯一内容源是 `local-training.data.json`：模块、组件来源、状态、要求、接口归属与输入输出、图的边及实施顺序。接口在 `interfaces` 中只定义一次；`owner` 指定负责模块，`related` 只建立引用，不复制契约。

`local-training.template.html` 仅维护页面样式与交互，不另写模块／接口事实。`local-training.html` 和 `local-training.mmd` 都由生成器输出，不直接手改。

在仓库根目录运行：

```text
python scripts/build_local_training_page.py --mermaid-js <mermaid.min.js 的本地路径>
```

若使用系统 Chrome，可增加 `--browser <Chrome 可执行文件路径>`；否则使用 Playwright 管理的 Chromium。依赖及 Mermaid 支持文件见 `docs/windows-handoff-20261109.md`。生成器检查模块、组件、API 和实施阶段之间的引用完整性。

当前页面含 9 个模块、6 份接口契约。图内点击、模块索引、详情选择器和实施阶段中的模块引用，都会定位到同一份模块定义；接口引用定位到其 `owner` 模块。打印时展开全部模块详情。

发布前核对图中文字、点选／键盘操作、移动端和公开数据检查；按 ShareOne skill 更新原分享的固定提交绑定，不另建链接或改成 main 自动跟随。
