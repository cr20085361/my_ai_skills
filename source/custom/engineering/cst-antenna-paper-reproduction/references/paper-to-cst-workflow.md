# Paper-to-CST antenna workflow

## 1. Freeze inputs and define the requested outcome

- Hash every supplied PDF, drawing, data file, and existing project.
- Decide whether the delivery is geometry-only, simulation-ready, or includes a
  solver run. Geometry-only is the safe default when feed or test-fixture data
  are missing.
- Record the CST version and the intended optimization variables.

## 2. Read the paper in two passes

First extract the antenna's electromagnetic idea: operating band, mode,
polarization, beam mechanism, matching mechanism, and claimed performance.
Then inspect figures, tables, captions, equations, scale bars, appendices, and
manufacturing notes for geometry.

For each equation, label its role before using it:

- geometry boundary or dimension;
- electromagnetic design relation;
- empirical fit or optimization objective;
- measurement/post-processing definition.

Only the first class directly defines CST solids. Other classes may justify a
derived parameter or validation target.

## 3. Supplement with primary sources

Search the paper title, DOI, authors, antenna name, thesis repositories,
patents, institutional archives, author-hosted drawings, and official
datasheets. Prefer the authors' dissertation or manufacturing drawing over a
third-party summary. Record direct URLs, document identifiers, page/figure/table
locations, and access dates in the evidence ledger.

Do not use a web source merely because its geometry looks similar. It must be
linked to the same design or be explicitly labeled as an analogy used for an
engineering assumption.

## 4. Resolve dimensions and topology

Choose one global coordinate convention and state the direction of aperture,
propagation, E plane, and H plane. For each published dimension decide whether
it refers to electromagnetic clearance, centerline, metal outer size, substrate
edge, or manufacturing stock. Make metal thickness grow in the documented
direction instead of silently shrinking a published clear aperture.

Create a topology inventory: components, materials, contacts, open faces,
symmetries, repeated elements, and features that appear/disappear as a parameter
changes. Distinguish continuous size changes from topology changes.

## 5. Pass the decision gate

Ask the user before building when unresolved information changes:

- feed family or port reference plane;
- conductor connectivity or material stack;
- coordinate/dimension interpretation;
- a dominant curve or taper that controls the antenna principle;
- whether the output may be called an exact reproduction.

For a lower-impact uncertainty, choose a conservative parameterized initial
value, explain its derivation, bound it, and include it in later optimization.

## 6. Create the analytical model first

Implement the dimensions and derived equations in a small external math module.
Generate an analytical fingerprint containing relevant envelope samples,
station coordinates, repeated-element counts, clear gaps, contact points, and
expected bounding boxes. This catches transcription and indexing errors before
CST startup cost is paid.

The external math is an oracle for validation, not the final geometry source.
Keep the optimization-ready geometry rebuildable inside CST History.

## 7. Build in isolated History stages

Use a disposable minimal project to verify CST launch and one simple History
operation. Then create the target project with stable stages such as parameters,
units/materials, validation, feed region, primary conductors, shaped surfaces,
and repeated structures. Save after every stage. If a block fails, restart from
the last saved stage plus one operation.

Use direct primitives for simple solids. Use closed `Polygon3D` profiles and
solid `LoftCurves` for rebuildable analytical surfaces or curved ribbons. Record
unverified native operations from the installed CST version before automating
them.

## 8. Regress and deliver

Use regular `Rebuild()` for the standard matrix. Compare CST tree names and
measured geometry to the analytical fingerprint. Run a full History rebuild
only as an isolated extra diagnostic when regular rebuilds are already stable
and the model size makes it safe.

After restoring the delivery values, save, close, reopen, and repeat nominal
checks. Document every excluded simulation object and every remaining unknown.
