---
name: cst-advanced-geometry-operations
title: CST Advanced Geometry Operations
description: Use when an AI agent must create, parameterize, validate, or debug complex CST Studio Suite geometry operations beyond primitives, including native cylindrical Bend, pivoted rigid-branch rotations, tapered gaps, local coordinate systems, transforms, booleans, arrays, sweep/loft sequencing, sheet-versus-solid branches, and planar-to-curved state changes through Python-injected History VBA.
category: engineering
audience: codex-project
tags: [cst, geometry, history-list, python, vba, parametric-modeling]
status: active
score: 10.0
---

# CST Advanced Geometry Operations

Use this skill with `cst-control-skill` and `cst-history-macro-skill` whenever
the geometry contains a native operation whose result depends on selected
objects, coordinate systems, operation order, or topology.

## Decision path

1. Need a rebuildable in-CST shape? Use CST primitives, curves, sheets, solids,
   and recorded History operations.
2. Need a planar panel bent into an arc or cylinder? Build the planar geometry
   first, then use the native cylindrical Bend workflow below.
3. Need Boolean, Transform, Mirror, Array, Sweep, Loft, Blend, or another
   native operation? Record that exact operation from the active CST version
   before automating it.
4. Need two conductor branches to open symmetrically around a feed-end pivot
   while attached elements and a tail load remain connected? Read
   `references/pivoted-rigid-branch-rotation.md`.
5. Need only visual exchange geometry? Use imported mesh and state explicitly
   that it is not internally parameter-rebuildable.

## Mandatory operation ledger

Before writing VBA, define:

- input object names/components and whether each is a sheet or solid;
- active coordinate system, operation axis, reference point, and sign
  convention;
- user parameters, derived parameters, bounds, and invalid states;
- output object names and whether inputs are consumed by the operation;
- three rebuild checks: nominal, boundary, and a changed-parameter state.

Write each logical operation into an individual named History item. Never merge
unrelated geometry construction, selection, and solver setup in one item.

## Native cylindrical Bend workflow

1. Generate and verify all flat strips or panels, with deterministic names.
2. Expose `panel_arc_deg`, `layer0_radius`, layer reference spacing, and the
   derived unfolded length as CST parameters.
3. For bend angles use the state convention: `0` flat, `(0, 360)` open arc,
   `360` closed cylinder. Reject values outside `[0, 360]`; require positive
   radius for nonzero angles.
4. Recompute the complete selected-object set whenever panel length or strip
   count is parameter dependent. Do not assume the initial object count.
5. Activate a local WCS at the selected bend reference plane, perform the
   recorded native Bend, restore the global WCS, save, and rebuild.
6. Test `0°`, one open angle such as `90°`, and `360°`; inspect the CST model
   tree and History after each test.

Use the verified CST 2026/SP2 Bend pattern in
`references/native-operations.md`. Treat it as a starting pattern only: still
record GUI History before applying it to a new topology.

## Other native operations

For Boolean, Transform, Mirror, Array, Sweep, Loft, Blend, Fillet, and Chamfer:

1. Perform one manual GUI operation on a disposable project copy.
2. Copy the exact generated History block.
3. Move dimensions to named CST parameters; preserve selection order and WCS.
4. Parameterize only values proven to rebuild correctly.
5. Test the operation alone before chaining it with another native operation.

Do not use a command name found online as proof of valid CST VBA syntax. Object
selection and sheet/solid behavior must be verified in the installed CST build.

For paired rigid branches, treat the branch solids, attached radiators, gap
body, feed contact, and tail termination as one coupled operation ledger. Use
the formulas, operation order, zero-angle branch, and physical measurements in
`references/pivoted-rigid-branch-rotation.md`.

## Failure isolation

- If History fails, reduce to the last successful History item plus one new
  operation and inspect the first CST error.
- If an update changes the number of generated strips, regenerate the selection
  list before a Bend, Boolean, or grouping operation.
- If geometry deforms around the wrong axis, verify local WCS origin, U vector,
  normal, and restored global WCS.
- If a sheet operation fails on solids or vice versa, keep separate generation
  branches; never sweep metal thickness through zero in one model state.
- Keep ports, boundaries, mesh, monitors, and solver setup outside geometry
  History until the geometry states rebuild successfully.

## Completion evidence

Report the saved `.cst` path, the final History captions, parameter values for
each tested state, whether the model was visually inspected, and any unverified
operations left for GUI recording.
