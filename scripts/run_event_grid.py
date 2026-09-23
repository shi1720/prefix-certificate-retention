"""Exploratory comparison of continuous TTL optimization and the frozen grid."""
from pathlib import Path
import sys,time,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from prefix_retention.trace import load_trace,split_trace,Grouping,PRICES
from prefix_retention.event_grid import event_tables
from prefix_retention.closure import build_certificates,solve_closure
from prefix_retention.replay import replay

def run():
    rows=[];profiles={}
    for name in ['conversation','toolagent','synthetic']:
        req,_=load_trace(ROOT/'data/raw'/f'{name}.jsonl')
        (train,te),(valid,ve),(test,xe)=split_trace(req)
        g=Grouping(train,'group_depth')
        start=time.perf_counter()
        grids,cost=event_tables(train,te,g)
        cert=build_certificates(train,g,grids)
        prep=time.perf_counter()-start
        for price in PRICES:
            start=time.perf_counter()
            sol,diag=solve_closure(cert,cost,price)
            elapsed=time.perf_counter()-start
            ttl=[grid[label] for grid,label in zip(grids,sol.labels)]
            out=replay(test,xe,g,ttl)
            tr=replay(train,te,g,ttl)
            assert abs(tr['cost']-sol.cost)<1e-4 and tr['hits']==sol.hits
            rows.append(dict(dataset=name,price=price,train_value=sol.value,train_hits=sol.hits,
                train_cost=sol.cost,test_utility=(out['hits']-price*out['cost'])/out['input_blocks'],
                prepare_seconds=prep,fit_seconds=elapsed,thresholds=sum(len(v)-1 for v in grids),
                **diag,**{k:v for k,v in out.items() if k!='bins'}))
            profiles[f'{name}_{price:g}']=dict(ttl=ttl,top=g.top)
        print(name,'done',len(cert.group),'certificates',flush=True)
    pd.DataFrame(rows).to_csv(ROOT/'results/event_grid_results.csv',index=False)
    (ROOT/'results/event_grid_profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')

if __name__=='__main__':run()
