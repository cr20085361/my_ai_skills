# CST reproduction delivery and validation

## Pre-build checks

- Source hashes recorded and unchanged.
- Evidence, geometry, and parameter contracts validate.
- Coordinate axes and all reference planes are unambiguous.
- Every assumption is a named parameter or an explicitly excluded feature.
- Planned History blocks and deterministic output names are listed.

## Geometry regression matrix

Test, where applicable:

1. zero-change/baseline-equivalent state;
2. requested nominal state;
3. smaller and larger valid states;
4. at least one topology-count change;
5. invalid states for each important inequality or singularity.

For valid states, check regular rebuild return value, new CST messages, expected
object names/counts, key coordinates, bounding boxes, contacts, clearances, and
self-intersection risk. Formula agreement without physical geometry evidence is
insufficient.

Validate invalid states in the external parameter contract by default. Keep
equivalent `Err.Raise` guards in History. Because CST may show a blocking
History Error dialog instead of raising a Python exception, execute an invalid
CST state only on a disposable copy with an explicit option and a human-visible
warning.

## Failure channels

Treat any of these as failure evidence:

- `Rebuild()` or another API call returns `False`;
- new messages contain a relevant error;
- expected objects are absent or stale objects remain;
- the CST connection closes during rebuild;
- a modal dialog blocks the frontend;
- saved values revert after reopen.

Do not catch only Python exceptions.

## Delivery package

Deliver the versioned `.cst`, source/configuration files, build script,
verification script/report, evidence ledger, geometry/parameter contracts,
operation ledger, and a concise user guide. Exclude `.cst` expanded directories,
`Model.lok`, caches, and temporary solver data from source control.

Restore nominal values, save, close, reopen, and record the final project hash.
Report History captions, model-tree fingerprints, tested states, visual
inspection status, intentionally absent simulation setup, and remaining
uncertainties.
