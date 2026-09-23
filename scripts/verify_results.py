"""Cross-check aggregate manuscript claims against every saved result row."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
c=pd.read_csv(ROOT/'results/closure_results.csv')
e=pd.read_csv(ROOT/'results/event_grid_results.csv')
p=pd.read_csv(ROOT/'results/policy_results.csv')
summary=json.loads((ROOT/'results/data_summary.json').read_text())
assert len(c)==480 and len(e)==30
assert sum(v['requests'] for v in summary.values())==39632
assert sum(summary[n]['requests'] for n in ['conversation','toolagent'])==35639
native=c[c.resolution=='native']
pv=native.pivot(index=['dataset','grouping','price'],columns='mode',values='train_value')
gaps=pv.cut-pv.dp
assert (gaps>=-1e-7).all()
assert (abs(gaps)<1e-7).sum()==118
assert (native.train_value<=native.relaxed_bound+1e-7).all()
base=native[(native.grouping=='group_depth')&(native['mode']=='cut')]
j=e.merge(base,on=['dataset','price'],suffixes=('_event','_grid'))
assert (j.train_value_event>=j.train_value_grid-1e-7).all()
assert c.residual.dropna().max()<1e-7 and e.residual.max()<1e-7
assert (c.hits<=c.raw_hits).all() and (p.hits<=p.raw_hits).all()
assert (c.mean_blocks<=c.peak_blocks+1e-7).all()
for item in json.loads((ROOT/'data/manifest.json').read_text()):
    assert hashlib.sha256((ROOT/'data/raw'/f"{item['name']}.jsonl").read_bytes()).hexdigest()==item['sha256']
report=dict(requests=39632,production_derived_requests=35639,native_cases=len(pv),
    coherent_equal_cases=int((abs(gaps)<1e-7).sum()),max_coherence_gap=float(gaps.max()),
    max_native_flow_residual=float(native.residual.max()),max_event_flow_residual=float(e.residual.max()),
    data_hashes_verified=True,full_closure_rows=len(c),event_grid_rows=len(e),
    continuous_training_dominance_verified=True)
(ROOT/'results/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
