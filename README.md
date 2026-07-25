# PGRMS - Personal Global Rules Management System

PGRMS stores, validates, compiles, and deploys local AI rules and skills for tools such as Codex, Cursor, Windsurf, Cline, Antigravity/Gemini, and VS Code Copilot.

The repository is optimized for safe coding-agent use: deployment is preview-first, generated and temporary artifacts are ignored, and tests only collect the repository's own test suite.

## What It Does

- Scans `source/custom/` and `source/registry/` into `metadata.json`.
- Compiles rules for Cursor, Windsurf, Cline, Antigravity/Gemini, and Codex.
- Supports project binding through `.pgrms.json` so only matching tagged skills are injected.
- Provides a static `dashboard.html` generated from metadata.
- Supports CST-related skills for Python control, History VBA modeling, and parametric CST workflows.
- Can deploy skills globally, but only when explicitly requested with `--apply`.

## Recommended Codex Workflow

For Codex programming sessions, use local validation and local skill output first:

```powershell
python scripts/pgrms.py scan
python scripts/pgrms.py compile --target codex
python -m pytest -q
python scripts/validate_repository.py
```

`compile --target codex` writes local skills to `dist/codex/skills` by default. When compiling for a bound project with `--path`, Codex skills are written to that project's `.codex/skills` directory.

Codex compilation only includes rules with `audience: codex-core` or `audience: codex-project`. Rules marked `archive` stay out of the generated Codex bundle.

For documentation-oriented skills such as `doc-coauthoring`, add matching project tags like `docs` or `writing`; they are no longer globally injected by default.

## Safe Deployment

Deployment is dry-run by default:

```powershell
python scripts/pgrms.py deploy
```

This scans and compiles, then prints the user-global targets that would be affected. It does not write `~/.agent`, `~/.agents`, VS Code prompts, `~/.gemini`, or global Git config.

To apply a real global deployment:

```powershell
python scripts/pgrms.py deploy --apply
```

To test global deployment without touching your real HOME:

```powershell
python scripts/pgrms.py deploy --apply --home .\temp_test_project\fake_home
```

Wrappers follow the same policy:

```powershell
.\deploy.ps1
.\deploy.ps1 -Apply
```

```bash
./deploy.sh
./deploy.sh --apply
```

Real deployments create logs under `.pgrms-deploy-logs` in the selected HOME and back up overwritten skill directories before replacement.

## Core Commands

```powershell
python scripts/pgrms.py scan
python scripts/pgrms.py list --sort score
python scripts/pgrms.py compile --target all
python scripts/pgrms.py compile --target codex
python scripts/pgrms.py bind --path <project> --tags python,git --ide codex --force
python scripts/pgrms.py deploy
python scripts/pgrms.py deploy --apply
```

## Repository Quality Gates

```powershell
python -m py_compile scripts\pgrms.py scripts\compiler.py scripts\utils.py scripts\dashboard.py scripts\evaluator.py scripts\fetcher.py scripts\validate_repository.py
python -m pytest -q
python scripts\validate_repository.py
```

CI runs the same checks on push and pull request.

## Rule Authoring Contract

Every `RULE.md` should include normalized frontmatter:

```markdown
---
name: example-skill
description: Short trigger-oriented description.
category: engineering
audience: codex-project
tags: [python, testing]
status: active
score: 10.0
---
```

Rule names must be lowercase kebab-case. Empty `tags` are not treated as global rules during project-bound compilation; use `general` explicitly for rules that should always load.

Use `audience: codex-core` for a very small set of always-allowed Codex rules, `audience: codex-project` for project-scoped rules, and `audience: archive` for rules that should not enter the default Codex bundle.

## CST Skills

The main branch now also carries these CST-focused engineering skills:

- `cst-control-skill`
- `cst-history-macro-skill`
- `cst-parametric-modeling`

These cover CST Studio Suite Python control, reproducible History/VBA modeling, and parameter-preserving CST workflows.

## Release History

### v1.3.0 - 2026-07-25

- Added the three CST engineering skills listed above.
- Refreshed repository metadata and dashboard generation inputs.
- Consolidated the former `release-v1.1.2` branch back into `main` so ongoing maintenance happens on a single branch.

### v1.2.0 - 2026-06-23

- Hardened Codex skill governance and deployment behavior.
- Added dry-run-first deployment, project-local Codex output, and repository validation paths.

### v1.1.2 - 2026-06-11

- Added repository-level GitHub release archiver instructions.

## Branching Policy

This repository is now managed from `main` only. Release and maintenance work should be merged back into `main` instead of being kept on long-lived side branches.
