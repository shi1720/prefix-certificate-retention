"""Independent event replay; reads precede all writes in simultaneous batches."""
import heapq
from itertools import groupby
from collections import OrderedDict
import numpy as np


def replay(requests, horizon, grouping, ttl, bucket_seconds=60.):
    expiry = {}
    queue = []
    used = 0
    clock = 0.
    area = 0.
    peak = 0
    hits = raw_hits = total = 0
    bcount = max(1, int(np.ceil(horizon / bucket_seconds)))
    bins = np.zeros((bcount, 3))  # usable hits, block-seconds, full input blocks

    def integrate(a, b, count):
        nonlocal area
        if b <= a:
            return
        area += count * (b-a)
        while a < b:
            k = min(int(a / bucket_seconds), bcount-1)
            end = min(b, (k+1)*bucket_seconds)
            if end <= a:  # floating-point final-boundary guard
                end = b
            bins[k, 1] += count * (end-a)
            a = end

    def advance(t, inclusive=False):
        nonlocal clock, used
        while queue and (queue[0][0] < t or inclusive and queue[0][0] <= t):
            et, block = heapq.heappop(queue)
            if expiry.get(block) != et:
                continue
            integrate(clock, et, used)
            clock = et
            del expiry[block]
            used -= 1
        integrate(clock, t, used)
        clock = t

    for t, batch in groupby(requests, key=lambda r: r.time):
        advance(t)
        insert = {}
        for r in batch:
            k = min(int(t / bucket_seconds), bcount-1)
            prefix_ok = True
            for block, g in zip(r.blocks, grouping.labels_for(r.blocks)):
                present = block in expiry
                raw_hits += int(present)
                prefix_ok = prefix_ok and present
                hits += int(prefix_ok)
                bins[k, 0] += int(prefix_ok)
                bins[k, 2] += 1
                total += 1
                insert[block] = float(ttl[g])
        # Simultaneous reads complete; expired-at-t blocks not refreshed disappear.
        advance(t, inclusive=True)
        for block, duration in insert.items():
            if duration <= 0:
                continue
            if block not in expiry:
                used += 1
            et = t + duration
            expiry[block] = et
            heapq.heappush(queue, (et, block))
        peak = max(peak, used)
    advance(horizon, inclusive=True)
    return dict(hits=hits, raw_hits=raw_hits, input_blocks=total, cost=area,
                mean_blocks=area/horizon, peak_blocks=peak,
                hit_rate=hits/total if total else 0., bins=bins)


def capacity_replay(requests, horizon, capacity, fifo=False):
    """Equal-sized block LRU/FIFO reference, with usable-prefix accounting.

    All accesses refresh LRU in stable file order after simultaneous reads.
    Fixed capacity concerns inactive prompt blocks only, not active decoding.
    """
    cache = OrderedDict()
    last = 0.
    area = 0.
    hits = total = raw = peak = 0
    for t, batch in groupby(requests, key=lambda r: r.time):
        area += len(cache) * (t-last)
        last = t
        writes = []
        for r in batch:
            okay = True
            for block in r.blocks:
                present = block in cache
                raw += int(present)
                okay = okay and present
                hits += int(okay)
                total += 1
                writes.append(block)
        for block in writes:
            if block in cache:
                if not fifo:
                    cache.move_to_end(block)
            elif capacity:
                cache[block] = None
                if len(cache) > capacity:
                    cache.popitem(last=False)
        peak = max(peak, len(cache))
    area += len(cache) * (horizon-last)
    return dict(hits=hits, raw_hits=raw, input_blocks=total, cost=area,
                mean_blocks=area/horizon, peak_blocks=peak, hit_rate=hits/total)
