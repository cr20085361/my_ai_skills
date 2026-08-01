# Evidence grading and missing-data policy

## Evidence grades

Use exactly these machine-readable grades:

| Grade | Meaning | Permitted claim |
|---|---|---|
| `paper_exact` | Explicit in the target paper, figure, table, or caption | Published paper value |
| `author_source_exact` | Explicit in a linked author thesis, patent, drawing, repository, or official design document | Author-source value |
| `derived` | Calculated from cited values and a stated equation | Derived value, not directly published |
| `engineering_assumption` | Chosen to complete a model because evidence is absent | Engineering assumption requiring sensitivity study |

An image measurement without a reliable dimension reference is not exact.
Grade it `derived` if a documented scale permits calculation; otherwise use
`engineering_assumption`.

## Ledger requirements

Every geometry-driving record needs:

- stable identifier and parameter/feature name;
- value and unit, or a textual topology fact;
- evidence grade;
- source title/identifier and direct locator;
- quoted or paraphrased support kept within copyright limits;
- interpretation and any conversion;
- affected geometry objects;
- uncertainty or sweep range when not exact.

Conflicting sources remain separate ledger rows. Resolve the conflict in the
geometry contract and state why one source controls the model.

## Missing-data decisions

Use this order:

1. Search author-controlled primary material.
2. Derive only when the governing relation and all inputs are supported.
3. Ask the user when the choice changes topology, feed, reference plane, or
   fidelity claim.
4. Otherwise create a bounded parameterized assumption and expose it in CST.
5. Exclude the feature when no defensible implementation exists and document
   the resulting validation limitation.

Do not infer hidden feed dimensions from VSWR alone, convert a phase equation
directly into a shape without a boundary derivation, or copy dimensions from a
visually similar antenna as though they belonged to the target design.

## Fidelity language

Use "geometry reproduction from published information" when any essential
dimension is derived or assumed. Use "exact reproduction" only when all
geometry and material details required by the claim are explicitly available
and verified. Report which measured paper results cannot be expected when the
feed, fixture, dielectric properties, or fabrication tolerances differ.
