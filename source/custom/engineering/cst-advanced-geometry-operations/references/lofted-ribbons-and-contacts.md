# Lofted ribbons and reliable terminal contacts

Use this pattern for curved conductive pins, ribs, fences, corrugations, tapers,
and other sweep-like solids whose centerline or cross-section must remain
parameterized inside CST.

## Geometry contract

Record before modeling:

- centerline parameter and its valid range;
- station parameter, tangent direction, and local outward normal;
- ribbon axial width and normal thickness;
- endpoint/contact surfaces and allowed overlap;
- neighbor-clearance and self-intersection constraints;
- evidence grade for the curve and every inferred coefficient.

An unpublished curve should be implemented as a named derived initial value
with a global and, when useful, per-element multiplier. Do not call it the
manufactured curve.

## Cross-section loft pattern

1. Use an odd number of centerline samples so a symmetric curve includes its
   midpoint.
2. At each sample create a closed, nonzero-area rectangular `Polygon3D`
   profile. Its two sides bound the ribbon width; its other two points extend
   along the chosen wall normal by the physical thickness.
3. Keep profile point order and normal sign consistent across all stations to
   prevent twist.
4. Add profiles to one `LoftCurves` operation in deterministic station order,
   set `.Solid "True"`, and assign a stable component/object name.
5. Prefer numeric VBA variables evaluated from CST parameters over large nested
   expression strings in point coordinates.

Do not use a zero-width terminal profile even when the analytical surface
vanishes at a plate. Terminate with a small finite section inside the adjoining
conductor or stop at the last nondegenerate station.

## Contact tolerance

Expose a small positive parameter such as `contact_eps`. Extend the terminal
profile across the intended mating surface by that amount. The overlap should
be large enough to avoid a numerical micro-gap but small relative to the local
feature and mesh scale.

Validate both sides of the tradeoff:

- the intended conductor contact exists in every valid state;
- the overlap does not bridge the designed gap, touch a neighboring ribbon, or
  protrude through an aperture.

Same-material solids may overlap when electrical continuity is the objective.
Avoid a global boolean union unless downstream operations require one; a large
union is more fragile under topology-changing rebuilds and makes failure
isolation harder.

## Regression checks

For nominal, straight/zero-curve, smaller, larger, and count-changing states:

- regular `Rebuild()` succeeds and returns a non-false value;
- expected deterministic solid names and counts exist;
- terminal coordinates overlap only their intended conductor;
- centerline sag/direction agrees with the analytical fingerprint;
- profiles retain positive width and thickness;
- adjacent ribbons do not cross and no solid exceeds the envelope.

Use a disposable CST copy for deliberately invalid states because History
`Err.Raise` may open a blocking modal instead of raising through Python.
