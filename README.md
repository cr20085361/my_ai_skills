# PGRMS - 个人全局规则与技能管理系统

PGRMS 用于集中存储、校验、编译和部署可供 Codex、Cursor、Windsurf、Cline、Antigravity/Gemini 与 VS Code Copilot 调用的本地规则与技能。

这个仓库面向代码代理与本地自动化场景，重点做了几件事：

- 统一维护 `source/` 下的 23 条原创规则（design 5 / engineering 10 / productivity 8）
- 通过 `metadata.json` 与 `dashboard.html` 提供可检索、可视化的规则索引
- 支持面向不同 IDE/代理的多目标编译
- 支持项目级绑定与按标签筛选注入
- 支持全局部署，并区分 Antigravity/Gemini、VS Code Copilot 与 Codex 的落地目录

## 架构一眼清

```mermaid
graph TB
    subgraph SRC["source/ 规则源"]
        D["design/ (5)"]
        E["engineering/ (10)"]
        P["productivity/ (8)"]
    end

    subgraph TOOLCHAIN["scripts/ 工具链"]
        SCAN["pgrms.py scan"]
        COMPILE["compiler.py compile"]
        EVAL["evaluator.py evaluate"]
        DEPLOY["pgrms.py deploy"]
        DASH["dashboard.py"]
    end

    subgraph OUTPUT["产物输出"]
        META["metadata.json"]
        BOARD["dashboard.html"]
        DIST["dist/ 多目标编译"]
    end

    subgraph TARGETS["部署目标"]
        CODEX["~/.codex/skills"]
        AGENT["~/.agent/skills"]
        AGENTS["~/.agents/skills"]
        GEMINI["~/.gemini/GEMINI.md"]
        VSCODE["VS Code prompts"]
    end

    SRC --> SCAN --> META
    META --> COMPILE --> DIST
    META --> DASH --> BOARD
    DIST --> DEPLOY
    DEPLOY --> CODEX
    DEPLOY --> AGENT
    DEPLOY --> AGENTS
    DEPLOY --> GEMINI
    DEPLOY --> VSCODE
```

## 逻辑一眼清

```mermaid
flowchart LR
    A["scan 扫描源目录"] --> B["metadata.json 索引"]
    B --> C{"compile 编译"}
    C -->|"单文件目标"| D["Cursor / Windsurf / Cline"]
    C -->|"目录目标"| E["Antigravity / Codex"]
    B --> F["evaluate 健康评估"]
    F --> G["dashboard.html 看板"]
    E --> H{"deploy 部署"}
    H -->|"--apply"| I["全局技能目录同步"]
    H -->|"默认 dry-run"| J["仅展示部署计划"]
    K["bind 项目绑定"] -->|".pgrms.json 标签过滤"| C
```

## 迭代一眼清

```mermaid
timeline
    title PGRMS 版本演进
    v1.0.0 : 骨架搭建
           : 基础 scan/compile/deploy 工具链
    v1.1.0 : VS Code Copilot 全局技能同步
           : 中文指令部署
    v1.2.0 : Codex 技能治理与部署强化
           : 预演模式与仓库验证
    v1.3.0 : 新增 CST 工程技能
           : 合并 release 分支至 main
    v1.4.0 : CST 增强（4 技能）
           : Codex 全局部署补齐
    v1.4.1 : 技能库清理（27→21）
           : 命名规范修复与广告移除
    v1.5.0 : 新增安装包版本命名规范
           : 3 个外部技能同步至上游最新
    v1.5.1 : 新增 PyInstaller 外部脚本打包模式
    v1.6.0 : CST 四技能实战增强
           : 持久化验收、参数契约与双支路旋转
```

## 项目作用

- 扫描 `source/custom/` 与 `source/registry/`，重建规则索引 `metadata.json`
- 编译生成适用于 Cursor、Windsurf、Cline、Antigravity/Gemini 与 Codex 的目标产物
- 通过 `.pgrms.json` 绑定项目技术栈，仅向目标项目注入匹配标签的规则
- 生成仓库看板 `dashboard.html`
- 内置面向 CST 的工程技能，覆盖 Python 控制、History VBA 建模、参数化建模与复杂几何原生操作

## 推荐的 Codex 工作流

```powershell
python scripts/pgrms.py scan
python scripts/pgrms.py compile --target codex
python -m pytest -q
python scripts/validate_repository.py
```

默认情况下，`compile --target codex` 会把 Codex 技能输出到 `dist/codex/skills`。如果使用 `--path` 绑定某个项目，则会输出到该项目的 `.codex/skills` 目录。

Codex 编译默认只纳入 `audience: codex-core` 或 `audience: codex-project` 的规则；`archive` 规则不会进入默认 Codex 技能包。

## 全局部署

预演模式不会写入用户环境，只会扫描、编译并展示部署计划：

```powershell
python scripts/pgrms.py deploy
```

执行真实全局部署：

```powershell
python scripts/pgrms.py deploy --apply
```

部署完成后，会把产物同步到以下位置：

- `~/.agent/skills`
- `~/.agents/skills`
- `~/.codex/skills`
- `~/.gemini/GEMINI.md`
- `~/.gitignore_global`
- VS Code Copilot 用户级 prompts 目录

如需在隔离环境中测试：

```powershell
python scripts/pgrms.py deploy --apply --home .\temp_test_project\fake_home
```

封装脚本：

```powershell
.\deploy.ps1
.\deploy.ps1 -Apply
```

```bash
./deploy.sh
./deploy.sh --apply
```

真实部署会在目标 HOME 下生成 `.pgrms-deploy-logs` 日志目录，并在覆盖已有技能前自动备份。

## 核心命令

```powershell
python scripts/pgrms.py scan
python scripts/pgrms.py list --sort score
python scripts/pgrms.py compile --target all
python scripts/pgrms.py compile --target codex
python scripts/pgrms.py bind --path <project> --tags python,git --ide codex --force
python scripts/pgrms.py deploy
python scripts/pgrms.py deploy --apply
```

## 仓库质量闸门

```powershell
python -m py_compile scripts\pgrms.py scripts\compiler.py scripts\utils.py scripts\dashboard.py scripts\evaluator.py scripts\fetcher.py scripts\validate_repository.py
python -m pytest -q
python scripts\validate_repository.py
```

CI 会在推送和拉取请求中运行同等校验。

## 规则编写约定

每个 `RULE.md` 都应包含规范化 frontmatter，例如：

```markdown
---
name: example-skill
description: 用于触发该技能的简短说明
category: engineering
audience: codex-project
tags: [python, testing]
status: active
score: 10.0
---
```

约束建议如下：

- `name` 使用小写 `kebab-case`
- `category` 仅使用 `design`、`engineering`、`productivity`、`registry`
- `audience` 仅使用 `codex-core`、`codex-project`、`archive`
- `tags` 使用内联列表语法

## CST 技能

当前主分支已纳入以下 CST 工程技能：

- `cst-control-skill`
- `cst-history-macro-skill`
- `cst-parametric-modeling`
- `cst-advanced-geometry-operations`

它们分别覆盖：

- CST Studio Suite 的精确工程连接、Python 控制、结果读取和关闭重开持久化验收
- History List / VBA 记录式建模，以及参数创建与描述元数据修改的隔离处理
- 带参数契约、有效边界、动态对象集合和多状态回归的 CST 参数化建模
- 原生 Bend、Transform、Boolean、WCS、双支路枢轴旋转和渐变间隙体编排

统一的 CST 操作闭环如下：

```mermaid
flowchart LR
    C1["精确连接目标工程"] --> C2["建立副本和保护指纹"]
    C2 --> C3["录制不确定的原生 History"]
    C3 --> C4["执行最小范围修改"]
    C4 --> C5["多参数状态重建"]
    C5 --> C6["测量实际几何与端点"]
    C6 --> C7["使用 CST 原生保存"]
    C7 --> C8["关闭并重开工程"]
    C8 --> C9["执行指纹回归"]
```

## 发布历史

### v1.6.0 - 2026-07-29

- 增强 `cst-control-skill`：移除安装盘符假设，增加目标工程精确匹配、保存持久化验收、原生保存回退、模型指纹保护和中文读回安全核验
- 增强 `cst-history-macro-skill`：区分参数创建与描述元数据修改，使用 `SetParameterDescription` 保持表达式、数值、顺序和依赖关系不变
- 增强 `cst-parametric-modeling`：加入参数契约、零变化/标称/大小值/非法状态回归矩阵、实际几何测量、动态对象集合和耦合结构联动规则
- 增强 `cst-advanced-geometry-operations`：加入双 Boom 绕馈电端内边缘对称外张、渐变间隙体、尾部负载和馈电接触的通用操作模式
- 新增 2 份 CST 持久化与复杂几何参考资料，并为 4 个技能各加入 3 条真实请求回归用例（共 12 条）

### v1.5.1 - 2026-07-26

- 新增 `pyinstaller-external-script-bundling` 技能：PyInstaller 打包外部解释器脚本的必备模式（CST/MATLAB worker 路径解析、`--add-data`、`_MEIPASS` 双模式兼容）

### v1.5.0 - 2026-07-26

- 新增 `installer-version-naming` 技能：离线安装包版本命名规范（程序名含版本号、六处一致、Inno Setup / NSIS 模板）
- 同步 `frontend-design` 至上游 v1.1.0（anthropics/claude-code）：全新两遍设计流程、反 AI 默认风格校准、UX 文案指导
- 同步 `matlab` 至上游 v1.1（K-Dense-AI, 2026-07-23）：安全边界、R2026a 钉定、7 步工作流、Python 互操作
- 同步 `ui-ux-pro-max` 至上游 v2.11.0（nextlevelbuilder）：84 styles / 192 palettes / 22 stacks、设计系统与表盘调节

### v1.4.1 - 2026-07-26

- 清理 6 个无效/低价值技能（brand-guidelines、internal-comms、web-artifacts-builder、skill-creator、antigravity、slack-gif-creator），技能库从 27 精简至 21
- 修复 `optimization_specialist` 目录命名为连字符规范（`code-iteration-optimization-specialist`）
- 移除 matlab 技能中嵌入的第三方商业广告
- README 新增三张 Mermaid 可视化图表（架构/逻辑/迭代）

### v1.4.0 - 2026-07-25

- 用增强版内容更新 `cst-control-skill`、`cst-history-macro-skill`、`cst-parametric-modeling`
- 新增 `cst-advanced-geometry-operations`，并纳入原生 Bend 参考资料
- 全局部署流程补齐 `~/.codex/skills` 同步路径

### v1.3.0 - 2026-07-25

- 新增 3 个 CST 工程技能
- 刷新规则索引与看板生成输出
- 将原 `release-v1.1.2` 分支合并回 `main`，后续统一在主分支维护

### v1.2.0 - 2026-06-23

- 强化 Codex 技能治理与部署行为
- 增加默认预演部署、项目本地 Codex 输出与仓库验证路径

### v1.1.2 - 2026-06-11

- 新增仓库级 GitHub 发布归档说明

## 分支策略

本仓库现已统一由 `main` 管理。后续发布、维护和规则更新均应直接落在 `main`，不再保留长期存在的发布分支。
