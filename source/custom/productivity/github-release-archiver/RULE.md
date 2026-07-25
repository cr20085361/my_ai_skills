---
name: github-release-archiver
description: 约束并自动执行 GitHub 版本存档流程步骤。当用户提到“执行 GitHub 存档步骤”、“进行版本归档”、“发布新版本 Release”、“打 Tag 归档”、“项目打包封存”，或需要自动生成/更新带可视化架构图（如 Mermaid 流程图、思维导图）的项目 README 文档时激活。
category: productivity
audience: codex-project
tags: [git, github, release]
status: active
score: 10.0
---

## 💡 核心定位与原则

本技能旨在帮助用户以高度标准化的步骤对 GitHub 项目进行阶段性归档（Release/Tag）。它通过约束前置检查、自动提取更新日志、语义化版本管理、**强制进行文档可视化渲染**，确保每一个被归档的版本都具备清晰的架构、运行逻辑和迭代线索，实现“一眼看懂项目”。

---

## 🛠️ 兼容性与先决条件

- **运行环境**：必须在有效的 Git 仓库根目录或其子目录中运行。
- **必要工具**：需可调用本地 `git` 命令行。若要进行远程 GitHub Release 部署，用户需配置好 GitHub 远程推送权限（如 SSH Key 或 Access Token），或使用 `gh` CLI（如有）。

---

## 🏃‍♂️ 执行流程约束（五阶段）

一旦触发此技能，必须严格按照以下五个阶段逐步执行，每一步完成后均需与用户进行简要反馈确认：

### 阶段 1：前置体检（Sanity Check）
1. **仓库有效性**：运行 `git rev-parse --is-inside-work-tree`。若不是 Git 仓库，礼貌告知用户并终止流程。
2. **工作区状态**：运行 `git status --porcelain`。
   - 若有未提交的修改，向用户发出警示，列出这些修改，并询问：“当前工作区不干净，建议提交或暂存后再进行版本归档。是否忽略并强制继续？”
3. **主分支校验**：运行 `git branch --show-current`。
   - 检查是否在 `main` 或 `master` 等生产发布分支。如果不是，友情提醒用户，确保用户明确知晓正在非主分支上打 Tag。

### 阶段 2：Git Commit 追溯与 Changelog 生成
1. **定位上一次版本**：运行 `git describe --tags --abbrev=0` 获取最新的 Git Tag。
   - 如果不存在任何历史 Tag，则默认追溯至首个 Commit：`git log --oneline --reverse`。
2. **提取提交日志**：运行 `git log <last_tag>..HEAD --oneline`（若无历史 Tag，则直接获取所有 log），提取出自上个版本以来的所有提交记录。
3. **编写规范中文 Changelog**：根据提取出的 Commit 信息，进行智能分类整理，输出结构化的中文更新日志：
   - 🚀 **新特性 (Features)**
   - 🐛 **问题修复 (Bug Fixes)**
   - ⚡ **性能与优化 (Performance & Refactoring)**
   - 📝 **文档变更 (Documentation)**
   - 展示给用户看，并支持用户进行微调。

### 阶段 3：语义化版本计算与 Tag 生成
1. **建议新版本号**：基于 Changelog 的改动幅度和当前的语义化版本（Semantic Versioning）规则，向用户推荐下一个版本号：
   - 若包含重大不兼容变更（Breaking Change） → 升级主版本号（Major，如 `v1.2.3` -> `v2.0.0`）
   - 若包含新特性且向下兼容 → 升级次版本号（Minor，如 `v1.2.3` -> `v1.3.0`）
   - 若仅包含 Bug 修复或日常优化 → 升级修订号（Patch，如 `v1.2.3` -> `v1.2.4`）
2. **打 Tag**：在用户确认版本号后，准备在本地执行：
   `git tag -a <version_name> -m "Release <version_name>: <brief_summary>"`

### 阶段 4：文档深度可视化渲染（核心特色）
为了确保项目“一眼看清”，必须为项目创建或更新 `README.md`。该文档必须包含以下三个维度的可视化图表（使用 **Mermaid** 格式嵌入）：

#### 1. 架构一眼清（Architecture Visualization）
* **展示形式**：系统模块图、类图或思维导图。
* **内容要求**：清晰体现项目有哪些核心文件夹/模块，它们之间是如何分层和交互的。

#### 2. 逻辑一眼清（Runtime & Logic Flow）
* **展示形式**：流程图（Flowchart）或时序图（Sequence Diagram）。
* **内容要求**：直观展示项目启动后，数据的输入、处理、输出的完整核心运行生命周期。

#### 3. 迭代一眼清（Iteration History）
* **展示形式**：时间线图（Timeline）或甘特图/演进图。
* **内容要求**：列出核心版本节点（如 v1.0.0 骨架搭建，v1.1.0 引入某特性，当前版本的定位等），展示迭代演进脉络。

> [!IMPORTANT]
> **Mermaid 语法防崩溃红线约束**：
> 1. 所有节点标签中的中文、括号、特殊字符，**必须使用双引号包裹**。例如，使用 `A["用户输入 (Prompt)"]`，严禁使用 `A[用户输入 (Prompt)]`。
> 2. 避免在节点名称中直接使用 `[` `]` `(` `)` `"` 等控制字符，如果必须使用，需使用转义或 HTML 实体。
> 3. 连接线描述若包含空格，线型两端必须加双引号，如 `A -->|"/deploy-config 触发"| B`。
> 4. 生成完毕后，在当前上下文中对 Mermaid 代码块进行静默语法扫描，确保不存在未闭合的括号。

展示生成的 `README.md` 预览（特别是 Mermaid 代码块），供用户审阅。

### 阶段 5：GitHub 远端同步与 Release 封存
1. **推送本地修改与 Tag**：
   - 提交更新后的 `README.md` 和 `Changelog` 到当前分支：
     `git add README.md` (如有单独 Changelog 文档则一并 add)
     `git commit -m "docs: update README with visualization for <version_name>"`
   - 推送代码到远端：`git push origin <current_branch>`
   - 推送本地 Tag 到远端：`git push origin <version_name>`
2. **GitHub Release 线上存档**：
   - 如果本地配置了 `gh` CLI 命令行工具，则直接使用命令行创建：
     `gh release create <version_name> --title "Release <version_name>" --notes "<changelog_content>"`
   - 若无命令行工具，则协助生成完整的 **GitHub Release 发布指南草稿**，提供可以直接一键复制的 Markdown 内容，并给出浏览器创建 Release 存档的快速链接（`https://github.com/<owner>/<repo>/releases/new?tag=<version_name>`）。

---

## 💬 交互示例与提问模板

* *在前置检查发现未提交修改时*：
  > “🚨 **工作区体检报告**：我发现您当前还有未提交的本地修改：
  > `[修改列表]`
  > 建议您先进行 Commit。您是希望我先帮您把这部分修改提交为草稿，还是直接强制忽略并继续存档流程？”
  
* *在生成 Mermaid 图表供用户审阅时*：
  > “📊 **README 可视化图表已就绪！**
  > 我为您在 `README.md` 中设计了三张 Mermaid 架构和逻辑图，分别是一眼看清架构的模块图、一眼看清启动与运行逻辑的流程图、以及记录本次迭代演进的时间线。
  > 
  > 您可以复制下方代码在编辑器中预览。是否有细节需要我微调，或者咱们直接进入推送到 GitHub 的步骤？”
