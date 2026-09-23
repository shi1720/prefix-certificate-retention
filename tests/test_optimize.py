import itertools
import numpy as np
import networkx as nx
from scipy.optimize import linprog
from prefix_retention.optimize import solve_tree, budget_frontier


def feasible(n, k, parents):
    for x in itertools.product(range(k), repeat=n):
        if all(p < 0 or x[i] <= x[p] for i, p in enumerate(parents)):
            yield np.array(x)


def mincut_value(scores, parents):
    # Independent maximum-closure encoding using incremental node rewards.
    graph = nx.DiGraph()
    source, sink = 's', 't'
    graph.add_nodes_from([source, sink])
    delta = np.diff(scores, axis=1)
    bound = float(np.abs(delta).sum() + 1)
    positive = 0.
    for v in range(len(parents)):
        for j in range(1, scores.shape[1]):
            node = (v, j)
            graph.add_node(node)
            w = delta[v, j-1]
            if w > 0:
                graph.add_edge(source, node, capacity=w)
                positive += w
            elif w < 0:
                graph.add_edge(node, sink, capacity=-w)
            if j > 1:
                graph.add_edge(node, (v, j-1), capacity=bound)
            if parents[v] >= 0:
                graph.add_edge(node, (int(parents[v]), j), capacity=bound)
    cut, _ = nx.minimum_cut(graph, source, sink)
    return float(scores[:, 0].sum() + positive-cut)


def test_exhaustive_and_cut():
    rng = np.random.default_rng(9023)
    for n in range(1, 8):
        for _ in range(20):
            parents = [-1] + [int(rng.integers(-1, v)) for v in range(1, n)]
            scores = rng.integers(-9, 10, (n, 4)).astype(float)
            solution = solve_tree(scores, parents)
            brute = max(scores[np.arange(n), x].sum() for x in feasible(n, 4, parents))
            assert solution.value == brute
            assert abs(solution.value - mincut_value(scores, parents)) < 1e-8


def test_frontier_against_full_policy_linear_program():
    rng = np.random.default_rng(35)
    for _ in range(30):
        parents = [-1, 0, 0, 1, 2]
        hits = np.cumsum(rng.integers(0, 8, (5, 4)), axis=1).astype(float)
        cost = np.cumsum(rng.uniform(.1, 10, (5, 4)), axis=1)
        hits[:, 0] = 0.; cost[:, 0] = 0.
        profiles = list(feasible(5, 4, parents))
        hs = np.array([hits[np.arange(5), p].sum() for p in profiles])
        cs = np.array([cost[np.arange(5), p].sum() for p in profiles])
        front, cert = budget_frontier(hits, cost, parents)
        for b in np.linspace(0, front[-1].cost, 15):
            lp = linprog(-hs, A_ub=[cs], b_ub=[b], A_eq=[np.ones(len(hs))], b_eq=[1], bounds=(0, None))
            interp = np.interp(b, [s.cost for s in front], [s.hits for s in front])
            assert lp.success
            assert abs(interp + lp.fun) < 1e-7
        assert all(c['oracle_gap'] < 1e-7 for c in cert)


def test_invalid_tree_rejected():
    import pytest
    with pytest.raises(ValueError):
        solve_tree([[0, 1]], [0])
