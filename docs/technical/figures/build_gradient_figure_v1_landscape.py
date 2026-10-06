"""The gradient picture for the 30 Sep 2026 update to Prof. Kearsley (Rick and Morty themed).

Prof. Kearsley wrote that we "have the gradient pointing in the right direction". This figure
takes the metaphor literally: a loss landscape L(theta) over our design choices, where L is
how hard the answer would be to defend. The paths are not hand-drawn curves; they are true
gradient flows of the L drawn here:
  line 0  the initial scope, a flow on the OLD landscape (with the trip-level valley); abandoned
  trunk   one straight step along -grad L from the restart point, which lands on a low dome
  1, 2, 3 flows from that dome into three different basins (small offsets, different basins)
Rick = Prof. Kearsley (sees the landscape). Four Mortys = Team FourSight (feel the slope).

Colours: line 1/2/3 = #fcc419 / #4dabf7 / #f06595, checked with the dataviz validator on the
#0b1020 surface (CVD and normal-vision separation pass; the yellow sits above the dark
lightness band on purpose, because line 1 is meant to dominate). Lines are also told apart by
number badges, direct labels and dash style.

Run: .venv/bin/python docs/technical/figures/build_gradient_figure.py
Superseded on 1 Oct 2026 by build_gradient_figure.py (portrait, no show references). Kept for history;
its outputs were moved to output/email/2026-09-30_kearsley/superseded/.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Ellipse, Circle, Polygon, FancyBboxPatch
from matplotlib import patheffects as pe

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/email/2026-09-30_kearsley/superseded"

# ------------------------------------------------------------------ palette and type
BG = "#0b1020"; INK = "#0b1020"; TXT = "#f1f3f5"; TXT2 = "#b9c4cf"; TXT3 = "#8391a2"
L1, L2, L3, L0 = "#fcc419", "#4dabf7", "#f06595", "#98a2b3"
PORTAL = "#97ce4c"; PORTAL_HI = "#e4ff9a"; PORTAL_LO = "#2f8f3a"
SKIN = "#f6d7b8"; MORTY_HAIR = "#6b3f1d"; MORTY_SHIRT = "#f7e04b"
RICK_HAIR = "#b9e4f2"; RICK_COAT = "#f4f6f8"; RICK_SHIRT = "#8ecde6"
HAND = "Chalkboard SE"; SANS = "Avenir Next"
LAND = LinearSegmentedColormap.from_list(
    "rm_land", ["#c9f779", "#7fd96b", "#2f9e72", "#1a5f63", "#173a55", "#141f40", "#0d1128"])

# ------------------------------------------------------------------ the landscape
W, H = 16.0, 9.0
WELLS = {                       # (cx, cy, depth, sx, sy)
    "W1": (12.9, 2.0, 1.00, 1.9, 1.4),   # line 1: simulation + dispatch
    "W2": (11.7, 6.9, 0.72, 1.3, 0.85),  # line 2: regimes + the calendar
    "W3": (3.7, 1.75, 1.25, 1.9, 1.2),   # line 3: under the fog
}
HILLS = {
    "NW": (1.6, 8.7, 1.15, 3.0, 2.3),    # the high ground where the proposal started
    "E": (14.9, 4.6, 0.45, 1.9, 0.75),   # a ridge that splits the two eastern basins
}
DOME = [8.4, 4.35, 0.20, 0.85, 0.8]      # a low dome at the fork: every direction is downhill
GHOST = (4.1, 5.2, 0.80, 1.15, 0.95)     # the valley the OLD landscape promised (trip-level data)


def g(x, y, c):
    cx, cy, a, sx, sy = c
    return a * np.exp(-((x - cx) ** 2 / (2 * sx ** 2) + (y - cy) ** 2 / (2 * sy ** 2)))


def L(x, y, old=False):
    z = 1.0 + g(x, y, DOME)
    for c in HILLS.values():
        z = z + g(x, y, c)
    for c in WELLS.values():
        z = z - g(x, y, c)
    z = z + 0.022 * np.sin(1.3 * x + 0.4) * np.cos(1.1 * y)   # a little texture
    if old:
        z = z - g(x, y, GHOST)
    return z


def grad(p, old=False, h=1e-5):
    x, y = p
    return np.array([(L(x + h, y, old) - L(x - h, y, old)) / (2 * h),
                     (L(x, y + h, old) - L(x, y - h, old)) / (2 * h)])


def flow(p0, old=False, eta=0.04, n=6000, tol=1.5e-3):
    P = [np.array(p0, float)]
    for _ in range(n):
        gr = grad(P[-1], old)
        if np.hypot(*gr) < tol:
            break
        P.append(P[-1] - eta * gr)
    return np.array(P)


# The restart point R and the one step we took: put the dome exactly where a step along
# -grad L(R) lands, and iterate because the dome itself tilts the gradient at R a little.
R = np.array([6.05, 6.35])
for _ in range(6):
    d = -grad(R); d /= np.linalg.norm(d)
    s = float(np.dot(np.array(DOME[:2]) - R, d))
    DOME[0], DOME[1] = R + s * d
F = np.array(DOME[:2])
assert L(*F) < L(*R), "the step must go downhill"
d_check = -grad(R) / np.linalg.norm(grad(R))
STEP_ANGLE_ERR = np.degrees(np.arccos(np.clip(np.dot(d_check, (F - R) / np.linalg.norm(F - R)), -1, 1)))
assert STEP_ANGLE_ERR < 1.0, STEP_ANGLE_ERR

def arclen_index(P, frac):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    return int(np.searchsorted(s, frac * s[-1]))


S = np.array([2.75, 6.95])                 # 15 Sep: the proposal
LINE0 = flow(S, old=True)
LINE0 = LINE0[: arclen_index(LINE0, 0.70)]  # the valley vanished before we reached it

START = {1: -40, 2: 95, 3: 172}            # initial directions off the dome (degrees)
TARGET = {1: "W1", 2: "W2", 3: "W3"}
LINES = {}
for k, ang in START.items():
    a = np.deg2rad(ang)
    fl = flow(F + 0.10 * np.array([np.cos(a), np.sin(a)]))
    end = min(WELLS, key=lambda w: np.hypot(*(fl[-1] - np.array(WELLS[w][:2]))))
    assert end == TARGET[k], (k, end)
    LINES[k] = fl


def resample(P, n):
    """n points evenly spaced in arc length (for the step dots)."""
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    t = np.linspace(0, s[-1], n)
    return np.c_[np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])]


# ------------------------------------------------------------------ drawing helpers
def halo(w=3.2, c=BG):
    return [pe.withStroke(linewidth=w, foreground=c)]


def label(ax, x, y, s, size=12, color=TXT, family=SANS, weight="normal", ha="left", va="center",
          box=True, z=30, style="normal", pad=0.35, alpha=0.78):
    kw = dict(fontsize=size, color=color, family=family, weight=weight, ha=ha, va=va, zorder=z,
              style=style, linespacing=1.25)
    if box:
        kw["bbox"] = dict(boxstyle=f"round,pad={pad}", fc=BG, ec="none", alpha=alpha)
    return ax.text(x, y, s, **kw)


def badge(ax, x, y, n, color, z=32, size=13):
    ax.text(x, y, str(n), fontsize=size, family=SANS, weight="bold", color=BG, ha="center", va="center",
            zorder=z, bbox=dict(boxstyle="circle,pad=0.28", fc=color, ec=BG, lw=1.5))


def bubble(ax, x, y, s, tail_to, size=12.5, z=40, width_pad=0.5):
    ax.annotate(s, xy=tail_to, xytext=(x, y), fontsize=size, family=HAND, color=INK, ha="center", va="center",
                zorder=z, linespacing=1.2,
                bbox=dict(boxstyle=f"round,pad={width_pad}", fc="white", ec=INK, lw=1.6),
                arrowprops=dict(arrowstyle="wedge,tail_width=0.55,shrink_factor=0.5", fc="white", ec=INK,
                                lw=1.4, shrinkA=0, shrinkB=3))


def portal(ax, x, y, r=0.42, z=12, squash=0.82):
    for k, a in zip(np.linspace(2.0, 1.05, 7), np.linspace(0.04, 0.22, 7)):
        ax.add_patch(Ellipse((x, y), 2 * r * k, 2 * r * k * squash, fc=PORTAL, ec="none", alpha=a, zorder=z))
    cols = LinearSegmentedColormap.from_list("p", [PORTAL_LO, PORTAL, PORTAL_HI])(np.linspace(0, 1, 9))
    for k, c in zip(np.linspace(1.0, 0.12, 9), cols):
        ax.add_patch(Ellipse((x, y), 2 * r * k, 2 * r * k * squash, fc=c, ec="none", zorder=z + 1))
    t = np.linspace(0, 5 * np.pi, 300); rr = r * 0.92 * (1 - t / (5.4 * np.pi))
    ax.plot(x + rr * np.cos(t), y + squash * rr * np.sin(t), color="#f7ffe0", lw=1.3, alpha=0.75, zorder=z + 2)


def morty(ax, x, y, s=0.3, z=50, look=(0.0, 0.0)):
    """A small Morty-ish head: brown mop, big round eyes, tiny pupils, yellow shirt."""
    ax.add_patch(Ellipse((x, y - 0.98 * s), 1.55 * s, 0.85 * s, fc=MORTY_SHIRT, ec=INK, lw=1.1, zorder=z))
    ax.add_patch(Ellipse((x, y), 1.22 * s, 1.30 * s, fc=SKIN, ec=INK, lw=1.1, zorder=z + 1))
    th = np.linspace(np.deg2rad(8), np.deg2rad(172), 30)
    rim = [(x + 0.66 * s * np.cos(t), y + 0.06 * s + 0.72 * s * np.sin(t)) for t in th]
    fringe = [(x - 0.60 * s, y + 0.20 * s), (x - 0.40 * s, y + 0.30 * s), (x - 0.22 * s, y + 0.22 * s),
              (x - 0.02 * s, y + 0.32 * s), (x + 0.20 * s, y + 0.22 * s), (x + 0.42 * s, y + 0.30 * s),
              (x + 0.62 * s, y + 0.18 * s)]
    ax.add_patch(Polygon(rim + fringe[::-1][::-1][::-1], closed=True, fc=MORTY_HAIR, ec=INK, lw=1.1, zorder=z + 2))
    for dx in (-0.22, 0.22):
        ax.add_patch(Circle((x + dx * s, y - 0.06 * s), 0.21 * s, fc="white", ec=INK, lw=1.0, zorder=z + 3))
        ax.add_patch(Circle((x + dx * s + look[0] * s, y - 0.06 * s + look[1] * s), 0.045 * s, fc=INK, zorder=z + 4))
    mx = np.linspace(-0.2, 0.2, 20)
    ax.plot(x + mx * s, y - 0.42 * s + 0.03 * s * np.sin(mx * 40), color=INK, lw=1.1, zorder=z + 4)


def rick(ax, x, y, s=0.46, z=60):
    """A small Rick-ish figure: spiky pale-blue hair, long face, unibrow, lab coat."""
    coat = [(x - 0.95 * s, y - 1.75 * s), (x + 0.95 * s, y - 1.75 * s), (x + 0.62 * s, y - 0.62 * s),
            (x - 0.62 * s, y - 0.62 * s)]
    ax.add_patch(Polygon(coat, closed=True, fc=RICK_COAT, ec=INK, lw=1.2, zorder=z))
    ax.add_patch(Polygon([(x - 0.28 * s, y - 0.66 * s), (x + 0.28 * s, y - 0.66 * s), (x, y - 1.35 * s)],
                         closed=True, fc=RICK_SHIRT, ec=INK, lw=1.0, zorder=z + 1))
    spikes = []
    for i, t in enumerate(np.linspace(np.deg2rad(-25), np.deg2rad(205), 15)):
        r = (1.05 if i % 2 == 0 else 0.62) * s
        spikes.append((x + r * np.cos(t), y + 0.12 * s + r * 1.05 * np.sin(t)))
    ax.add_patch(Polygon(spikes, closed=True, fc=RICK_HAIR, ec=INK, lw=1.1, zorder=z + 2))
    ax.add_patch(Ellipse((x, y - 0.05 * s), 1.0 * s, 1.32 * s, fc=SKIN, ec=INK, lw=1.1, zorder=z + 3))
    ax.plot([x - 0.36 * s, x - 0.1 * s, x + 0.1 * s, x + 0.36 * s],
            [y + 0.2 * s, y + 0.27 * s, y + 0.27 * s, y + 0.2 * s], color="#9cc9da", lw=3.2,
            solid_capstyle="round", zorder=z + 5)
    for dx in (-0.2, 0.2):
        ax.add_patch(Circle((x + dx * s, y + 0.03 * s), 0.17 * s, fc="white", ec=INK, lw=0.9, zorder=z + 4))
        ax.add_patch(Circle((x + dx * s - 0.05 * s, y - 0.02 * s), 0.045 * s, fc=INK, zorder=z + 5))
    ax.plot([x - 0.22 * s, x + 0.2 * s], [y - 0.42 * s, y - 0.38 * s], color=INK, lw=1.2, zorder=z + 5)
    ax.plot([x + 0.12 * s, x + 0.14 * s], [y - 0.4 * s, y - 0.56 * s], color="#bfe7a8", lw=1.6,
            solid_capstyle="round", zorder=z + 5)   # the drool, of course


def fog(ax, cx, cy, rx, ry, z=20):
    xs = np.linspace(cx - 1.6 * rx, cx + 1.6 * rx, 360); ys = np.linspace(cy - 1.8 * ry, cy + 1.8 * ry, 200)
    X, Y = np.meshgrid(xs, ys)
    r2 = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
    rng = np.random.default_rng(7)
    noise = rng.normal(size=(40, 72))
    from scipy.ndimage import zoom, gaussian_filter
    noise = gaussian_filter(zoom(noise, (200 / 40, 360 / 72), order=1), 6)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    alpha = np.clip(1.25 - r2, 0, 1) ** 0.8 * (0.62 + 0.38 * noise) * 0.93
    rgba = np.zeros(X.shape + (4,)); rgba[..., :3] = matplotlib.colors.to_rgb("#c9d3de"); rgba[..., 3] = alpha
    ax.imshow(rgba, extent=(xs[0], xs[-1], ys[0], ys[-1]), origin="lower", zorder=z, interpolation="bilinear")


# ------------------------------------------------------------------ the figure
def along(P, frac, off=(0.0, 0.0)):
    x, y = P[arclen_index(P, frac)]
    return x + off[0], y + off[1]


def build():
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
    ax.set_facecolor(BG)

    # ---- the landscape, a few stars on the high ground, the ghost of the old valley, the fog
    x = np.linspace(0, W, 640); y = np.linspace(0, H, 360); X, Y = np.meshgrid(x, y); Z = L(X, Y)
    lev = np.linspace(Z.min(), Z.max(), 26)
    ax.contourf(X, Y, Z, lev, cmap=LAND, zorder=1)
    ax.contour(X, Y, Z, lev, colors="#c9f7c0", linewidths=0.55, alpha=0.20, zorder=2)
    rng = np.random.default_rng(11)
    sx, sy = rng.uniform(0, W, 420), rng.uniform(0, H, 420)
    keep = L(sx, sy) > 1.12
    ax.scatter(sx[keep], sy[keep], s=rng.uniform(0.3, 3.5, keep.sum()), c="white", alpha=0.55, lw=0, zorder=3)
    ax.contour(X, Y, L(X, Y, old=True) - Z, [-0.55, -0.3, -0.1], colors=L0, linewidths=1.0,
               linestyles="--", alpha=0.42, zorder=4)
    fog(ax, 3.35, 1.75, 2.75, 1.25)

    # ---- line 0: the initial scope, a flow on the old landscape; abandoned
    ax.plot(*LINE0.T, color=L0, lw=2.4, ls=(0, (6, 4)), zorder=15)
    ax.plot(*S, marker="o", ms=11, mfc=L0, mec=BG, mew=2, zorder=16)
    label(ax, S[0] - 0.28, S[1] + 0.02, "15 Sep · proposal", size=12, color=TXT2, ha="right")
    bx, by = along(LINE0, 0.42)
    badge(ax, bx - 0.36, by, 0, L0)
    label(ax, bx - 0.66, by, "initial scope:\nreplay April\ntrip by trip", size=11.5, color=TXT2, ha="right")
    xe, ye = LINE0[-1]
    portal(ax, xe, ye, r=0.26, z=13)
    ax.plot(xe, ye, marker="X", ms=17, mfc="#ff6b6b", mec=BG, mew=1.5, zorder=17)
    label(ax, xe + 0.42, ye - 0.42, "28 Sep · the valley vanished:\nthe trip-level data never came", size=11.5,
          color="#ffc9c9", ha="left", va="top")
    bubble(ax, xe - 1.95, ye - 0.52, "Wubba lubba\ndub dub!*", tail_to=(xe - 0.22, ye - 0.08), size=12.5)

    # ---- the portal restart, from the dead end to the restart point R
    portal(ax, *R, r=0.40, z=13)
    t = np.linspace(0, 1, 60)
    arc = np.c_[xe + (R[0] - xe) * t, ye + (R[1] - ye) * t + 0.9 * np.sin(np.pi * t)]
    ax.plot(*arc.T, color=PORTAL, lw=1.8, ls=(0, (1, 2.5)), zorder=14)
    apex = arc[len(arc) // 2]
    label(ax, apex[0], apex[1] + 0.28, "portal restart", size=12, color=PORTAL_HI, ha="center", family=HAND)
    label(ax, R[0] + 0.45, R[1] + 0.55, "29 Sep · plan v2:\nrestart on the new landscape", size=11.5,
          color=TXT2, ha="left")

    # ---- the trunk: one step along -grad L (stages 1-2, done)
    ax.annotate("", xy=F, xytext=R, zorder=22,
                arrowprops=dict(arrowstyle="-|>,head_length=0.9,head_width=0.45", color="white", lw=3.2,
                                shrinkA=14, shrinkB=10))
    u = (F - R) / np.linalg.norm(F - R); n = np.array([-u[1], u[0]])
    if n[1] < 0:
        n = -n
    ang = np.degrees(np.arctan2(u[1], u[0]))
    p1 = R + 0.52 * (F - R) + 0.30 * n; p2 = R + 0.46 * (F - R) - 0.30 * n
    ax.text(*p1, "one step along $-\\nabla L$", rotation=ang, rotation_mode="anchor", fontsize=12.5,
            family=SANS, weight="bold", color=TXT, ha="center", va="center", zorder=31, path_effects=halo())
    ax.text(*p2, "digitized · mined · G1 passed", rotation=ang, rotation_mode="anchor", fontsize=11,
            family=SANS, color=TXT2, ha="center", va="center", zorder=31, path_effects=halo())

    # ---- lines 1, 2, 3: the future, as dotted flows with evenly spaced step dots
    style = {1: (L1, (0, (1.2, 2.2)), 3.2), 2: (L2, (0, (5, 2.2, 1.2, 2.2)), 2.8), 3: (L3, (0, (1, 2.6)), 2.6)}
    for k, P in LINES.items():
        col, ls, lw = style[k]
        Q = P if k != 3 else P[: arclen_index(P, 0.62)]      # line 3 fades into the fog
        ax.plot(*Q.T, color=col, lw=lw, ls=ls, zorder=24, dash_capstyle="round")
        dots = resample(Q, 11 if k != 3 else 6)[1:]
        ax.scatter(*dots.T, s=34, c=col, edgecolors=BG, linewidths=1.6, zorder=25)
    P1, P2, P3 = LINES[1], LINES[2], LINES[3]
    for f, sz in [(0.70, 18), (0.81, 21), (0.92, 25)]:
        ax.text(*along(P3, f), "?", fontsize=sz, family=HAND, weight="bold", color=L3, ha="center", va="center",
                zorder=26, path_effects=halo(3, "#c9d3de"))
    portal(ax, *P1[-1], r=0.46, z=18)
    portal(ax, *P2[-1], r=0.34, z=18)

    # line 1: simulation + dispatch
    badge(ax, 8.72, 2.02, 1, L1)
    label(ax, 9.02, 2.02, "Simulation + dispatch\n(our project)", size=13.5, color=L1, weight="bold", va="center")
    label(ax, 9.02, 1.42, "synthetic nights consistent\nwith the aggregates; five\ndispatchers on identical nights",
          size=11, color=TXT2, va="top")
    e1 = P1[-1]
    label(ax, e1[0] + 0.72, e1[1] + 0.02, "the value ladder\nN · A · B · C · H\npooling · waiting ·\ncoordination · information",
          size=11.5, color=TXT, ha="left", va="center")

    # line 2: regimes + the calendar
    sx2, sy2 = along(P2, 0.45)
    ax.plot(sx2, sy2, marker="*", ms=19, mfc=L2, mec=BG, mew=1.3, zorder=27)
    label(ax, sx2 + 0.3, sy2 - 0.12, "Apr 17: the system slowed\n(opening night of the 150th\nAll-Alumni Weekend)", size=10.5,
          color=TXT2, ha="left", va="top")
    badge(ax, 9.05, 7.32, 2, L2)
    label(ax, 9.35, 7.32, "Regimes + the calendar\n(side-branch)", size=13.5, color=L2, weight="bold")
    e2 = P2[-1]
    label(ax, e2[0] + 0.55, e2[1] + 0.06, "event-aware forecast of\nload and slowdowns,\nscored each new month", size=11, color=TXT,
          ha="left")

    # line 3: the unseen
    badge(ax, 4.78, 3.66, 3, L3)
    label(ax, 5.08, 3.66, "What's in plain sight\nthat we can't see", size=13.5, color=L3, weight="bold")
    ax.text(3.2, 1.2, "unsampled: a saddle, or the global minimum?\nOnly Rick can see this far.", fontsize=12,
            family=HAND, color="#1f2937", ha="center", va="center", zorder=28, linespacing=1.3)

    # ---- the fork: you are here (four Mortys = FourSight)
    ax.plot(*F, marker="o", ms=13, mfc="white", mec=BG, mew=2.2, zorder=34)
    mx = F[0] + np.array([0.72, 1.19, 1.66, 2.13]); my = F[1] + 0.08
    for xi, lk in zip(mx, [(-0.05, 0.02), (0.03, 0.04), (0.05, 0.0), (0.02, 0.05)]):
        morty(ax, xi, my, s=0.24, look=lk)
    label(ax, mx[0] - 0.2, my + 0.5, "YOU ARE HERE · 30 Sep", size=12.5, color=TXT, weight="bold", ha="left",
          va="bottom", alpha=0.85)
    label(ax, mx[0] + 0.25, my - 0.5, "4 Mortys = Team FourSight", size=11, color=TXT2, ha="left", va="top")
    bubble(ax, mx[-1] + 1.75, my + 0.02, "Aw geez, Rick...\nwhich valley?", tail_to=(mx[-1] + 0.2, my + 0.02),
           size=12.5)

    # ---- Rick, up where the whole landscape is visible
    rx, ry = 14.95, 7.72
    portal(ax, rx + 0.05, ry - 0.05, r=0.78, z=55, squash=0.9)
    rick(ax, rx, ry + 0.08, s=0.42)
    label(ax, rx, ry - 1.2, "Rick = Prof. A. J. Kearsley\nsees the landscape", size=11, color=TXT2, ha="center",
          va="top")
    bubble(ax, rx - 2.3, ry + 0.8, "\"...the gradient pointing in\nthe right direction.\" *burp*",
           tail_to=(rx - 0.55, ry + 0.25), size=12)

    # ---- title block
    ax.text(0.42, 8.55, "Gradient descent, Morty!", fontsize=34, family=HAND, weight="bold", color=TXT, ha="left",
            va="center", zorder=40, path_effects=halo(5))
    ax.text(0.45, 7.98, "Where “the gradient pointing in the right direction” has taken Team FourSight  "
            "·  30 Sep 2026", fontsize=14, family=SANS, color=TXT2, ha="left", va="center", zorder=40,
            path_effects=halo(4))
    ax.text(0.45, 7.56, "Rick sees the landscape. The Mortys feel the slope.", fontsize=13, family=SANS,
            style="italic", color=PORTAL_HI, ha="left", va="center", zorder=40, path_effects=halo(4))

    # ---- the L(theta) scale, bottom centre
    ax.add_patch(FancyBboxPatch((13.02, 0.41), 2.66, 0.55, boxstyle="round,pad=0.03", fc=BG, ec="none",
                                alpha=0.78, zorder=35))
    cb = fig.add_axes([0.822, 0.066, 0.15, 0.014])
    cb.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=LAND, extent=(0, 1, 0, 1))
    cb.set_xticks([]); cb.set_yticks([])
    for sp in cb.spines.values():
        sp.set_edgecolor(TXT3)
    fig.text(0.822, 0.089, "L(θ): how hard the answer is to defend", fontsize=10.5, family=SANS, color=TXT2)
    fig.text(0.822, 0.061, "defensible", fontsize=9.5, family=SANS, color=TXT3, va="top")
    fig.text(0.972, 0.061, "Cronenberg territory", fontsize=9.5, family=SANS, color=TXT3, va="top", ha="right")

    # ---- footnotes
    fig.text(0.012, 0.016, "*Birdperson's translation: “I am in great pain, please help me.” "
             "Said by every data scientist whose data got yanked.", fontsize=9, family=SANS, color=TXT2, va="bottom",
             bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec="none", alpha=0.72))
    fig.text(0.988, 0.016, "θ: our design choices. Every path is a true gradient flow of the L drawn here. "
             "No Mortys were harmed.", fontsize=9, family=SANS, color=TXT2, va="bottom", ha="right",
             bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec="none", alpha=0.72))
    return fig


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig = build()
    png = OUT / "foursight_gradient_descent.png"; pdf = OUT / "foursight_gradient_descent.pdf"
    fig.savefig(png, dpi=150, facecolor=BG)
    fig.savefig(pdf, facecolor=BG)
    print(png, pdf, f"step angle error {STEP_ANGLE_ERR:.2f} deg", f"L(R)={L(*R):.3f} L(F)={L(*F):.3f}", sep="\n")
