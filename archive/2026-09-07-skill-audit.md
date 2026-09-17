# 技能清理与计划增强接入（2026-09-07）

## 结论与依据

本次评估的是技能的增量价值、触发成本和与当前工作方式的冲突，不是证明新模型可以替代全部技能。未定位到用户提及的 OpenAI 工程师原帖，因此不将“删除全部 Skills”当作官方结论。官方仍说明技能的按需加载和复用机制：[Build skills](https://learn.chatgpt.com/docs/build-skills)。

仓库原有 26 条规则，评分均为 10，使用次数均为 0；这不是有效的质量或使用证据。按源码、资源、编译筛选与本次用户需求作保守判断。对停用项保留源码、许可证和资源，不永久删除知识。没有进行跨模型效果 A/B 测试，也没有证据证明停用后所有任务质量不变。

## 全量处置清单

| 规则 | 处置 | 依据 |
| --- | --- | --- |
| algorithmic-art | 停用 | 已是 Codex archive；强制哲学文档再实现的流程不适合作为通用默认，保留创作资源供专项恢复 |
| canvas-design | 停用 | 已是 archive；保留字体和资源，当前视觉任务已有工具技能入口 |
| theme-factory | 停用 | 已是 archive；预设主题库有复用价值但不需作为默认工作流 |
| docx、pdf、pptx、xlsx | 停用 | 旧本地副本已是 archive，当前会话有对应官方文档工具技能；跨客户端需要旧工具时可恢复 |
| code-iteration-optimization-specialist | 停用 | 每次强制改版本文件名、逐行中文注释增加维护和 token 成本；通用迭代边界已有项目规范和 isolation guard |
| doc-coauthoring | 停用 | 通用写作能力与现有文档能力重叠，固定多轮询问和读者测试不宜每次执行 |
| skill-creator-cn | 停用 | 与已提供的系统 skill-creator 重叠；多层确认与当前自主实施偏好冲突；中文可作为语言偏好表达 |
| chinese-output-constraint | 精简、退出 Codex 默认编译 | 保留个人语言偏好供其他目标；移除强制内部思考展示和无关代码翻译要求 |
| frontend-design | 保留 | 有明确审美与文案偏好，并属于 Web UI 技能族；尚无质量对比证据支持拆除 |
| ui-ux-pro-max | 保留 | 本地搜索脚本和设计数据库属于外部知识资源，不由模型常识替代 |
| webapp-testing | 保留 | 有服务器生命周期工具与浏览器验证资源，维持 Web UI 闭环 |
| matlab | 保留 | MATLAB/Octave 区分、MAT 文件工具和版本相关资源有具体增量价值 |
| mcp-builder | 保留 | MCP 工具设计、参考实现与评测脚本仍有用途；未证明与 ChatGPT Apps 专用技能完全等价 |
| cst-control-skill | 保留 | 本机 CST 通道、版本、持久化与故障经验 |
| cst-history-macro-skill | 保留 | History/VBA 操作契约及工具资源 |
| cst-parametric-modeling | 保留 | 参数化耦合、重建与验证约束 |
| cst-advanced-geometry-operations | 保留 | 原生几何操作及拓扑顺序经验 |
| cst-antenna-paper-reproduction | 保留 | 论文证据、几何合同与复现检查 |
| cst-skills-retrospective | 保留 | 专用经验沉淀和同步职责，不在此次清理中修改已验证的 CST 体系 |
| installer-version-naming | 保留 | 明确个人安装包版本显示偏好，模型无法自行推断 |
| pyinstaller-external-script-bundling | 保留 | 外部解释器脚本随包交付的具体故障经验 |
| github-release-archiver | 保留 | 中文发布记录及可视化偏好；阶段确认较重，但本次未重新设计发布流程 |
| skill-family-governance | 保留 | 支撑两个现有技能族的依赖、知识归属和同步校验 |
| plan-enhancer | 新增 | 保留原生 Plan 与手动换模型流程，补充精简的交接约定 |

## 已实施的清理

- 10 项设置 `status: disabled`；这会使所有目标的默认编译排除它们。仅 `audience: archive` 原先只影响 Codex，不能代表所有目标已停用。
- 中文规则改为短偏好，同时修正本仓库 GEMINI.md。仍启用以服务非 Codex 目标；`archive` 在本项目表示 Codex 排除，不代表资源删除。
- 导入 `source/custom/productivity/plan-enhancer/RULE.md`、`agents/openai.yaml` 和 `evals/evals.json`。规则正文及两个资源文件与此前安装版本保持一致；RULE.md 增加管理字段。
- 重新生成 metadata、看板和 Codex 编译包。默认 Codex 条目从 19 降至 16；描述总字符从 5,333 降至 4,555，约减少 14.6%。这是本项目静态目录口径，不能代表会话总 token 或费用节省。
- 现有规则中 17 项 active、10 项 disabled；16 项进入 Codex 编译，中文偏好为另一目标的启用项。
- 从 `.codex/skills`、`.agents/skills`、`.agent/skills` 及本仓库 `.codex/skills` 按确切停用名称备份移出 25 个残留目录。备份位于 `C:/Users/62531/.pgrms-deploy-logs/skill-cleanup-20260907-220310`，`manifest.json` 记录原路径与备份路径。
- 只向三个个人技能根同步 plan-enhancer，更新已存在的中文规则副本；未全量同步，避免覆盖尚未回收到仓库的 CST 等本地版本。未安装缺失的其他技能，未改动插件、系统技能或无归属的旧目录。

## 验证与限制

清理前 36 项测试通过；清理后更新四处与旧目录/标题绑定的预期，36 项再次通过。包括新的计划技能默认编译、旧文档协作技能在 docs 标签下仍被排除、中文偏好继续生成 VS Code 指令。仓库验证通过：27 条规则、2 个技能族。范围检查确认 scripts 和 CST 源码未改；用户原有未跟踪 `.qoder/` 保留。

技能数量和源码审查并非模型表现测试。自动触发仍需新会话观察；不同客户端是否载入相同目录亦不等同。个人技能根中未纳入本仓库的旧名字、本地新版本及重叠安装保持原状，避免按相似名称误删。当前 sync-skills 不会自动删除停用项，也可能重装短中文偏好；本次清理不改动部署引擎。

## 后续维护与恢复

修改计划增强时编辑仓库 RULE.md，再编译并定向同步，不手工维护安装副本。AGENTS.md 的个人触发规则已在前一任务安装，属于独立配置，现有 sync-skills 不覆盖它。

恢复某项：将其 RULE.md 的 `status` 改回 `active`，按需恢复 audience，运行 scan、compile 和相关验证后定向部署；若要精确恢复本机旧版本，按备份 manifest 对应关系恢复目录。不要将整个备份目录放回技能发现根。

对保留项继续采取“出现实际失败再加规则”的方式维护；尤其 frontend-design、发布流程和 MATLAB 的长说明，下一轮应按真实任务收益决定删减，而不是按模型发布周期整体删除。
