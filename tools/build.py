import csv, json, re, html
import os
# Path to a checkout of github.com/ego2act/ego2act (default: a sibling folder)
EGO2ACT=os.environ.get('EGO2ACT_ROOT',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','ego2act'))+'/'
R=EGO2ACT+'analysis/results/'
TOOLS=os.path.dirname(os.path.abspath(__file__))+'/'
SITE=os.path.dirname(TOOLS[:-1])+'/'
SCORES=EGO2ACT+'analysis/csv/scores_ego2act.csv'
# Static fragments (failure carousels from the paper appendix, paper Tables 2 and 3b) live in tools/fragments/
# and are post-processed below (logos, score pills, human labels).
frag=lambda n: open(TOOLS+'fragments/'+n+'.html').read()
fail_inner,t2,t3,failov,jtree=frag('fail'),frag('t2'),frag('t3'),frag('overview'),frag('jtree')
assert 'fgroup' in fail_inner and 'Table 2' in t2 and 'Table 3(b)' in t3

LB={}
for r in csv.DictReader(open(R+'leaderboard.csv')):
    LB[(r['evaluator'],r['group'])]={k:(float(r[k]) if r[k] else None) for k in ('task','physics','overall')}
MODELS=[('seedance_2_0','Seedance-2.0','ByteDance','bytedance'),('kling_v3_pro','Kling-v3-Pro','Kuaishou','kuaishou'),
('wan_2_7','Wan-2.7','Alibaba','alibaba'),('grok_imagine_video_1_5','Grok-1.5','xAI','xai'),
('minimax_h3','MiniMax-H3','MiniMax','minimax'),('cosmos_3','Cosmos-3 Nano','NVIDIA','nvidia')]
MODELS.sort(key=lambda m:-LB[('ego2act',m[0])]['overall'])
f1=lambda x:'&ndash;' if x is None else f'{x:.1f}'
LOGO={k:(name,org,logo) for k,name,org,logo in MODELS}
NAME2KEY={name:k for k,name,org,logo in MODELS}

# ---- shared label helpers (app.js builds the same markup for the comparison grid)
def person(ok):
    badge=('<circle cx="17" cy="17" r="6" fill="#15803d"/><path d="M14.2 17.1l2 2 3.6-3.8" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>' if ok else
           '<circle cx="17" cy="17" r="6" fill="#b91c1c"/><path d="M14.7 14.7l4.6 4.6M19.3 14.7l-4.6 4.6" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>')
    return ('<svg class=pic viewBox="0 0 24 24" width=18 height=18 aria-hidden=true><circle cx="10" cy="7" r="4" fill="currentColor"/>'
            '<path d="M2 21c0-4.4 3.6-8 8-8 1.6 0 3 .4 4.3 1.2" fill="currentColor"/>'+badge+'</svg>')
def human(ok): return f'<span class="who {"ok" if ok else "bad"}">{person(ok)}Human ({"correct" if ok else "wrong"})</span>'
def pcls(x):
    if x is None: return 'na'
    x=round(x)   # band follows the number shown on the badge
    return 'hi' if x>=70 else 'gd' if x>=60 else 'mid' if x>=30 else 'lo'
def pill(x): return f'<b class="score {pcls(x)}"{" title=\"no judge score\"" if x is None else ""}>{"&ndash;" if x is None else round(x)}</b>'
def logo_img(k,size=18):
    name,org,logo=LOGO[k]
    return f'<img src="assets/logos/{logo}.png" width={size} height={size} alt="{org}" loading=lazy>'

# ---- human labels in the paper tables
for a,b in (('Human (+)','Human (correct)'),('Human (&minus;)','Human (wrong)'),('Human (−)','Human (wrong)'),('Human (-)','Human (wrong)')):
    t2,t3,fail_inner=(x.replace(f'<th scope=row>{a}</th>',f'<th scope=row>{human("correct" in b)}</th>').replace(a,b) for x in (t2,t3,fail_inner))

# ---- failure carousel tags: logo + model name + Ego2ActJudge Final pill for that exact video
_rows=list(csv.DictReader(open(SCORES)))
SC={r['video_id']:r['ego2act_score'] for r in _rows}
# the judge returned no Physics score for this video, so its badge shows the Task score the judge did return
SC['coffee_beans::cosmos_3__202']=next(r['ego2act_task'] for r in _rows if r['video_id']=='coffee_beans::cosmos_3__202')
def tag(m):
    k,case,seed,name=m.group(2),m.group(3),m.group(4),m.group(6)
    v=SC.get(f'{case}::{k}__{seed}'); v=float(v) if v else None
    return m.group(1)+m.group(5)+f'<span class=tag>{logo_img(k)}<span>{name}</span>{pill(v)}</span>'
fail_inner,n=re.subn(r'(data-src="assets/fail/(\w+?)__(\w+?)__seed_(\d+)\.mp4")(.*?)<span class=tag>([^<]*)</span>',tag,fail_inner)
assert n>0 and 'class=tag>' not in re.sub(r'class=tag><img','',fail_inner), n

# --- model lineup: two ranked lists, human panel vs Ego2ActJudge
def ranked(ev,title,cls,note):
    rows=sorted(MODELS,key=lambda m:-LB[(ev,m[0])]['overall'])
    li=''.join(f'<li><i>#{i}</i><img src="assets/logos/{logo}.png" width=22 height=22 alt="{org} logo" loading=lazy onerror="this.remove()"><b>{name}</b><em>{f1(LB[(ev,k)]["overall"])}</em></li>'
               for i,(k,name,org,logo) in enumerate(rows,1))
    return f'<div class="rank {cls}"><h3>{title}</h3><p>{note}</p><ul>{li}</ul></div>'
lineup=(ranked('human','Human raters<sup>*</sup> <span class="ourtag man">Manual</span>','hum','Final score, 0&ndash;100')
        +ranked('ego2act','<span class=sc>Ego2ActJudge</span> <span class=ourtag>Auto</span>','jdg','Final score, 0&ndash;100, all 110 cases'))

# --- leaderboard (human + judge): best bold, second-best underlined among generators; Task blue, Physics purple
rows=[]
RANK={}
for ev in ('human','ego2act'):
    for x in ('task','physics','overall'):
        vals=sorted({round(LB[(ev,k)][x],1) for k,*_ in MODELS if LB[(ev,k)][x] is not None},reverse=True)
        RANK[(ev,x)]=vals[:2]
def cellv(ev,g,x,rank):
    v=LB[(ev,g)][x]; s=f1(v)
    if rank and v is not None:
        r=RANK[(ev,x)]
        if round(v,1)==r[0]: s=f'<b>{s}</b>'
        elif len(r)>1 and round(v,1)==r[1]: s=f'<u>{s}</u>'
    c={'task':' class=vt','physics':' class=vp'}.get(x,'')
    return f'<td{c}>{s}</td>'
def row(label,g,cls='',rank=False):
    return f'<tr{cls}><th scope=row>{label}</th>'+''.join(cellv('human',g,x,rank) for x in ('task','physics','overall'))+''.join(cellv('ego2act',g,x,rank) for x in ('task','physics','overall'))+'</tr>'
rows.append(row(human(True),'human_reference',' class=hum'))
rows.append(row(human(False),'human_wrong',' class=hum'))
for i,(k,name,org,logo) in enumerate(MODELS):
    rows.append(row(f'<img src="assets/logos/{logo}.png" width=16 height=16 alt="" onerror="this.remove()"><span class=nm>{name}</span>',k,' class=sep' if i==0 else '',True))
lbtable='\n'.join(rows)

# --- heatmap
S=json.load(open(R+'subgoal_action_types.json'))
fams=S['families']; FK=[f'A{i}' for i in range(1,10)]
def cell(v,n,metric,mname,fname,extra=''):
    if v is None: return '<td class=na>&ndash;</td>'
    p=round(v*100); lvl=min(8,int(v*100)//12.5)
    return f'<td class="c{int(lvl)}{extra}" data-t="{mname} &middot; {fname}: {p}% {metric} ({n})">{p}</td>'
def heat(metric):
    out=['<thead><tr><th></th><th scope=col class=all><span>Overall</span></th>'+''.join(f'<th scope=col title="{html.escape(fams[f]["name"])}"><span>{html.escape(fams[f]["name"].split("/")[0])}</span></th>' for f in FK)+'</tr></thead><tbody>']
    for k,name,org,logo in MODELS:
        bm=S['by_model'][k]; tds=[]
        for f in FK:
            d=bm.get(f)
            if metric=='task': v,n=(d['task']['complete'],f"n = {d['task']['n']}") if d and d.get('task') and d['task']['n'] else (None,0); lab='complete'
            else: v,n=(d['physics']['valid'],f"n = {d['physics']['judgeable']}") if d and d.get('physics') and d['physics']['judgeable'] and d['physics']['valid'] is not None else (None,0); lab='valid'
            tds.append(cell(v,n,lab,name,fams[f]['name']))
        ls=S['level_share'][k]
        allv= ls['task']['3'] if metric=='task' else ls['physics']['4']/(1-ls['physics']['NA'])
        tds.insert(0,cell(allv,'all subgoals',('complete' if metric=='task' else 'valid'),name,'all families',' all'))
        out.append(f'<tr><th scope=row><img src="assets/logos/{logo}.png" width=16 height=16 alt="" onerror="this.remove()"><span class=nm>{name}</span></th>'+''.join(tds)+'</tr>')
    out.append('</tbody>'); return '\n'.join(out)
heat_task=heat('task'); heat_phys=heat('physics')
cov=json.load(open(R+'benchmark_statistics.json'))['family_coverage']

A=lambda e,ax:[r for r in json.load(open(R+'human_alignment.json'))['alignment'] if r['evaluator']==e and r['axis']==ax][0]['pearson']
ra=json.load(open(R+'ranking_agreement.json'))
fc=S['failure_concentration']['pooled']['task_level0_or_2']
hj=json.load(open(R+'human_alignment.json'))['agreement']; icc=[a for a in hj if a['axis']=='final'][0]['icc']
V=dict(
 best_h=LB[('human','seedance_2_0')]['overall'], best_ht=LB[('human','seedance_2_0')]['task'], cos_h=LB[('human','cosmos_3')]['overall'],
 best_j=LB[('ego2act','seedance_2_0')]['overall'], cos_j=LB[('ego2act','cosmos_3')]['overall'],
 kling_hp=LB[('human','kling_v3_pro')]['physics'], cos_hp=LB[('human','cosmos_3')]['physics'], seed_hp=LB[('human','seedance_2_0')]['physics'],
 r=A('ego2act','final'), rb=A('rbench','final'), vs=A('videoscore','final'), loo=A('human_leave_one_out','final'),
 rho=ra['spearman'], fc=fc*100, a4=fams['A4']['task']['complete']*100, a6=fams['A6']['task']['complete']*100,
 hp=LB[('ego2act','human_reference')]['overall'], hm=LB[('ego2act','human_wrong')]['overall'],
 vsp=LB[('videoscore','human_reference')]['overall'], vsm=LB[('videoscore','human_wrong')]['overall'], icc=icc)
print({k:round(v,3) for k,v in V.items()})

# suite construction strip: counts from the benchmark statistics, model list and seeds in the score file
_bc=json.load(open(R+'benchmark_statistics.json'))['benchmark_cases']
_seeds=len({x['seed'] for x in csv.DictReader(open(SCORES)) if x['source_type']=='ai'})
_hper=3  # paper protocol: 3 successful + 3 unsuccessful human attempts per case
V.update(b_cases=_bc,b_hper=_hper,b_human=_bc*2*_hper,b_models=len(MODELS),b_seeds=_seeds,b_gen=_bc*len(MODELS)*_seeds)
V['b_total']=V['b_human']+V['b_gen']; assert V['b_total']==2640, V['b_total']
import charts
SCAT,SCN=charts.scatter(MODELS); STAB=charts.stability(MODELS); ABLN=charts.ablation()
V.update(sc_n=SCN['n'],sc_ht=SCN['ht'],sc_hp=SCN['hp'],sc_jt=SCN['jt'],sc_jp=SCN['jp'],sc_dt=SCN['dt'],sc_dp=SCN['dp'])
print('scatter', {k:(round(v,2) if isinstance(v,float) else v) for k,v in SCN.items() if k!='per'})
for nm,m,n in SCN['per']: print('  ',nm,n,[round(x,1) for x in m])
tpl=open(TOOLS+'template.html').read()
# Table 2 / 3b: model logo before each generator row label
for _k,_name,_org,_logo in MODELS:
    _img=f'<img src="assets/logos/{_logo}.png" width=16 height=16 alt="" class=rl onerror="this.remove()">'
    t2=t2.replace(f'<th scope=row>{_name}</th>',f'<th scope=row>{_img}{_name}</th>')
    t3=t3.replace(f'<th scope=row>{_name}</th>',f'<th scope=row>{_img}{_name}</th>')
for k,v in dict(LINEUP=lineup,LBTABLE=lbtable,HEAT_TASK=heat_task,HEAT_PHYS=heat_phys,FAIL=fail_inner,FAILOV=failov,JTREE=jtree,SCAT=SCAT,STAB=STAB,T2=t2,T3=t3).items():
    tpl=tpl.replace('{{'+k+'}}',v)

# success vs failure: Mann-Whitney AUC and one-sided p (normal approximation) on Ego2ActJudge Final
import math as _m, bisect as _b
_r=list(csv.DictReader(open(SCORES)))
_c=[float(x['ego2act_score']) for x in _r if x['source_type']=='human_reference' and x['ego2act_score']]
_w=sorted(float(x['ego2act_score']) for x in _r if x['source_type']=='human_wrong' and x['ego2act_score'])
_U=sum(_b.bisect_left(_w,v)+0.5*(_b.bisect_right(_w,v)-_b.bisect_left(_w,v)) for v in _c)
_n1,_n2=len(_c),len(_w); _z=(_U-_n1*_n2/2)/_m.sqrt(_n1*_n2*(_n1+_n2+1)/12); _p=0.5*_m.erfc(_z/_m.sqrt(2))
V.update(auc=_U/(_n1*_n2), auc_pct=100*_U/(_n1*_n2), p_exp=int(-_m.log10(_p))//10*10, mc=sum(_c)/_n1, mw=sum(_w)/_n2, nc=_n1, nw=_n2)
def fmt(m):
    k,spec=m.group(1),m.group(2); return format(V[k],spec)
tpl=re.sub(r'\{\{(\w+):([^}]*)\}\}',fmt,tpl)
assert not re.findall(r'\{\{[A-Z_a-z]+(:[^}]*)?\}\}',tpl), re.findall(r'\{\{[^}]*\}\}',tpl)
# paper colours: Task teal-blue, Physics muted purple, in every "T / P" cell
def tp(m):
    a,b_=m.group(2),m.group(3)
    return f'{m.group(1)}<span class=vt>{a}</span> / <span class=vp>{b_}</span></td>'
tpl=re.sub(r'(<td class="?tp[^>]*>)(.*?) / (.*?)</td>',tp,tpl)
open(SITE+'index.html','w').write(tpl)
