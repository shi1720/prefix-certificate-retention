"""Exact finite-label tree optimization; no smoothness assumptions."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Solution:
    labels: np.ndarray
    value: float
    hits: float = 0.0
    cost: float = 0.0


def solve_tree(scores, parents):
    """Maximize sum scores[v, label[v]] subject to child label <= parent.

    Parents must precede children; -1 denotes a root. The smallest maximizer
    breaks ties. Runtime and stored traceback are O(number_nodes * labels).
    """
    scores = np.asarray(scores, dtype=float)
    parents = np.asarray(parents, dtype=int)
    if scores.ndim != 2 or len(parents) != len(scores) or not scores.shape[1]:
        raise ValueError("Expected a nonempty label axis and one parent per node")
    if not np.isfinite(scores).all():
        raise ValueError("Scores must be finite")
    n, k = scores.shape
    if np.any(parents < -1) or np.any(parents >= np.arange(n)):
        raise ValueError("Each parent must precede its child or be -1")
    dp = scores.copy()
    choice = np.zeros((n, k), dtype=np.int32)
    for v in range(n - 1, -1, -1):
        best = 0
        for j in range(k):
            if dp[v, j] > dp[v, best]:
                best = j
            choice[v, j] = best
        if parents[v] >= 0:
            dp[parents[v]] += dp[v, choice[v]]
    labels = np.empty(n, dtype=np.int32)
    for v in range(n):
        cap = k - 1 if parents[v] < 0 else labels[parents[v]]
        labels[v] = choice[v, cap]
    value = float(scores[np.arange(n), labels].sum())
    return Solution(labels, value)


def price_solution(hits, cost, parents, price):
    if price < 0 or not np.isfinite(price):
        raise ValueError("Price must be finite and nonnegative")
    s = solve_tree(hits - price * cost, parents)
    rows = np.arange(len(s.labels))
    s.hits = float(hits[rows, s.labels].sum())
    s.cost = float(cost[rows, s.labels].sum())
    return s


def budget_frontier(hits, cost, parents, tolerance=1e-8):
    """All supported empirical profiles, using the tree solver as an oracle.

    Adjacent points define optimal mixtures for an *expected* memory-time
    budget, not a pathwise capacity constraint. Returns certificates for each
    segment: price and maximum supporting-line violation in hit units.
    """
    hits, cost = np.asarray(hits), np.asarray(cost)
    if np.any(hits[:, 0] != 0) or np.any(cost[:, 0] != 0):
        raise ValueError("Label zero must represent no retention")
    zero = Solution(np.zeros(len(parents), dtype=np.int32), 0., 0., 0.)
    high = price_solution(hits, cost, parents, 0.)
    if high.cost == 0:
        return [zero], []
    points = {tuple(zero.labels): zero, tuple(high.labels): high}
    todo = [(zero, high)]
    certificates = []
    while todo:
        a, b = todo.pop()
        if b.cost <= a.cost:
            raise RuntimeError("Frontier must be strictly ordered by cost")
        price = (b.hits - a.hits) / (b.cost - a.cost)
        q = price_solution(hits, cost, parents, max(0., price))
        gap = q.value - (a.hits - price * a.cost)
        if gap <= tolerance:
            certificates.append(dict(low_cost=a.cost, high_cost=b.cost,
                                     price=price, oracle_gap=max(0., gap)))
        else:
            if not a.cost < q.cost < b.cost:
                raise RuntimeError("Numerical failure in supporting-line oracle")
            key = tuple(q.labels)
            if key in points:
                raise RuntimeError("Oracle made no progress")
            points[key] = q
            todo.extend([(a, q), (q, b)])
    return sorted(points.values(), key=lambda x: x.cost), sorted(certificates, key=lambda x: x['low_cost'])
