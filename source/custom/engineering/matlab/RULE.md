---
name: matlab
title: matlab
description: Build, review, migrate, and safely plan MATLAB or GNU Octave numerical workflows, including arrays, tabular/time data, tests, projects, graphics, MAT files, and explicit Python interoperability.
license: MIT
compatibility: >-
  Documentation is pinned where noted to proprietary MATLAB R2026a and free
  GNU Octave 11.3.0. Bundled Python CLIs require Python 3.11+ and run locally
  without MATLAB or Octave; optional MAT inventory uses scipy and/or h5py.
metadata:
  version: "1.1"
  last-reviewed: "2026-07-23"
category: engineering
audience: codex-project
tags: [matlab, octave]
status: active
score: 10.0
---

# MATLAB and GNU Octave

Use this skill to design or review numerical code, migrate MATLAB releases,
prepare reproducible projects, and plan trusted execution. MATLAB and GNU
Octave are distinct products: compatibility is partial, not a license or
behavior guarantee.

## Product and license gate

- **MATLAB R2026a is proprietary.** Do not assume MATLAB, MATLAB Online, a
  named toolbox, MATLAB Test, MATLAB Compiler, MATLAB Coder, Parallel Computing
  Toolbox, or an add-on is installed, licensed, or available to the user.
- **MATLAB Runtime is not MATLAB.** It runs compatible applications produced
  with MATLAB Compiler; it cannot run arbitrary source or host MATLAB Engine
  for Python. Building artifacts needs the applicable licensed compiler and
  every product used by the source.
- **GNU Octave 11.3.0 is free software under GPLv3+.** Octave packages are not
  MATLAB toolboxes. Similar names do not imply API, numerical, graphics, or
  licensing equivalence.
- Ask which runtime, release, platform, installed products, and license context
  the user actually has. Treat availability as `unknown` until confirmed.

## Nonnegotiable safety boundary

Never run an untrusted `.m`, `.mlx`, MEX binary, MAT file, project startup or
shutdown action, package installer, or generated artifact. Static review does
not prove safety.

Treat these as execution or code-loading surfaces:

- `eval`, `evalin`, `assignin`, text-derived `feval`, `str2func`, callbacks,
  timers, app callbacks, and dynamically modified paths;
- `system`, `unix`, `dos`, shell escape `!`, Java, .NET, Python (`py.*`,
  `pyrun`, `pyrunfile`), MEX, and native libraries;
- `mex`, `codegen`, MATLAB Compiler, build tasks, package/project startup, and
  generated code;
- `load`, object deserialization (`loadobj`, custom serialization), function
  handles, Java/System objects, and class code reachable from MAT files.

`.mlx` is an opaque archive for this toolkit and MEX is native executable code.
Do not use Python pickle for exchange. Inspect first, isolate when appropriate,
obtain explicit approval, then invoke a user-confirmed executable and license.

## Default workflow

1. **Clarify target.** Record MATLAB release or Octave version, OS/architecture,
   base product versus required toolboxes/packages, expected inputs/outputs,
   numerical tolerances, and whether execution is authorized.
2. **Inventory statically.** Scan `.m` files, opaque artifacts, project paths,
   required products, and MAT headers before any runtime loads them.
3. **Choose code form.** Prefer functions with an `arguments` block for
   automation. Use scripts only for controlled orchestration and live scripts
   for reviewed interactive narratives.
4. **Make semantics explicit.** Record shapes, classes, units, missing-value
   rules, indexing, implicit expansion, RNG algorithm/seed, tolerances, and
   output formats.
5. **Test without hidden state.** Keep fixtures synthetic, paths project-local,
   graphics deterministic, and tests independent of base-workspace residue.
6. **Plan execution.** Generate an argv plan, review startup/path effects and
   licenses, and launch only after explicit approval outside these helpers.
7. **Capture provenance.** Hash named inputs/code and record release, products,
   RNG policy, tolerances, and command plan without dumping the environment.

## Language and data checklist

### Scripts, functions, and live scripts

- Scripts share the caller/base workspace and leave variables behind.
  Functions have local workspaces and explicit inputs/outputs.
- Live scripts (`.mlx`) mix code and rich output but are not plain-text
  review artifacts. Export reviewed code to `.m` for static inspection.
- Avoid `clear all`, broad `addpath(genpath(...))`, dependence on `pwd`, global
  variables, and silent name shadowing. Use project roots and `fullfile`.
- Validate sizes, classes, and values in `arguments` blocks. Remember that
  type declarations can convert inputs; validators check without converting.
- A main function file should match the main function name. Local functions
  are private to the file; since R2024a they can appear anywhere in a script
  outside conditional contexts.

```matlab
function y = scaleSignal(x, options)
arguments
    x (:,1) double {mustBeFinite}
    options.Scale (1,1) double {mustBeFinite, mustBeNonzero} = 1
end
y = x .* options.Scale;
end
```

### Arrays, indexing, and numerics

- MATLAB uses 1-based, column-major indexing. `A(i,j)`, `A(k)`, `A(:,j)`,
  `A{...}`, and `A.(name)` have different semantics.
- `*`, `/`, `\`, and `^` are matrix operations; dotted forms are
  element-wise. Use `A\b`, not `inv(A)*b`.
- Since R2016b, compatible dimensions expand implicitly. Assert intended shape
  before operations that could accidentally form an outer result.
- Preallocate when output size is known, but do not vectorize at the cost of
  huge temporaries or unreadable code. Measure with `timeit` or the profiler.
- Compare floating-point results with domain-chosen absolute and relative
  tolerances, not blanket `==` or a magic multiple of `eps`.
- Pin both random algorithm and seed. Use named `RandStream` substreams for
  independent parallel work; do not use time-based `rng("shuffle")` for a
  reproducibility claim.

### Tables, timetables, and missing values

- A `table` has named, equal-height variables that may have different types.
  `T(rows,vars)` returns a table; `T{rows,vars}` extracts contents; `T.Var`
  selects one variable.
- A `timetable` additionally has row times. Sort, validate time zones and
  uniqueness, then use `retime`/`synchronize` intentionally.
- Missing sentinels are type-specific: `NaN`, `NaT`, `<missing>`,
  `<undefined>`, and empty character vectors. Integer and logical arrays have
  no standard missing sentinel.
- Define import options rather than relying on inference for production data.
  Preserve units, time zones, variable names, encodings, and missing rules.

## Graphics and export

Use explicit figure/axes handles and `tiledlayout`; label units; set limits,
color scales, font sizes, and colormaps deliberately. Prefer `exportgraphics`
over `saveas` for publication output. In R2026a it exports raster, PDF/EPS/EMF,
SVG, GIF, and interactive HTML; format capabilities differ. Specify
`ContentType="vector"` for suitable PDF/SVG-style output and `Resolution` for
raster output. Review accessibility and embedded-raster behavior.

## MAT files and exchange

- Version 7 is the normal `save` default; `matfile` creates 7.3 by default.
  Versions 4/6/7/7.3 differ in types, compression, and per-variable limits.
- Version 7.3 is HDF5-based, not an arbitrary HDF5 interchange contract.
  Partial access and chunking can help large arrays.
- Never load an untrusted MAT file. Inventory headers/datasets first. Objects
  can invoke class deserialization behavior; opaque/function/native content
  requires escalation.
- Prefer CSV/JSON/Parquet/HDF5 with a documented schema for simple exchange.
  Do not rename pickle payloads as MAT files and do not deserialize pickle.

## Projects, analysis, and tests

- Use MATLAB Projects for controlled paths, startup/shutdown tasks,
  dependencies, source control, and reproducible entry points. Review project
  actions before opening an untrusted project.
- `matlab.codetools.requiredFilesAndProducts` and Dependency Analyzer are
  static approximations; dynamic dispatch can cause misses or false positives.
  A required-product report does not prove a license is available.
- Use Code Analyzer (`codeIssues`; legacy text workflows can use `checkcode`)
  and `codeCompatibilityReport` before migration.
- Base MATLAB includes script-, function-, and class-based
  `matlab.unittest` workflows. Parallel runs require Parallel Computing
  Toolbox. Dependency-based selection, richer quality dashboards, generated
  tests, and advanced coverage/equivalence features can require MATLAB Test or
  other products.
- R2026a `runtests` automatically opens and later closes a project when target
  tests belong to a project that is not already open. Account for startup and
  shutdown actions before using this behavior.

## Python integration, pinned to R2026a

- R2026a supports 64-bit CPython 3.9-3.13 for MATLAB Interface to Python,
  MATLAB Engine for Python, and MATLAB Compiler SDK for Python.
- The current R2026a PyPI package reviewed here is
  `matlabengine==26.1.12` (released 2026-05-08). It requires an installed
  R2026a; MATLAB Runtime alone is insufficient. R2026a also ships a
  preinstalled Engine distribution under one named `matlabroot` path.
- Package installation does not grant MATLAB or toolbox licenses. Configure
  one named interpreter/executable; do not print the full environment,
  `PATH`, `PYTHONPATH`, or credentials.
- `pyenv` controls MATLAB-to-Python interpreter selection. In-process Python
  generally requires restarting MATLAB to switch; out-of-process Python can
  be terminated and reconfigured.
- Starting Engine is an explicit execution action:
  `matlab.engine.start_matlab()` starts a MATLAB process and can check out a
  license. Never call it merely to probe availability.
- Verify conversion semantics for NumPy arrays, pandas DataFrames,
  tables/timetables, strings/missing values, datetime/duration, dictionaries,
  shape/order, and unsupported sparse/object/categorical cases.

## References

- [MATLAB R2026a documentation](https://www.mathworks.com/help/matlab/)
- [MATLAB R2026a release notes](https://www.mathworks.com/help/matlab/release-notes.html)
- [R2026a system requirements](https://www.mathworks.com/support/requirements/matlab-system-requirements.html)
- [Python compatibility by release](https://www.mathworks.com/support/requirements/python-compatibility.html)
- [MATLAB Engine installation](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)
- [GNU Octave 11.3.0 release](https://octave.org/)
- [GNU Octave current manual](https://docs.octave.org/latest/)
