"""House style for every chart in bods-analysis: the OpenCheck palette (navy ink,
one blue series, the navy emphasis bar), Bitter titles and DM Sans text, 10in wide
at 200 dpi for Medium. Imported by make_charts.py (the MEIP posts) and
make_estonia_charts.py (the Estonia register comparison)."""
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
def rd(p): return list(csv.DictReader(open(p)))

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

