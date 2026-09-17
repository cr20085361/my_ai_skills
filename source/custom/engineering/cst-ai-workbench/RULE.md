---
name: cst-ai-workbench
title: CST AI Workbench
description: Use the shared CST AI workbench to research antenna requirements or papers, create composable native parametric ModelPlans, validate geometry, deliver projects and reuse measured capabilities.
category: engineering
audience: codex-project
tags: [cst, antenna, workbench, mcp, model-plan]
status: active
score: 10.0
---

# CST AI Workbench

Distribution version: 0.5.0. Use the current MCP schema rather than stale copied scripts.

Use this skill when a local CST antenna project should use the shared workbench rather than direct ad-hoc scripts.

Before modeling, call `get_environment_status`. Register the current workspace if it is not listed. Submit only an operation that the server reports as supported, and set `project_id` on the job. Use the registered workspace for relative source paths; keep source projects protected.

After a task, query its job state and use the delivered artifact location. The workbench is modeling-only: do not request solver, post-processing, optimization, or result-reading actions.

For a manual or external-AI lesson, call `submit_experience` with the operation, symptom or successful behavior, applicability, and explicitly selected evidence. Mark the cause as a hypothesis unless a reproducible check validates it. Search experience before repeating an unfamiliar CST action.

Capabilities imported from another computer are references until `revalidate_imported_capability` completes its local CST evaluation. Do not describe them as active before that result.

## 中文参数说明（长期规则 zh-CN-v1）

今后通过该 MCP 建模，所有新生成参数的 `description` 固定使用简体中文，不因客户端、项目或资料语言改变。参数名、表达式和对象引用保留合法标识符。写清物理含义、方向、适用单位；模式参数说明各值含义，派生量说明几何关系。允许公式、X/Y/Z 和技术缩写，不声明未经仿真验证的性能变化。

提交前补齐说明，再调用 `validate_model_plan`。缺失、空白、纯英文和换行控制字符会被拒绝；按 `description_errors` 修正，不能用参数名作为占位说明。Schema 1.1 能力片段可在 `bindings.descriptions` 按片段原始输入参数名提供中文覆盖，展开后的全部参数都须合规，不改写历史能力修订或冻结测试。实际任务记录 zh-CN-v1，并检查参数重建与保存关闭重开后的说明一致性。旧任务仅保留原历史状态，重新提交须符合本规则。

## Generic modeling and source-driven design

1. Discover the environment and call `list_modeling_operations`. Separate implementation, dependency availability and local native validation. An implemented operation can still require an isolated trial. Certification is limited to the tested recipe and parameter range.
2. Register the actual workspace using project tools. The central state directory remains independent of it.
3. For uncertain operations, use `search_reference` in Chinese or English and `get_reference` for the located chapter. Register explicitly selected papers, manuals, drawings or client-researched URL extracts using `ingest_reference`. Network research and scanned-page interpretation use the client's available tools. If unavailable, explicitly use local-only research; do not invent online findings.
4. Consult the existing `cst-antenna-paper-reproduction`, `cst-parametric-modeling`, `cst-history-macro-skill` and `cst-advanced-geometry-operations` Skills for domain method. Their direct scripts do not bypass workbench task recording or authorize arbitrary History execution.
5. Call `get_operation_schema` and construct a schema 1.0 ModelPlan. Decompose the structure into objects and dependency-ordered steps; pin operation version 1.0.0. Declare units, independent parameters, derived expressions, constraints, materials, geometry assertions, regression states and a modeling budget. Never use CST/VBA object names such as `slot`, `solid`, `material` or `array` as parameters; use `slot_width`, for example. Parameter names are case-insensitive.
6. Record facts in `evidence.facts` with source ID and page/figure/URL locator. Distinguish published numbers, derivations, image estimates and engineering assumptions. Every reproduction parameter has `source_fact_id`. Product-internal structures unavailable in a manual are assumptions, not exact reproduction. Essential topology/feed uncertainties go in `evidence.unresolved` or `open_questions` and block execution until decided.
7. Use `validate_model_plan`; static passing is not native success. No arbitrary Python/VBA, solver, ports, boundary or monitor configuration is exposed. Unknown mapped commands are adapter gaps. Unsupported measurements must remain unverified.
8. Submit using `submit_model_plan` with project ID and a stable idempotency key. Poll `get_job`. Do not repeat uncertain actions. Deterministic jobs continue in their detached worker after client disconnection. Bounded exploration uses fresh isolated targets, at most the declared candidates and total execution time; repeated failure becomes a documented `needs_reasoning` case.
9. Inspect native dimension/volume/material/count checks, direct parameter rebuild and save/close/reopen evidence. Use delivered project files. From-performance models remain initial designs requiring user simulation. Geometry-contact/symmetry/section assertions lacking a native measuring adapter cannot count as passed.
10. Submit failure or successful-execution evidence to the experience tools. A verified project trial is not automatically a global capability. `propose_modeling_capability` requires an independently operator-frozen benchmark containing normal, boundary, negative and held-out cases. `evaluate_modeling_capability` runs native tasks; publication is automatic only after the independent evidence gate. The exploratory client cannot change frozen tests. Inspect `get_modeling_evaluation` and `list_modeling_releases`; reuse compatible releases through `get_modeling_release` and `submit_modeling_recipe`. Runtime/CST upgrades require new validation.

Large documents, History, logs and measurements stay in artifacts. Return concise evidence-linked summaries and clearly state untested ranges and unresolved measurements.

## Repository capability library and task closure

Before an unfamiliar operation, call `search_general_capabilities` by mechanism and operation, not only antenna family. Read a fixed revision with `get_general_capability`; imported evidence never inherits machine activation. Use `revalidate_general_capability` only for selected capabilities and inspect `get_general_evaluation`. Missing dependencies or external fixtures remain explicit.

Schema 1.1 client plans can contain capability call steps `{id, capability, bindings, component}` and registered checker revisions in `capability_guards`; the server expands them into schema 1.0 native plans and pins the revisions. Fragment bindings contain `parameters`, `objects` and optional `material` / `descriptions`. Do not load generated Python/VBA from repository files.

At task closure, call `claim_learning_events` with a stable client owner ID. Use selected event evidence to propose a class-level lesson via `submit_generalized_lesson`: problem_class, mechanism, variables, applicability, counterexamples, diagnosis, remedy, validation, existing_capability and cause_status. Preserve hypothesis status when the cause is not established. Successful execution alone does not establish a mechanism. A session interruption leaves events pending for another claim after the lease expires.

Prefer reusable parameter checks, operation-order guards and parametric fragments over one-model recipes. Supply cross-context normal, boundary, illegal and held-out tests; exploratory clients cannot freeze or change operator acceptance. Use lightweight text sources and measurements, never full CST projects or embedded Base64. If an original project is indispensable, describe it as external_fixture_required with its hash and preserve the exception.

Collection is automatic; network sync is explicit. Call `preview_library_sync` to report size, pending records and conflicts. Call `sync_capability_library` only when the user requests synchronization. Conflicting revisions remain separate; `resolve_library_conflict` creates a new merge revision needing verification. Do not auto-edit executor source or Skill rules from individual cases.
