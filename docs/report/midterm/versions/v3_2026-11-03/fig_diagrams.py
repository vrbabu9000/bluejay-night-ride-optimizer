"""Report-size versions of the three methodology diagrams (system, request lifecycle, transfer timeline).

The originals live in docs/technical/methodology_pdf/make_figures.py (a separate, versioned PDF) and are
not touched. Here each drawing is redone at its final printed size so the fonts follow fig_style.FS.
Content, colours and meaning are unchanged; wording changes are listed in the function docstrings.

Coordinates: one axes fills the figure and one data unit is one inch, so every gap and pad below
is a printed distance (0.03 in is about 2 pt).

Run:  .venv/bin/python docs/report/midterm/fig_diagrams.py
Writes figures/d_system.pdf, figures/d_lifecycle.pdf, figures/d_transfer.pdf.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "docs/technical/methodology_pdf"))
sys.path.insert(0, str(HERE))
import make_figures as mf  # noqa: E402,F401  (palette; sets its own rcParams, overridden below)
from make_figures import C_EVID, C_INPUT, C_OUT, C_POL, C_SIM, C_WARN, INK, MUTED  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

plt.switch_backend("agg")  # make_figures selects the pdf backend, which has no renderer for fig_style.check

from fig_style import FS, TEXTW, apply_style, save  # noqa: E402

apply_style()

LW = 0.9          # box borders and arrows, pt
HEAD = 7          # arrowhead mutation scale (same on every arrow)
LS = 1.2          # line spacing factor
GAP = 0.04        # inches between an arrow and its label (about 3 pt)
PAD = 0.03        # fig_style.save pads the saved PDF by this on every side
W_FULL = TEXTW - 2 * PAD   # canvas width so the saved full-width PDF is exactly TEXTW


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def lh(fs):
    """Line height in inches for a font size in pt."""
    return fs * LS / 72


def rbox(ax, cx, cy, w, h, colours, title=None, body=None, bold_body=False, ls="-", title_fs=None):
    """Rounded box with an optional bold title line and regular body lines, centred as a block."""
    face, edge = colours
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0,rounding_size=0.05",
                                fc=face, ec=edge, lw=LW, ls=ls, zorder=2))
    tfs = title_fs or FS["title"]
    lines = []
    if title:
        lines += [(t, tfs, "bold") for t in title.split("\n")]
    if body:
        lines += [(t, FS["body"], "bold" if bold_body else "normal") for t in body.split("\n")]
    total = sum(lh(f) for _, f, _ in lines)
    y = cy + total / 2
    for text, f, wgt in lines:
        y -= lh(f) / 2
        ax.text(cx, y, text, ha="center", va="center", fontsize=f, weight=wgt, color=INK, zorder=3)
        y -= lh(f) / 2


def arr(ax, p0, p1, colour=INK, lw=LW):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=HEAD, color=colour, lw=lw,
                                 shrinkA=0, shrinkB=0, zorder=1))


def note(ax, x, y, text, ha="center", va="center", colour=MUTED, fs=None):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs or FS["small"], color=colour, zorder=3,
            linespacing=LS)


# ---------------------------------------------------------------- Figure 1: system
def fig_system():
    """Wording change: arrow label "booking" -> "Lyft order"; Lyft service box line
    "booking, delay, ride" -> "ordering, delay, ride"."""
    W, H = W_FULL, 2.85
    fig, ax = canvas(W, H)
    # rows (centre y, height)
    yT, hT = 2.55, 0.48
    yM, hM = 1.50, 0.74
    yB, hB = 0.33, 0.60
    topM, botM, topB = yM + hM / 2, yM - hM / 2, yB + hB / 2

    rbox(ax, 1.95, yT, 3.1, hT, C_INPUT, "Scenario inputs (frozen)", "requests, vans on duty, hidden rider traits")
    rbox(ax, 5.15, yT, 1.75, hT, C_INPUT, "Travel table $t_0$", "(local OSRM, hashed)")
    rbox(ax, 2.45, yM, 3.7, hM, C_SIM, "Event simulator (the referee)",
         "clock, event order, van movement;\napplies hidden traits only when events happen")
    rbox(ax, 5.75, yM, 1.75, hM, C_OUT, "Evaluation", "from the event log:\nrider outcomes,\nLyft counts, van-km")
    rbox(ax, 1.0, yB, 1.9, hB, C_POL, "Van dispatcher", "plans routes, gives ETAs\n(sees no hidden traits)")
    rbox(ax, 3.4, yB, 1.8, hB, C_POL, "Lyft transfer rule", "reads the board\n(sees no hidden traits)")
    rbox(ax, 5.75, yB, 1.75, hB, C_SIM, "Lyft service", "ordering, delay, ride")

    # inputs -> simulator, table -> simulator, simulator -> evaluation
    arr(ax, (1.95, yT - hT / 2), (1.95, topM))
    arr(ax, (4.75, yT - hT / 2), (4.0, topM))
    arr(ax, (4.3, yM), (4.875, yM))
    # dispatcher <-> simulator
    arr(ax, (0.80, botM), (0.80, topB))
    note(ax, 0.80 - GAP, (botM + topB) / 2, "requests\nso far", ha="right")
    arr(ax, (1.20, topB), (1.20, botM))
    note(ax, 1.20 + GAP, (botM + topB) / 2, "routes,\nETAs", ha="left")
    # transfer rule <-> simulator
    arr(ax, (3.15, botM), (3.15, topB))
    note(ax, 3.15 - GAP, (botM + topB) / 2, "open requests\n+ ETAs", ha="right")
    arr(ax, (3.55, topB), (3.55, botM))
    note(ax, 3.55 + GAP, (botM + topB) / 2, "transfer\ndecisions", ha="left")
    # simulator -> Lyft service (order), Lyft service -> evaluation
    p0, p1 = (4.12, botM), (5.05, topB)
    arr(ax, p0, p1)
    note(ax, 4.76, (botM + topB) / 2 + 0.03, "Lyft order", ha="left", va="center")
    arr(ax, (6.15, topB), (6.15, botM))
    note(ax, 6.15 + GAP, (botM + topB) / 2, "arrival,\ndrop-off", ha="left")
    save(fig, "d_system")


# ---------------------------------------------------------------- Figure 9: request lifecycle
def fig_lifecycle():
    """No wording changes. lyft_failed (sensitivity) moved from between the Lyft rows to the
    curb row of the right-hand column; same box, same arrow source."""
    W, Hf = W_FULL, 4.25
    fig, ax = canvas(W, Hf)
    BW, BH = 1.45, 0.44            # state boxes
    SW, SH = 0.92, 0.30            # single-line outcome boxes on the sides
    MW, MH = 1.00, 0.44            # cancellation boxes in the middle
    CW, CH = 1.45, 0.30            # completed boxes
    NX, VX, MX, LX, RX = 0.47, 1.85, 3.30, 4.85, 6.22
    y0 = 4.03
    y1, y2, y3, y4, y5 = 3.40, 2.58, 1.76, 0.94, 0.18
    h2 = BH / 2

    rbox(ax, MX, y0, 1.25, 0.28, C_EVID, "request arrives")
    ax.text(VX, y0, "van path", ha="center", va="center", fontsize=FS["title"], weight="bold", color=C_INPUT[1])
    ax.text(LX, y0, "transfer path", ha="center", va="center", fontsize=FS["title"], weight="bold", color=C_POL[1])

    rbox(ax, VX, y1, BW, BH, C_INPUT, body="pending_van\nmay be reassigned")
    rbox(ax, VX, y2, BW, BH, C_INPUT, body="committed\nvan departed to curb")
    rbox(ax, VX, y3, BW, BH, C_SIM, body="van at the curb\npresence test")
    rbox(ax, VX, y4, BW, BH, C_INPUT, body="onboard\nmay share the ride")
    rbox(ax, VX, y5, CW, CH, C_OUT, body="van_completed", bold_body=True)
    rbox(ax, NX, y4, SW, SH, C_WARN, body="noshow_van", bold_body=True)
    rbox(ax, MX, y2, MW, MH, C_WARN, body="cancel_\npending_van", bold_body=True)

    rbox(ax, LX, y1, BW, BH, C_POL, body="xfer_hold\nout of van planning")
    rbox(ax, LX, y2, BW, BH, C_POL, body="lyft_booked\nLyft on its way")
    rbox(ax, LX, y3, BW, BH, C_SIM, body="Lyft at the curb\nsame presence test")
    rbox(ax, LX, y4, BW, BH, C_POL, body="direct Lyft ride")
    rbox(ax, LX, y5, CW, CH, C_OUT, body="lyft_completed", bold_body=True)
    rbox(ax, RX, y4, SW, SH, C_WARN, body="noshow_lyft", bold_body=True)
    rbox(ax, MX, y3, MW, MH, C_WARN, body="cancel_after_\ntransfer", bold_body=True)
    rbox(ax, RX, y3, SW, BH, C_WARN, body="lyft_failed\n(sensitivity)", ls="--")

    mid = lambda a, b: (a + b) / 2  # noqa: E731
    g12, g23, g34 = mid(y1, y2), mid(y2, y3), mid(y3, y4)
    g45 = mid(y4 - h2, y5 + CH / 2)

    # entry
    arr(ax, (MX - 0.63, y0 - 0.06), (VX + 0.45, y1 + h2))
    # van path
    arr(ax, (VX, y1 - h2), (VX, y2 + h2)); note(ax, VX - GAP, g12, "van departs", ha="right")
    arr(ax, (VX, y2 - h2), (VX, y3 + h2)); note(ax, VX - GAP, g23, "arrives", ha="right")
    arr(ax, (VX, y3 - h2), (VX, y4 + h2)); note(ax, VX + GAP, g34, "present:\nboards", ha="left")
    arr(ax, (VX, y4 - h2), (VX, y5 + CH / 2)); note(ax, VX - GAP, g45, "drop-off", ha="right")
    arr(ax, (VX - 0.45, y3 - h2), (NX + 0.15, y4 + SH / 2))
    note(ax, 0.12, g34 + 0.02, "absent:\n180 s wait", ha="left")
    # van-side cancellations
    a0, a1 = (VX + BW / 2, y1 - 0.12), (MX - 0.30, y2 + MH / 2)
    arr(ax, a0, a1)
    xg = a0[0] + (a1[0] - a0[0]) * (a0[1] - g12) / (a0[1] - a1[1])   # arrow x at the label height
    note(ax, xg + 0.08, g12, "deadline passes", ha="left")
    arr(ax, (VX + BW / 2, y2), (MX - MW / 2, y2))
    # transfer path
    arr(ax, (VX + BW / 2, y1 + 0.08), (LX - BW / 2, y1 + 0.08))
    note(ax, MX, y1 + 0.08 + GAP, "transfer decision", va="bottom")
    arr(ax, (LX, y1 - h2), (LX, y2 + h2)); note(ax, LX + GAP, g12, r"after lag $\ell$", ha="left")
    arr(ax, (LX, y2 - h2), (LX, y3 + h2)); note(ax, LX + GAP, g23, r"after $\lambda_r$", ha="left")
    arr(ax, (LX, y3 - h2), (LX, y4 + h2)); note(ax, LX - GAP, g34, "present:\nboards", ha="right")
    arr(ax, (LX, y4 - h2), (LX, y5 + CH / 2)); note(ax, LX + GAP, g45, "drop-off", ha="left")
    arr(ax, (LX + 0.45, y3 - h2), (RX - 0.15, y4 + SH / 2))
    note(ax, W - 0.12, g34 + 0.02, "absent:\n180 s wait", ha="right")
    # transfer-side cancellations and failure
    arr(ax, (LX - 0.50, y1 - h2), (MX + 0.38, y3 + MH / 2))
    b0, b1 = (LX - BW / 2, y2 - 0.12), (MX + 0.18, y3 + MH / 2)
    arr(ax, b0, b1)
    yl = g23 - lh(FS["small"])   # bottom of the two-line label, where the arrow comes closest
    xg = b0[0] + (b1[0] - b0[0]) * (b0[1] - yl) / (b0[1] - b1[1])
    note(ax, xg - 0.12, g23, "deadline passes\n(lag or Lyft wait)", ha="right")
    arr(ax, (LX + BW / 2, y2), (RX, y3 + h2), colour=MUTED)
    save(fig, "d_lifecycle")


# ---------------------------------------------------------------- Figure 12: transferred-rider timeline
def fig_transfer():
    """No wording changes ("booking" kept: the caption refers to it)."""
    W, H = W_FULL, 1.42
    fig, ax = canvas(W, H)
    x0, x1 = 0.35, 6.40
    sx = lambda u: x0 + (x1 - x0) * u / 10.0  # noqa: E731  (original 0-10 layout units)
    yl = 0.98          # time line
    yb0, yb1 = 0.62, 0.78   # span bars
    pts = [(0.0, "request\n$t_r$"), (2.2, "transfer\ndecision $\\tau$"), (3.9, "booking\n$\\tau+\\ell$"),
           (7.2, "Lyft at\nthe curb"), (10.0, "drop-off")]
    ax.plot([sx(0), sx(10)], [yl, yl], color=INK, lw=LW)
    for u, lab in pts:
        ax.plot(sx(u), yl, "o", color=INK, ms=3.5)
        note(ax, sx(u), yl + 0.07, lab, va="bottom", colour=INK, fs=FS["body"])
    spans = [(0.0, 2.2, "waiting with\nthe vans", C_INPUT), (2.2, 3.9, "lag $\\ell$\n(xfer_hold)", C_POL),
             (3.9, 7.2, "Lyft delay $\\lambda_r$", C_POL), (7.2, 8.0, "board\n30 s", C_SIM),
             (8.0, 10.0, "direct ride", C_OUT)]
    for a0, a1, lab, col in spans:
        ax.add_patch(FancyBboxPatch((sx(a0), yb0), sx(a1) - sx(a0), yb1 - yb0, boxstyle="square,pad=0",
                                    fc=col[0], ec=col[1], lw=LW * 0.8))
        note(ax, (sx(a0) + sx(a1)) / 2, yb0 - 0.05, lab, va="top", colour=INK, fs=FS["body"])
    ya = 0.05
    ax.annotate("", xy=(sx(7.2), ya), xytext=(sx(0.0), ya),
                arrowprops=dict(arrowstyle="<|-|>", mutation_scale=HEAD, color=C_OUT[1], lw=LW,
                                shrinkA=0, shrinkB=0))
    note(ax, (sx(0.0) + sx(7.2)) / 2, ya + GAP, "patience clock: from the request until a vehicle reaches the curb",
         va="bottom", colour=C_OUT[1], fs=FS["body"])
    save(fig, "d_transfer")


if __name__ == "__main__":
    fig_system()
    fig_lifecycle()
    fig_transfer()
