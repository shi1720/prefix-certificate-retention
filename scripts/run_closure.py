"""Exploratory exact-prefix extension and timestamp-resolution sensitivity."""
from pathlib import Path
import json,sys,time
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from prefix_retention.trace import load_trace,split_trace,Grouping,GRID,PRICES,tables,Request
from prefix_retention.closure import build_certificates,solve_closure
from prefix_retention.optimize import price_solution
from prefix_retention.replay import replay


def run():
    rows=[]; stored={}
    for resolution in ['native','one_second']:
        for name in ['conversation','toolagent','synthetic']:
            req,_=load_trace(ROOT/'data/raw'/f'{name}.jsonl')
            if resolution=='one_second':
                req=[Request(float(np.floor(r.time)),r.blocks) for r in req]
            (train,te),(valid,ve),(test,xe)=split_trace(req)
            for kind in ['global','group','depth','group_depth']:
                g=Grouping(train,kind)
                start=time.perf_counter()
                h,c=tables(train,te,g)
                cert=build_certificates(train,g,GRID)
                prep=time.perf_counter()-start
                for price in PRICES:
                    for mode in ['cut','dp']:
                        start=time.perf_counter()
                        if mode=='cut':
                            sol,diag=solve_closure(cert,c,price)
                        else:
                            sol=price_solution(h,c,g.parents,price)
                            diag={}
                        fit=time.perf_counter()-start
                        ttl=GRID[sol.labels]
                        actual_train=replay(train,te,g,ttl)
                        assert abs(actual_train['hits']-sol.hits)<1e-7
                        assert abs(actual_train['cost']-sol.cost)<1e-4
                        out=replay(test,xe,g,ttl)
                        v=replay(valid,ve,g,ttl)
                        relaxed=float(np.max(h-price*c,axis=1).sum())
                        row=dict(resolution=resolution,dataset=name,grouping=kind,mode=mode,price=price,
                            train_value=sol.value,relaxed_bound=relaxed,train_hits=sol.hits,train_cost=sol.cost,
                            test_utility=(out['hits']-price*out['cost'])/out['input_blocks'],
                            validation_utility=(v['hits']-price*v['cost'])/v['input_blocks'],
                            prepare_seconds=prep,fit_seconds=fit,
                            **{k:v for k,v in out.items() if k!='bins'},**diag)
                        rows.append(row)
                        stored[f'{resolution}_{name}_{kind}_{mode}_{price:g}']=dict(ttl=ttl.tolist(),parents=g.parents.tolist(),top=g.top)
                print(resolution,name,kind,'done',len(cert.group),'certificate nodes',flush=True)
    pd.DataFrame(rows).to_csv(ROOT/'results/closure_results.csv',index=False)
    (ROOT/'results/closure_profiles.json').write_text(json.dumps(stored,indent=2)+'\n')

if __name__=='__main__': run()
