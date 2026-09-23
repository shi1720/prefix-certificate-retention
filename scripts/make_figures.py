"""Build manuscript figures and tables directly from the committed result CSVs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures'
TAB=ROOT/'paper/tables'
OUT.mkdir(exist_ok=True,parents=True); TAB.mkdir(exist_ok=True,parents=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,
    'axes.labelsize':8,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,
    'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,
    'grid.alpha':.18,'figure.dpi':150,'savefig.bbox':'tight'})
COLORS=['#163d6b','#009b83','#cf5b3a','#8457a8','#6d737c']
NAMES={'conversation':'Conversation','toolagent':'Tool agent','synthetic':'Synthetic'}
prices=np.array([0,.0001,.0003,.001,.003,.01,.03,.1,.3,1.])
ticks=['0','','',r'$10^{-3}$','',r'$10^{-2}$','',r'$10^{-1}$','','1']
p=pd.read_csv(ROOT/'results/policy_results.csv')
c=pd.read_csv(ROOT/'results/closure_results.csv')
e=pd.read_csv(ROOT/'results/event_grid_results.csv')
contr=pd.read_csv(ROOT/'results/contrasts.csv')
summary=json.loads((ROOT/'results/data_summary.json').read_text())

def save(fig,name):
    fig.savefig(OUT/f'{name}.pdf')
    fig.savefig(OUT/f'{name}.png',dpi=200)
    if name=='utility_differences':
        fig.set_size_inches(8.5,2.7)
        fig.tight_layout()
        fig.savefig(ROOT/'output/poster-utility.pdf')
    plt.close(fig)

fig,axs=plt.subplots(1,3,figsize=(6.3,2.7))
for ax,(name,title) in zip(axs,NAMES.items()):
    for j,comp in enumerate(['global','group']):
        q=contr[(contr.dataset==name)&(contr.comparator==comp)].sort_values('price')
        ax.plot(range(10),q.difference,color=COLORS[j],marker='o',ms=3,label=f'vs. {comp} TTL')
        ax.fill_between(range(10),q.bootstrap_low,q.bootstrap_high,color=COLORS[j],alpha=.12)
    ax.axhline(0,color='#444',lw=.7)
    ax.set_xticks(range(10),ticks);ax.set_xlabel(r'Storage price $\lambda$')
    ax.set_title(title);ax.ticklabel_format(axis='y',style='plain')
axs[0].set_ylabel('Test utility difference per input block')
axs[0].legend(frameon=False,loc='upper left')
fig.tight_layout();save(fig,'utility_differences')

fig,axs=plt.subplots(1,3,figsize=(6.3,3.0))
for ax,(name,title) in zip(axs,NAMES.items()):
    for j,method in enumerate(['global','group','selected']):
        q=p[(p.dataset==name)&(p.method==method)].sort_values('price',ascending=False)
        ax.plot(q.mean_blocks,q.hit_rate,color=COLORS[j],marker='o',ms=3,
            label={'global':'Global TTL','group':'Group TTL','selected':'Selected coherent'}[method],lw=1.3)
    q=e[e.dataset==name].sort_values('price',ascending=False)
    ax.plot(q.mean_blocks,q.hit_rate,':',color=COLORS[3],marker='.',ms=4,label='PCR: all event ages')
    q=p[(p.dataset==name)&(p.method=='LRU')]
    ax.scatter(q.mean_blocks,q.hit_rate,marker='x',s=24,color='#333',label='LRU (hard capacity)',zorder=5)
    ax.set_xscale('symlog',linthresh=1)
    ax.set_xticks([0,1,100,10000],['0','1',r'$10^2$',r'$10^4$'])
    ax.set_xlabel('Mean resident full blocks');ax.set_title(title)
axs[0].set_ylabel('Usable prefix-hit fraction')
fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,-.05),ncol=3,frameon=False)
fig.tight_layout(rect=[0,.12,1,1]);save(fig,'test_tradeoffs')

base=c[(c.resolution=='native')&(c.grouping=='group_depth')&(c['mode']=='cut')]
joined=e.merge(base,on=['dataset','price'],suffixes=('_event','_grid'))
fig,axs=plt.subplots(1,2,figsize=(6.3,2.6))
for j,(name,title) in enumerate(NAMES.items()):
    q=joined[joined.dataset==name].sort_values('price')
    n=summary[name]['splits']['train']['full_blocks']
    axs[0].plot(range(10),(q.train_value_event-q.train_value_grid)/n,'o-',ms=3,color=COLORS[j],label=title)
    axs[1].plot(range(10),q.test_utility_event-q.test_utility_grid,'o-',ms=3,color=COLORS[j])
for ax in axs:
    ax.axhline(0,color='#555',lw=.7);ax.set_xticks(range(10),ticks);ax.set_xlabel(r'Storage price $\lambda$')
axs[0].set_title('Training: event ages minus fixed grid')
axs[1].set_title('Test: event ages minus fixed grid')
axs[0].set_ylabel('Utility difference per input block');axs[0].legend(frameon=False)
fig.tight_layout();save(fig,'event_grid_effect')

front=json.loads((ROOT/'results/frontiers.json').read_text())
fig,axs=plt.subplots(1,3,figsize=(6.3,2.7))
for ax,(name,title) in zip(axs,NAMES.items()):
    for j,kind in enumerate(['global','group','group_depth']):
        pts=front[f'{name}_{kind}']['points'];n=summary[name]['splits']['train']['full_blocks']
        t=summary[name]['splits']['train']['seconds']
        ax.plot([v['cost']/t for v in pts],[v['hits']/n for v in pts],color=COLORS[j],lw=1.5,
                label={'global':'Global TTL','group':'Group TTL','group_depth':'Group-depth coherent'}[kind])
    ax.set_xscale('symlog',linthresh=1);ax.set_xticks([0,1,100,10000],['0','1',r'$10^2$',r'$10^4$'])
    ax.set_xlabel('Expected mean blocks (training)');ax.set_title(title)
axs[0].set_ylabel('Expected usable prefix-hit fraction');axs[0].legend(frameon=False)
fig.tight_layout();save(fig,'budget_frontiers')

# A schematic built entirely from vector primitives, with no external artwork.
fig,axs=plt.subplots(1,2,figsize=(6.3,2.5),gridspec_kw={'width_ratios':[1.0,1.25]})
ax=axs[0];ax.set_xlim(-.6,20.7);ax.set_ylim(-.6,2.6);ax.set_yticks([.4,1.5],['Child B','Ancestor A'])
ax.set_xticks([0,5,10,15,20]);ax.set_xlabel('Time (seconds)');ax.grid(axis='x',alpha=.2)
ax.hlines(1.5,0,11,color=COLORS[0],lw=7,alpha=.28)
ax.hlines(.4,0,20,color=COLORS[1],lw=7,alpha=.28)
ax.scatter(range(11),[1.5]*11,color=COLORS[0],s=22,zorder=3)
ax.scatter([0,10],[.4,.4],color=COLORS[1],s=28,zorder=3)
ax.text(12,1.52,r'$\tau_A=1$',va='center',color=COLORS[0])
ax.text(11,.62,r'$\tau_B=10$',color=COLORS[1])
ax.text(.3,2.2,'Short ancestor timeout suffices',fontsize=7.5,weight='bold')
ax.text(.3,-.15,r'$\lambda=0.04$: exact 9.76; coherent 9.56',fontsize=7)
ax=axs[1];ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(0,5)
nodes={'yA':(2,3.55,r'$y_{A,1}$'),'yB1':(5,3.55,r'$y_{B,1}$'),'yB2':(8,3.55,r'$y_{B,2}$'),
       'z1':(2,1.6,r'$z_{r,1}$'),'z2':(6.5,1.6,r'$z_{r,2}$')}
for name,(x,y,label) in nodes.items():
    color=COLORS[0] if name.startswith('y') else COLORS[1]
    ax.add_patch(FancyBboxPatch((x-.65,y-.35),1.3,.7,boxstyle='round,pad=.08',fc=color,ec='none'))
    ax.text(x,y,label,ha='center',va='center',color='white',fontsize=9)
for a,b in [('yB2','yB1'),('z1','yA'),('z2','yB2'),('z2','z1')]:
    x,y,_=nodes[a];u,v,_=nodes[b]
    ax.add_patch(FancyArrowPatch((x,y),(u,v),arrowstyle='-|>',mutation_scale=12,color='#42546b',
                               shrinkA=24,shrinkB=25,lw=1.3))
ax.text(5,4.65,'Timeout thresholds + prefix prerequisites',ha='center',fontsize=7.5,weight='bold')
ax.text(5,4.15,r'Threshold weight: $-\lambda\,\Delta C_g$',ha='center',fontsize=8)
ax.text(5,.53,'Positive hit rewards; arrows require their targets.',ha='center',fontsize=7)
ax.text(5,.1,'Source/sink arcs omitted.',ha='center',fontsize=7)
fig.tight_layout();save(fig,'certificate_model')

# Complete utility table: no price selection or omission of negative outcomes.
lines=[r'\begin{tabular}{llrrrrrr}',r'\toprule',
       r'Trace & $\lambda$ & Global & Group & Selected & PCR grid & PCR ages & Sel.\ $-$ Global\\',r'\midrule']
for name in NAMES:
    for price in prices:
        vals=[]
        for method in ['global','group','selected']:
            vals.append(float(p[(p.dataset==name)&(p.method==method)&(p.price==price)].utility_per_block.iloc[0]))
        vals.append(float(base[(base.dataset==name)&(base.price==price)].test_utility.iloc[0]))
        vals.append(float(e[(e.dataset==name)&(e.price==price)].test_utility.iloc[0]))
        vals.append(vals[2]-vals[0])
        lines.append(f'{NAMES[name]} & {price:g} & '+' & '.join(f'{v:.5f}' for v in vals)+r'\\')
    if name!='synthetic':lines.append(r'\midrule')
lines.extend([r'\bottomrule',r'\end{tabular}'])
(TAB/'complete_utilities.tex').write_text('\n'.join(lines)+'\n')

lines=[r'\begin{tabular}{llrrrr}',r'\toprule',r'Trace & Policy & Capacity & Hit fraction & Mean blocks & Peak blocks\\',r'\midrule']
for name in NAMES:
    for _,r in p[(p.dataset==name)&(p.method.isin(['LRU','FIFO','unbounded_reference']))].iterrows():
        method='Unbounded' if r.method=='unbounded_reference' else r.method
        cap='--' if pd.isna(r.capacity) else f'{r.capacity:.0f}'
        lines.append(f'{NAMES[name]} & {method} & {cap} & {r.hit_rate:.5f} & {r.mean_blocks:.2f} & {r.peak_blocks:.0f}'+r'\\')
    if name!='synthetic':lines.append(r'\midrule')
lines.extend([r'\bottomrule',r'\end{tabular}'])
(TAB/'capacity_baselines.tex').write_text('\n'.join(lines)+'\n')

lines=[r'\begin{tabular}{lrrrrr}',r'\toprule',r'Trace & Grid nodes & Event nodes & Grid solve (ms) & Event solve (ms) & Prep. (s)\\',r'\midrule']
for name in NAMES:
    a=base[base.dataset==name];b=e[e.dataset==name]
    lines.append(f'{NAMES[name]} & {int(a.nodes.iloc[0]):,} & {int(b.nodes.iloc[0]):,} & {a.fit_seconds.median()*1000:.2f} & {b.fit_seconds.median()*1000:.2f} & {b.prepare_seconds.iloc[0]:.2f}'+r'\\')
lines.extend([r'\bottomrule',r'\end{tabular}'])
(TAB/'runtime.tex').write_text('\n'.join(lines)+'\n')
print('Generated five vector figures and three result tables.')
