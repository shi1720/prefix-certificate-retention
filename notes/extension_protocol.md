# Exact dependency accounting extension

23 September 2026, after inspecting the first chronological evaluation.

The first study optimizes a sufficient coherence constraint: ancestor TTLs are
at least descendant TTLs. This can be conservative because an ancestor may be
refreshed by other requests. We therefore extend the optimization to unrestricted
group TTLs while charging only **usable contiguous prefix** hits. This extension
is exploratory, not covered by the prospective protocol's primary designation.

For each request and depth, a positive-reward hit node requires the preceding
prefix-hit node and the local group's TTL threshold for that block's age.
TTL-threshold nodes have incremental memory-time costs and nested prerequisites.
This is a maximum-closure problem. A minimum cut should optimize the exact
finite-trace utility without requiring ordered group TTLs. The existing DP is
the restricted coherent baseline and the independent-block score is an upper
bound (not a valid usable-hit objective).

Verify against exhaustive enumeration of all grid profiles on small request
traces, and check returned flows/cuts against an independent event replay.
Use exactly the existing data, grid, grouping and prices; fit only on training.
Compare against every baseline on validation and test without choosing a new
price. Do not claim a confirmatory statistical test for this extension.

Also perform a separate timestamp-resolution sensitivity: coalesce timestamps
to 1 second, refit all compared TTL methods, and report the effect. This is
necessary because the released traces have many adjacent 1-millisecond batches;
it is not evidence of actual hardware response within a millisecond.

## Subsequent mathematical extension

After the fixed-grid comparisons, implement group-specific grids containing all
positive training reuse ages. The breakpoint argument removes the discretization
restriction for the same static finite-trace objective. Evaluate group-depth only
at every existing price, with no retuning from test outcomes. This is an additional
exploratory analysis, not a revised primary endpoint. Compare every price to the
frozen grid; do not assume exact training optimization improves future workloads.
