"""Result figures for the 26 Nov preview and the 1 Dec final (Visio-style: flat shapes, swimlanes, callouts).

Figures (wording approved by the user, 19 Nov 2026; Figure B's count corrected from the data):
  A  fig_a_gap_by_condition  - MILP (C) minus greedy (G), share not reached within 20 min, by condition (M5b)
  B  fig_b_every_night       - one dot per primary night (base, 5 vans), C vs G
  C  fig_c_speed_vs_riders   - speed vs riders at high load (M5b, M5c, M5d)
  D  fig_d_lyft_rules        - Lyft-rule trade-off, 5 and 6 vans (M7; layout approved 25 Nov)

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
import numpy as np
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


M5 = ROOT / "outputs/sim/m5"


def _median_min(folder, cell):
    import json
    w = [json.loads(f.read_text())["wall_s"] for f in (M5 / folder / cell).glob("r*/rep1/manifest.json")]
    assert len(w) == 30, (folder, cell, len(w))
    return float(pd.Series(w).median()) / 60


def figure_c(df):
    """Speed vs riders at high load. Each shortcut's gap is measured against C on its own nights (frozen analyses):
    fixed drop order (C-F) on M5c r00-r29 less r26; full-van switch (C-S6) on M5d r30-r59; greedy from M5b (r00-r25)."""
    cf = pd.read_csv(M5 / "m5c/comparison_m5c_per_night.csv")
    cf = cf[cf.comparison.str.startswith("high")]
    s6 = pd.read_csv(M5 / "m5d/comparison_m5d_per_night.csv")
    s6 = s6[s6.comparison.str.startswith("high")]
    hi = df[df.cell.str.startswith("3 ")]
    gaps = {"Fixed drop order": paired_bootstrap(cf.CF_not_reached_20_pp - cf.C_not_reached_20_pp),
            "Fixed when van is full": paired_bootstrap(s6.CS6_not_reached_20_pp - s6.C_not_reached_20_pp),
            "Greedy": paired_bootstrap(hi.G_not_reached_20_pp - hi.C_not_reached_20_pp)}
    expect = {"Fixed drop order": (2.08, 0.50, 3.78, 29), "Fixed when van is full": (0.12, -0.68, 0.92, 30),
              "Greedy": (12.47, 10.10, 14.78, 26)}
    for k, (m, lo, h, n) in gaps.items():
        assert (round(m, 2), round(lo, 2), round(h, 2), n) == expect[k], (k, m, lo, h, n)
    t = {"MILP (exact)": _median_min("m5b", "high5_C_R0_t120"), "Fixed drop order": _median_min("m5c", "high5_CF_R0_t120"),
         "Fixed when van is full": _median_min("m5d", "high5_CS6_R0_t120"),
         "Greedy": _median_min("m5b", "high5_G_R0_t120")}
    pts = [("MILP (exact)", t["MILP (exact)"], (0.0, 0.0, 0.0)), *[(k, t[k], gaps[k][:3]) for k in gaps]]

    fig = plt.figure(figsize=(13.333, 7.5), facecolor="white")
    ax = fig.add_axes([0.10, 0.15, 0.84, 0.66])
    ax.set_xscale("log")
    ax.set_xlim(0.002, 2000)
    ax.set_ylim(-2.5, 16)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.tick_params(colors=GREY, labelsize=12, length=0, pad=6)
    xt = [0.01, 0.1, 1, 10, 60]
    ax.set_xticks(xt)
    ax.set_xticklabels(["0.6 s", "6 s", "1 min", "10 min", "1 h"])
    ax.minorticks_off()
    ax.set_yticks(range(0, 16, 5))
    ax.set_yticklabels(["0"] + [f"+{v}" for v in range(5, 16, 5)])
    ax.axhspan(-2, 2, color=GREY_PALE, zorder=0)
    ax.axhline(0, color=LINE, lw=1.0, zorder=1)
    ax.axvline(15, color=GREY, lw=1.5, ls=(0, (6, 4)), zorder=1)
    ax.text(15 * 1.08, 15.3, "15-min budget", color=GREY, fontsize=13, va="center")
    ax.text(0.0024, 1.55, "within ±2 pp", color=GREY, fontsize=11, va="center")
    # label boxes at fixed places (axes fraction), each joined to its point by a thin connector
    place = {"MILP (exact)": (0.89, 0.12), "Fixed drop order": (0.47, 0.40),
             "Fixed when van is full": (0.86, 0.40), "Greedy": (0.24, 0.80)}
    for name, x, (m, lo, h) in pts:
        main = name == "MILP (exact)"
        col = BLUE if main else (GREY if name == "Greedy" else BLUE_LIGHT)
        if h != lo:
            ax.plot([x, x], [lo, h], color=col, lw=3, solid_capstyle="round", zorder=4)
        ax.scatter([x], [m], s=260, color=col, edgecolor="white", linewidth=2, zorder=5)
        fx, fy = ax.transAxes.inverted().transform(ax.transData.transform((x, m)))
        cx, cy = place[name]
        w, hgt = 0.19, 0.11
        ax.plot([cx, fx], [cy, fy], color=col, lw=1.1, transform=ax.transAxes, zorder=2, clip_on=False)
        lab = (f"{name}\n{x:.0f} min per hour" if main else
               f"{name}\n< 1 s · +{m:.1f} pp" if name == "Greedy" else f"{name}\n{x:.0f} min · +{m:.1f} pp")
        box(ax, cx - w / 2, cy - hgt / 2, w, hgt, lab, BLUE if main else "white", col, "white" if main else INK,
            size=13, weight="bold" if main else "normal", r=0.012, transform=ax.transAxes)
    ax.set_xlabel("Computing time per busy-night hour (log scale)", fontsize=13, color=INK, labelpad=10)
    ax.set_ylabel("Extra requests not reached vs MILP (percentage points)", fontsize=13, color=INK, labelpad=12)
    fig.text(0.04, 0.91, "Exact re-planning costs computing time; the shortcuts cost riders", ha="left",
             va="center", fontsize=24, fontweight="bold", color=INK)
    return fig


M7_CSV = ROOT / "outputs/sim/m7/per_night.csv"
D_LABEL = {"R0": "Never", "R1(10)": "After 10 min", "R1(15)": "After 15 min", "R2(15)": "Predicted wait > 15 min",
           "R3(2)": "Lyft sooner by 2 min"}
D_EXPECT = {  # rule means over 30 nights (m7_results_2026-11-24.md §2 and §4): (not reached ≤20 min %, bookings /100)
    5: {"R0": (23.8, 0.0), "R1(10)": (22.4, 7.6), "R1(15)": (22.4, 1.9), "R1u(10)": (23.8, 0.0), "R2(15)": (17.5, 8.8),
        "R3(2)": (15.6, 12.1)},
    6: {"R0": (14.2, 0.0), "R1(10)": (14.5, 2.1), "R1(15)": (14.3, 0.3), "R1u(10)": (14.2, 0.0), "R2(15)": (13.3, 2.2),
        "R3(2)": (12.4, 3.4)}}
# label positions (bookings, %) per panel, chosen so labels do not overlap; joined to the point by a connector
D_PLACE = {5: {"R0": (0.6, 25.6), "R1(15)": (2.6, 24.2), "R1(10)": (6.4, 24.6), "R2(15)": (5.2, 15.4),
               "R3(2)": (9.6, 13.4)},
           6: {"R0": (0.6, 11.6), "R1(15)": (1.0, 17.6), "R1(10)": (3.6, 16.4), "R2(15)": (6.2, 13.6),
               "R3(2)": (6.0, 11.4)}}


def figure_d():
    """Lyft-rule trade-off (M7): rule means over 30 full base evenings, 5 and 6 vans. The line joins the rules that reach
    more riders than every rule with fewer bookings (paired 95% interval of the difference below 0, from the frozen
    M7 analysis). Descriptive; the preregistered dominance rule is in the notes."""
    d = pd.read_csv(M7_CSV)
    iv = pd.read_csv(M7_CSV.with_name("pair_intervals.csv"))
    iv = iv[iv.measure == "not_reached_20_pp"]

    def better(f, a, b):          # a reaches more riders than b: upper bound of (a - b) below 0
        x = iv[(iv.fleet == f) & (iv.A == a) & (iv.B == b)]
        return bool(x.hi.iloc[0] < 0) if len(x) else bool(iv[(iv.fleet == f) & (iv.A == b) & (iv.B == a)].lo.iloc[0] > 0)
    assert len(d) == 360 and set(d.night) == {f"r{i:02d}" for i in range(30)}
    m = d.groupby(["fleet", "rule"])[["not_reached_20_pp", "lyft_per_100"]].mean()
    for f, e in D_EXPECT.items():
        for r, (y, x) in e.items():
            got = (round(m.loc[(f, r), "not_reached_20_pp"], 1), round(m.loc[(f, r), "lyft_per_100"], 1))
            assert got == (y, x), (f, r, got)
    assert (m.loc[5, "R1u(10)"] == m.loc[5, "R0"]).all() and (m.loc[6, "R1u(10)"] == m.loc[6, "R0"]).all()

    fig = plt.figure(figsize=(13.333, 7.5), facecolor="white")
    axes = [fig.add_axes([0.08, 0.15, 0.40, 0.66]), fig.add_axes([0.56, 0.15, 0.40, 0.66])]
    for ax, f in zip(axes, (5, 6)):
        pts = {r: (m.loc[(f, r), "lyft_per_100"], m.loc[(f, r), "not_reached_20_pp"]) for r in D_LABEL}
        front = sorted((r for r in pts if all(better(f, r, b) for b in pts if pts[b][0] < pts[r][0])),
                       key=lambda r: pts[r][0])
        assert front == (["R0", "R1(15)", "R2(15)", "R3(2)"] if f == 5 else ["R0", "R2(15)", "R3(2)"]), (f, front)
        ax.set_xlim(-0.8, 13.5)
        ax.set_ylim(10, 27)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(LINE)
        ax.tick_params(colors=GREY, labelsize=12, length=0, pad=6)
        ax.set_xticks(range(0, 13, 4))
        ax.set_yticks(range(10, 26, 5))
        ax.set_yticklabels([f"{v}%" for v in range(10, 26, 5)])
        ax.plot([pts[r][0] for r in front], [pts[r][1] for r in front], color=BLUE_LIGHT, lw=2, zorder=2)
        for r, (x, y) in pts.items():
            on = r in front
            ax.scatter([x], [y], s=200, color=BLUE if on else "white", edgecolor=BLUE if on else GREY, linewidth=2,
                       zorder=5)
            lx, ly = D_PLACE[f][r]
            ax.plot([x, lx], [y, ly], color=LINE, lw=1.0, zorder=3)
            ax.text(lx, ly, D_LABEL[r], ha="center", va="center", fontsize=13, color=INK if on else GREY, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))
        ax.set_title(f"{f} vans", fontsize=18, fontweight="bold", color=BLUE if f == 5 else INK, loc="left", pad=12)
        ax.set_xlabel("Lyft bookings per 100 requests", fontsize=13, color=INK, labelpad=10)
    axes[0].set_ylabel("Not reached within 20 min", fontsize=13, color=INK, labelpad=12)
    fig.text(0.08, 0.035, "“After 10 min with no van assigned” never fired: it sits on “Never”.", fontsize=11,
             color=GREY, ha="left")
    fig.text(0.04, 0.92, "Lyft rules matter with 5 vans, barely with 6", ha="left", va="center", fontsize=26,
             fontweight="bold", color=INK)
    return fig


def main():
    df = pd.read_csv(CSV)
    OUT.mkdir(exist_ok=True)
    for name, fig in (("fig_a_gap_by_condition", figure_a(df)), ("fig_b_every_night", figure_b(df)),
                      ("fig_c_speed_vs_riders", figure_c(df)), ("fig_d_lyft_rules", figure_d())):
        for ext in ("svg", "png"):
            fig.savefig(OUT / f"{name}.{ext}", dpi=200, facecolor="white")
        plt.close(fig)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
