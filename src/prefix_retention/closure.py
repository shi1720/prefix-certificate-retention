"""Exact usable-prefix TTL optimization by a maximum-closure reduction.

This is a new cache accounting formulation implemented with the established
maximum-closure/minimum-cut algorithm, not a new generic graph-cut algorithm.
"""
from dataclasses import dataclass
from itertools import groupby
import numpy as np
import maxflow
from .optimize import Solution
from .trace import TICKS


@dataclass
class Certificates:
    """A DAG of hit prerequisites, compressed by identical certificate chains."""
    group: np.ndarray
    threshold: np.ndarray
    previous: np.ndarray
    multiplicity: np.ndarray
    lookup_count: int


def build_certificates(requests, grouping, grid):
    last = {}
    index = {}
    groups, thresholds, previous, mult = [], [], [], []
    lookups = 0
    ragged = isinstance(grid, (list, tuple)) and len(grid) > 0 and np.ndim(grid[0]) > 0
    grids = grid if ragged else [grid]*len(grouping.parents)
    grid_ticks = [np.rint(np.asarray(x)*TICKS).astype(np.int64) for x in grids]
    for t, batch in groupby(requests, key=lambda r: round(r.time*TICKS)):
        writes = set()
        for r in batch:
            chain = -1
            possible = True
            for block, g in zip(r.blocks, grouping.labels_for(r.blocks)):
                lookups += 1
                writes.add(block)
                if not possible:
                    continue
                if block not in last:
                    possible = False
                    continue
                age = t-last[block]
                k = max(1, int(np.searchsorted(grid_ticks[g], age, side='left')))
                if k >= len(grids[g]):
                    possible = False
                    continue
                key = (chain, g, k)
                if key not in index:
                    index[key] = len(groups)
                    groups.append(g); thresholds.append(k); previous.append(chain); mult.append(0)
                chain = index[key]
                mult[chain] += 1
        for block in writes:
            last[block] = t
    return Certificates(np.asarray(groups,dtype=int),np.asarray(thresholds,dtype=int),
                        np.asarray(previous,dtype=int),np.asarray(mult,dtype=int),lookups)


def certificate_hits(cert, labels):
    active = np.zeros(len(cert.group),dtype=bool)
    for i in range(len(active)):
        active[i] = labels[cert.group[i]] >= cert.threshold[i] and (cert.previous[i] < 0 or active[cert.previous[i]])
    return float(cert.multiplicity[active].sum())


def solve_closure(cert, cost, price, parents=None):
    """Optimize H_usable - price*C over arbitrary static grouped TTL labels.

    Add parents only to verify the coherent restriction against the tree DP.
    The returned objective is re-evaluated independently of the flow objective.
    The graph's mincut identity is checked in floating-point tolerance.
    """
    cost = [np.asarray(row, dtype=float) for row in cost]
    if price < 0 or not np.isfinite(price) or any(np.any(np.diff(row) < -1e-7) for row in cost):
        raise ValueError("Nonnegative price and nondecreasing finite costs required")
    if any(not np.isfinite(row).all() or not len(row) or row[0] != 0 for row in cost):
        raise ValueError("Finite costs and zero no-cache cost required")
    n = len(cost)
    if parents is not None and len({len(row) for row in cost}) > 1:
        raise ValueError('Coherent verification requires a common grid')
    offsets = np.r_[0, np.cumsum([len(row)-1 for row in cost])]
    nchoice = int(offsets[-1])
    nbonus = len(cert.group)
    graph = maxflow.Graph[float](nchoice+nbonus, 3*(nchoice+nbonus))
    graph.add_nodes(nchoice+nbonus)
    total_reward = float(cert.multiplicity.sum())
    infinity = total_reward + 1.  # larger than the all-sink feasible cut
    def ynode(v,j):
        return int(offsets[v])+int(j)-1
    dc = [np.maximum(np.diff(row),0.) for row in cost]
    for v in range(n):
        for j in range(1,len(cost[v])):
            node = ynode(v,j)
            graph.add_tedge(node,0.,price*dc[v][j-1])
            if j>1:
                graph.add_edge(node,ynode(v,j-1),infinity,0.)
            if parents is not None and parents[v]>=0:
                graph.add_edge(node,ynode(parents[v],j),infinity,0.)
    for i in range(nbonus):
        node=nchoice+i
        graph.add_tedge(node,float(cert.multiplicity[i]),0.)
        graph.add_edge(node,ynode(cert.group[i],cert.threshold[i]),infinity,0.)
        if cert.previous[i]>=0:
            graph.add_edge(node,nchoice+int(cert.previous[i]),infinity,0.)
    flow=graph.maxflow()
    labels=np.zeros(n,dtype=np.int32)
    for v in range(n):
        for j in range(1,len(cost[v])):
            if graph.get_segment(ynode(v,j))==0:
                labels[v]=j
    # Canonicalize zero-weight/slack cut choices: retain only thresholds needed
    # for training hits already selected. This preserves every positive reward
    # and weakly reduces cost, avoiding arbitrary retention on unobserved groups.
    active = np.zeros(nbonus,dtype=bool)
    needed = np.zeros(n,dtype=np.int32)
    for i in range(nbonus):
        active[i] = labels[cert.group[i]] >= cert.threshold[i] and (cert.previous[i]<0 or active[cert.previous[i]])
        if active[i]:
            needed[cert.group[i]] = max(needed[cert.group[i]],cert.threshold[i])
    if parents is not None:
        for v in range(n-1,-1,-1):
            if parents[v]>=0:
                needed[parents[v]]=max(needed[parents[v]],needed[v])
    labels=needed
    h=certificate_hits(cert,labels)
    c=float(sum(cost[v][labels[v]] for v in range(n)))
    objective=h-price*c
    residual=abs(objective-(total_reward-flow))
    if residual>1e-6*max(1.,total_reward):
        raise ArithmeticError(f"Flow/certificate objective mismatch: {residual}")
    return Solution(labels,objective,h,c), dict(nodes=nchoice+nbonus,certificates=nbonus,
              flow_objective=total_reward-flow,residual=residual)
