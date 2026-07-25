# Native operations reference

## Verified CST 2026/SP2 cylindrical Bend pattern

This pattern was exercised on a parameterized finite multilayer polarizer with
both zero-thickness PEC sheets and finite-thickness solids. It supports flat,
open-arc, and closed-cylinder states in one history-driven project.

Prerequisites:

- Build all flat objects before bending and keep deterministic names.
- Select every target object with `Bending.Shape`; regenerate this list if a
  parameter update changes the strip count.
- Set the local WCS at the innermost layer reference plane.
- Validate `0 <= panel_arc_deg <= 360` and require `layer0_radius > 0` when
  `panel_arc_deg > 0`.

```vb
Bending.Reset
' Repeat once per selected object; selection is parameter-dependent.
Bending.Shape solidNameValue

WCS.AlignWCSWithGlobalCoordinates
WCS.ActivateWCS "local"
WCS.SetOrigin 0, 0, zLayer0
WCS.SetUVector 1, 0, 0
WCS.SetNormal 0, 0, 1

With Bending
    .Centralized "True"
    .Angle "0"
    .Radius CStr(layer0Radius)
    .FlexBend
End With

WCS.ActivateWCS "global"
```

For a nonzero arc, derive the unwrapped panel length before rebuilding as
`panel_length_curved = layer0_radius × panel_arc_deg × π / 180`. Store the
result through the project's existing parameter-bootstrap mechanism; do not
assume a bare `pi` symbol is available in History VBA.

Test the same saved project at `panel_arc_deg = 0`, `90`, and `360`. Check the
History list, object count, layer reference radii, and visual shape before
adding ports or solver settings.

## General recording protocol

For unverified Boolean, Transform, Mirror, Array, Sweep, Blend, Fillet, or
Chamfer work, perform the operation once in the CST GUI and copy the resulting
History item. Preserve the recorded selection order, WCS commands, and object
names. Only after the one-operation test succeeds should dimensions be replaced
by CST parameter expressions and included in a rebuildable template.
