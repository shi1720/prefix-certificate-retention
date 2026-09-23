"""Lossless full-block trace preparation and additive TTL accounting."""
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import numpy as np

GRID = np.array([0, .001, .1, .3, 1, 3, 10, 30, 60, 120, 300, 600, 900.])
PRICES = np.array([0, .0001, .0003, .001, .003, .01, .03, .1, .3, 1.])
DEPTH_ENDS = np.array([1, 2, 4, 8, 16, 32, 64, 128, np.inf])


@dataclass
class Request:
    time: float
    blocks: tuple


def load_trace(path):
    rows = [json.loads(s) for s in open(path)]
    parents = {}
    requests = []
    for x in rows:
        ids = x['hash_ids']
        if len(ids) != (x['input_length'] + 511) // 512:
            raise ValueError("Trace block count inconsistent with token count")
        # An incomplete block cannot be reused as a full cached prefix block.
        ids = tuple(ids[:x['input_length'] // 512])
        for d, block in enumerate(ids):
            parent = ids[d - 1] if d else None
            if block in parents and parents[block] != parent:
                raise ValueError("Cumulative hash violates unique-parent contract")
            parents[block] = parent
        requests.append(Request(x['timestamp'] / 1000., ids))
    requests.sort(key=lambda x: x.time)  # stable; all same-time reads occur first
    return requests, rows


def split_trace(requests):
    end = requests[-1].time
    bounds = [(0., .4 * end), (.4 * end, .6 * end), (.6 * end, end)]
    windows = []
    for i, (lo, hi) in enumerate(bounds):
        part = [Request(r.time - lo, r.blocks) for r in requests
                if r.time >= lo and (r.time < hi or i == 2 and r.time <= hi)]
        windows.append((part, hi - lo))
    return windows


class Grouping:
    """One shared first-block label, then a chain for each prefix group.

    Group keys are cumulative hashes of the second block. Unseen keys use a
    pooled fallback. Equal labels inside depth bins preserve prefix coherence.
    """
    def __init__(self, train, kind='group_depth', top_k=8):
        self.kind = kind
        counts = Counter(r.blocks[1] for r in train if len(r.blocks) > 1)
        self.top = [v for v, _ in sorted(counts.items(), key=lambda p: (-p[1], p[0]))[:top_k]]
        if kind in ('global', 'depth'):
            self.top = []
        self.keys = {v: i for i, v in enumerate(self.top)}
        self.groups = len(self.top) + 1
        if kind == 'global':
            self.parents = np.array([-1])
            self.names = ['all']
        else:
            bands = 1 if kind == 'group' else len(DEPTH_ENDS) - 1
            self.parents = np.array([-1] + [0 if b == 0 else 1 + g * bands + b - 1
                                           for g in range(self.groups) for b in range(bands)])
            self.names = ['shared_root'] + [f'group_{g}_band_{b+1}' for g in range(self.groups) for b in range(bands)]

    def labels_for(self, blocks):
        if self.kind == 'global':
            return [0] * len(blocks)
        g = self.keys.get(blocks[1], len(self.top)) if len(blocks) > 1 else len(self.top)
        out = [0] if blocks else []
        for depth in range(2, len(blocks) + 1):
            b = int(np.searchsorted(DEPTH_ENDS, depth)) - 1
            out.append(1 + g if self.kind == 'group' else 1 + g * (len(DEPTH_ENDS)-1) + b)
        return out


def block_events(requests, grouping):
    events = defaultdict(lambda: defaultdict(int))
    node = {}
    for r in requests:
        for block, group in zip(r.blocks, grouping.labels_for(r.blocks)):
            if block in node and node[block] != group:
                raise ValueError("Inconsistent grouping for one block")
            node[block] = group
            events[block][r.time] += 1
    return events, node


def tables(requests, horizon, grouping, grid=GRID):
    """Hits and exact occupied block-seconds, including final right censoring.

    Hit multiplicity uses the number of requests in a timestamp batch; each
    physical block occupies space only once. Cache starts empty.
    """
    events, node = block_events(requests, grouping)
    h = np.zeros((len(grouping.parents), len(grid)))
    c = np.zeros_like(h)
    for block, times in events.items():
        ts = np.array(sorted(times))
        g = node[block]
        if len(ts) > 1:
            gaps = np.diff(ts)
            counts = np.array([times[t] for t in ts[1:]])
            h[g] += ((gaps[:, None] <= grid) & (grid > 0)).T @ counts
        exposure = np.diff(np.append(ts, horizon))
        c[g] += np.minimum(exposure[:, None], grid).sum(axis=0)
    return h, c
