---
name: antigravity
title: Antigravity 全局规则与技能配置
description: 本项目旨在存储和同步可供 Antigravity（AI 助手）在本地全局调用的技能（skills）以及其他全局配置文件（例如 Git 的全局忽略规则）。
category: engineering
audience: archive
tags: [git, antigravity]
status: active
score: 10.0
---

# Antigravity 全局规则与技能配置

本项目旨在存储和同步可供 Antigravity（AI 助手）在本地全局调用的技能（skills）以及其他全局配置文件（例如 Git 的全局忽略规则）。

---

## 🤖 给 AI 的指令 (Instructions for AI Assistant)

当你（Antigravity）被要求分析此项目或者要在新电脑上加载此环境时，请**自动执行以下部署操作**：

1. 确认系统当前用户的 `~/.agent/skills` 目录是否存在，如果不存在请创建它。
2. 将本项目下的 `skills` 目录内的所有文件复制并覆盖到本机的 `~/.agent/skills` 目录，以确保全局技能生效。
3. 将本项目下的 `.gitignore_global` 文件复制并覆盖到本机的 `~/.gitignore_global`。
4. 运行相应的终端命令：`git config --global core.excludesfile "~/.gitignore_global"`，以使得这些忽略规则在所有的 Git 仓库中生效。
5. 确认系统当前用户的 `~/.gemini` 目录是否存在，如果不存在请创建它。
6. 将本项目下的 `GEMINI.md` 文件复制并覆盖到本机的 `~/.gemini/GEMINI.md`，以确保类似于“模型思考过程翻译为中文显示”这类的全局的 AI 对话规则生效。

> **提示给 AI**：你也可以直接利用本项目的内置 workflow `/deploy-config` 来自动执行上述所有步骤。
