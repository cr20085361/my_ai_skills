---
name: cst-parametric-modeling
title: CST Parametric Modeling
description: Use when building or iterating CST models that must retain internal parameter optimization, including CST Parameter List variables, derived parameters, rebuildable History VBA geometry, Parameter Sweep, Optimizer, and Tuning workflows.
category: engineering
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
- Surface construction: `Polygon3D + CoverCurve`

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

## Warnings

- Do not treat DXF import as the final parametric-modeling route.
- Do not assume a giant `AnalyticalCurve` expression will scale reliably to
  complex models.
- Do not make one closed profile responsible for every face of a complex metal
  surface.
- Do not commit CST's automatically expanded project directory as source code.

## Deliverables

At minimum, produce:

- A rebuildable `.cst` template.
- An `example_spiral_config.json` or equivalent parameter sample.
- Documentation describing the control flow and pitfalls.
- A reusable harness or checklist.
