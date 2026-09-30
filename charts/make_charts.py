"""Draw every chart used in the two posts from the CSVs in meip-global/results and
meip-uk-psc/results. Static PNGs (Medium cannot embed interactive charts), 2x density.
Fonts: DM Sans / Bitter (OFL, Google Fonts) in charts/fonts. Run from the repo root:
  python3 charts/make_charts.py"""
import csv, os, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
HERE = os.path.dirname(os.path.abspath(__file__))
for f in os.listdir(os.path.join(HERE, 'fonts')):
    if f.endswith('.ttf'): fm.fontManager.addfont(os.path.join(HERE, 'fonts', f))
plt.rcParams.update({'font.family': 'DM Sans', 'font.size': 11, 'axes.edgecolor': '#e5e7eb',
                     'axes.linewidth': 1, 'xtick.color': '#4b5563', 'ytick.color': '#1f2937'})
INK, INK2, MUTED, GRID = '#0d1b3e', '#374151', '#6b7280', '#e5e7eb'
BLUE, EMPH = '#3b82f6', '#0d1b3e'            # single-series hue; the one bar the story is about
ORD = ['#60a5fa', '#2563eb', '#1e3a8a']       # ordinal ramp Known < Partial < Unknown (light -> dark)
OUT = os.path.join(HERE, 'png'); os.makedirs(OUT, exist_ok=True)
G = 'meip-global/results/'; U = 'meip-uk-psc/results/'
def rd(p): return list(csv.DictReader(open(p)))
SOURCE_G = 'Source: OECD-UNSD MEIP Global Register (31 Dec 2024). Analysis: Stephen Abbott Pugh, github.com/StephenAbbott/bods-analysis'
SOURCE_U = ('Sources: OECD-UNSD MEIP Global Register (31 Dec 2024); Companies House PSC snapshot (23 Sep 2026). '
            'Analysis: github.com/StephenAbbott/bods-analysis')

def frame(title, subtitle, source, h=5.6):
    fig = plt.figure(figsize=(10, h), dpi=200, facecolor='white')
    fig.text(0.04, 0.95, title, fontfamily='Bitter', fontweight='bold', fontsize=16, color=INK, va='top')
    fig.text(0.04, 0.95 - 0.52 / h, subtitle, fontsize=11, color=INK2, va='top')
    fig.text(0.04, 0.025, source, fontsize=7.5, color=MUTED)
    return fig
def style(ax, grid_axis='x'):
    for s in ('top', 'right', 'left', 'bottom'): ax.spines[s].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1); ax.set_axisbelow(True)
    ax.tick_params(length=0)
def hbars(ax, labels, values, emph=(), fmt='{:,}', xmax=None, pct=False):
    y = list(range(len(labels)))[::-1]
    cols = [EMPH if l in emph else BLUE for l in labels]
    ax.barh(y, values, height=0.62, color=cols)
    ax.set_yticks(y, labels)
    m = xmax or max(values)
    for yi, v in zip(y, values):
        ax.text(v + m * 0.01, yi, (fmt.format(v) + ('%' if pct else '')), va='center', fontsize=9.5, color=INK2)
    ax.set_xlim(0, m * 1.12); style(ax)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f'{v:,.0f}'))
def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, facecolor='white'); plt.close(fig); print('wrote', name)

# ---------- Global post ----------
S = json.load(open(G + 'summary.json'))
hosts = rd(G + 'hosts.csv')
# G1 hierarchy by host (15 largest hosts + all)
top = [h for h in hosts if h['iso3']][:15]

fig = frame('MEIP cannot place most subsidiaries in their group\'s structure',
            'Hierarchy status of subsidiaries in the 15 largest host jurisdictions, % of rows', SOURCE_G, 6.4)
ax = fig.add_axes([0.24, 0.1, 0.62, 0.68])
rows = json.load(open(G + 'hierarchy_by_host.json'))
labels = ['All 126,157 subsidiaries'] + [h['name'] for h in top]
y = list(range(len(labels)))[::-1]
for yi, lab in zip(y, labels):
    k, p, u = rows[lab]
    left = 0
    for val, col in ((k, ORD[0]), (p, ORD[1]), (u, ORD[2])):
        ax.barh(yi, val - 0.25 if val > 0.5 else val, left=left, height=0.62, color=col); left += val
    ax.text(101, yi, f'{u:.0f}%', va='center', fontsize=9.5, color=INK2, fontweight='bold' if lab.startswith('All') else 'normal')
ax.set_yticks(y, labels); ax.set_xlim(0, 100); style(ax)
ax.set_xticks([0, 25, 50, 75, 100], ['0', '25', '50', '75', '100%'])
ax.text(101, len(labels) - 0.2, 'Unknown', fontsize=9, color=MUTED)
for i, (lab, col) in enumerate((('Known', ORD[0]), ('Partial', ORD[1]), ('Unknown', ORD[2]))):
    fig.patches.append(FancyBboxPatch((0.24 + i * 0.12, 0.815), 0.012, 0.022, boxstyle='round,pad=0', color=col, transform=fig.transFigure, figure=fig))
    fig.text(0.24 + i * 0.12 + 0.017, 0.817, lab, fontsize=9.5, color=INK2)
save(fig, 'g1_hierarchy_by_host.png')

# G2 no identifier by host (20 largest hosts)
t20 = [h for h in hosts if h['iso3']][:20]
t20.sort(key=lambda h: float(h['no_identifier_pct']))
fig = frame('How identifiable are subsidiaries in each jurisdiction?',
            'Share of subsidiaries with no OpenCorporates, LEI, PermID or DUNL identifier, 20 largest host jurisdictions',
            SOURCE_G, 6.4)
ax = fig.add_axes([0.24, 0.1, 0.68, 0.74])
hbars(ax, [h['name'] for h in t20][::-1][::-1], [float(h['no_identifier_pct']) for h in t20], emph=('United Kingdom',), fmt='{:.0f}', xmax=70, pct=True)
ax.set_xticks([0, 20, 40, 60], ['0', '20', '40', '60%'])
save(fig, 'g2_no_identifier_by_host.png')

# G3a sink jurisdictions
sk = sorted(rd(G + 'sinks_by_jurisdiction.csv'), key=lambda r: -int(r['subsidiaries']))[:12]
fig = frame(f'{S["sink_subsidiaries"]:,} subsidiaries sit in the 24 "sink" offshore financial centres',
            f'Subsidiaries by sink jurisdiction (Garcia-Bernardo et al. 2017). {S["groups_with_any_sink"]} of 500 groups hold at least one',
            SOURCE_G)
ax = fig.add_axes([0.24, 0.1, 0.68, 0.72])
hbars(ax, [r['name'] for r in sk], [int(r['subsidiaries']) for r in sk], emph=('Cayman Islands',))
save(fig, 'g3a_sink_jurisdictions.png')

# G3b groups by sink count
gs = rd(G + 'group_sink_share.csv')[:10]
fig = frame('Private equity leads the offshore count',
            'Groups with the most subsidiaries in sink jurisdictions (share of the group\'s subsidiaries in brackets)', SOURCE_G)
ax = fig.add_axes([0.30, 0.1, 0.62, 0.72])
labs = [f"{r['group'].replace(' Holdings PLC','').replace(' Inc','').replace(' SE','').replace(' Corp','').replace(' SA','').replace(' Group','')} ({float(r['sink_pct']):.0f}%)" for r in gs]
hbars(ax, labs, [int(r['sink_subsidiaries']) for r in gs])
save(fig, 'g3b_groups_by_sink_count.png')

# G4 HQ countries
hq = rd(G + 'hq_countries.csv')[:12]
fig = frame('Where the 500 groups are headquartered',
            'Country of the group head as MEIP records it (about 4% of head rows are not the listed parent)', SOURCE_G)
ax = fig.add_axes([0.24, 0.1, 0.68, 0.72])
hbars(ax, [r['name'] for r in hq], [int(r['groups']) for r in hq], emph=('Cayman Islands',))
save(fig, 'g4_hq_countries.png')

# G5 depth (MEIP Parent of Subsidiary)
dp = rd(G + 'depth_to_head.csv')
fig = frame('Where MEIP knows the chain, it can be nine layers deep',
            f'Layers between a subsidiary and its group head, for the {S["placed_under_head"]:,} subsidiaries MEIP can place ({S["placed_under_head"]/S["subsidiaries"]*100:.0f}% of all)',
            SOURCE_G)
ax = fig.add_axes([0.08, 0.12, 0.86, 0.68])
xs = [int(r['layers_below_head']) for r in dp]; vs = [int(r['subsidiaries']) for r in dp]
ax.bar(xs, vs, width=0.6, color=BLUE)
for x, v in zip(xs, vs): ax.text(x, v + max(vs) * 0.015, f'{v:,}', ha='center', fontsize=9.5, color=INK2)
ax.set_xticks(xs); ax.set_xlabel('layers below the head', color=MUTED); style(ax, 'y')
ax.set_yticks([]); ax.set_ylim(0, max(vs) * 1.12)
save(fig, 'g5_depth_meip.png')

# ---------- UK post ----------
US = json.load(open(U + 'uk_summary.json'))
fn = rd(U + 'uk_funnel.csv')
fig = frame('The UK register places most of what MEIP could not',
            'MEIP\'s UK subsidiaries, from "Unknown" to linked through the register of people with significant control', SOURCE_U)
ax = fig.add_axes([0.34, 0.1, 0.58, 0.72])
labs = [r['stage'] for r in fn]; vals = [int(r['subsidiaries']) for r in fn]
cols = ['#cbd5e1', '#94a3b8', '#64748b', BLUE, EMPH]
y = list(range(len(labs)))[::-1]
ax.barh(y, vals, height=0.62, color=cols); ax.set_yticks(y, labs)
base = vals[2]
for yi, v, i in zip(y, vals, range(5)):
    extra = f'  ({v/base*100:.1f}% of those that existed)' if i >= 3 else ''
    ax.text(v + 150, yi, f'{v:,}{extra}', va='center', fontsize=9.5, color=INK2)
ax.set_xlim(0, max(vals) * 1.45); style(ax); ax.set_xticks([])
save(fig, 'u1_funnel.png')

hdp = rd(U + 'uk_head_depth.csv')
fig = frame('Through the UK register, chains run up to twelve layers',
            'Layers between a UK subsidiary and the group head, found by walking the PSC register (MEIP "Unknown" rows)', SOURCE_U)
ax = fig.add_axes([0.08, 0.12, 0.86, 0.68])
xs = [int(r['layers_to_head']) for r in hdp]; vs = [int(r['subsidiaries']) for r in hdp]
ax.bar(xs, vs, width=0.6, color=BLUE)
for x, v in zip(xs, vs): ax.text(x, v + max(vs) * 0.015, f'{v:,}', ha='center', fontsize=9.5, color=INK2)
ax.set_xticks(xs); ax.set_xlabel('layers below the head (the walk stops at 12)', color=MUTED); style(ax, 'y')
ax.set_yticks([]); ax.set_ylim(0, max(vs) * 1.12)
save(fig, 'u2_depth_psc.png')

tr = rd(U + 'uk_trail_end.csv')
fig = frame('Where the UK trail stops short of the head',
            'UK subsidiaries whose PSC chain reaches the group but not its head, by where the chain ends', SOURCE_U, 4.2)
ax = fig.add_axes([0.40, 0.14, 0.52, 0.6])
hbars(ax, [r['where the trail stops'] for r in tr], [int(r['subsidiaries']) for r in tr])
save(fig, 'u3_trail_end.png')

nat = [('over 50% of shares or votes', 10922), ('25–50% only', 268), ('significant influence only', 129), ('right to appoint directors only', 28)]
fig = frame('The first link is almost always majority control',
            'Nature of control of the parent at the first PSC link (subsidiaries that reach their group)', SOURCE_U, 4.2)
ax = fig.add_axes([0.34, 0.14, 0.58, 0.6])
hbars(ax, [n for n, _ in nat], [v for _, v in nat])
save(fig, 'u4_natures_of_control.png')

dy = rd(U + 'uk_dissolved_before_vintage_by_year.csv')
fig = frame(f'{US["dissolved_before_vintage"]:,} UK "subsidiaries" had closed before MEIP\'s own date',
            'MEIP UK rows whose company was dissolved before 31 Dec 2024, by year of dissolution', SOURCE_U)
ax = fig.add_axes([0.08, 0.12, 0.86, 0.68])
xs = [int(r['year_dissolved']) for r in dy]; vs = [int(r['subsidiaries']) for r in dy]
ax.bar(xs, vs, width=0.6, color=BLUE)
for x, v in zip(xs, vs): ax.text(x, v + max(vs) * 0.015, f'{v:,}', ha='center', fontsize=8.5, color=INK2)
ax.set_xticks(xs, [str(x) for x in xs], fontsize=9); style(ax, 'y'); ax.set_yticks([]); ax.set_ylim(0, max(vs) * 1.12)
save(fig, 'u5_dissolved_before_vintage.png')
