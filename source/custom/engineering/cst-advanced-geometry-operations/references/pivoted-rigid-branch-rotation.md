# Pivoted rigid-branch rotation with a tapered gap

Use this pattern for two conductive branches that start with a top clear gap
and open symmetrically to a larger bottom clear gap. It applies to paired booms,
rails, feed lines, and similar assemblies whose attached solids must rotate
rigidly with each branch.

## Parameter and coordinate contract

Define:

- `gap_top`: clear gap between inner faces at the common top/feed pivot;
- `gap_bottom`: clear gap at the tail control point;
- `angle_length`: distance from the top pivot to the bottom control point along
  the unrotated branch;
- `half_angle`: rotation magnitude of one branch;
- `included_angle = 2*half_angle`;
- `pivot_z`: global axial coordinate of the top pivot.

For a symmetric opening:

```text
gap_ratio = (gap_bottom - gap_top) / (2*angle_length)
half_angle = asin(gap_ratio)
bottom_z = pivot_z - angle_length*cos(half_angle)
```

Convert the angle to degrees only at the CST Transform interface if that
interface expects degrees. Validate:

```text
gap_top >= 0
gap_bottom >= gap_top
angle_length > 0
abs(gap_ratio) <= 1
```

Raise a clear History error before constructing geometry when any condition is
false.

## Pivot and branch membership

Place the `+Y` pivot on the top inner edge at `Y=+gap_top/2` and the `-Y` pivot
at `Y=-gap_top/2`, both parallel to the X axis. Build an explicit branch list:

- positive branch: positive boom/rail plus every attached positive-side solid;
- negative branch: negative boom/rail plus every attached negative-side solid.

Derive repeated object names from the current CST element-count parameter. Do
not freeze the object list at the count present when the macro was first
recorded.

## Recorded Transform pattern

Record one native Rotate in the installed CST version and preserve every field.
A CST 2026/SP2 shape-rotation block has this general form:

```vb
With Transform
    .Reset
    .Name "component:positive_branch_object"
    .Origin "Free"
    .Center "0", "gap_top/2", "pivot_z"
    .Angle "half_angle_deg", "0", "0"
    .MultipleObjects "False"
    .GroupObjects "False"
    .Repetitions "1"
    .MultipleSelection "False"
    .AutoDestination "True"
    .Transform "Shape", "Rotate"
End With
```

Use the opposite pivot and angle sign for the negative branch. Confirm the sign
with a disposable GUI recording; axis and view conventions can make a guessed
sign appear plausible while opening inward.

Wrap both transforms in a zero-angle condition. Skipping a zero-degree native
transform preserves exact baseline topology and makes the equal-gap state a
strong regression.

## Stable operation order

Use this sequence:

1. build the straight branches and attached elements;
2. complete face offsets, shelling, fillets, and topology-changing booleans;
3. validate the gap parameters;
4. rotate the positive branch as one named History item;
5. rotate the negative branch as a second named History item;
6. rebuild the gap body from top and bottom profiles;
7. rebuild the tail short or lumped load from the derived bottom endpoints;
8. verify feed and port contact at the pivot;
9. rebuild, save, close, and reopen.

Doing shell and face-ID operations before rotation reduces dependence on face
numbers that may change after a transform.

## Tapered gap body

If a vacuum or dielectric body fills the space, do not keep the original
constant-width brick. Build a loft between closed top and bottom profiles.

When the gap body ends at an axial length `spacer_length` shorter than
`angle_length`, derive:

```text
spacer_bottom_gap =
    gap_top + (gap_bottom-gap_top)*spacer_length/angle_length
spacer_bottom_z =
    pivot_z - spacer_length*cos(half_angle)
```

Use the same pivot and angle parameters as the conductive branches so the gap
body cannot drift independently.

## Feed and tail termination

Keep the feed assembly fixed only when its conductive contact lies on the pivot
axis and remains valid in every tested state. Otherwise rebuild the contact
from parameterized reference points.

For a bottom lumped load or short, derive its endpoints from the rotated inner
edges, for example `(0, +gap_bottom/2, bottom_z)` and
`(0, -gap_bottom/2, bottom_z)`. Preserve the existing electrical mode and
resistance/short-selection logic.

## Verification

Test at least:

- `gap_bottom = gap_top`: zero angle and baseline-equivalent geometry;
- nominal opening;
- smaller and larger valid openings;
- one invalid opening that exercises each validation boundary.

For every valid state:

- run a full History rebuild;
- measure top and bottom clear gaps from actual vertices or load endpoints;
- compare the measured half-angle with the formula;
- check all expected branch objects exist and remain conductive;
- inspect branch and gap-body bounding boxes and selected volumes;
- verify tail endpoints touch the intended inner edges;
- verify port/feed contact and unchanged solver-object counts.

Restore the requested delivery state and repeat the nominal checks after a
save/close/reopen cycle.
