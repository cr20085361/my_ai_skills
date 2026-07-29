---
name: cst-control-skill
title: CST Studio Suite Python Control
description: Use when an AI agent needs to connect to, open, create, save, inspect, or safely deliver CST Studio Suite 2026/SP2 projects through Python or the CST GUI, including installation discovery, exact-project selection, cst.interface/cst.results imports, close/reopen persistence checks, Chinese text encoding, model fingerprints, script execution, and automation failure diagnosis.
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
2. Prefer the CST-bundled Python at `<install>/Python/python.exe` when
   available.
3. Do not hard-code a drive letter in reusable scripts. Discover the install folder
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
enumerate the running environments and select the one whose open project path
exactly matches the requested `.cst`. Do not mutate the first PID merely because
it appears first.

## Persistence and delivery contract

Treat in-memory success and on-disk persistence as separate checks:

1. Resolve the exact target project path and confirm the active CST project
   matches it before mutation.
2. Record a backup/hash plus fingerprints for every protected domain.
3. Apply the smallest requested change.
4. Save, close, reopen, and read the changed state again. An in-memory API
   readback is not delivery evidence.
5. If `project.save()` returns without error but the file hash does not change
   or the reopened value reverts, use CST's native Save command in the GUI,
   wait for the modified marker to clear, then close and reopen once more.
6. Compare protected fingerprints and report exactly what changed.

For metadata-only work, protect parameter expressions and numeric values,
History, geometry, ports, monitors, lumped elements, units, and solver setup.
Read `references/persistence-encoding-and-fingerprints.md` before changing
parameter descriptions, notes, labels, or other text stored inside a `.cst`.

## Complex-operation execution contract

For Bend, boolean, transform, array, or coordinate-system work, keep the
automation transport deliberately simple:

1. Build or open a copy of the project, never the only validated source file.
2. Make one operation in CST's GUI when its History syntax is not already
   verified, then capture the exact generated History block.
3. Inject one named operation per `add_to_history` item and save immediately.
4. Reopen the project or change one parameter and rebuild before adding the
   next operation.
5. Report the output project path, latest History caption, and the tested
   parameter states.

This separates Python connection failures from CST geometry failures and keeps
complex modeling reproducible.

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
- Save appears successful but text reverts after reopening: use the native CST
  Save command and repeat the close/reopen verification.
- Chinese descriptions read back as mojibake through `cst.interface` while the
  CST GUI displays them correctly: treat the GUI as the presentation check and
  use the reversible GBK/Latin-1 normalization described in the persistence
  reference only for comparison. Never write the mojibake back to the model.
- CST hangs on startup: check license availability and whether an old modal
  dialog is waiting in CST.
- Result export fails: confirm the solver has completed and the result path
  exists.
