"""Inline SVG charts for the 'More analysis' block of #q3 (replace paper Figs 4a, 4b, 5).
All numbers are read from analysis outputs; nothing is typed in by hand."""
import csv, html, json, os
EGO2ACT = os.environ.get('EGO2ACT_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ego2act')) + '/'
PD = EGO2ACT + 'analysis/results/plots_data/'
ABL = EGO2ACT + 'analysis/csv/rubric_ablation_pilot.json'
HUM, JDG = '#d4a017', '#3d8bc4'
esc = lambda s: html.escape(s, quote=True)
f1 = lambda x: f'{x:.1f}'
sg = lambda x: f'{x:+.1f}'


def scatter(models):
    """models: list of (key, name, org, logo). Returns (svg html, caption numbers)."""
    rows = [r for r in csv.DictReader(open(PD + 'task_physics_scatter.csv'))
            if all(r[k] for k in ('human_task', 'human_physics', 'judge_task', 'judge_physics'))]
    K = ('human_task', 'human_physics', 'judge_task', 'judge_physics')
    mean = lambda rs: [sum(float(r[k]) for r in rs) / len(rs) for k in K]
    S, L, T, P = 400, 46, 12, 340          # viewBox, left, top, plot size
    X = lambda v: L + v / 100 * P
    Y = lambda v: T + P - v / 100 * P
    o = [f'<svg class="ch sc-ch vshow" viewBox="0 0 {S} {S}" role="img" aria-labelledby="scT">'
         '<title id="scT">Mean Task and Physics score per model: human rating versus Ego2ActJudge</title>'
         f'<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
         '<path d="M0 0L10 5L0 10z" fill="#555"/></marker></defs><g class=grid>']
    for v in range(0, 101, 20):
        o.append(f'<line x1="{X(v)}" y1="{T}" x2="{X(v)}" y2="{T+P}"/><line x1="{L}" y1="{Y(v)}" x2="{L+P}" y2="{Y(v)}"/>'
                 f'<text x="{X(v)}" y="{T+P+15}" text-anchor=middle>{v}</text><text x="{L-6}" y="{Y(v)+4}" text-anchor=end>{v}</text>')
    o.append(f'</g><text class=axl x="{L+P/2}" y="{S-6}" text-anchor=middle fill="var(--task)">Task</text>'
             f'<text class=axl transform="translate(13 {T+P/2}) rotate(-90)" text-anchor=middle fill="var(--phys)">Physics</text>')
    # faint per-video dots (toggle)
    o.append('<g class=vids>' + ''.join(
        f'<circle cx="{X(float(r["human_task"])):.1f}" cy="{Y(float(r["human_physics"])):.1f}" r="2.3" fill="{HUM}"/>'
        f'<circle cx="{X(float(r["judge_task"])):.1f}" cy="{Y(float(r["judge_physics"])):.1f}" r="2.3" fill="{JDG}"/>' for r in rows) + '</g>')

    placed = []   # logo boxes already drawn, to keep the top-right cluster readable
    def spot(x, y):
        pts = [(ht_, hp_) for ht_, hp_ in dots]
        for dx, dy in ((5, -19), (6, -7), (-19, -19), (-20, -7), (5, 5), (-19, 5), (-7, -24), (-7, 10)):
            bx, by = x + dx, y + dy
            if all(abs(bx - px) > 15 or abs(by - py) > 15 for px, py in placed) and \
               all(not (bx - 4 < px < bx + 18 and by - 4 < py < by + 18) for px, py in pts):
                placed.append((bx, by)); return bx, by
        placed.append((x + 5, y - 19)); return x + 5, y - 19

    def arrow(ht, hp, jt, jp, label, cls, logo=None, n=0):
        tip = (f'{label} (n = {n} videos)\nHuman: Task {f1(ht)}, Physics {f1(hp)}\n'
               f'Ego2ActJudge: Task {f1(jt)}, Physics {f1(jp)}\nShift: Task {sg(jt-ht)}, Physics {sg(jp-hp)}')
        g = [f'<g class="{cls}" tabindex=0 data-tip="{esc(tip)}" aria-label="{esc(tip)}">',
             f'<line class=hit x1="{X(ht):.1f}" y1="{Y(hp):.1f}" x2="{X(jt):.1f}" y2="{Y(jp):.1f}"/>',
             f'<line class=arr x1="{X(ht):.1f}" y1="{Y(hp):.1f}" x2="{X(jt):.1f}" y2="{Y(jp):.1f}" marker-end="url(#ah)"/>',
             f'<circle class=ph cx="{X(ht):.1f}" cy="{Y(hp):.1f}" r="{6 if cls=="all" else 4.5}" fill="{HUM}"/>',
             f'<circle class=pj cx="{X(jt):.1f}" cy="{Y(jp):.1f}" r="{6 if cls=="all" else 4.5}" fill="{JDG}"/>']
        if logo:
            bx, by = spot(X(jt), Y(jp))
            g.append(f'<image href="assets/logos/{logo}.png" x="{bx:.1f}" y="{by:.1f}" width="14" height="14"/>')
        else:
            g.append(f'<text class=alllab x="{X(ht)-9:.1f}" y="{Y(hp)+4:.1f}" text-anchor=end>All videos</text>')
        return ''.join(g) + '</g>'
    per = []
    M = {k: mean([r for r in rows if r['model'] == k]) for k, *_ in models}
    dots = [(X(m[i]), Y(m[i + 1])) for m in list(M.values()) + [mean(rows)] for i in (0, 2)]
    A = mean(rows)
    o.append(arrow(*A, 'All videos', 'all', None, len(rows)))   # drawn first so model marks stay hoverable on top
    for k, name, org, logo in models:
        rs = [r for r in rows if r['model'] == k]
        m = mean(rs); per.append((name, m, len(rs)))
        o.append(arrow(*m, name, 'mdl', logo, len(rs)))
    # single annotation: direction of the average human -> judge shift, in the empty lower-right corner
    import math
    dx, dy = A[2]-A[0], A[3]-A[1]; k = 26 / math.hypot(dx, dy)
    x0, y0 = 80, 6; x1, y1 = x0 + dx*k, y0 + dy*k
    o.append(f'<defs><marker id="rh" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#c0392b"/></marker></defs>'
             f'<g class=bias><line x1="{X(x0):.1f}" y1="{Y(y0):.1f}" x2="{X(x1):.1f}" y2="{Y(y1):.1f}" stroke="#c0392b" stroke-width="3" stroke-linecap="round" marker-end="url(#rh)"/>'
             f'<text x="{X(x0)-8:.1f}" y="{Y(y0+14):.1f}" text-anchor=end fill="#c0392b" font-weight="700" font-size="13">Automated judge</text>'
             f'<text x="{X(x0)-8:.1f}" y="{Y(y0+14)+16:.1f}" text-anchor=end fill="#c0392b" font-weight="700" font-size="13">upward bias</text>'
             f'<g transform="translate({X(x0)-8:.1f} {Y(y0+14)+34:.1f})"><text x="0" y="0" text-anchor=end font-size="11" fill="var(--muted)">'
             f'<tspan fill="{HUM}" font-size="13">&#9679;</tspan> human rating &#8594; <tspan fill="{JDG}" font-size="13">&#9679;</tspan> Ego2ActJudge</text></g></g>')
    o.append('</svg>')
    return ''.join(o), dict(n=len(rows), ht=A[0], hp=A[1], jt=A[2], jp=A[3], dt=A[2]-A[0], dp=A[3]-A[1], per=per)


def stability(models):
    R = list(csv.DictReader(open(PD + 'trial_instability.csv')))
    d = {(r['evaluator'], r['model']): r for r in R}
    info = {k: (name, org, logo) for k, name, org, logo in models}
    order = sorted({r['model'] for r in R}, key=lambda k: -float(d[('Human', k)]['average']))
    W, L, RR, GH = 380, 112, 12, 40
    X = lambda v: L + v / 100 * (W - L - RR)
    H = 14 + GH * len(order) + 22
    o = [f'<svg class="ch st-ch" viewBox="0 0 {W} {H}" role="img" aria-labelledby="stT"><title id="stT">Worst seed, average and best-of-3 Final score per model</title><g class=grid>']
    for v in range(0, 101, 25):
        o.append(f'<line x1="{X(v)}" y1="8" x2="{X(v)}" y2="{H-22}"/><text x="{X(v)}" y="{H-8}" text-anchor=middle>{v}</text>')
    o.append('</g>')
    for i, k in enumerate(order):
        name, org, logo = info[k]; y0 = 14 + i * GH
        o.append(f'<image href="assets/logos/{logo}.png" x="2" y="{y0+6}" width="16" height="16"/><text class=mn x="23" y="{y0+18}">{esc(name)}</text>')
        for j, (ev, lab, c) in enumerate((('Human', 'Human', HUM), ('Ego2ActJudge', 'Ego2ActJudge', JDG))):
            r = d[(ev, k)]; w, a, b = float(r['worst_seed']), float(r['average']), float(r['best_at_3']); y = y0 + 7 + j * 14
            tip = f'{name} · {lab} ({r["cases"]} cases)\nWorst seed {f1(w)} · Average {f1(a)} · Best-of-3 {f1(b)}'
            o.append(f'<g class=db tabindex=0 data-tip="{esc(tip)}" aria-label="{esc(tip)}" style="--c:{c}">'
                     f'<rect class=hit x="{L}" y="{y-7}" width="{W-L-RR}" height="14"/>'
                     f'<line class=seg pathLength=1 x1="{X(a):.1f}" y1="{y}" x2="{X(w):.1f}" y2="{y}"/>'
                     f'<line class=seg pathLength=1 x1="{X(a):.1f}" y1="{y}" x2="{X(b):.1f}" y2="{y}"/>'
                     f'<circle class=end cx="{X(w):.1f}" cy="{y}" r="2.6"/><circle class=end cx="{X(b):.1f}" cy="{y}" r="2.6"/>'
                     f'<circle cx="{X(a):.1f}" cy="{y}" r="4.2" fill="{c}" stroke="#fff" stroke-width="1"/></g>')
    o.append('</svg>')
    return ''.join(o)


def ablation():
    data = json.load(open(ABL))
    vals = {key: [(r['variant'], r['mae']) for r in data[key.lower()]] for key in ('TASK', 'PHYSICS')}
    out = []
    mx = max(v for rows in vals.values() for _, v in rows)
    for axis, key, col in (('Task', 'TASK', 'var(--task)'), ('Physics', 'PHYSICS', 'var(--phys)')):
        rows = vals[key]; W, L, BH = 400, 84, 22
        H = 18 + BH * len(rows) + 4
        X = lambda v: v / mx * (W - L - 44)
        o = [f'<svg class="ch ab-ch" viewBox="0 0 {W} {H}" role="img" aria-label="{axis} MAE per rubric variant">'
             f'<text class=axl x="0" y="12" fill="{col}">{axis}</text>']
        for i, (lab, v) in enumerate(rows):
            y = 20 + i * BH; full = lab == 'Full rubric'; ind = lab == 'Independent'
            cls = 'full' if full else 'ind' if ind else 'abl'
            tip = f'{axis} · {lab}: MAE {v:.3f}' + (f' ({v - rows[0][1]:+.3f} vs full rubric)' if not full else '')
            o.append(f'<g class="bar {cls}" tabindex=0 data-tip="{esc(tip)}" aria-label="{esc(tip)}">'
                     f'<text class=bl x="{L-6}" y="{y+BH/2+1}" text-anchor=end>{esc(lab)}</text>'
                     f'<rect x="{L}" y="{y+3}" width="{X(v):.1f}" height="{BH-6}" rx="2" style="--c:{col}"/>'
                     f'<text class=bv x="{L+X(v)+4:.1f}" y="{y+BH/2+1}">{v:.3f}</text></g>')
        out.append(''.join(o) + '</svg>')
    return ''.join(out)
