# CST persistence, encoding, and fingerprint checks

Use this checklist when the requested change is narrow and the delivery file
must preserve all unrelated CST state.

## 1. Isolate the target

- Keep the validated source `.cst` read-only.
- Create a clearly named working or delivery copy.
- Record the source and target SHA-256 hashes.
- Connect only to the design environment whose open project path exactly
  matches the target path.
- Stop if several projects match ambiguously or if a modal dialog is active.

## 2. Capture protected fingerprints

Choose fingerprints according to the change boundary:

- Parameter core: ordered parameter names, expressions, and evaluated numeric
  values. Exclude descriptions only when descriptions are the intended change.
- History: History captions and payload, or the packaged `ModelHistory.json`
  hash when available.
- Geometry: shape count, deterministic object names, loose bounding boxes, and
  selected volumes or point coordinates.
- Simulation objects: port, monitor, lumped-element, and mesh counts plus
  endpoint coordinates for references that may move.
- Project setup: units, boundaries, frequency range, solver type, and material
  names when they are protected.

Canonicalize numeric output before hashing so harmless formatting differences
do not create false regressions. Keep object ordering deterministic.

## 3. Save and prove persistence

After the mutation:

1. Read the changed value in memory as a diagnostic only.
2. Call the normal project save route.
3. Confirm the CST title no longer carries the modified marker when a GUI is
   present.
4. Close and reopen the same file.
5. Read the changed value again and compare all protected fingerprints.
6. If the value reverted, use CST's native GUI Save command and repeat the
   close/reopen cycle. Some CST 2026 text metadata changes can remain dirty in
   memory even when the Python save call returns normally.

Do not accept screenshots from the pre-save session as persistence evidence.

## 4. Chinese text readback

CST 2026 can display a Chinese parameter description correctly in the GUI while
`cst.interface` returns the same bytes as mojibake after reopening. For audit
comparison only, try this reversible normalization:

```python
def normalize_cst_text_for_compare(value: str) -> str:
    try:
        return value.encode("latin1").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
```

Apply the conversion only when it produces the expected Chinese text. Never
write a raw mojibake string or a speculative conversion back into CST. Verify
the final presentation in the CST parameter table.

## 5. Delivery evidence

Report:

- delivery file and backup paths;
- intended changed fields;
- close/reopen verification result;
- protected fingerprints that stayed identical;
- final file hash;
- any CST API/GUI discrepancy that remains relevant.
