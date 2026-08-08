---
name: skill-family-governance
title: Skill Family Governance
description: Use when a user asks to review, strengthen, coordinate, or synchronize a managed skill family based on completed work, reusable lessons, workflow gaps, ownership, or deployment behavior. Do not use for ordinary task execution or a one-off skill edit that does not affect a family.
category: productivity
audience: codex-project
tags: [skill, governance, family, validation, synchronization]
status: active
score: 10.0
---

# Skill Family Governance

Turn evidence from completed work into deliberate, reversible improvements to a managed skill family.

## Scope gate

Use this skill only when the request concerns a reusable lesson, shared workflow, ownership boundary, dependency edge, evaluation, or deployment rule for an existing skill family.

Do not create a family merely because several skills share tags, a category, or a toolchain. A candidate must have a stable end-to-end workflow, clear topic ownership, and a deployment boundary that can be checked.

## Candidate and approval gates

Before writing, inspect the family manifest, member RULE.md files, references, scripts, evals, test coverage, and the source diff. Accept a change only when it is reusable across tasks, not already covered by the owner, actionable as a rule/check/eval, and assigned to one clear owner.

Present the evidence, owner, behavioral change, regression coverage, and synchronization scope. Wait for explicit user approval before modifying skills, manifests, or deployment state.

## Source-first workflow

Treat the repository source as canonical. Preserve unrelated worktree changes. Keep frequent mandatory guidance in the owner RULE.md, detailed cases in references, deterministic checks in scripts, and every behavior change in evals.

Use `source/families/<family-id>/family.json` only for members, dependencies, ownership, and governance. Do not duplicate member guidance in the manifest.

## Family acceptance checklist

Before synchronization, verify:

1. Every family member has a non-empty `evals/evals.json` whose `skill_name` matches the member.
2. Dependencies are acyclic and reflect actual handoffs, not merely similar tags.
3. Every owned topic has one owner; shared governance may own only the family-governance topic.
4. An explicit Codex deployment will include every member; archive-only members must be reclassified deliberately or kept out of that family.
5. The family has only the members needed for the workflow. Two-member closed loops are valid; unrelated skills are not filler.

## Validation and synchronization

Run the focused family validation, the relevant eval/test suite, repository validation, and a dry-run before any real synchronization:

```text
python scripts/pgrms.py family validate <family-id>
python -m pytest -q
python scripts/validate_repository.py
python scripts/pgrms.py sync-skills --family <family-id>
```

Use `--apply` only after the dry-run and explicit user approval. Do not commit, tag, push, or create a release unless separately requested.
