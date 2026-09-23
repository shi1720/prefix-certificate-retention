import itertools
import numpy as np
from prefix_retention.trace import Request,Grouping,tables
from prefix_retention.replay import replay
from prefix_retention.closure import build_certificates,solve_closure,certificate_hits
from prefix_retention.optimize import price_solution


def test_closure_against_all_profiles_and_event_replay():
    rng=np.random.default_rng(714)
    grid=np.array([0.,1.,3.,10.])
    for _ in range(80):
        req=[Request(float(t),(1,2) if rng.random()<.5 else (1,3))
             for t in np.sort(rng.integers(0,20,12))]
        g=Grouping(req,'group',top_k=1)  # only three labels; enumerate 4^3
        h,c=tables(req,22.,g,grid)
        cert=build_certificates(req,g,grid)
        price=float(rng.uniform(0,1))
        best=-np.inf
        for labels in itertools.product(range(4),repeat=len(g.parents)):
            out=replay(req,22,g,grid[list(labels)])
            assert certificate_hits(cert,labels)==out['hits']
            assert abs(c[np.arange(len(labels)),labels].sum()-out['cost'])<1e-9
            best=max(best,out['hits']-price*out['cost'])
        sol,diag=solve_closure(cert,c,price)
        assert abs(best-sol.value)<1e-8
        restricted,_=solve_closure(cert,c,price,g.parents)
        dp=price_solution(h,c,g.parents,price)
        assert abs(restricted.value-dp.value)<1e-8


def test_ordered_ttls_are_strictly_conservative():
    # Ancestor refreshes keep it present despite a short TTL. The child's long
    # TTL remains useful without the ancestor's long terminal storage exposure.
    req=[Request(0,(1,2))]+[Request(float(t),(1,)) for t in range(1,10)]+[Request(10,(1,2))]
    g=Grouping(req,'group',top_k=0)
    grid=np.array([0.,1.,10.])
    h,c=tables(req,20,g,grid)
    cert=build_certificates(req,g,grid)
    exact,_=solve_closure(cert,c,.04)
    dp=price_solution(h,c,g.parents,.04)
    assert exact.value>dp.value
    assert exact.labels[0]<exact.labels[1]
