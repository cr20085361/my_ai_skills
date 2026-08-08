---
name: cst-skills-retrospective
title: CST Skills Retrospective
description: Use when a user asks to review, summarize, distill, improve, strengthen, or synchronize CST-related skills or lessons learned, including Chinese requests combining CST with skills、复盘、总结、踩坑、经验、沉淀、补强、改进 or similar intent. Do not use for ordinary CST modeling, simulation, S-parameter analysis, or result summaries unless the user is explicitly asking to improve the reusable CST skills workflow.
category: engineering
audience: codex-project
tags: [cst, skill, retrospective, governance, validation, synchronization]
status: active
score: 10.0
---

# CST Skills Retrospective

Use this skill to turn evidence from completed CST work into durable improvements without forcing every task to produce a new rule.

## Canonical repository

Resolve the source repository in this order:

1. `MY_AI_SKILLS_REPO` when it is set.
2. `D:\AI_project\my_ai_skills` as the user-specific fallback.

Before continuing, verify that the selected directory contains `.pgrms.json`, `scripts/pgrms.py`, `source/custom`, and `source/families/cst/family.json`. Treat this repository as the only source of truth. Never copy an installed global skill back over its source.

## Trigger boundary

Use the retrospective workflow when CST is combined with an intent to review or improve reusable skills, workflows, lessons, pitfalls, or governance. Semantic matches are sufficient; exact phrases are not required.

Do not activate this workflow for:

- ordinary CST geometry creation or parameter adjustment;
- solver, S-parameter, far-field, or mesh result summaries;
- debugging whose requested outcome is only to fix the current model.

Those tasks continue to use the relevant modeling skills. Run this retrospective only when the user also wants reusable learning to be evaluated.

## Candidate gate

Read the task evidence and the relevant family manifest, `RULE.md`, references, scripts, and evals. Accept a candidate only when all of these are true:

1. It is reusable across projects, or it is a deterministic CST trap severe enough to justify prevention after one occurrence.
2. Existing skills do not already cover it adequately.
3. It can be expressed as an actionable rule, check, script, or evaluation.
4. The CST family ownership map identifies one clear owner.

Reject project-specific dimensions, names, incidental UI state, and speculative advice. Do not create content merely to make a retrospective appear productive.

If nothing passes the gate, report `本次没有值得补强的 CST skills 操作点` and stop without editing, compiling, or synchronizing anything.

## Approval gate

When candidates exist, present a compact proposal containing:

- evidence and reusable lesson;
- owning skill and target file type;
- intended behavioral change;
- regression or eval coverage;
- synchronization scope.

Wait for explicit user approval before writing. Approval of the retrospective workflow itself is not blanket approval for every future candidate batch.

## Source-first update

After approval, inspect Git status and preserve unrelated changes. If a target skill already has overlapping uncommitted edits, stop and request direction.

Place content according to its function:

- frequent mandatory workflow guidance in `RULE.md`;
- long explanations, compatibility tables, or cases in `references/`;
- deterministic repeated checks in `scripts/`;
- every behavior change in `evals/evals.json`.

Prefer improving the existing owner skill. Create another CST skill only when the workflow is independently triggerable and cannot fit any current owner.

## Validation and synchronization

Run, in order:

```text
python scripts/pgrms.py scan
python scripts/pgrms.py family validate cst
python -m pytest -q
python scripts/validate_repository.py
python scripts/pgrms.py sync-skills --family cst --apply
```

Use `--home <temporary-path>` before the real synchronization when changing deployment behavior. Verify the installed file trees against the fresh build manifest. Do not use the broad `deploy` command for a skills-only retrospective because it also manages unrelated global configuration.

Report the source diff, validation evidence, synchronization targets, backups, and a suggested commit message. Do not commit, tag, push, or create a release.

## Initial evidence batch

When the antenna taper incident is reviewed, evaluate these as candidates rather than assuming they must be written:

- parser-safe CST VBA identifiers and complete `If ... Then` guards;
- an explicit mapping between parameter semantics and physical coordinate endpoints;
- endpoint geometry measurements, orientation checks, and zero-change regression for tapers;
- structure update, rebuild, save, close, reopen, and persistence checks after History errors.

Route accepted items through the family ownership map and keep one canonical copy of each rule.
