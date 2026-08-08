---
name: cst-history-macro-skill
title: CST History List and VBA Modeling
description: Use when an AI agent must create or modify CST Studio Suite 2026 geometry or parameter metadata through History List/VBA snippets and Python, including CST parameters and descriptions, materials, primitives, curves, lofts, boolean operations, transforms, imports, rebuilds, and History debugging.
category: engineering
audience: codex-project
tags: [cst, history-list, vba, python, geometry, parametric-modeling]
status: active
score: 10.0
---

# CST History Macro Skill

Use CST's History List as the source of truth for modeling commands. Python is
the transport layer; CST VBA history commands are the modeling layer.

## Workflow

1. If a CST command is uncertain, perform it once in the CST GUI.
2. Open the History List and copy the generated command block.
3. Replace fixed dimensions with CST parameters when the model needs sweeps.
4. Inject the block from Python:

```python
prj.model3d.add_to_history("meaningful operation title", vba_block)
```

5. Save the `.cst`, reopen or rebuild if needed, and inspect the model tree.

For recorded snippets saved as files, use:

```powershell
& '<CST_INSTALL>\Python\python.exe' scripts\apply_history_snippet.py --project .\test.cst --title "AI recorded operation" --snippet examples\history_snippets\operation.vba --close
```

## Parameter Descriptions

Separate one-time parameter creation from replayable History initialization.
When a parameter bootstrap is stored in History, use
`MakeSureParameterExists` followed by `SetParameterDescription`:

```vb
MakeSureParameterExists "sub_h", "1.6"
SetParameterDescription "sub_h", "介质基板厚度，增大时馈线与贴片离地高度增加。"
MakeSureParameterExists "patch_w", "30"
SetParameterDescription "patch_w", "贴片沿 X 方向的宽度，主要影响谐振频率和输入阻抗。"
```

This preserves a value changed by Parameter Sweep, Tuning, or Python when the
History is replayed. `StoreParameterWithDescription` remains suitable for a
one-time external creation step that is not itself replayed; do not place it in
a rebuildable bootstrap block when it can overwrite the current value.

Good descriptions state:

- Which physical part or setup item the parameter controls.
- The unit or implied unit when helpful.
- What happens when the value increases or decreases.

Avoid putting one-off project notes in this skill. Keep project-specific
parameter names and formulas in that project's own documentation.

## History/VBA parser preflight

Treat CST History's VBA host as a parser that must be verified in the target
CST release. A snippet accepted by a desktop VBA editor is not sufficient
evidence that the History parser will accept it.

Before attaching a new parameterized geometry block, run a small, separately
named preflight History item containing only local declarations, assignments,
and the intended validation branches. Use simple, purpose-specific local names
such as `modelLength`, `feedWidthTop`, `gapAtTail`, and `interpolationT`.
Avoid generic host-like identifiers such as `length`, which can be parsed as a
member or reserved token rather than as a local scalar.

Keep declarations and guards explicit:

```vb
Dim modelLength As Double, feedWidthTop As Double

If modelLength <= 0 Then
    Err.Raise 1004, "CST parameter preflight", "modelLength must be positive"
End If
```

Use a complete `If ... Then` / `End If` block and confirm that the exact
comparison syntax survives the CST History parser before generating solids.
If CST reports an unknown scalar, a missing variable name, or a syntax error,
reduce the preflight to the failing declaration or guard; do not continue by
embedding the same unverified statement in a larger geometry macro. Keep the
same bounds in the external Python contract so normal automated regression
rejects invalid inputs without waiting on a modal `Err.Raise` dialog.

### Description-only edits

When the user asks to translate or revise parameter descriptions while keeping
everything else unchanged, do not use the parameter-creation pattern above.
Use `SetParameterDescription` so the expression, numeric value, parameter order,
and dependency graph are not rewritten:

```python
model.SetParameterDescription("patch_w", "贴片沿 X 方向的宽度（mm）")
```

Apply this as a metadata-only operation:

1. Enumerate the current parameter names and fail if an expected name is
   missing.
2. Keep an explicit name-to-description mapping; do not translate parameter
   names or expressions.
3. Capture parameter-core, History, geometry, port, monitor, and load
   fingerprints before editing.
4. Save through CST, close, reopen, and verify every description.
5. Compare protected fingerprints and confirm they are unchanged.

Read
`../cst-control-skill/references/persistence-encoding-and-fingerprints.md`
for CST 2026 save persistence and Chinese readback behavior. Do not round-trip
mojibake returned by `cst.interface` back into the project.

## Advanced native operations

Treat CST native operations as a recorded-operation workflow, not as an API to
guess. Use one History item for each logical operation and keep the pre-operation
solids named and selectable.

1. Build the parameterized flat or primitive geometry first.
2. In CST GUI, perform the operation once and copy its History item verbatim.
3. Replace dimensions with existing CST parameter names; retain the GUI's
   object-selection and WCS setup commands.
4. Rebuild each representative state before composing a second operation.

For a verified native cylindrical-bend pattern, select every named solid with
`Bending.Shape`, activate a local WCS at the bend reference plane, then call
`Bending.FlexBend` with `.Centralized "True"` and a parameterized radius. The
full audited pattern and its state checks are in
`../cst-advanced-geometry-operations/references/native-operations.md`.

Do not invent History syntax for Boolean, Transform, Mirror, Array, Sweep, or
Blend operations. Record it from the target CST version first; selection order,
active WCS, and body-vs-sheet behavior are operation-specific.

## Reliable Primitive Pattern

```vb
MakeSureParameterExists "body_x", "10"
SetParameterDescription "body_x", "实体沿 X 方向的尺寸。"

With Brick
    .Reset
    .Name "object_name"
    .Component "component_name"
    .Material "PEC"
    .Xrange "-body_x/2", "body_x/2"
    .Yrange "-5", "5"
    .Zrange "0", "1"
    .Create
End With
```

Set units and frequency range near the start of every generated model. Create
named materials before objects that reference them. Use short, descriptive
History titles because they become the audit trail.

## CST-Native Smooth Geometry Pattern

When geometry must stay editable and sweepable inside CST, use CST-native
parameters and geometry commands rather than imported mesh. For smooth freeform
or analytical surfaces, a robust general pattern is:

1. Store controlling CST parameters with Chinese descriptions.
2. Create multiple `Polygon3D` profile curves whose point coordinates contain
   CST parameter expressions.
3. Use `.SetInterpolation "Spline"` on profiles that should be smooth.
4. Use `LoftCurves` with `.Solid "True"` to create a solid.
5. Rebuild after changing parameters.

Generic shape:

```vb
MakeSureParameterExists "profile_w", "40"
SetParameterDescription "profile_w", "轮廓宽度，增大时实体横向尺寸变大。"
MakeSureParameterExists "profile_h", "10"
SetParameterDescription "profile_h", "轮廓高度，增大时顶面或外形高度增加。"

Curve.NewCurve "profile_curve_00"
With Polygon3D
    .Reset
    .Name "profile_00"
    .Curve "profile_curve_00"
    .SetInterpolation "Spline"
    .Point "-profile_w/2", "-10", "0"
    .Point "-profile_w/2", "-10", "profile_h"
    .Point " profile_w/2", "-10", "profile_h"
    .Point " profile_w/2", "-10", "0"
    .Point "-profile_w/2", "-10", "0"
    .Create
End With

With LoftCurves
    .Reset
    .Name "lofted_solid"
    .Component "AI_Generated"
    .Material "material_name"
    .Solid "True"
    .MinimizeTwist "False"
    .AddCurve "profile_curve_00:profile_00"
    .AddCurve "profile_curve_01:profile_01"
    .Create
End With
```

Practical rules verified in CST 2026 SP2:

- `Polygon3D.Point` can accept string expressions containing CST parameters.
- `Polygon3D.SetInterpolation "Spline"` works for smooth profile curves.
- `LoftCurves` supports `.Solid "True"`, `.AddCurve`, and `.Create`.
- Avoid degenerate profiles, such as zero width or coincident control points.
- Avoid complex nested functions inside `Polygon3D.Point`; precompute constants
  in Python and keep CST expressions simple.

For a curved conductive ribbon or wall rib, generate an odd number of closed
rectangular profiles along the current parameterized centerline, then loft them
as one solid. Keep every profile nondegenerate, extend terminal profiles by a
small named contact tolerance when reliable electrical contact is required,
and validate self-intersection and neighbor clearance at changed parameter
states. Read
`../cst-advanced-geometry-operations/references/lofted-ribbons-and-contacts.md`
for the complete pattern.

## Dynamic topology and deterministic names

Read count parameters with `Evaluate`, validate their integer bounds before
geometry creation, and generate curves and solids inside History loops. Derive
names from the current index, for example `pin_L_01` or `cell_003`, so the model
tree and regression harness agree after the count changes. Do not build a fixed
initial object list in Python and expect it to remain valid after a rebuild.

Split parameter setup, validation, major geometry subsystems, and mirrored or
repeated sets into separate named History items. Save after every successful
item; when a failure occurs, test the last saved project plus one item rather
than replaying an opaque monolithic block.

## Imported Mesh Fallback

Use STL/OBJ import when the goal is geometry exchange, visual inspection, or a
fallback for fragile native construction. Imported mesh geometry is not reshaped
by changing CST parameters; geometry sweeps require regenerating and reimporting
the mesh.

STL import pattern:

```vb
With STL
    .Reset
    .FileName ("C:\\path\\to\\model.stl")
    .Id (1)
    .Name ("imported_model")
    .Component ("AI_Imported")
    .ImportToActiveCoordinateSystem (False)
    .Read
End With
```

OBJ import pattern:

```vb
With OBJ
    .Reset
    .FileName ("C:\\path\\to\\model.obj")
    .ScaleToUnit "False"
    .CopyFileToProject "True"
    .Read
End With
```

For OBJ, use `With OBJ ... .Read`; do not use guessed forms such as
`OBJImport` or `.Import`.

## Debugging

- If a VBA block fails, reduce it to the last successful History item plus one
  new operation.
- Check quotation marks: CST VBA expects strings like `"PEC"`; Python raw
  strings help avoid accidental escaping.
- If parameter changes do not affect geometry, run `Rebuild`.
- If a rebuild reports no Python exception, still check its return value, new
  CST messages, expected model-tree names, and whether a modal History Error is
  blocking the frontend.
- If an object name already exists, delete it intentionally first or use a new
  name; do not rely on silent overwrite.
- For repeated test runs, start from a fresh `.cst` or record a cleanup History
  block for the component being regenerated.
- Treat ports, boundary spacing, and solver setup as separate iterations after
  geometry is visually correct. Copy exact commands from GUI History when the
  command depends on selected faces, picked points, or solver-specific objects.
