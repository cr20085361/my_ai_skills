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

### Reliable CST 2026 launch

For a new Microwave Studio frontend, prefer an explicit studio type:

```python
de = cst.interface.DesignEnvironment.new(options=["--m"])
```

Do not assume `--hide` registers a usable automation frontend on every CST
2026/SP2 installation. The first launch can take substantially longer than a
normal Python API call while CST acquires a license and registers the design
environment. Use a bounded startup timeout with progress reporting, then check
license availability, existing CST processes, and modal dialogs before retrying.

After connecting, inspect the actual `project.model3d` methods required by the
task (for example `Polygon3D`, `LoftCurves`, `Rebuild`, or
`full_history_rebuild`). CST installations and project types can expose
different automation surfaces; capability detection is stronger evidence than
an online example or an assumed wrapper method.

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

For a generated project, use deterministic, versioned output names and refuse
to overwrite a validated `.cst` by default. CST may create a sibling expanded
project directory and `Model.lok` while the file is open; treat these as runtime
cache, not delivery source. Save each successful named History block so a later
failure can be isolated to one stage.

## Automation failure channels

Do not treat "no Python exception" as success. Check all four channels:

1. API return values such as `Rebuild() is False`;
2. new entries from `project.get_messages()`;
3. expected model-tree or geometry changes;
4. frontend state, including a blocking modal dialog or a closed connection.

A History `Err.Raise` may produce `False` plus a visible modal instead of a
Python exception. Exercise such invalid states only in a disposable project and
behind an explicit diagnostic option. Validate the same contract in Python so
normal automated regressions do not deliberately block on expected UI errors.

### Recovery after a History error

When CST reports a History Error or says that model information is inconsistent
and a structure update is required, stop editing immediately. Capture the first
error text, the failing History caption, new Messages, and the current save
state before attempting another mutation.

1. Dismiss only the known error dialog and confirm no second modal remains.
2. Use CST's native structure-update/rebuild action on a disposable copy; do
   not guess an API replacement for a GUI-only recovery command.
3. Check the normal `Rebuild()` return, Messages, model-tree objects, and
   connection state after the update.
4. If recovery fails or the model remains inconsistent, close without relying
   on unsaved state, reopen the last verified saved copy, and isolate the next
   History item there.
5. After a successful recovery, save, close, reopen, and compare the protected
   fingerprints before resuming edits.

This prevents a parser or validation failure from being mistaken for a valid
partial model and prevents later edits from compounding inconsistent geometry.

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
  dialog is waiting in CST; when a hidden launch cannot register, retry a clean
  explicit Microwave Studio launch with `options=["--m"]`.
- A rebuild did not raise but the model is invalid: inspect the Boolean return,
  new CST messages, expected tree objects, and modal state.
- The automation connection closes during a dense rebuild: preserve the last
  saved stage, reopen a disposable copy, and prefer a regular `Rebuild()` for
  parameter regression before considering a full History rebuild.
- Result export fails: confirm the solver has completed and the result path
  exists.
