"""Run the frozen chronological evaluation; write every method and price."""
from pathlib import Path
import json, sys, time, platform, hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from prefix_retention.trace import load_trace, split_trace, Grouping, GRID, PRICES, tables
from prefix_retention.optimize import price_solution, budget_frontier
from prefix_retention.replay import replay, capacity_replay


def clean(result):
    return {k: v for k, v in result.items() if k != 'bins'}


def paired_interval(a, b, price, seed=20260923):
    # Descriptive resampling of contiguous one-minute buckets, not iid requests.
    rng = np.random.default_rng(seed)
    diff = a[:, 0] - b[:, 0] - price * (a[:, 1] - b[:, 1])
    denom = a[:, 2]
    choices = rng.integers(0, len(diff), (10000, len(diff)))
    sums = denom[choices].sum(axis=1)
    estimates = diff[choices].sum(axis=1) / np.maximum(sums, 1)
    return np.quantile(estimates, [.025, .975]).tolist()


def main():
    rows, contrasts, profiles, diagnostics, frontiers = [], [], {}, {}, {}
    all_start = time.perf_counter()
    for name in ['conversation', 'toolagent', 'synthetic']:
        requests, raw = load_trace(ROOT/'data/raw'/f'{name}.jsonl')
        windows = split_trace(requests)
        train, train_end = windows[0]
        valid, valid_end = windows[1]
        test, test_end = windows[2]
        diagnostics[name] = dict(requests=len(requests), full_block_lookups=sum(len(r.blocks) for r in requests),
            unique_full_blocks=len(set(b for r in requests for b in r.blocks)), horizon=requests[-1].time,
            input_tokens=sum(r['input_length'] for r in raw),
            splits={k:dict(requests=len(w[0]), full_blocks=sum(len(r.blocks) for r in w[0]), seconds=w[1])
                    for k,w in zip(['train','validation','test'], windows)})
        cached = {}
        groups = {}
        for kind in ['global', 'group', 'depth', 'group_depth']:
            g = Grouping(train, kind)
            groups[kind] = g
            h, c = tables(train, train_end, g)
            cached[kind] = (h, c)
        profiles[name] = {}
        for price in PRICES:
            outcomes, validation_utility = {}, {}
            for kind in ['global', 'group', 'depth', 'group_depth', 'unconstrained']:
                base = 'group_depth' if kind == 'unconstrained' else kind
                g = groups[base]
                h, c = cached[base]
                start = time.perf_counter()
                if kind == 'unconstrained':
                    labels = np.argmax(h-price*c, axis=1)
                    objective = float((h-price*c)[np.arange(len(labels)), labels].sum())
                else:
                    sol = price_solution(h, c, g.parents, price)
                    labels, objective = sol.labels, sol.value
                elapsed = time.perf_counter()-start
                ttl = GRID[labels]
                profiles[name][f'{kind}_{price:g}'] = dict(ttl=ttl.tolist(), names=g.names, top=g.top, train_objective=objective)
                out = replay(test, test_end, g, ttl)
                outcomes[kind] = out
                rows.append(dict(dataset=name, method=kind, price=price, fit_seconds=elapsed,
                    utility_per_block=(out['hits']-price*out['cost'])/out['input_blocks'], **clean(out)))
                if kind in ['depth', 'group_depth']:
                    v = replay(valid, valid_end, g, ttl)
                    validation_utility[kind] = v['hits']-price*v['cost']
            selected = max(['depth','group_depth'], key=lambda k: validation_utility[k])
            out = outcomes[selected]
            rows.append(dict(dataset=name, method='selected', selected=selected, price=price, fit_seconds=0.,
                utility_per_block=(out['hits']-price*out['cost'])/out['input_blocks'], **clean(out)))
            for comparator in ['global', 'group']:
                ref = outcomes[comparator]
                diff = (out['hits']-ref['hits']-price*(out['cost']-ref['cost']))/out['input_blocks']
                low, high = paired_interval(out['bins'], ref['bins'], price)
                contrasts.append(dict(dataset=name, price=price, comparator=comparator, selected=selected,
                    difference=diff, bootstrap_low=low, bootstrap_high=high,
                    buckets=len(out['bins']), selected_hit=out['hit_rate'], baseline_hit=ref['hit_rate'],
                    selected_mean=out['mean_blocks'], baseline_mean=ref['mean_blocks']))
            print(name, f'price={price:g}', 'selected='+selected,
                  'utility='+str(round((out['hits']-price*out['cost'])/out['input_blocks'],5)), flush=True)
        for kind in ['global','group','depth','group_depth']:
            start = time.perf_counter()
            h,c = cached[kind]
            points, cert = budget_frontier(h,c,groups[kind].parents)
            frontiers[f'{name}_{kind}'] = dict(seconds=time.perf_counter()-start,
                points=[dict(hits=p.hits,cost=p.cost,labels=p.labels.tolist()) for p in points], certificates=cert)
        for capacity in [256, 1024, 4096, 16384]:
            for fifo in [False, True]:
                out = capacity_replay(test, test_end, capacity, fifo)
                rows.append(dict(dataset=name,method='FIFO' if fifo else 'LRU', capacity=capacity, **out))
        out = replay(test,test_end,groups['global'],[test_end+1])
        rows.append(dict(dataset=name,method='unbounded_reference',**clean(out)))
    pd.DataFrame(rows).to_csv(ROOT/'results/policy_results.csv',index=False)
    pd.DataFrame(contrasts).to_csv(ROOT/'results/contrasts.csv',index=False)
    for file,obj in [('profiles',profiles),('data_summary',diagnostics),('frontiers',frontiers)]:
        (ROOT/f'results/{file}.json').write_text(json.dumps(obj,indent=2)+'\n')
    metadata=dict(elapsed_seconds=time.perf_counter()-all_start,python=platform.python_version(),platform=platform.platform(),
                  grid=GRID.tolist(),prices=PRICES.tolist(),seed=20260923,
                  protocol_sha256=hashlib.sha256((ROOT/'notes/protocol.md').read_bytes()).hexdigest())
    (ROOT/'results/run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('Completed',metadata,flush=True)

if __name__ == '__main__':
    main()
