# Computational protocol, version 1

Written before policy fitting or comparison on 23 September 2026. This is a local
prospective analysis plan, not an externally registered protocol.

## Question and proposed contribution

Can a prefix-coherent time-to-live (TTL) profile improve the measured tradeoff
between reusable prompt blocks and memory-time relative to a single timeout?
The optimization target is **saved full prompt blocks minus a declared price per
block-second**. It is not measured GPU latency, energy, dollars, or model accuracy.

The mathematical target is an exact finite-grid optimizer with an independently
checkable objective, respecting ancestor dependencies under reset-on-access.
Existing TTL theory, soft-TTL, dependency-aware caching and Kareto group TTL are
explicit antecedents. No claim to invent TTL, prefix-aware caching, tree dynamic
programming, maximum closure, or general Lagrangian optimization is intended.

## Data

Pinned Mooncake FAST'25 release: conversation and toolagent (production-derived),
synthetic (secondary). Raw download hashes are in data/manifest.json. Each has
arrival times and cumulative prefix hashes for 512-token blocks. Discard the
final incomplete block; do not assume it is reusable. No prompts, user identifiers,
model calls, or new participants are needed.

Use chronological time windows: [0,40%) training; [40%,60%) validation;
[60%,100%] test, relative to each trace's final timestamp. Begin every replay
empty. Report warm-start sensitivity separately if performed. Tied timestamps
are treated as simultaneous batches: inspect all requests before any insertion,
so tied cold requests cannot obtain artificial sequential hits. TTL zero means
no retention. Retention is inclusive at positive timeout boundaries.

## Policies and fitting

Timeout grid (seconds): 0, 0.001, 0.1, 0.3, 1, 3, 10, 30, 60, 120, 300, 600, 900.
Prices (saved blocks per block-second): 0, 0.0001, 0.0003, 0.001, 0.003, 0.01,
0.03, 0.1, 0.3, 1. Fit at each price on training only.

Compare: no cache; infinite-within-window cache (reference); best global TTL;
prefix-group TTL; depth-only coherent TTL; group-by-depth coherent TTL;
unconstrained group-by-depth TTL (diagnostic; actual usable prefixes measured).
Group structure is fixed from training: the eight most frequent second-block
hashes and one pooled fallback group. Depth bins are [1], [2], [3,4], [5..8],
[9..16], [17..32], [33..64], [65..128], [129..]. The first block has a shared
parent label, followed by one chain per group. This grouping is an intentional
restriction of the full prefix tree and allows unseen hashes to receive a policy.

Validation compares group-depth and depth-only profiles at each price, choosing
the higher realized validation utility (ties favor depth-only). The selected
policy is the primary method. Always report both ablations, even if unsuccessful.
No change to the grid, grouping, split, or price range based on test results.

## Endpoints

Primary: test utility (saved blocks minus price * occupied block-seconds),
normalized per full input block. Also report prefix-hit fraction, mean and peak
resident blocks, fitting time, and complete tradeoff curves at every price.
Use paired 60-second time-block bootstrap intervals for **descriptive** uncertainty
of fixed test-policy differences, not iid requests or independent deployment
replications. Show all prices; no post hoc choice of a best price as a headline.

Capacity-constrained LRU and FIFO are additional deployment baselines at declared
capacities (256, 1024, 4096, 16384 blocks). Their different constraint must be
explicit. Policies with memory-time budgets do not guarantee hard memory caps.

## Verification and limitations

Independently enumerate all feasible labels on small random trees; compare a
separate minimum-cut formulation and tree dynamic program. Check event replay
against analytic occupancy/hit tables, including ties, censored final intervals,
zero TTL, and prefix dependencies. Compare relaxed bounds and rounding.

The finite-trace optimizer proves empirical optimality within its declared
profile class. Out-of-sample performance is empirical. One-hour sampled traces
cannot establish production-wide or future-workload guarantees. Runtime mutation,
decode blocks, active-request pinning, network transfers and actual GPU scheduling
are outside this replay. Include unfavorable comparisons and failure regimes.
