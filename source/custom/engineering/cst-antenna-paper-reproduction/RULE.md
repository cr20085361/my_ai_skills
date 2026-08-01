---
name: cst-antenna-paper-reproduction
title: CST Antenna Paper Reproduction
description: Use when reproducing an antenna from one or more papers, PDFs, theses, patents, drawings, or datasheets as a traceable and internally parameterized CST Studio Suite model. Trigger for requests such as 论文天线复现、根据论文建立 CST 参数化模型、从 PDF 提取天线尺寸后建模、literature-to-CST antenna reconstruction, including supplementary web research, evidence grading, missing-dimension decisions, geometry contracts, rebuild regressions, and delivery validation. Do not use for a simple paper summary or a small edit to an already-defined CST model.
category: engineering
audience: codex-project
tags: [cst, antenna, paper-reproduction, evidence, parametric-modeling, validation]
status: active
score: 10.0
---

# CST Antenna Paper Reproduction

Turn published antenna information into a traceable, rebuildable CST project.
The target is an engineering reproduction whose known, derived, and assumed
parts are explicit—not an unsupported claim of exact reverse engineering.

## Required companion skills

Use the available PDF-reading capability for the supplied paper, then route CST
work through:

- `cst-control-skill` for installation discovery, connection, persistence, and
  delivery;
- `cst-history-macro-skill` for replayable CST History construction;
- `cst-parametric-modeling` for the parameter contract and regression matrix;
- `cst-advanced-geometry-operations` when topology, lofts, sweeps, transforms,
  booleans, or local coordinate systems are involved.

Read `references/paper-to-cst-workflow.md` before starting research or modeling.
Read `references/evidence-and-missing-data.md` whenever a dimension, curve,
feed, or manufacturing detail is incomplete. Read
`references/delivery-and-validation.md` before creating the CST project.

## Non-negotiable outputs before CST starts

Create these project-local artifacts from the templates in `assets/`:

1. `evidence-ledger.json`: every modeling fact with source, locator, evidence
   grade, and interpretation.
2. `geometry-contract.json`: coordinate system, reference planes, topology,
   dimensions, material interpretation, and modeling scope.
3. `parameter-contract.json`: user parameters, derived quantities, constraints,
   dynamic topology, and regression states.
4. `acceptance-report.md`: build, reopen, geometry, provenance, and remaining-
   uncertainty evidence.

Validate the three JSON contracts with:

```powershell
python scripts/validate_contracts.py `
  --evidence evidence-ledger.json `
  --geometry geometry-contract.json `
  --parameters parameter-contract.json
```

Do not launch CST until the contracts are internally consistent and every
geometry-driving fact has an evidence grade.

## Decision gates

- Ask the user when a missing choice changes antenna topology, feed type,
  electrical reference planes, or the claim that will be made about fidelity.
- For a lower-impact missing detail, choose a conservative initial value only
  when it can be exposed as a CST parameter, marked `engineering_assumption`,
  and included in the regression/optimization plan.
- If the feed is unpublished, default to the reproducible antenna geometry and
  an explicit reference plane. Do not invent a coax probe, cavity, transition,
  port, or matching feature.
- Treat a paper equation as geometry only after its variables and physical
  meaning prove that it defines a boundary or dimension. Performance, phase,
  dispersion, and fitting equations may guide a derived initial value without
  directly defining the solid.

## CST build contract

1. Preserve the source PDFs and validated projects; create a versioned output.
2. Set coordinates, units, materials, and frequency band in early named History
   items.
3. Bootstrap replayable parameters with `MakeSureParameterExists` and update
   metadata with `SetParameterDescription` so a rebuild does not overwrite a
   swept value.
4. Generate dynamic topology from current CST parameters and use deterministic
   component, curve, and solid names.
5. Keep each logical subsystem in a separate History item and save after every
   successful block.
6. Establish an analytical fingerprint outside CST before comparing CST
   geometry: key stations, envelopes, counts, contacts, and reference planes.
7. Build geometry first. Add feeds, ports, boundaries, mesh, monitors, and
   solver settings only if they are in scope and supported by the evidence.

## Completion standard

Run regular parameter rebuilds for unchanged, nominal, smaller, larger, and
topology-changing valid states. Validate invalid inputs in Python and keep the
same guards in History; exercise modal-producing CST errors only on a disposable
copy with an explicit diagnostic option. Restore the delivery state, save,
close, reopen, and compare parameter, History, geometry, and simulation-object
fingerprints.

Report the exact reproduction boundary. Use terms such as "paper value",
"author-source value", "derived initial value", and "engineering assumption".
Never collapse those categories into "reproduced exactly".
