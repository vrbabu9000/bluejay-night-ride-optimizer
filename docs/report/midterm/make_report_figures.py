"""New figures for the midterm report (the reused f1-f9 come from the methodology PDF).

Every number is read from saved files; nothing is simulated here:
  docs/presentations/midterm/v0.4/derived/numbers.json   (the deck's numbers)
  data/scenarios/v2/L5/r*/requests.csv                    (the 30 pilot nights)

Every figure is drawn at its final printed size (fig_style: COLW, TEXTW) and is included at
natural size, so the font sizes below (fig_style.FS) are the printed sizes. Diagrams are drawn
on an axes whose data units are inches, so gaps and paddings are physical.

Run:  .venv/bin/python docs/report/midterm/make_report_figures.py
Writes PDF figures into docs/report/midterm/figures/.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "docs/technical/methodology_pdf"))
sys.path.insert(0, str(HERE))
import make_figures as mf  # noqa: E402  (shared palette)
from make_figures import (C_EVID, C_INPUT, C_OUT, C_POL, C_SIM, C_WARN, GRID, INK, MUTED,  # noqa: E402
                          plt)
from fig_style import COLW, FS, OUT, TEXTW, apply_style, save  # noqa: E402

plt.switch_backend("Agg")  # make_figures selects the pdf backend; the fig_style checks need a raster renderer
apply_style()  # after make_figures, which sets its own rcParams

NUM = json.load(open(REPO / "docs/presentations/midterm/v0.4/derived/numbers.json"))
L5 = REPO / "data/scenarios/v2/L5"
PREDICTIVE = {"R2(15)", "R3(2)"}
WIDE = 0.95 * TEXTW   # figure* drawn at 0.95 \textwidth
LW = 0.9              # box borders and arrows, all diagrams
PAD = 0.08            # inches, text padding inside a box
LH_T = FS["title"] * 1.25 / 72   # line height, inches
LH_B = FS["body"] * 1.25 / 72


def label(code):
    return f"{NUM['names'][code]} [{code}]"


# ------------------------------------------------------------ diagram helpers (inch units)
def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def card(ax, x0, y0, w, h, title, body, colours, ls="-"):
    """Box with lower-left (x0, y0); bold title at the top, body centred in the space below it."""
    face, edge = colours
    ax.add_patch(mf.FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.05",
                                   fc=face, ec=edge, lw=LW, ls=ls, zorder=2))
    top = y0 + h - PAD
    xc = x0 + w / 2
    if title:
        ax.text(xc, top, title, ha="center", va="top", fontsize=FS["title"], color=INK,
                weight="bold", zorder=3, linespacing=1.15)
        top -= (title.count("\n") + 1) * LH_T + 0.04
    if body:
        ax.text(xc, (top + y0 + PAD) / 2, body, ha="center", va="center", fontsize=FS["body"],
                color=INK, zorder=3, linespacing=1.25)


def card_h(title_lines, body_lines):
    return 2 * PAD + title_lines * LH_T + 0.04 + body_lines * LH_B + 0.04


def arrow(ax, p0, p1):
    ax.add_patch(mf.FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=8, color=INK, lw=LW,
                                    shrinkA=0, shrinkB=0, zorder=1))


def arrow_label(ax, x, y, text, va):
    ax.text(x, y, text, ha="center", va=va, fontsize=FS["small"], color=MUTED, linespacing=1.15)


def chain(ax, xs, y0, w, h, items, colours_of):
    """A row of equal cards joined left to right by arrows."""
    for x0, (title, body, *rest) in zip(xs, items):
        card(ax, x0, y0, w, h, title, body, colours_of(rest))
    for xa, xb in zip(xs[:-1], xs[1:]):
        arrow(ax, (xa + w + 0.04, y0 + h / 2), (xb - 0.04, y0 + h / 2))


def row_x(total_w, n, w):
    gap = (total_w - n * w) / (n - 1)
    return [i * (w + gap) for i in range(n)]


# ------------------------------------------------------------ R1 workload chain
def fig_workload():
    a = NUM["april"]
    steps = [
        ("Completed rides,\n6 pm hour", f"{a['tooltip_18']:,} in 30 days\n≈ 170 per evening", "DERIVED"),
        ("Requests per\ncompleted ride", f"{a['status']['requests']:,} ÷ {a['status']['completed']:,}\n≈ {a['r_per_c']:.2f}", "DERIVED"),
        ("Requests in\nthat hour", "170 × 2.09\n≈ 355 per evening", "DERIVED + ASSUMED"),
        ("Per vehicle\non duty", f"355 ÷ {a['vehicles']['18:00']}\n≈ {a['rho']['18:00']} per\nvehicle-hour", "DERIVED + ASSUMED"),
    ]
    w, h, y0 = 1.36, card_h(2, 3), 0.22
    fig, ax = canvas(WIDE, y0 + h + 0.02)
    xs = row_x(WIDE, 4, w)
    chain(ax, xs, y0, w, h, steps, lambda r: C_INPUT if "ASSUMED" in r[0] else C_EVID)
    for x0, (*_, tag) in zip(xs, steps):
        ax.text(x0 + w / 2, y0 - 0.07, tag, ha="center", va="top", fontsize=FS["small"], color=MUTED,
                weight="bold")
    save(fig, "r1_workload")


# ------------------------------------------------------------ R2 pilot arrivals
def fig_arrivals():
    nights = sorted(p for p in L5.iterdir() if (p / "requests.csv").exists())
    counts = [0] * 12
    for n in nights:
        for row in csv.DictReader(open(n / "requests.csv")):
            counts[min(int(row["t_request_s"]) // 300, 11)] += 1
    mean = [c / len(nights) for c in counts]
    fig, ax = plt.subplots(figsize=(COLW, 2.0))
    ax.axvspan(20, 30, color=C_SIM[0], zorder=0, lw=0)
    ax.bar([5 * i + 2.5 for i in range(12)], mean, width=4.4, color=C_POL[1], zorder=2)
    # label beside the band, centred between the 6 and 8 gridlines so it touches neither
    ax.text(31.5, 7.0, "burst window\n18:20–18:30", ha="left", va="center",
            fontsize=FS["small"], color=MUTED, linespacing=1.15)
    ax.set_xticks(range(0, 61, 10))
    ax.set_xticklabels([f"18:{m:02d}" if m < 60 else "19:00" for m in range(0, 61, 10)])
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 9.0)
    ax.set_ylabel("requests per 5 min\n(mean of 30 nights)")
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "r2_arrivals", max_width=COLW)
    return len(nights), sum(counts)


# ------------------------------------------------------------ R3 reach by rule
def fig_reach():
    b = NUM["batch"]
    rules = NUM["rules"]
    fig, ax = plt.subplots(figsize=(COLW, 2.3))
    ys = list(range(len(rules)))[::-1]
    for y, code, r, sd, lyft in zip(ys, rules, b["reached"], b["reached_sd"], b["bookings"]):
        # deck colours: blue predictive, green unassigned-time, grey waiting-time rules
        c = C_INPUT[1] if code in PREDICTIVE else (C_POL[1] if code == "R1u(10)" else C_EVID[1])
        ax.barh(y, r, height=0.62, color=c, zorder=2)
        ax.errorbar(r, y, xerr=sd, color=INK, lw=0.8, capsize=2, capthick=0.8, zorder=3)
        ax.text(0.025, y, f"{r:.2f}", va="center", ha="left", fontsize=FS["small"], color="white",
                weight="bold", zorder=4)
        ax.text(1.0, y, f"{lyft:.1f}", va="center", ha="right", fontsize=FS["small"], color=INK)
    ax.text(1.0, len(rules) - 0.45, "Lyft orders\nper night", ha="right", va="bottom", fontsize=FS["small"],
            color=MUTED, linespacing=1.15, clip_on=False)
    ax.set_yticks(ys)
    ax.set_yticklabels(rules)
    ax.set_ylim(-0.5, len(rules) - 0.5)
    ax.set_xlim(0, 1.0)
    ax.set_xticks([0, 0.25, 0.5, 0.75])
    ax.set_xlabel("share of the 28 requests reached by a vehicle\nwithin 15 min (mean ± SD over 30 nights)")
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "r3_reach", max_width=COLW)


# ------------------------------------------------------------ R4 transfer fates
def fig_fates():
    f = NUM["batch"]["fates"]
    rules = ["R1(10)", "R1(15)", "R1u(10)", "R2(15)", "R3(2)"]
    parts = [("completed", "Lyft trip completed", C_POL[1]),
             ("noshow", "Lyft no-show", C_EVID[1]),
             ("lag", "cancelled during the 2-min ordering lag", "#e8a09a"),
             ("after", "cancelled after the Lyft was ordered", C_WARN[1])]
    W = 0.78 * TEXTW
    fig, ax = plt.subplots(figsize=(W, 2.4))
    # keep the long rule names and the n column inside the figure so the printed width stays at W
    fig.subplots_adjust(left=2.42 / W, right=1 - 0.42 / W, top=0.97, bottom=0.33)
    ys = list(range(len(rules)))[::-1]
    for y, code in zip(ys, rules):
        left = 0.0
        n = f[code]["transfers"]
        for key, name, col in parts:
            w = f[code][key] / n
            ax.barh(y, w, left=left, height=0.62, color=col, edgecolor="white", lw=0.8,
                    label=name if code == rules[0] else None)
            if w > 0.08:
                ax.text(left + w / 2, y, f"{f[code][key]}", ha="center", va="center", fontsize=FS["small"],
                        color="white", weight="bold")
            left += w
        ax.text(1.02, y, f"n = {n}", va="center", fontsize=FS["small"], color=INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([label(c) for c in rules])
    ax.set_ylim(-0.5, len(rules) - 0.5)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("share of transferred requests (totals over 30 nights; n = transfers)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.27), ncol=2, frameon=False,
              handlelength=1.2, columnspacing=1.5)
    save(fig, "r4_fates")


# ------------------------------------------------------------ R5 architecture
def fig_architecture():
    W, H = WIDE, 2.9
    fig, ax = canvas(W, H)
    h1, h2, h3, h5 = card_h(1, 1), card_h(1, 2), card_h(1, 3), card_h(1, 5)
    # left column: what is built once, offline
    lx, lw = 0.02, 1.40
    gy = H - 0.02 - h1
    card(ax, lx, gy, lw, h1, "Scenario generator", "built once, offline", C_INPUT)
    iy = gy - 0.25 - h3
    card(ax, lx, iy, lw, h3, "Scenario inputs", "requests, places,\nparties, vans,\ntravel times", C_INPUT)
    hy = 0.10
    card(ax, lx, hy, lw, h3, "Hidden draws", "patience, presence,\nLyft delay; never\nshown to dispatcher", C_WARN)
    arrow(ax, (lx + lw / 2, gy - 0.04), (lx + lw / 2, iy + h3 + 0.04))
    # middle column: the simulator and what it records
    sx, sw, sy = 1.72, 1.45, 0.60
    card(ax, sx, sy, sw, h5, "Simulator (referee)",
         "clock, van positions,\nriders aboard,\nrequest states;\nreveals each event\nonly when it happens", C_SIM)
    card(ax, sx, gy, sw, h1, "Recorded outcomes", "waits, Lyft, van-km", C_OUT)
    arrow(ax, (sx + sw / 2, sy + h5 + 0.04), (sx + sw / 2, gy - 0.04))
    arrow(ax, (lx + lw + 0.04, iy + h3 / 2), (sx - 0.04, sy + h5 - 0.25))
    arrow(ax, (lx + lw + 0.04, hy + h3 / 2), (sx - 0.04, sy + 0.25))
    # right: the decision step, which sees only the past
    rx0, rx1, ry0, ry1 = 3.92, W - 0.02, 0.02, H - 0.02
    ax.add_patch(mf.FancyBboxPatch((rx0, ry0), rx1 - rx0, ry1 - ry0, boxstyle="round,pad=0,rounding_size=0.06",
                                   fc="none", ec=C_POL[1], lw=LW, ls=(0, (4, 3))))
    rc = (rx0 + rx1) / 2
    ax.text(rc, ry1 - PAD, "Decision step: sees only the past", ha="center", va="top", fontsize=FS["title"],
            color=C_POL[1], weight="bold")
    cw = 2.15
    cx = rc - cw / 2
    t1 = ry1 - PAD - LH_T - 0.12
    card(ax, cx, t1 - h1, cw, h1, "Route generation", "candidate routes per van", C_POL)
    t2 = t1 - h1 - 0.28
    card(ax, cx, t2 - h1, cw, h1, "Van optimizer (MILP)", "one route per van", C_POL)
    t3 = t2 - h1 - 0.28
    card(ax, cx, t3 - h2, cw, h2, "Transfer rule", "reads plan predictions;\nmay move requests to Lyft", C_POL)
    arrow(ax, (rc, t1 - h1 - 0.04), (rc, t2 + 0.04))
    arrow(ax, (rc, t2 - h1 - 0.04), (rc, t3 + 0.04))
    # simulator <-> decision step: two horizontal arrows, labels in the clear gap above and below
    gx = (sx + sw + rx0) / 2
    ya, yb = sy + h5 - 0.30, sy + 0.28
    arrow(ax, (sx + sw + 0.04, ya), (rx0 - 0.04, ya))
    arrow_label(ax, gx, ya + 0.06, "observable\nstate", "bottom")
    arrow(ax, (rx0 - 0.04, yb), (sx + sw + 0.04, yb))
    arrow_label(ax, gx, yb - 0.06, "plan and\ntransfers", "top")
    save(fig, "r5_architecture")


# ------------------------------------------------------------ R6 roadmap
def fig_roadmap():
    steps = [("1  Behavioural\nsensitivity", "rerun saved nights\nunder other patience\nshapes, Lyft delays"),
             ("2  Five-van\nfeasibility", "run the 168-request\nevening; check solve\ntimes, candidate limits"),
             ("3  Agreed evaluation\ncriteria", "price one more rider\nreached per Lyft order;\npaired intervals"),
             ("4  Baseline, then\nthreshold search", "matched-budget\nbaseline; tune on some\nnights, report on fresh")]
    w, h = 1.36, card_h(2, 3)
    ph = 2 * PAD + 2 * LH_B + 0.02
    y0 = ph + 0.18
    fig, ax = canvas(WIDE, y0 + h + 0.02)
    chain(ax, row_x(WIDE, 4, w), y0, w, h, steps, lambda r: C_POL)
    card(ax, 0, 0, WIDE, ph, "", "In parallel, from step 2: dispatcher benchmark, rolling-horizon MILP vs greedy "
         "insertion,\nacross fleet size, demand pattern and re-planning interval", C_SIM)
    save(fig, "r6_roadmap")


# ------------------------------------------------------------ R7 trade-off (report wording: Lyft orders)
def fig_tradeoff():
    rows = list(csv.DictReader(open(REPO / "outputs/sim/batch_L5_v1/tradeoff_rule_summary.csv")))
    fig, ax = plt.subplots(figsize=(COLW, 2.4))
    offsets = {"R0": (-0.55, 0.0), "R1(10)": (0.55, 0.0), "R1(15)": (0.55, 0.0),
               "R1u(10)": (0.45, -0.035), "R2(15)": (-0.55, 0.0), "R3(2)": (0.55, -0.02)}
    for r in rows:
        name = r[""]
        x, y = float(r["lyft_bookings_mean"]), float(r["reached_15_share_mean"])
        nd = r["nondominated_on_means_2obj"] == "True"
        ax.plot(x, y, "o", ms=6, mec=C_POL[1], mfc=C_POL[1] if nd else "white", mew=1.0, zorder=3)
        dx, dy = offsets.get(name, (0.55, 0.0))
        ax.text(x + dx, y + dy, name, fontsize=FS["small"], va="center", ha="left" if dx > 0 else "right",
                color=INK)
    ax.set_xlim(-1.6, 12.5)
    ax.set_ylim(0.40, 0.80)
    ax.set_xlabel("Lyft orders per night (mean of 30 nights)")
    ax.set_ylabel("share of all requests reached\nwithin 15 min (mean)")
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.plot([], [], "o", ms=6, mec=C_POL[1], mfc=C_POL[1], label="not dominated by another tested rule")
    ax.plot([], [], "o", ms=6, mec=C_POL[1], mfc="white", mew=1.0, label="dominated (by R0)")
    ax.legend(loc="upper left", frameon=False, handletextpad=0.3, borderaxespad=0.3)
    save(fig, "r7_tradeoff", max_width=COLW)


if __name__ == "__main__":
    fig_workload()
    n, total = fig_arrivals()
    fig_reach()
    fig_fates()
    fig_architecture()
    fig_roadmap()
    fig_tradeoff()
    print(f"arrivals: {n} nights, {total} requests; figures written to {OUT}")
