---
name: project-version-manager
title: 项目版本迭代管理
description: 在完成项目功能、修复、配置或文档迭代后，依据兼容性更新语义化版本并维护可跨会话追溯的累计迭代次数。不要用于纯调查、规划、未完成工作或仅执行同版本发布。
category: engineering
audience: codex-core
tags: [versioning, semver, iteration, release, project-management]
status: active
score: 10.0
---

# 项目版本迭代管理

在一次有效修改完成且相关验证通过后，维护项目版本和累计迭代次数。输出格式为 `v主.次.修订 · 第 N 次迭代`；版本表达影响范围，次数表达启用本规则后的已完成迭代数。

## 适用边界

- 只在实际修改已完成、验证已通过且本次工作不是同一版本的发布、同步或发布文档生成时使用。
- 调查、规划、无文件或行为变化、失败工作和同一任务中的调试/补测不登记。
- 同一任务只创建一个稳定的 `iteration_id`。重复运行登记命令必须复用该 ID，绝不能增加第二次。
- 不替项目猜测历史次数。首次接入既有项目时以当前版本建立零次基线；新项目首次有效交付使用 `v1.0.0 · 第 1 次迭代`。

## 判断与编号

按用户可见行为和兼容性判断，不按文件数或代码行数判断。混合改动采用最高级别。

| 级别 | 条件 | 示例 |
| --- | --- | --- |
| `patch` | 兼容的修复、优化、独立文档或配置改进 | `v1.2.9` → `v1.2.10` |
| `minor` | 向下兼容的新能力或明显功能扩展 | `v1.2.10` → `v1.3.0` |
| `major` | 不兼容接口、数据格式或使用方式，需要迁移 | `v1.3.4` → `v2.0.0` |

标准版本号不以 9 为上限。`v1.2.9` 的下一个修订版是 `v1.2.10`。现有预发布版本、项目自己的版本文件和发布策略先调查后遵循；不要用常规 bump 覆盖它们。脚本遇到预发布版本时要求显式提供下一个版本。

## 执行流程

1. 查找项目已有版本源（例如 package manifest、构建配置、`VERSION`），核对本次实际差异与验证结果。没有版本源时由根目录 `.iteration-version.json` 作为唯一版本源。
2. 为本次任务生成并保留一个 UUID 作为 `iteration_id`；先运行脚本 `preview`，记录预览时的旧版本，再写入项目版本源。项目版本源显示格式遵循自身约定，台账统一使用带 `v` 的版本。
3. 用预览时的旧版本运行 `record --verified`，随后核对项目版本源与台账 `current_version` 一致。台账通过原子替换写入；相同 ID 的相同记录会返回 `reused`，字段冲突会报错。
4. 报告旧版本、新版本、累计次数、级别、判断依据和验证结果。提交、推送、Tag、Release 仅在当前任务已授权时执行。

## 脚本

脚本位于 `scripts/version_ledger.py`，无需第三方依赖。常规既有项目示例：

```text
python scripts/version_ledger.py preview --project <项目根目录> --current-version v1.2.9 --level patch
python scripts/version_ledger.py record --project <项目根目录> --current-version v1.2.9 --level patch --iteration-id <UUID> --summary "修复导入失败" --verification "python -m pytest -q" --verified
```

新项目首次交付使用 `--new-project --level initial`。若项目处于预发布版本或有自己的编号策略，先确定目标版本，再以 `--next-version` 显式传入。不要让发布归档再次递增：已有台账记录的迭代发布当前 `current_version` 即可。
