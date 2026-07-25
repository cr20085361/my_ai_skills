# PGRMS - 个人全局规则与技能管理系统

PGRMS 用于集中存储、校验、编译和部署可供 Codex、Cursor、Windsurf、Cline、Antigravity/Gemini 与 VS Code Copilot 调用的本地规则与技能。

这个仓库面向代码代理与本地自动化场景，重点做了几件事：

- 统一维护 `source/` 下的原创规则与第三方规则
- 通过 `metadata.json` 与 `dashboard.html` 提供可检索、可视化的规则索引
- 支持面向不同 IDE/代理的多目标编译
- 支持项目级绑定与按标签筛选注入
- 支持全局部署，并区分 Antigravity/Gemini、VS Code Copilot 与 Codex 的落地目录

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

- CST Studio Suite 的 Python 控制与结果读取
- History List / VBA 记录式建模
- 保留参数的 CST 参数化建模
- 原生 Bend、Transform、Boolean、WCS 与复杂几何操作编排

## 发布历史

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
