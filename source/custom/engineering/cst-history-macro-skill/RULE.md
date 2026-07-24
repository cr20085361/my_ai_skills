---
name: cst-history-macro-skill
title: CST History List and VBA Modeling
description: Use when an AI agent must create or modify CST Studio Suite 2026 geometry through History List/VBA snippets injected from Python, including CST parameters, materials, primitives, curves, lofts, boolean operations, transforms, imports, rebuilds, and History debugging.
category: engineering
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

For optimization-ready CST models, prefer `StoreParameterWithDescription`.
Descriptions should be Chinese, concise, and useful in the CST parameter table:

```vb
StoreParameterWithDescription "sub_h", "1.6", "介质基板厚度，增大时馈线与贴片离地高度增加。"
StoreParameterWithDescription "patch_w", "30", "贴片沿 X 方向的宽度，主要影响谐振频率和输入阻抗。"
```

Good descriptions state:

- Which physical part or setup item the parameter controls.
- The unit or implied unit when helpful.
- What happens when the value increases or decreases.

Avoid putting one-off project notes in this skill. Keep project-specific
parameter names and formulas in that project's own documentation.

## Reliable Primitive Pattern

```vb
StoreParameterWithDescription "body_x", "10", "实体沿 X 方向的尺寸。"

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
StoreParameterWithDescription "profile_w", "40", "轮廓宽度，增大时实体横向尺寸变大。"
StoreParameterWithDescription "profile_h", "10", "轮廓高度，增大时顶面或外形高度增加。"

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
- If an object name already exists, delete it intentionally first or use a new
  name; do not rely on silent overwrite.
- For repeated test runs, start from a fresh `.cst` or record a cleanup History
  block for the component being regenerated.
- Treat ports, boundary spacing, and solver setup as separate iterations after
  geometry is visually correct. Copy exact commands from GUI History when the
  command depends on selected faces, picked points, or solver-specific objects.
