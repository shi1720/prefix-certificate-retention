"""All reuse-age breakpoints: exact continuous nonnegative TTL optimization.

Every between-event TTL can be decreased to a group reuse age without losing
a hit or increasing storage. Distinct timestamp batches imply positive ages.
"""
import numpy as np
from .trace import block_events, TICKS


def event_tables(requests, horizon, grouping):
    events, node = block_events(requests, grouping)
    n = len(grouping.parents)
    ages = [set() for _ in range(n)]
    exposures = [[] for _ in range(n)]
    for block, times in events.items():
        ts = np.unique(np.rint(np.array(sorted(times))*TICKS).astype(np.int64))
        g = node[block]
        gaps = np.diff(ts)
        ages[g].update(gaps.tolist())
        exposures[g].extend(np.diff(np.r_[ts, round(horizon*TICKS)]).tolist())
    grids, costs = [], []
    for reuse, exp in zip(ages, exposures):
        q = np.array([0]+sorted(reuse), dtype=np.int64)
        e = np.sort(np.array(exp, dtype=np.int64))
        prefix = np.r_[0, np.cumsum(e)]
        j = np.searchsorted(e, q, side='left')
        c = (prefix[j]+(len(e)-j)*q)/TICKS
        grids.append(q/TICKS)
        costs.append(c)
    return grids, costs
