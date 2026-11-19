"""Result figures for the 26 Nov preview and the 1 Dec final (Visio-style: flat shapes, swimlanes, callouts).

Figures (wording approved by the user, 19 Nov 2026; Figure B's count corrected from the data):
  A  fig_a_gap_by_condition  - MILP (C) minus greedy (G), share not reached within 20 min, by condition (M5b)
  B  fig_b_every_night       - one dot per primary night (base, 5 vans), C vs G
  C  fig_c_speed_vs_riders   - drawn after the frozen M5d analysis (not in this script yet)

Data: outputs/sim/m5/m5b/comparison_preview_per_night.csv (written by `python -m sim.m5 m5b compare --analysis preview`).
Intervals: the preregistered paired bootstrap (sim.m5.paired_bootstrap), checked against m5b_preview_2026-11-16.md.

Run from the repository root:  .venv/bin/python docs/presentations/final/make_result_figures.py
"""
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from sim.m5 import paired_bootstrap  # noqa: E402

CSV = ROOT / "outputs/sim/m5/m5b/comparison_preview_per_night.csv"
OUT = Path(__file__).resolve().parent / "figures"

# Visio-like palette: one brand blue for the MILP, greys for everything else.
BLUE, BLUE_LIGHT, BLUE_PALE = "#002D72", "#4A90C8", "#E8F0F9"
INK, GREY, GREY_LIGHT, GREY_PALE, LINE = "#1F2937", "#6B7280", "#D1D5DB", "#F3F4F6", "#9CA3AF"
MINUS = "−"

plt.rcParams.update({"font.family": "Helvetica", "font.size": 12, "axes.unicode_minus": True,
                     "svg.fonttype": "none"})

ROWS = [  # (cell prefix in the CSV, label on the figure, highlighted, expected mean, lo, hi from the preview note)
    ("2 ", "6 vans, normal night", False, -4.17, -5.68, -2.71),
    ("1 ", "5 vans, normal night", True, -6.35, -8.65, -4.17),
    ("3 ", "5 vans, busy night", False, -12.47, -14.78, -10.10),
]


def box(ax, x, y, w, h, text, fc, ec, tc, size=12, weight="normal", r=0.12, transform=None, ha="center"):
    """A rounded Visio-style shape with centred text."""
    tr = transform or ax.transData
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.2,
                                transform=tr, zorder=3, clip_on=False))
    tx = x + w / 2 if ha == "center" else x + 0.04 * w
    ax.text(tx, y + h / 2, text, ha=ha, va="center", color=tc, fontsize=size, fontweight=weight, transform=tr,
            zorder=4)


def fmt(v):
    return f"{MINUS}{abs(round(v)):.0f} pp" if v < 0 else f"+{round(v):.0f} pp"


def figure_a(df):
    stats = []
    for prefix, label, hi_lite, em, elo, ehi in ROWS:
        c = df[df.cell.str.startswith(prefix)]
        mean, lo, hi, n = paired_bootstrap(c.C_not_reached_20_pp - c.G_not_reached_20_pp)
        assert (round(mean, 2), round(lo, 2), round(hi, 2)) == (em, elo, ehi), (label, mean, lo, hi)
        stats.append((label, hi_lite, mean, lo, hi, n))

    fig = plt.figure(figsize=(13.333, 7.5), facecolor="white")
    ax = fig.add_axes([0.30, 0.22, 0.64, 0.60])
    xmin, xmax = -16, 6
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.85, len(stats) - 0.5)
    ax.invert_yaxis()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([])
    ax.tick_params(axis="x", colors=GREY, labelsize=12, length=0, pad=8)
    ax.set_xticks(range(-15, 6, 5))
    ax.set_xticklabels([f"{MINUS}{abs(t)}" if t < 0 else ("0" if t == 0 else f"+{t}") for t in range(-15, 6, 5)])

    # band: no real difference
    ax.axvspan(-2, 2, ymin=0, ymax=1 - 0.4 / (len(ROWS) + 0.35), color=GREY_PALE, zorder=0)
    ax.axvline(0, color=LINE, lw=1.2, zorder=1)
    box(ax, -3.4, -0.80, 6.8, 0.28, "No real difference (±2 pp)", "white", GREY_LIGHT, GREY, size=12)

    for i, (label, hi_lite, mean, lo, hi, n) in enumerate(stats):
        # swimlane
        ax.add_patch(FancyBboxPatch((xmin, i - 0.36), xmax - xmin, 0.72, boxstyle="round,pad=0,rounding_size=0.15",
                                    fc=BLUE_PALE if hi_lite else "none", ec=BLUE_LIGHT if hi_lite else GREY_LIGHT,
                                    lw=1.4 if hi_lite else 0.8, zorder=0.5, clip_on=False))
        col = BLUE if hi_lite else BLUE_LIGHT
        ax.plot([lo, hi], [i, i], color=col, lw=3, solid_capstyle="round", zorder=5)
        for e in (lo, hi):
            ax.plot([e, e], [i - 0.09, i + 0.09], color=col, lw=2, zorder=5)
        ax.scatter([mean], [i], s=230, color=col, edgecolor="white", linewidth=2, zorder=6)
        ax.text(mean, i - 0.2, fmt(mean), ha="center", va="bottom", fontsize=14, color=col, fontweight="bold",
                zorder=6)
        # row label shape on the left (figure coords)
        y_fig = 0.22 + 0.60 * (len(stats) - 0.5 - i) / (len(stats) + 0.35)
        box(fig.axes[0], 0.04, y_fig - 0.045, 0.23, 0.09, label, BLUE if hi_lite else "white",
            BLUE if hi_lite else LINE, "white" if hi_lite else INK, size=14, weight="bold" if hi_lite else "normal",
            r=0.015, transform=fig.transFigure)

    # direction arrows under the axis
    for x0, x1, txt, col in ((-2.4, -15.5, "MILP better", BLUE), (2.4, 5.6, "greedy better", GREY)):
        ax.add_patch(FancyArrowPatch((x0, 3.1), (x1, 3.1), arrowstyle="-|>,head_length=8,head_width=5",
                                     color=col, lw=1.6, clip_on=False, zorder=3))
        ax.text((x0 + x1) / 2, 3.03, txt, ha="center", va="bottom", color=col, fontsize=13,
                fontweight="bold", clip_on=False)
    fig.text(0.62, 0.03, "Requests not reached within 20 min: MILP minus greedy (percentage points)",
             ha="center", color=INK, fontsize=13)
    fig.text(0.04, 0.89, "The busier each van, the more re-planning pays", ha="left", va="center",
             fontsize=26, fontweight="bold", color=INK)
    return fig


def figure_b(df):
    p = df[df.cell.str.startswith("1 ")]
    g, c = p.G_not_reached_20_pp.to_numpy(), p.C_not_reached_20_pp.to_numpy()
    better, tie, worse = int((c < g).sum()), int((c == g).sum()), int((c > g).sum())
    assert (better, tie, worse) == (27, 1, 2), (better, tie, worse)

    fig = plt.figure(figsize=(13.333, 7.5), facecolor="white")
    ax = fig.add_axes([0.30, 0.13, 0.42, 0.74])
    lo, hi = 10, 46
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.tick_params(colors=GREY, labelsize=12, length=0, pad=6)
    ticks = range(10, 46, 10)
    ax.set_xticks(ticks), ax.set_yticks(ticks)
    ax.set_xticklabels([f"{t}%" for t in ticks]), ax.set_yticklabels([f"{t}%" for t in ticks])

    # regions
    ax.add_patch(Polygon([(lo, lo), (hi, hi), (hi, lo)], closed=True, fc=BLUE_PALE, ec="none", zorder=0))
    ax.add_patch(Polygon([(lo, lo), (hi, hi), (lo, hi)], closed=True, fc=GREY_PALE, ec="none", zorder=0))
    ax.plot([lo, hi], [lo, hi], color=LINE, lw=1.5, ls=(0, (6, 4)), zorder=1)

    # dots; nights with identical results are nudged apart along the diagonal so every night is visible
    seen = {}
    for gi, ci in zip(g, c):
        k = seen.get((gi, ci), 0)
        seen[(gi, ci)] = k + 1
        dx = 0.55 * k
        col = BLUE if ci < gi else (GREY if ci > gi else LINE)
        ax.scatter([gi + dx], [ci + dx], s=120, color=col, edgecolor="white", linewidth=1.5, zorder=4)

    # region labels sit inside their regions; the diagonal gets a callout with a connector
    fig_pt = lambda x, y: fig.transFigure.inverted().transform(ax.transData.transform((x, y)))  # noqa: E731
    box(ax, 34.5, 11.5, 10, 3, "MILP better", BLUE, BLUE, "white", size=14, weight="bold", r=0.6)
    box(ax, 11.5, 41.5, 10, 3, "Greedy better", "white", GREY, GREY, size=14, weight="bold", r=0.6)
    box(ax, 0.76, 0.76, 0.15, 0.07, "Same result", "white", LINE, GREY, size=13, r=0.012, transform=fig.transFigure)
    for (bx, by), (px, py), col in (((0.76, 0.795), (44, 44), LINE),):
        fx, fy = fig_pt(px, py)
        fig.add_artist(matplotlib.lines.Line2D([bx, fx], [by, fy], color=col, lw=1.2, transform=fig.transFigure,
                                               zorder=2))
    ax.set_xlabel("Greedy: % not reached within 20 min", fontsize=13, color=INK, labelpad=10)
    ax.set_ylabel("MILP: % not reached within 20 min", fontsize=13, color=INK, labelpad=16)
    fig.text(0.04, 0.94, f"MILP did better on {better} of {len(g)} nights", ha="left", va="center", fontsize=26,
             fontweight="bold", color=INK)
    return fig


def main():
    df = pd.read_csv(CSV)
    OUT.mkdir(exist_ok=True)
    for name, fig in (("fig_a_gap_by_condition", figure_a(df)), ("fig_b_every_night", figure_b(df))):
        for ext in ("svg", "png"):
            fig.savefig(OUT / f"{name}.{ext}", dpi=200, facecolor="white")
        plt.close(fig)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
