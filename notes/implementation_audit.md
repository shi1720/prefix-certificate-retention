# Implementation corrections during internal verification

1. The first strict-coherence witness used a storage price at which neither
   optimizer should keep the child. The witness was corrected to price 0.04;
   no algorithm or result was changed to make an invalid claim hold.
2. Exact timeout-boundary comparisons are performed in integer microseconds.
   Decimal binary floating point can disagree between `t_last + ttl >= t` and
   `t - t_last <= ttl`. A dedicated decimal-boundary regression test exercises
   this case. The source traces have integer millisecond timestamps.
3. Minimum cuts may assign zero-weight, unobserved threshold nodes arbitrarily.
   Returned labels are canonicalized to the smallest thresholds preserving all
   selected training hit certificates (and coherence if imposed). This removes
   arbitrary retention without changing the optimum objective. No test outcomes
   are used by this rule.

All reported final tables are regenerated after these corrections. Earlier
results remain in the Git history, not in the manuscript's final tables.
