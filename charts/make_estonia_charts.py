"""Draw the charts for the Estonia register-comparison post from the files in
estonia-register-comparison/results. Same house style as the MEIP posts
(charts/house.py). Run from the repo root:
  python3 charts/make_estonia_charts.py"""
import json
from house import *   # noqa: F401,F403 — palette, frame, style, hbars, save, rd

E = 'estonia-register-comparison/results/'
F = json.load(open(E + 'post_figures.json'))
SOURCE = ('Sources: Estonian e-Business Register (RIK open data, 4 Jul 2026) and GLEIF, via the OpenCheck Estonia BODS dataset. '
          'Analysis: github.com/StephenAbbott/bods-analysis')
SOURCE_T = ('Sources: Norway — T-rank, "The Danish Beneficial Ownership Register" (18 Sep 2026); Estonia — e-Business Register '
            '(4 Jul 2026) via OpenCheck. Analysis: github.com/StephenAbbott/bods-analysis')

# E1 — the funnel to the companies that can be compared
fn = rd(E + 'funnel.csv')
fig = frame('From Estonia\'s LEI holders to the companies that can be checked',
            'Each step keeps the companies the shareholder data can be compared for', SOURCE)
ax = fig.add_axes([0.40, 0.1, 0.52, 0.72])
labs = [r['step'] for r in fn]; vals = [int(r['companies']) for r in fn]
cols = ['#cbd5e1', '#94a3b8', '#64748b', BLUE, EMPH]
y = list(range(len(labs)))[::-1]
ax.barh(y, vals, height=0.62, color=cols); ax.set_yticks(y, labs)
for yi, v in zip(y, vals): ax.text(v + vals[0] * 0.01, yi, f'{v:,}', va='center', fontsize=9.5, color=INK2)
ax.set_xlim(0, vals[0] * 1.15); style(ax); ax.set_xticks([])
save(fig, 'e1_funnel.png')

# E2 — Estonia beside T-rank's Norway figures
tc = rd(E + 'trank_comparison.csv')
fig = frame(f'In {F["classes"]["same_people"]["pct"]:.0f}% of companies, the register names who the shares point to',
            f'Declared beneficial owners against owners above 25% calculated from shareholdings ({F["comparable"]:,} Estonian companies)',
            SOURCE_T, 5.2)
ax = fig.add_axes([0.40, 0.11, 0.52, 0.62])
labs = [r['class'] for r in tc]
y = list(range(len(labs)))[::-1]
h = 0.36
ax.barh([v + h / 2 for v in y], [float(r['norway_trank_pct']) for r in tc], height=h, color='#94a3b8')
ax.barh([v - h / 2 for v in y], [float(r['estonia_pct']) for r in tc], height=h, color=BLUE)
for yi, r in zip(y, tc):
    ax.text(float(r['norway_trank_pct']) + 1, yi + h / 2, f"{float(r['norway_trank_pct']):.0f}%", va='center', fontsize=9, color=MUTED)
    ax.text(float(r['estonia_pct']) + 1, yi - h / 2, f"{float(r['estonia_pct']):.1f}%", va='center', fontsize=9.5, color=INK2, fontweight='bold')
ax.set_yticks(y, labs); ax.set_xlim(0, 110); style(ax); ax.set_xticks([])
for i, (lab, col) in enumerate((('Norway (T-rank)', '#94a3b8'), ('Estonia (this analysis)', BLUE))):
    fig.patches.append(FancyBboxPatch((0.40 + i * 0.2, 0.755), 0.012, 0.022, boxstyle='round,pad=0', color=col, transform=fig.transFigure, figure=fig))
    fig.text(0.40 + i * 0.2 + 0.017, 0.757, lab, fontsize=9.5, color=INK2)
save(fig, 'e2_trank_comparison.png')

# E3 — who the register names that the shares do not
do = rd(E + 'declared_only.csv')
fig = frame('Who the register names that the shares do not',
            f'The {F["declared_only_people"]["total"]:,} declared beneficial owners not found above 25% in the shareholder data, by what the data shows',
            SOURCE, 4.6)
ax = fig.add_axes([0.40, 0.14, 0.52, 0.62])
hbars(ax, [r['reason'] for r in do], [int(r['people']) for r in do], emph=('holds exactly 25%',))
ax.set_xticks([])
save(fig, 'e3_declared_only.png')

# E4 — the match by ownership shape
bs = rd(E + 'by_shape.csv')
labs = [f"{r['shape']} ({int(r['comparable']):,})" for r in bs]
fig = frame('With more than one owner, about four in five match',
            'Share of comparable companies where the register and the shareholdings name the same people, by ownership shape',
            SOURCE, 4.4)
ax = fig.add_axes([0.40, 0.15, 0.52, 0.58])
hbars(ax, labs, [float(r['pct_same']) for r in bs], emph=(labs[1], labs[2]), fmt='{:.1f}', xmax=100, pct=True)
ax.set_xticks([])
save(fig, 'e4_by_shape.png')

# E5 — why some chains cannot be followed in the dataset
inc = F['not_comparable']['incomplete_by_kind']
lab = {'estonian_no_lei': 'an Estonian company without an LEI', 'foreign': 'a foreign company',
       'estonian_no_lei+foreign': 'both'}
items = sorted(((lab.get(k, 'a circular holding' if not k else k), v) for k, v in inc.items()), key=lambda x: -x[1])
fig = frame(f'{F["not_comparable"]["incomplete_chain"]:,} chains leave the dataset before they reach a person',
            'Companies where a holding of more than 25% passes to a company whose shareholders are not in the dataset', SOURCE, 4.2)
ax = fig.add_axes([0.40, 0.16, 0.52, 0.56])
hbars(ax, [k for k, _ in items], [v for _, v in items], emph=('a foreign company',))
ax.set_xticks([])
save(fig, 'e5_incomplete.png')
