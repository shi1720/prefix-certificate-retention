import numpy as np
from prefix_retention.trace import Request, Grouping, tables
from prefix_retention.replay import replay
from prefix_retention.optimize import price_solution


def test_replay_matches_accounting_random_and_tied():
    rng = np.random.default_rng(777)
    for _ in range(60):
        ts = np.sort(rng.integers(0, 100, 50)).astype(float)
        req = [Request(t, (1, 2, 3) if rng.random() < .5 else (1, 4, 5, 6)) for t in ts]
        group = Grouping(req, 'group_depth')
        grid = np.array([0., 1., 3., 10., 200.])
        h, c = tables(req, 105, group, grid)
        sol = price_solution(h, c, group.parents, rng.uniform(0, 1))
        out = replay(req, 105, group, grid[sol.labels])
        assert out['hits'] == sol.hits
        assert abs(out['cost']-sol.cost) < 1e-8
        assert out['hits'] == out['raw_hits']
        assert abs(out['bins'][:, 1].sum()-out['cost']) < 1e-8


def test_zero_and_ties():
    req = [Request(0, (1, 2)), Request(0, (1, 2)), Request(1, (1, 2))]
    g = Grouping(req, 'global')
    assert replay(req, 2, g, [0])['hits'] == 0
    r = replay(req, 2, g, [1])
    assert r['hits'] == 2  # no same-batch hit; equality at expiry does hit
    assert r['cost'] == 4


def test_decimal_boundaries_use_integer_source_time():
    req=[Request(.3,(1,)),Request(.4,(1,))]
    g=Grouping(req,'global')
    h,c=tables(req,.5,g,np.array([0.,.1]))
    out=replay(req,.5,g,[.1])
    assert h[0,1]==out['hits']==1
    assert abs(c[0,1]-out['cost'])<1e-12


def test_orphans_overcount_and_terminal_censoring():
    req = [Request(0, (1, 2)), Request(5, (1, 2))]
    g = Grouping(req, 'depth')
    ttl = np.array([1] + [10] * (len(g.parents)-1))
    r = replay(req, 6, g, ttl)
    assert r['raw_hits'] == 1 and r['hits'] == 0
    assert r['cost'] == 8  # root [0,1] and [5,6], child [0,6]


def test_grouping_prefix_order():
    req = [Request(0, tuple(range(300)))]
    g = Grouping(req, 'group_depth')
    nodes = g.labels_for(req[0].blocks)
    for a, b in zip(nodes, nodes[1:]):
        assert a == b or g.parents[b] == a
