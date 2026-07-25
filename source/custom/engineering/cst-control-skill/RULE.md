---
name: cst-control-skill
title: CST Studio Suite Python Control
description: Use when an AI agent needs to connect to, open, create, save, or inspect CST Studio Suite 2026/SP2 projects through Python, including CST installation discovery, cst.interface/cst.results imports, script execution, and automation failure diagnosis.
category: engineering
audience: codex-project
tags: [cst, python, electromagnetic, antenna, automation, parametric-modeling]
status: active
score: 10.0
---

# CST Control Skill

Use this skill before generating CST modeling code. The goal is to make the CST
control channel repeatable so the agent can focus on geometry and RF intent.

## Baseline

1. Work on Windows with CST Studio Suite 2026 SP2.
2. Prefer the CST-bundled Python at:
   `F:\EDA\CST Studio Suite 2026\Python\python.exe`
   when available.
3. Do not hard-code that path in reusable scripts. Discover the install folder
   from `CST_STUDIO_SUITE_2026`, `CST_INSTALL_DIR`, or the Windows uninstall
   registry key.
4. Add `<install>/AMD64/python_cst_libraries` to `sys.path` before importing
   `cst` if the Python process did not already get that path from CST.

## Standard Commands

From the project root:

```powershell
& '<CST_INSTALL>\Python\python.exe' scripts\cst_env_check.py
& '<CST_INSTALL>\Python\python.exe' scripts\create_minimal_brick.py --project .\test.cst
& '<CST_INSTALL>\Python\python.exe' scripts\create_patch_antenna.py --project .\test.cst
& '<CST_INSTALL>\Python\python.exe' scripts\create_saddle_lens_demo.py --project .\test.cst --nx 7 --ny 7
```

Use `--cst-install "<folder>"` only when auto-discovery fails.

## Python Control Pattern

```python
from pathlib import Path

from cst_common import ensure_cst_python_path, open_or_create_mws, add_history

ensure_cst_python_path()
de, prj = open_or_create_mws(Path("test.cst"))
prj.model3d.add_to_history("AI operation name", "... CST VBA commands ...")
prj.save(str(Path("test.cst").resolve()))
```

Use `DesignEnvironment.connect_to_any_or_new()` when you are allowed to open or
reuse CST. If several CST frontends are running and connection is ambiguous,
start from a clean CST session or pass the project path explicitly.

## Result Reading

Use `cst.results.ProjectFile` after a solver run when result data exists:

```python
from cst.results import ProjectFile

project = ProjectFile("test.cst", allow_interactive=True)
item = project.get_3d().get_result_item(r"1D Results\S-Parameters\S1,1")
```

If the result path fails, inspect the CST result tree in the GUI and update the
path; do not guess silently.

## Failure Checklist

- `ModuleNotFoundError: cst`: run CST-bundled Python or add
  `<install>/AMD64/python_cst_libraries`.
- `running_design_environments()` returns empty while CST is visible: the
  frontend may not be registered for automation in the current session; use
  `connect_to_any_or_new()` or open the target project through the script.
- Project opens but history is not visible: ensure commands are sent through
  `model3d.add_to_history(title, vba)`, then save.
- CST hangs on startup: check license availability and whether an old modal
  dialog is waiting in CST.
- Result export fails: confirm the solver has completed and the result path
  exists.
