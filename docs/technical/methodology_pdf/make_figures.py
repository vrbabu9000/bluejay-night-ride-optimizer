"""Figures for the scenario-methodology companion PDF.

Every number drawn here is quoted from the authoritative documents
(scenario_methodology.md v1.0, scenario_spec.md v0.4, model_design.md v0.2,
decision_log.md). Nothing is simulated: no figure shows a simulation outcome.
The two curves in Figure 4 are drawn from the stated placeholder parameters
(Weibull shape 1.5, median 18 min; lognormal median 8 min, P90 ~15 min).

Run:  .venv/bin/python docs/technical/methodology_pdf/make_figures.py
Writes PDF figures into docs/technical/methodology_pdf/figures/.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 9.5,
    "axes.titlesize": 10,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
})

# Shared palette (matches the marker colours in methodology.tex)
INK = "#1f2933"
MUTED = "#5b6370"
GRID = "#e5e7eb"
C_INPUT = ("#e7f0fd", "#3b6fb6")     # inputs / assumed
C_SIM = ("#fff3bf", "#b08900")       # simulator (referee) and services
C_POL = ("#e9f5ec", "#2d6a4f")       # policies
C_OUT = ("#f3e8fd", "#7b3fb6")       # produced outcomes
C_EVID = ("#eeeeee", "#6b7280")      # April aggregate evidence
C_WARN = ("#fde8e8", "#b42318")      # cancellation / no-show / failure

TEXTW = 6.3  # inches, equals \textwidth in methodology.tex


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def box(ax, x, y, w, h, text, colours, fs=9.5, weight="normal", lw=1.2, ls="-", split=True):
    face, edge = colours
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle="round,pad=0.02,rounding_size=0.06",
                       fc=face, ec=edge, lw=lw, ls=ls, zorder=2)
    ax.add_patch(p)
    if split and weight == "bold" and "\n" in text:
        # bold title line, regular body lines
        title, body = text.split("\n", 1)
        fig = ax.figure
        ax_h_in = fig.get_size_inches()[1] * ax.get_position().height
        y0, y1 = ax.get_ylim()
        lh = fs * 1.3 / 72 * (y1 - y0) / ax_h_in
        nbody = body.count("\n") + 1
        top = y + (1 + nbody) * lh / 2
        ax.text(x, top - lh / 2, title, ha="center", va="center", fontsize=fs, color=INK,
                weight="bold", zorder=3)
        ax.text(x, top - lh - nbody * lh / 2, body, ha="center", va="center", fontsize=fs - 0.5,
                color=INK, zorder=3, linespacing=1.3)
        return
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK,
            weight=weight, zorder=3, linespacing=1.25)


def arrow(ax, p0, p1, colour=INK, text=None, toff=(0, 0), fs=8.5, rad=0.0, lw=1.1):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11, color=colour, lw=lw,
                        connectionstyle=f"arc3,rad={rad}", zorder=1, shrinkA=1, shrinkB=1)
    ax.add_patch(a)
    if text:
        mx = (p0[0] + p1[0]) / 2 + toff[0]
        my = (p0[1] + p1[1]) / 2 + toff[1]
        ax.text(mx, my, text, fontsize=fs, color=MUTED, ha="center", va="center", zorder=3,
                linespacing=1.15)


# ---------------------------------------------------------------- F1 system
def fig_system():
    fig, ax = plt.subplots(figsize=(TEXTW, 4.7))
    ax.set_xlim(0, 10)
    ax.set_ylim(2.0, 8.35)
    ax.axis("off")
    box(ax, 3.0, 7.8, 5.2, 0.95, "Scenario inputs (frozen)\nrequests, vans on duty, hidden rider traits",
        C_INPUT, weight="bold")
    box(ax, 8.0, 7.8, 3.2, 0.95, "Travel table $t_0$\n(local OSRM, hashed)", C_INPUT, weight="bold")
    box(ax, 3.9, 5.3, 5.4, 1.25, "Event simulator (the referee)\nclock, event order, van movement;\n"
        "applies hidden traits only when events happen", C_SIM, weight="bold")
    box(ax, 8.55, 5.3, 2.7, 1.25, "Evaluation\nfrom the event log:\nrider outcomes,\nLyft counts, van-km",
        C_OUT, weight="bold", fs=9)
    box(ax, 1.6, 2.75, 3.1, 1.15, "Van dispatcher\nplans routes, gives ETAs\n(sees no hidden traits)",
        C_POL, weight="bold", fs=8.8)
    box(ax, 5.0, 2.75, 2.9, 1.15, "Lyft transfer rule\nreads the board\n(sees no hidden traits)",
        C_POL, weight="bold", fs=8.8)
    box(ax, 8.45, 2.75, 2.9, 1.15, "Lyft service\nbooking, delay, ride", C_SIM, weight="bold", fs=8.8)

    arrow(ax, (3.0, 7.32), (3.0, 5.93))
    arrow(ax, (8.0, 7.32), (5.9, 5.93))
    arrow(ax, (6.6, 5.3), (7.2, 5.3))
    arrow(ax, (1.25, 4.67), (1.25, 3.33), text="requests\nso far", toff=(-0.62, 0.0))
    arrow(ax, (1.95, 3.33), (1.95, 4.67), text="routes,\nETAs", toff=(0.55, 0.0))
    arrow(ax, (4.7, 4.67), (4.7, 3.33), text="open requests\n+ ETAs", toff=(-0.8, 0.0))
    arrow(ax, (5.3, 3.33), (5.3, 4.67), text="transfer\ndecisions", toff=(0.62, 0.0))
    arrow(ax, (6.45, 4.67), (7.75, 3.33), text="booking", toff=(-0.15, -0.3))
    arrow(ax, (8.8, 3.33), (8.8, 4.67), text="arrival,\ndrop-off", toff=(0.62, 0.0))
    save(fig, "f1_system")


# ---------------------------------------------------------------- F2 volume
def fig_volume():
    hours = ["18:00–19:00", "19:00–20:00", "20:00–21:00"]
    rho = [12.85, 10.10, 10.71]
    exact = [r * 5 for r in rho]             # 64.25, 50.50, 53.55
    floors = [math.floor(x) for x in exact]   # 64, 50, 53
    final = [64, 50, 54]
    fig, ax = plt.subplots(figsize=(TEXTW, 2.7))
    x = list(range(3))
    ax.bar(x, floors, width=0.55, color=C_INPUT[0], edgecolor=C_INPUT[1], lw=1.0,
           label=r"floor of $5\,\rho_h$")
    extra = [f - fl for f, fl in zip(final, floors)]
    ax.bar(x, extra, bottom=floors, width=0.55, color=C_INPUT[1], edgecolor=C_INPUT[1], lw=1.0,
           label="leftover unit")
    for i, (e, f) in enumerate(zip(exact, final)):
        ax.plot([i - 0.36, i + 0.36], [e, e], color=INK, lw=1.0, ls=(0, (3, 2)))
        ax.text(i + 0.39, e, f"{e:.2f}", va="center", ha="left", fontsize=9, color=MUTED)
        ax.text(i, f + 1.8, f"{f}", ha="center", va="bottom", fontsize=11, weight="bold", color=INK)
        if f > floors[i]:
            ax.text(i + 0.16, f + 2.3, "+1", ha="left", va="center", fontsize=9, weight="bold",
                    color=C_INPUT[1])
    ax.set_xticks(x, hours)
    ax.set_ylim(0, 78)
    ax.set_ylabel("requests in the hour")
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.plot([], [], color=INK, lw=1.0, ls=(0, (3, 2)), label=r"exact $5\,\rho_h$")
    ax.legend(loc="upper center", frameon=False, ncol=3, bbox_to_anchor=(0.5, 1.17))
    save(fig, "f2_volume")


# ---------------------------------------------------------------- F3 no-show denominators
def fig_noshow():
    completed, noshow, total = 24_095, 2_359, 50_297
    other = total - completed - noshow
    fig, ax = plt.subplots(figsize=(TEXTW, 2.2))
    y_all, y_arr, h = 1.0, 0.0, 0.42
    for y in (y_all, y_arr):
        ax.barh(y, completed, height=h, color=C_OUT[0], edgecolor=C_OUT[1], lw=0.9)
        ax.barh(y, noshow, left=completed, height=h, color=C_WARN[1], edgecolor=C_WARN[1], lw=0.9)
        ax.text(completed / 2, y, "Completed 24,095", ha="center", va="center", fontsize=9)
    ax.barh(y_all, other, left=completed + noshow, height=h, color=C_EVID[0], edgecolor=C_EVID[1], lw=0.9)
    ax.text(completed + noshow + other / 2, y_all, "Canceled (≈ 47%)", ha="center", va="center", fontsize=9)
    ax.annotate("No Show 2,359", xy=(completed + noshow / 2, y_all + h / 2),
                xytext=(completed + noshow / 2, y_all + 0.55), ha="center", fontsize=9, color=C_WARN[1],
                arrowprops=dict(arrowstyle="-", color=C_WARN[1], lw=0.8))
    ax.text(total + 700, y_all, "÷ 50,297 requests\n= 4.7%", va="center", fontsize=9.5, weight="bold")
    ax.text(completed + noshow + 700, y_arr, "÷ 26,454 van arrivals ≈ 8.9%\n(only if the status mapping holds)",
            va="center", fontsize=9.5, weight="bold")
    ax.set_yticks([y_all, y_arr], ["all recorded\nrequests", "van arrivals\n(mapping)"])
    ax.set_xlim(0, total * 1.36)
    ax.set_ylim(-0.4, 1.78)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "f3_noshow")


# ---------------------------------------------------------------- F4 assumed distributions
def fig_assumed():
    fig, axes = plt.subplots(1, 3, figsize=(TEXTW, 2.3), gridspec_kw={"wspace": 0.45})
    ax = axes[0]
    ps = [0.73, 0.18, 0.055, 0.025, 0.01]
    ax.bar(range(1, 6), ps, color=C_INPUT[0], edgecolor=C_INPUT[1], lw=0.9, width=0.7)
    ax.set_xticks(range(1, 6))
    ax.set_xlabel("riders in the booking")
    ax.set_ylabel("share of bookings")
    ax.set_ylim(0, 0.85)
    ax.set_title("Party size", loc="left", weight="bold")
    ax.text(5, 0.05, "XL", ha="center", fontsize=8.5, color=C_INPUT[1])

    ax = axes[1]
    k, med = 1.5, 18.0
    lam = med / (math.log(2) ** (1 / k))
    ts = [i * 0.25 for i in range(0, 241)]
    ax.plot(ts, [math.exp(-((t / lam) ** k)) for t in ts], color=C_INPUT[1], lw=1.6)
    ax.axvline(med, color=MUTED, lw=0.8, ls=(0, (3, 2)))
    ax.text(med + 1.5, 0.9, "median 18", fontsize=8.5, color=MUTED)
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 1.03)
    ax.set_xlabel("minutes since request")
    ax.set_ylabel("share still willing to wait")
    ax.set_title("Patience (placeholder)", loc="left", weight="bold")

    ax = axes[2]
    mu = math.log(8.0)
    sig = math.log(15.0 / 8.0) / 1.2815515655446004
    xs = [0.05 + i * 0.1 for i in range(0, 300)]
    pdf = [math.exp(-((math.log(x) - mu) ** 2) / (2 * sig * sig)) / (x * sig * math.sqrt(2 * math.pi)) for x in xs]
    ax.fill_between(xs, pdf, color=C_INPUT[0])
    ax.plot(xs, pdf, color=C_INPUT[1], lw=1.4)
    for v, lab, f in [(8, "median 8", 1.12), (15, "P90 ≈ 15", 1.12)]:
        ax.axvline(v, color=MUTED, lw=0.8, ls=(0, (3, 2)))
        pass
    ax.set_xlim(0, 30)
    ax.set_ylim(0, max(pdf) * 1.25)
    ax.set_yticks([])
    ax.set_xlabel("minutes, booking to Lyft arrival")
    ax.set_title("Lyft delay", loc="left", weight="bold")
    save(fig, "f4_assumed")


# ---------------------------------------------------------------- F5 wait penalty
def phi(w):
    bps = [0, 5, 10, 15, 20]
    slopes = [1, 2.5, 5, 10, 20]
    total = 0.0
    for i, b in enumerate(bps):
        hi = bps[i + 1] if i + 1 < len(bps) else float("inf")
        if w > b:
            total += slopes[i] * (min(w, hi) - b)
    return total


def fig_phi():
    fig, ax = plt.subplots(figsize=(TEXTW, 3.0))
    ws = [i * 0.05 for i in range(0, 501)]
    ax.plot(ws, [phi(w) for w in ws], color=C_POL[1], lw=2.0, label=r"waiting penalty $\varphi(W)$")
    ax.plot(ws, ws, color=MUTED, lw=1.0, ls=(0, (4, 3)), label="straight line, 1 point per minute")
    for w in (5, 10, 15, 20):
        ax.plot(w, phi(w), "o", color=C_POL[1], ms=4.5, zorder=4)
        ax.text(w - 0.45, phi(w) + 5, f"{phi(w):g}", ha="right", fontsize=9, color=INK)
    for xm, s in [(2.5, "1"), (7.5, "2.5"), (12.5, "5"), (17.5, "10"), (22.5, "20")]:
        ax.text(xm, -15, s, ha="center", fontsize=9, color=C_POL[1])
    ax.text(-0.4, -15, "slope", ha="right", fontsize=9, color=C_POL[1])
    ax.set_xlim(0, 25)
    ax.set_ylim(-22, 200)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.set_yticks([0, 50, 100, 150, 200])
    ax.set_xlabel("total wait $W$ since the request (min)")
    ax.set_ylabel("points per passenger")
    for b in (5, 10, 15, 20):
        ax.axvline(b, color=GRID, lw=0.7, zorder=0)
    ax.legend(loc="upper left", frameon=False)
    save(fig, "f5_phi")


# ---------------------------------------------------------------- F6 worked example
def fig_example():
    fig = plt.figure(figsize=(TEXTW, 3.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[2.2, 1.0], wspace=0.3, hspace=0.85)
    routes = {
        "A": [(0, "start"), (4, "pick r1"), (7, "pick r2"), (12, "drop r1"), (16, "drop r2")],
        "B": [(0, "start"), (5, "pick r2"), (8, "pick r1"), (13, "drop r1"), (15, "drop r2")],
    }
    colours = {"r1": C_INPUT[1], "r2": C_OUT[1]}
    for row, key in enumerate(["A", "B"]):
        ax = fig.add_subplot(gs[row, 0])
        ax.plot([0, 16.5], [0, 0], color=MUTED, lw=1.0)
        for t, lab in routes[key]:
            who = lab.split()[-1]
            c = colours.get(who, MUTED)
            mk = "^" if lab.startswith("pick") else ("v" if lab.startswith("drop") else "s")
            ax.plot(t, 0, mk, color=c, ms=8 if mk != "s" else 5, zorder=3)
            if lab != "start":
                ax.text(t + {"drop r1": 0.25, "drop r2": -0.25}.get(lab, 0), 0.42 if lab.startswith("pick") else -0.75, lab, ha={"drop r1": "right", "drop r2": "left"}.get(lab, "center"), fontsize=8.8, color=c)
        ax.set_xlim(-0.5, 17.8)
        ax.set_ylim(-0.9, 0.95)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_xticks(range(0, 17, 2))
        ax.set_title(f"Route {key}: {'r1' if key == 'A' else 'r2'} first", loc="left", weight="bold")
        if row == 1:
            ax.set_xlabel("minutes from now (both routes 10 km; dwell omitted)")
    ax = fig.add_subplot(gs[:, 1])
    parts = {"A": (52.5, 13.0, 1.0), "B": (67.5, 12.5, 1.0)}
    cols = [C_POL[1], C_POL[0], "#9ca3af"]
    labels = ["waiting", "riding", "driving"]
    for i, k in enumerate(["A", "B"]):
        bottom = 0
        for j, v in enumerate(parts[k]):
            ax.bar(i, v, bottom=bottom, color=cols[j], edgecolor=C_POL[1], lw=0.8, width=0.6,
                   label=labels[j] if i == 0 else None)
            bottom += v
        ax.text(i, bottom + 2, f"{bottom:g}", ha="center", fontsize=10.5, weight="bold")
    ax.set_xticks([0, 1], ["A", "B"])
    ax.set_ylim(0, 105)
    ax.set_ylabel("route score (points)")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    save(fig, "f6_example")


# ---------------------------------------------------------------- F7 lifecycle
def fig_lifecycle():
    fig, ax = plt.subplots(figsize=(TEXTW, 6.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(1.2, 10.9)
    ax.axis("off")
    W, H, FS, TFS = 2.4, 0.74, 8.8, 8.3
    VX, MX, LX, RX, NX = 2.65, 5.0, 7.35, 9.35, 0.65
    MW, RW = 1.6, 1.25
    y1, y2, y3, y4, y5 = 9.15, 7.35, 5.55, 3.75, 1.85
    h2 = H / 2

    box(ax, MX, 10.45, 2.4, 0.6, "request arrives", C_EVID, weight="bold")
    box(ax, VX, y1, W, H, "pending_van\nmay be reassigned", C_INPUT, fs=FS)
    box(ax, VX, y2, W, H, "committed\nvan departed to curb", C_INPUT, fs=FS)
    box(ax, VX, y3, W, H, "van at the curb\npresence test", C_SIM, fs=FS)
    box(ax, VX, y4, W, H, "onboard\nmay share the ride", C_INPUT, fs=FS)
    box(ax, VX, y5, W, 0.6, "van_completed", C_OUT, fs=FS, weight="bold")
    box(ax, NX, y4, RW, 0.6, "noshow_van", C_WARN, fs=7.0, weight="bold")
    box(ax, MX, y2, MW, 0.7, "cancel_\npending_van", C_WARN, fs=TFS, weight="bold", split=False)

    box(ax, LX, y1, W, H, "xfer_hold\nout of van planning", C_POL, fs=FS)
    box(ax, LX, y2, W, H, "lyft_booked\nLyft on its way", C_POL, fs=FS)
    box(ax, LX, y3, W, H, "Lyft at the curb\nsame presence test", C_SIM, fs=FS)
    box(ax, LX, y4, W, H, "direct Lyft ride", C_POL, fs=FS)
    box(ax, LX, y5, W, 0.6, "lyft_completed", C_OUT, fs=FS, weight="bold")
    box(ax, RX, y4, RW, 0.6, "noshow_lyft", C_WARN, fs=7.0, weight="bold")
    box(ax, MX, y3, MW, 0.7, "cancel_after_\ntransfer", C_WARN, fs=TFS, weight="bold", split=False)
    box(ax, RX, 6.45, RW, 0.62, "lyft_failed\n(sensitivity)", C_WARN, fs=7.8, ls="--")

    arrow(ax, (MX - 0.9, 10.15), (VX + 0.4, y1 + h2))
    arrow(ax, (VX, y1 - h2), (VX, y2 + h2), text="van departs", toff=(-0.8, 0))
    arrow(ax, (VX, y2 - h2), (VX, y3 + h2), text="arrives", toff=(-0.6, 0))
    arrow(ax, (VX, y3 - h2), (VX, y4 + h2), text="present:\nboards", toff=(0.6, 0.05))
    arrow(ax, (VX, y4 - h2), (VX, y5 + 0.3), text="drop-off", toff=(-0.62, 0))
    arrow(ax, (VX - 0.8, y3 - h2), (NX + 0.1, y4 + 0.3), text="absent:\n180 s wait", toff=(-0.62, 0.38))
    arrow(ax, (VX + W / 2, y1 - 0.2), (MX - 0.45, y2 + 0.35))
    arrow(ax, (VX + W / 2, y2), (MX - MW / 2, y2))
    ax.text(MX + 0.05, 8.35, "deadline passes", ha="center", va="center", fontsize=8.5, color=MUTED)

    arrow(ax, (VX + W / 2, y1 + 0.12), (LX - W / 2, y1 + 0.12), text="transfer decision", toff=(0, 0.27))
    arrow(ax, (LX, y1 - h2), (LX, y2 + h2), text=r"after lag $\ell$", toff=(0.78, 0))
    arrow(ax, (LX, y2 - h2), (LX, y3 + h2), text=r"after $\lambda_r$", toff=(0.66, 0))
    arrow(ax, (LX, y3 - h2), (LX, y4 + h2), text="present:\nboards", toff=(-0.6, 0.05))
    arrow(ax, (LX, y4 - h2), (LX, y5 + 0.3), text="drop-off", toff=(0.62, 0))
    arrow(ax, (LX + 0.8, y3 - h2), (RX - 0.1, y4 + 0.3), text="absent:\n180 s wait", toff=(0.62, 0.38))
    arrow(ax, (LX - W / 2 + 0.05, y1 - h2), (MX + 0.8, y3 + 0.35))
    arrow(ax, (LX - W / 2, y2 - 0.2), (MX + 0.5, y3 + 0.35))
    ax.text(MX - 0.25, 6.45, "deadline passes\n(lag or Lyft wait)", ha="center", va="center", fontsize=8.5, color=MUTED)
    arrow(ax, (LX + W / 2, y2 - 0.15), (RX, 6.45 + 0.31), colour=MUTED, lw=0.9)

    ax.text(VX, 10.45, "van path", ha="center", fontsize=10, weight="bold", color=C_INPUT[1])
    ax.text(LX + 0.4, 10.45, "transfer path", ha="center", fontsize=10, weight="bold", color=C_POL[1])
    save(fig, "f7_lifecycle")


# ---------------------------------------------------------------- F8 transfer timeline
def fig_transfer():
    fig, ax = plt.subplots(figsize=(TEXTW, 2.1))
    ax.set_xlim(-0.4, 10.4)
    ax.set_ylim(-1.5, 1.25)
    ax.axis("off")
    pts = [(0.0, "request\n$t_r$"), (2.2, "transfer\ndecision $\\tau$"), (3.9, "booking\n$\\tau+\\ell$"),
           (7.2, "Lyft at\nthe curb"), (10.0, "drop-off")]
    ax.plot([0, 10], [0, 0], color=INK, lw=1.2)
    for x, lab in pts:
        ax.plot(x, 0, "o", color=INK, ms=4.5)
        ax.text(x, 0.25, lab, ha="center", va="bottom", fontsize=9)
    spans = [(0.0, 2.2, "waiting with\nthe vans", C_INPUT), (2.2, 3.9, "lag $\\ell$\n(xfer_hold)", C_POL),
             (3.9, 7.2, "Lyft delay $\\lambda_r$", C_POL), (7.2, 8.0, "board\n30 s", C_SIM),
             (8.0, 10.0, "direct ride", C_OUT)]
    for a0, a1, lab, col in spans:
        ax.add_patch(FancyBboxPatch((a0, -0.4), a1 - a0, 0.24, boxstyle="square,pad=0",
                                    fc=col[0], ec=col[1], lw=0.8))
        ax.text((a0 + a1) / 2, -0.5, lab, ha="center", va="top", fontsize=8.8, color=INK)
    ax.annotate("", xy=(7.2, -1.43), xytext=(0.0, -1.43),
                arrowprops=dict(arrowstyle="<->", color=C_OUT[1], lw=1.0))
    ax.text(3.6, -1.38, "patience clock: from the request until a vehicle reaches the curb",
            ha="center", va="bottom", fontsize=8.8, color=C_OUT[1])
    save(fig, "f8_transfer")


if __name__ == "__main__":
    for f in (fig_system, fig_volume, fig_noshow, fig_assumed, fig_phi, fig_example,
              fig_lifecycle, fig_transfer):
        f()
    print("figures written to", OUT)
