---
name: cst-parametric-modeling
title: CST Parametric Modeling
description: Use when building or iterating CST models that must retain internal parameter optimization, including CST Parameter List variables, derived parameters, rebuildable and coupled History VBA geometry, validation bounds, zero-state regression, Parameter Sweep, Optimizer, and Tuning workflows.
category: engineering
audience: codex-project
tags: [cst, parametric-modeling, parameter-sweep, optimizer, tuning, python, vba]
status: active
score: 10.0
---

# CST Parametric Modeling Skill

## When to Use

Use this skill when any of the following applies:

- The user wants fully parameterized modeling inside CST.
- The user will later use `Parameter Sweep`, `Optimizer`, or `Tuning`.
- The geometry is complex enough that manual construction is expensive.
- Externally imported geometry cannot satisfy later optimization requirements.

## Core Principle

Keep the following priorities fixed:

1. Preserve parameters in the CST Parameter List.
2. Perform geometry rebuilds inside CST.
3. Split complex boundaries into stable patches.
4. Prefer numeric History operations over giant symbolic expression blocks.

## Default Stack

- External driver: `Python`
- CST interface: `cst.interface`
- Internal rebuild: `History VBA`
- Surface construction: `Polygon3D + LoftCurves` for solids or `CoverCurve`
  for verified sheet workflows

## Workflow

1. Define user parameters and derived parameters.
2. Decide whether the target structure needs to be split into multiple patches.
3. Open or create the CST project with Python.
4. Write user parameters into the CST Parameter List.
5. Inject rebuildable History VBA.
6. Read parameters in History VBA and generate geometry numerically.
7. Add adaptive sampling and point-count limits for high-curvature or
   high-frequency boundaries.
8. Produce a reusable `.cst` template.

## Parameter contract and regression matrix

Before editing geometry, make a small parameter contract:

- user inputs, defaults, physical meaning, and units;
- derived parameters and formulas;
- coordinate convention and reference points;
- valid inequalities and singular states;
- geometry, feed, port, load, spacer, and mesh objects affected by each input.

Validate expressions before geometry creation and raise a clear CST error for an
invalid state. For inverse trigonometric formulas, explicitly bound the
dimensionless argument. Keep derived geometry references in CST parameters so
loads and spacers use the same source of truth as the transformed solids.

Every parameterized change needs at least:

1. a zero-change state that must reproduce the baseline;
2. a nominal state;
3. one smaller and one larger valid state;
4. an invalid state that must fail with the intended message.

For each valid state, run the normal `model3d.Rebuild()` first and measure the
physical outcome from geometry or endpoints rather than trusting the formula
alone. Check its Boolean return, new CST messages, expected model-tree objects,
and connection state. A History error may return `False` or display a blocking
modal instead of raising a Python exception.

Use a full History rebuild only as an additional isolated diagnostic after
regular rebuilds are stable, on a disposable copy, and when the model size and
CST behavior make it safe. Dense loft models can close the automation
connection during a full rebuild even though regular parameter rebuilds work.
Check dynamic object sets against the current parameter values; do not hard-code
an initial element or strip count in transforms or validation scripts.

Validate invalid states in the external Python parameter contract by default
and keep matching `Err.Raise` guards in CST History. Exercise an invalid CST
state only with an explicit diagnostic option because the expected error may
open a modal dialog. Treat exception, `False`, relevant Messages, missing
expected geometry, or a closed connection as rejection evidence.

After the last state, restore the requested delivery values, save, close,
reopen, and repeat the nominal checks. Compare the protected parameter core,
History, geometry, port, monitor, and load fingerprints described in
`../cst-control-skill/references/persistence-encoding-and-fingerprints.md`.

## Coupled structural transforms

Treat a transform of a conductor branch as a coupled parameterization when it
changes any physical contact or reference:

- rotate the conductor and every electrically attached element as one rigid
  branch;
- rebuild gap fillers or vacuum bodies from the same top and bottom reference
  parameters;
- recompute lumped-load endpoints and any tail short;
- keep the feed/port fixed only when its contact at the pivot is proven;
- perform topology-changing shell, face-offset, fillet, or boolean work before
  the transform when possible, because fixed face IDs are fragile afterward.

Use `cst-advanced-geometry-operations` for the recorded native transform and
its operation ledger.

## Geometry-state parameters

When a model can switch between planar and curved forms, model the state inside
CST rather than maintaining unrelated geometry files. Use an explicit state
parameter and derived quantities, for example:

- `panel_arc_deg = 0` for a flat panel, `0 < panel_arc_deg < 360` for an open
  cylindrical arc, and `360` for a closed cylinder.
- `layer0_radius` as the inner reference-plane radius; subsequent layer
  reference radii are `layer0_radius + i*grid_layer_d`.
- `panel_length_curved = layer0_radius*panel_arc_deg*pi/180` as the unfolded
  bend length for a nonzero arc.

Validate at least the flat, open-arc, and closed-cylinder states after every
History change. Keep metal thickness as a separate branch: zero thickness may
use PEC sheets, while positive thickness uses solids; do not sweep through zero
in a single CST run.

For complex operation sequencing and verified Bend details, use
`cst-advanced-geometry-operations` together with this skill.

## Warnings

- Do not treat DXF import as the final parametric-modeling route.
- Do not assume a giant `AnalyticalCurve` expression will scale reliably to
  complex models.
- Do not make one closed profile responsible for every face of a complex metal
  surface.
- Do not commit CST's automatically expanded project directory as source code.
- Do not use a successful formula evaluation as the only regression result;
  compare deterministic names, counts, key coordinates, envelopes, contacts,
  and clearances against an analytical fingerprint.

## Deliverables

At minimum, produce:

- A rebuildable `.cst` template.
- An `example_spiral_config.json` or equivalent parameter sample.
- Documentation describing the control flow and pitfalls.
- A reusable harness or checklist.
- A machine-readable parameter contract and analytical geometry fingerprint.
