import itertools
import numpy as np
from prefix_retention.trace import Request, Grouping
from prefix_retention.event_grid import event_tables
from prefix_retention.closure import build_certificates, solve_closure
from prefix_retention.replay import replay


def test_event_grid_matches_every_integer_timeout():
    rng = np.random.default_rng(519)
    for _ in range(20):
        req = [Request(float(t), (1,2) if rng.random()<.5 else (1,))
               for t in np.sort(rng.integers(0,9,8))]
        g = Grouping(req, 'group', top_k=0)
        grids, costs = event_tables(req, 10., g)
        cert = build_certificates(req, g, grids)
        price = float(rng.uniform(.01, .5))
        sol, _ = solve_closure(cert, costs, price)
        brute = max((lambda out: out['hits']-price*out['cost'])(replay(req,10,g,ttl))
                    for ttl in itertools.product(range(11), repeat=2))
        assert abs(sol.value-brute)<1e-8
        ttl = [grid[label] for grid,label in zip(grids, sol.labels)]
        out = replay(req, 10., g, ttl)
        assert out['hits']==sol.hits
        assert abs(out['cost']-sol.cost)<1e-8
