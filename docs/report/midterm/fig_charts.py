"""Report-size copies of the methodology charts used in the midterm report (Figures 3, 5, 6, 7, 10, 11).

The originals live in docs/technical/methodology_pdf/make_figures.py and belong to the versioned
methodology PDF; that file is imported (for data, palette and helpers) but never edited. Each
function here redraws one chart at its final printed size under the report standard (fig_style.py),
so the font sizes set are the sizes on the page. Content, colours and numbers are unchanged.

Run:  .venv/bin/python docs/report/midterm/fig_charts.py
Writes figures/c_volume.pdf, c_assumed.pdf, c_noshow.pdf, c_example.pdf, c_phi.pdf, c_map.pdf.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "docs/technical/methodology_pdf"))
sys.path.insert(0, str(HERE))
import make_figures as mf  # noqa: E402  (palette, phi(); sets its own rcParams, so apply_style() after)
from make_figures import C_INPUT, C_OUT, C_POL, C_WARN, C_EVID, GRID, INK, MUTED, plt  # noqa: E402
from fig_style import COLW, FS, TEXTW, apply_style, save  # noqa: E402

plt.switch_backend("Agg")  # make_figures selects the pdf backend; the checks need a renderer
apply_style()

# shared mark constants across all report charts
LW_DATA = 1.2      # data lines
LW_REF = 0.7       # reference / dashed lines
LW_EDGE = 0.7      # bar edges
MS = 5.0           # point markers
DASH = (0, (3, 2))


def _grid_y(ax):
    ax.yaxis.grid(True, color=GRID, lw=0.5)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------- Figure 3: hourly volume
def fig_volume():
    hours = ["18:00–19:00", "19:00–20:00", "20:00–21:00"]
    rho = [12.85, 10.10, 10.71]
    exact = [r * 5 for r in rho]
    floors = [math.floor(x) for x in exact]
    final = [64, 50, 54]
    fig, ax = plt.subplots(figsize=(0.8 * TEXTW, 2.1))
    x = list(range(3))
    ax.bar(x, floors, width=0.5, color=C_INPUT[0], edgecolor=C_INPUT[1], lw=LW_EDGE,
           label=r"floor of $5\,\rho_h$")
    extra = [f - fl for f, fl in zip(final, floors)]
    ax.bar(x, extra, bottom=floors, width=0.5, color=C_INPUT[1], edgecolor=C_INPUT[1], lw=LW_EDGE,
           label="leftover unit")
    for i, (e, f) in enumerate(zip(exact, final)):
        ax.plot([i - 0.33, i + 0.33], [e, e], color=INK, lw=LW_REF + 0.3, ls=DASH)
        ax.text(i + 0.37, e, f"{e:.2f}", va="center", ha="left", fontsize=FS["small"], color=MUTED)
        ax.text(i, f + 3.0, f"{f}", ha="center", va="bottom", fontsize=FS["title"], weight="bold", color=INK)
        if f > floors[i]:
            ax.text(i + 0.17, f + 3.4, "+1", ha="left", va="bottom", fontsize=FS["small"], weight="bold",
                    color=C_INPUT[1])
    ax.set_xticks(x, hours)
    ax.set_xlim(-0.6, 2.75)
    ax.set_ylim(0, 78)
    ax.set_yticks([0, 20, 40, 60])
    ax.set_ylabel("requests in the hour")
    _grid_y(ax)
    ax.plot([], [], color=INK, lw=LW_REF + 0.3, ls=DASH, label=r"exact $5\,\rho_h$")
    ax.legend(loc="lower center", frameon=False, ncol=3, bbox_to_anchor=(0.5, 1.0), borderaxespad=0.2,
              handlelength=1.8, columnspacing=1.6)
    return save(fig, "c_volume")


# ---------------------------------------------------------------- Figure 6: three assumed distributions
def fig_assumed():
    fig, axes = plt.subplots(1, 3, figsize=(0.92 * TEXTW, 2.0), gridspec_kw={"wspace": 0.42})
    ax = axes[0]
    ps = [0.73, 0.18, 0.055, 0.025, 0.01]
    ax.bar(range(1, 6), ps, color=C_INPUT[0], edgecolor=C_INPUT[1], lw=LW_EDGE, width=0.65)
    ax.set_xticks(range(1, 6))
    ax.set_xlabel("riders in the request")
    ax.set_ylabel("share of requests")
    ax.set_ylim(0, 0.85)
    ax.set_title("Party size", loc="left", weight="bold")
    ax.text(5, 0.06, "XL", ha="center", va="bottom", fontsize=FS["small"], color=C_INPUT[1])
    _grid_y(ax)

    ax = axes[1]
    k, med = 1.5, 18.0
    lam = med / (math.log(2) ** (1 / k))
    ts = [i * 0.25 for i in range(0, 241)]
    ax.plot(ts, [math.exp(-((t / lam) ** k)) for t in ts], color=C_INPUT[1], lw=LW_DATA)
    ax.axvline(med, color=MUTED, lw=LW_REF, ls=DASH)
    ax.text(med + 2.0, 0.92, "median 18", fontsize=FS["small"], color=MUTED, va="center")
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 1.03)
    ax.set_xlabel("minutes since request")
    ax.set_ylabel("share still willing to wait")
    ax.set_title("Patience (placeholder)", loc="left", weight="bold")
    _grid_y(ax)

    ax = axes[2]
    mu = math.log(8.0)
    sig = math.log(15.0 / 8.0) / 1.2815515655446004
    xs = [0.05 + i * 0.1 for i in range(0, 300)]
    pdf = [math.exp(-((math.log(x) - mu) ** 2) / (2 * sig * sig)) / (x * sig * math.sqrt(2 * math.pi)) for x in xs]
    ax.fill_between(xs, pdf, color=C_INPUT[0], lw=0)
    ax.plot(xs, pdf, color=C_INPUT[1], lw=LW_DATA)
    for v in (8, 15):
        ax.axvline(v, color=MUTED, lw=LW_REF, ls=DASH)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, max(pdf) * 1.25)
    ax.set_yticks([])
    ax.set_xlabel("minutes, Lyft order to arrival")
    ax.set_title("Lyft delay", loc="left", weight="bold")
    return save(fig, "c_assumed")


# ---------------------------------------------------------------- Figure 7: no-show denominators
def fig_noshow():
    completed, noshow, total = 24_095, 2_359, 50_297
    other = total - completed - noshow
    fig, ax = plt.subplots(figsize=(0.85 * TEXTW, 1.75))
    y_all, y_arr, h = 1.0, 0.0, 0.42
    for y in (y_all, y_arr):
        ax.barh(y, completed, height=h, color=C_OUT[0], edgecolor=C_OUT[1], lw=LW_EDGE)
        ax.barh(y, noshow, left=completed, height=h, color=C_WARN[1], edgecolor=C_WARN[1], lw=LW_EDGE)
        ax.text(completed / 2, y, "Completed 24,095", ha="center", va="center", fontsize=FS["body"], color=INK)
    ax.barh(y_all, other, left=completed + noshow, height=h, color=C_EVID[0], edgecolor=C_EVID[1], lw=LW_EDGE)
    ax.text(completed + noshow + other / 2, y_all, "Canceled (≈ 47%)", ha="center", va="center",
            fontsize=FS["body"], color=INK)
    ax.annotate("No Show 2,359", xy=(completed + noshow / 2, y_all + h / 2 + 0.03),
                xytext=(completed + noshow / 2, y_all + 0.62), ha="center", va="bottom",
                fontsize=FS["body"], color=C_WARN[1],
                arrowprops=dict(arrowstyle="-", color=C_WARN[1], lw=LW_REF, shrinkA=1.5, shrinkB=0))
    ax.text(total + 1200, y_all, "÷ 50,297 requests\n= 4.7%", va="center", fontsize=FS["body"],
            weight="bold", color=INK, linespacing=1.25)
    ax.text(completed + noshow + 1200, y_arr, "÷ 26,454 van arrivals ≈ 8.9%\n(only if the status mapping holds)",
            va="center", fontsize=FS["body"], weight="bold", color=INK, linespacing=1.25)
    ax.set_yticks([y_all, y_arr], ["all recorded\nrequests", "van arrivals\n(mapping)"])
    ax.set_xlim(0, total * 1.33)
    ax.set_ylim(-0.32, 1.85)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=4, labelsize=FS["body"])
    return save(fig, "c_noshow")


# ---------------------------------------------------------------- Figure 10: worked example
def fig_example():
    fig = plt.figure(figsize=(0.85 * TEXTW, 2.9))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.2, 1.0], wspace=0.32, hspace=1.0)
    routes = {
        "A": [(0, "start"), (4, "pick r1"), (7, "pick r2"), (12, "drop r1"), (16, "drop r2")],
        "B": [(0, "start"), (5, "pick r2"), (8, "pick r1"), (13, "drop r1"), (15, "drop r2")],
    }
    colours = {"r1": C_INPUT[1], "r2": C_OUT[1]}
    for row, key in enumerate(["A", "B"]):
        ax = fig.add_subplot(gs[row, 0])
        ax.plot([0, 16.5], [0, 0], color=MUTED, lw=1.0, zorder=1)
        for t, lab in routes[key]:
            who = lab.split()[-1]
            c = colours.get(who, MUTED)
            mk = "^" if lab.startswith("pick") else ("v" if lab.startswith("drop") else "s")
            ax.plot(t, 0, mk, color=c, ms=6.5 if mk != "s" else 4, zorder=3, mec="white", mew=0.6)
            if lab != "start":
                dx = {"drop r1": -0.2, "drop r2": 0.2}.get(lab, 0)
                ha = {"drop r1": "right", "drop r2": "left"}.get(lab, "center")
                if lab.startswith("pick"):
                    ax.text(t, 0.38, lab, ha="center", va="bottom", fontsize=FS["body"], color=c)
                else:
                    ax.text(t + dx, -0.38, lab, ha=ha, va="top", fontsize=FS["body"], color=c)
        ax.set_xlim(-0.5, 17.8)
        ax.set_ylim(-1.0, 1.0)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_xticks(range(0, 17, 2))
        ax.set_title(f"Route {key}: {'r1' if key == 'A' else 'r2'} first", loc="left", weight="bold", pad=4)
        if row == 1:
            ax.set_xlabel("minutes from now (both routes 10 km; dwell omitted)")
    ax = fig.add_subplot(gs[:, 1])
    parts = {"A": (52.5, 13.0, 1.0), "B": (67.5, 12.5, 1.0)}
    cols = [C_POL[1], C_POL[0], "#9ca3af"]
    labels = ["waiting", "riding", "driving"]
    for i, k in enumerate(["A", "B"]):
        bottom = 0
        for j, v in enumerate(parts[k]):
            ax.bar(i, v, bottom=bottom, color=cols[j], edgecolor=C_POL[1], lw=LW_EDGE, width=0.6,
                   label=labels[j] if i == 0 else None)
            bottom += v
        ax.text(i, bottom + 2.5, f"{bottom:g}", ha="center", va="bottom", fontsize=FS["title"], weight="bold",
                color=INK)
    ax.set_xticks([0, 1], ["A", "B"])
    ax.tick_params(axis="x", labelsize=FS["body"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 20, 40, 60, 80])
    ax.set_ylabel("route score (points)")
    _grid_y(ax)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h[::-1], l[::-1], frameon=False, loc="upper left", fontsize=FS["small"], handlelength=1.2,
              borderaxespad=0.1, labelspacing=0.3)
    return save(fig, "c_example")


# ---------------------------------------------------------------- Figure 11: convex waiting penalty
def fig_phi():
    phi = mf.phi
    fig, ax = plt.subplots(figsize=(COLW, 2.45))
    ws = [i * 0.05 for i in range(0, 501)]
    ax.plot(ws, [phi(w) for w in ws], color=C_POL[1], lw=LW_DATA + 0.4, label=r"waiting penalty $\varphi(W)$",
            zorder=3)
    ax.plot(ws, ws, color=MUTED, lw=LW_REF + 0.3, ls=(0, (4, 3)), label="straight line, 1 point per minute")
    for w in (5, 10, 15, 20):
        ax.plot(w, phi(w), "o", color=C_POL[1], ms=MS - 1, zorder=4, mec="white", mew=0.6)
        ax.text(w - 0.6, phi(w) + 6, f"{phi(w):g}", ha="right", va="bottom", fontsize=FS["small"], color=INK)
    for xm, s in [(2.5, "1"), (7.5, "2.5"), (12.5, "5"), (17.5, "10"), (22.5, "20")]:
        ax.text(xm, -20, s, ha="center", va="center", fontsize=FS["small"], color=C_POL[1])
    ax.text(-0.5, -20, "slope", ha="right", va="center", fontsize=FS["small"], color=C_POL[1])
    ax.set_xlim(0, 25)
    ax.set_ylim(-32, 200)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.set_yticks([0, 50, 100, 150, 200])
    ax.set_xlabel("total wait $W$ since the request (min)")
    ax.set_ylabel("points per passenger")
    for b in (5, 10, 15, 20):
        ax.axvline(b, color=GRID, lw=0.5, zorder=0)
    ax.axhline(0, color=GRID, lw=0.5, zorder=0)
    ax.legend(loc="upper left", frameon=False, borderaxespad=0.1, handlelength=2.0)
    return save(fig, "c_phi", max_width=COLW)


# ---------------------------------------------------------------- Figure 5: the synthetic map
def fig_map():
    """Report copy of docs/presentations/midterm/v0.4/make_map.py (same inputs, marks and labels) at COLW."""
    import pandas as pd

    z = pd.read_csv(REPO / "data/processed/zones_v1.csv")
    loc = pd.read_csv(REPO / "data/processed/locations_v1.csv").drop_duplicates("loc_id").set_index("loc_id")
    r = pd.read_csv(REPO / "data/scenarios/v2/L5/r00/requests.csv")
    fig, ax = plt.subplots(figsize=(COLW, 3.95))
    ax.scatter(loc.lon, loc.lat, s=2.5, color="#c9c8c2", lw=0, zorder=1, label="188 April map places")
    for _, x in r.iterrows():
        o, d = loc.loc[x.o_loc], loc.loc[x.d_loc]
        ax.plot([o.lon, d.lon], [o.lat, d.lat], color="#a3a29d", lw=0.6, zorder=2)
    ax.scatter(loc.loc[r.o_loc].lon, loc.loc[r.o_loc].lat, s=14, color="#2a78d6", edgecolor="white", lw=0.6,
               zorder=3, label="pickup")
    ax.scatter(loc.loc[r.d_loc].lon, loc.loc[r.d_loc].lat, s=14, marker="s", color="#eb6834", edgecolor="white",
               lw=0.6, zorder=3, label="drop-off")
    names = {"Z08": ("Homewood campus", (32, -13)), "Z02": ("Charles Village", (26, 10)),
             "Z03": ("Mount Vernon\n(Peabody)", (20, 0)), "Z09": ("Inner Harbor", (18, 0))}
    for zid, (nm, off) in names.items():
        row = z[z.zone_id == zid].iloc[0]
        ax.annotate(nm, (row.lon, row.lat), xytext=off, textcoords="offset points", fontsize=FS["small"],
                    color="#333", va="center", linespacing=1.15,
                    arrowprops=dict(arrowstyle="-", color="#888", lw=0.5, shrinkA=1, shrinkB=2))
    ax.set_aspect(1 / 0.773)
    ax.set_xlim(loc.lon.min() - 0.004, loc.lon.max() + 0.03)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color("#d0cfc9")
        s.set_linewidth(0.6)
    ax.legend(loc="upper right", frameon=False, fontsize=FS["small"], handletextpad=0.2, borderaxespad=0.3,
              labelspacing=0.3)
    ax.set_title("One constructed hour: 28 requests", fontsize=FS["title"], loc="left", color="#222", pad=4)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)
    return save(fig, "c_map", max_width=COLW)


if __name__ == "__main__":
    for f in (fig_volume, fig_assumed, fig_noshow, fig_example, fig_phi, fig_map):
        f()
    print("wrote c_volume, c_assumed, c_noshow, c_example, c_phi, c_map")
