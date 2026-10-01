"""The three-approaches figure for the update to Prof. Kearsley (portrait, 1 Oct 2026).

Prof. Kearsley wrote that we "have the gradient pointing in the right direction". This
figure draws that literally. Height is defensibility D(theta): how defensible an answer
from a given project design would be. Dark ground is non-defensible; green ground is
defensible. Every path is a true gradient flow of the D drawn here:
  initial scope  an ascent on the OLD landscape (whose peak needed trip-level data), cut
                 off where that data failed to arrive
  the step       one straight step along +grad D from the restart point; it lands on a
                 shallow dip (the fork), from which every direction climbs
  approaches     the fork is a flat point (the gradient vanishes there), so each approach
                 leaves it with one short first step in its own direction and then follows
                 the gradient flow into its own peak (asserted below)
The Blue Jay van (the team) climbs Approach 1; Prof. AJK holds a lantern toward the fog
that hides Approach 3.

Replaces the landscape-format version (build_gradient_figure_v1_landscape.py, 30 Sep).
Colours: approaches 1/2/3 = #fcc419 / #4dabf7 / #f06595, checked with the dataviz palette
validator on the #0b1020 surface (CVD and normal-vision separation pass); paths are also
told apart by dash style, number badges and the legend.

Run: .venv/bin/python docs/technical/figures/build_gradient_figure.py
Writes output/email/2026-09-30_kearsley/FourSight_three_approaches.png (and .pdf).
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.patches import Ellipse, Circle, Polygon, FancyBboxPatch, Rectangle
from matplotlib.transforms import Affine2D
from matplotlib import patheffects as pe
from scipy.ndimage import zoom, gaussian_filter

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/email/2026-09-30_kearsley"

# ------------------------------------------------------------------ palette and type
BG = "#0b1020"; INK = "#0b1020"; TXT = "#f1f3f5"; TXT2 = "#c3ccd6"; TXT3 = "#8391a2"
A1, A2, A3, A0 = "#fcc419", "#4dabf7", "#f06595", "#98a2b3"
PORTAL = "#97ce4c"; PORTAL_HI = "#e4ff9a"; PORTAL_LO = "#2f8f3a"
SANS = "Avenir Next"; HAND = "Chalkboard SE"
LAND = LinearSegmentedColormap.from_list(   # defensible (bright green) ... non-defensible (dark)
    "land", ["#c9f779", "#7fd96b", "#2f9e72", "#1a5f63", "#173a55", "#141f40", "#0d1128"])

# ------------------------------------------------------------------ the landscape
W, H = 10.0, 12.5
PEAKS = {                                   # (cx, cy, height, sx, sy)
    "P1": (5.0, 9.0, 0.95, 1.55, 1.25),     # Approach 1: simulation + dispatch
    "P2": (8.4, 5.6, 0.95, 1.30, 1.05),     # Approach 2: events, zones and traffic
    "P3": (2.0, 7.4, 1.15, 1.55, 1.35),     # Approach 3: under the fog (the tallest)
}
DIP = [5.1, 4.8, 0.24, 0.62, 0.58]          # a shallow dip at the fork: every direction climbs
GHOST = (2.5, 3.6, 0.85, 0.95, 0.85)        # the peak the initial plan aimed for (old landscape)
TILT = (0.035, 0.055)                       # the ground rises gently to the upper right


def g(x, y, c):
    cx, cy, a, sx, sy = c
    return a * np.exp(-((x - cx) ** 2 / (2 * sx ** 2) + (y - cy) ** 2 / (2 * sy ** 2)))


def D(x, y, old=False):
    z = TILT[0] * x + TILT[1] * y - g(x, y, DIP)
    for c in PEAKS.values():
        z = z + g(x, y, c)
    z = z + 0.02 * np.sin(1.25 * x + 0.3) * np.cos(1.05 * y)
    if old:
        z = z + g(x, y, GHOST)
    return z


def grad(p, old=False, h=1e-5):
    x, y = p
    return np.array([(D(x + h, y, old) - D(x - h, y, old)) / (2 * h),
                     (D(x, y + h, old) - D(x, y - h, old)) / (2 * h)])


def climb(p0, old=False, eta=0.04, n=8000, tol=1.5e-3):
    P = [np.array(p0, float)]
    for _ in range(n):
        gr = grad(P[-1], old)
        if np.hypot(*gr) < tol:
            break
        P.append(P[-1] + eta * gr)
    return np.array(P)


def arclen_index(P, frac):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    return int(np.searchsorted(s, frac * s[-1]))


def along(P, frac, off=(0.0, 0.0)):
    x, y = P[min(arclen_index(P, frac), len(P) - 1)]
    return x + off[0], y + off[1]


def tangent_deg(P, frac):
    i = min(max(arclen_index(P, frac), 1), len(P) - 2)
    d = P[i + 1] - P[i - 1]
    return float(np.degrees(np.arctan2(d[1], d[0])))


def resample(P, n):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    t = np.linspace(0, s[-1], n)
    return np.c_[np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])]


# The restart point R and the one step we took: put the dip exactly where a step along
# +grad D(R) lands, iterating because the dip itself tilts the gradient at R a little.
R = np.array([3.35, 1.45])
for _ in range(8):
    d = grad(R); d /= np.linalg.norm(d)
    s = float(np.dot(np.array(DIP[:2]) - R, d))
    DIP[0], DIP[1] = R + s * d
F = np.array(DIP[:2])
assert D(*F) > D(*R), "the step must climb"
_u = grad(R) / np.linalg.norm(grad(R))
STEP_ANGLE_ERR = np.degrees(np.arccos(np.clip(np.dot(_u, (F - R) / np.linalg.norm(F - R)), -1, 1)))
assert STEP_ANGLE_ERR < 1.0, STEP_ANGLE_ERR

S = np.array([1.0, 0.95])                   # 15 Sep: the initial plan
LINE0 = climb(S, old=True)
LINE0 = LINE0[: arclen_index(LINE0, 0.70)]  # the data never came, so the climb stopped here

START = {1: 95, 2: 0, 3: 170}               # directions of the first step off the fork (degrees)
KICK = 0.6                                  # length of that first step
TARGET = {1: "P1", 2: "P2", 3: "P3"}
PATHS = {}
for k, ang in START.items():
    a = np.deg2rad(ang)
    fl = climb(F + KICK * np.array([np.cos(a), np.sin(a)]))
    end = min(PEAKS, key=lambda p: np.hypot(*(fl[-1] - np.array(PEAKS[p][:2]))))
    assert end == TARGET[k], (k, end)
    PATHS[k] = np.vstack([F, fl])


# ------------------------------------------------------------------ drawing helpers
def halo(w=3.5, c=BG):
    return [pe.withStroke(linewidth=w, foreground=c)]


def label(ax, x, y, s, size=13.5, color=TXT, ha="left", va="center", weight="normal", z=40, alpha=0.8, pad=0.32):
    return ax.text(x, y, s, fontsize=size, color=color, family=SANS, weight=weight, ha=ha, va=va, zorder=z,
                   linespacing=1.25, bbox=dict(boxstyle=f"round,pad={pad}", fc=BG, ec="none", alpha=alpha))


def badge(ax, x, y, n, color, size=16, z=45):
    ax.text(x, y, str(n), fontsize=size, family=SANS, weight="bold", color=BG, ha="center", va="center", zorder=z,
            bbox=dict(boxstyle="circle,pad=0.3", fc=color, ec=BG, lw=1.8))


def portal(ax, x, y, r=0.42, z=12, squash=0.82):
    for k, a in zip(np.linspace(2.0, 1.05, 7), np.linspace(0.04, 0.22, 7)):
        ax.add_patch(Ellipse((x, y), 2 * r * k, 2 * r * k * squash, fc=PORTAL, ec="none", alpha=a, zorder=z))
    cols = LinearSegmentedColormap.from_list("p", [PORTAL_LO, PORTAL, PORTAL_HI])(np.linspace(0, 1, 9))
    for k, c in zip(np.linspace(1.0, 0.12, 9), cols):
        ax.add_patch(Ellipse((x, y), 2 * r * k, 2 * r * k * squash, fc=c, ec="none", zorder=z + 1))
    t = np.linspace(0, 5 * np.pi, 300); rr = r * 0.92 * (1 - t / (5.4 * np.pi))
    ax.plot(x + rr * np.cos(t), y + squash * rr * np.sin(t), color="#f7ffe0", lw=1.3, alpha=0.75, zorder=z + 2)


def fog(ax, cx, cy, rx, ry, z=20):
    xs = np.linspace(cx - 1.6 * rx, cx + 1.6 * rx, 320); ys = np.linspace(cy - 1.7 * ry, cy + 1.7 * ry, 260)
    X, Y = np.meshgrid(xs, ys)
    r2 = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
    noise = np.random.default_rng(7).normal(size=(52, 64))
    noise = gaussian_filter(zoom(noise, (260 / 52, 320 / 64), order=1), 6)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    alpha = np.clip(1.25 - r2, 0, 1) ** 0.8 * (0.62 + 0.38 * noise) * 0.94
    rgba = np.zeros(X.shape + (4,)); rgba[..., :3] = to_rgb("#c9d3de"); rgba[..., 3] = alpha
    ax.imshow(rgba, extent=(xs[0], xs[-1], ys[0], ys[-1]), origin="lower", zorder=z, interpolation="bilinear")


def van(ax, x, y, ang, s=0.95, z=60):
    """The Blue Jay shuttle as a rocket: drawn in its own frame (x forward, rear at 0), then
    rotated to the path's direction and centred on (x, y)."""
    flip = 90 < ang % 360 < 270          # heading left: mirror it so the wheels stay on the downhill side
    rot = ang - 180 if flip else ang
    T = Affine2D().translate(-0.96, -0.48).scale(-s if flip else s, s).rotate_deg(rot).translate(x, y)
    tr = T + ax.transData

    def poly(pts, fc, ec=INK, lw=1.3, zz=0, alpha=1.0):
        ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, alpha=alpha, transform=tr, zorder=z + zz,
                             joinstyle="round"))

    def circ(cx, cy, r, fc, ec=INK, lw=1.2, zz=0, alpha=1.0):
        ax.add_patch(Circle((cx, cy), r, fc=fc, ec=ec, lw=lw, alpha=alpha, transform=tr, zorder=z + zz))

    for (cx, cy, r, a) in [(-1.12, 0.47, 0.11, 0.28), (-1.33, 0.45, 0.14, 0.16)]:
        circ(cx, cy, r, "#dee2e6", ec="none", alpha=a, zz=-2)                              # smoke
    poly([(-0.20, 0.29), (-0.58, 0.20), (-1.02, 0.48), (-0.58, 0.76), (-0.20, 0.67)], "#ff922b", ec="none", zz=-1)
    poly([(-0.20, 0.36), (-0.50, 0.31), (-0.80, 0.48), (-0.50, 0.65), (-0.20, 0.60)], "#ffd43b", ec="none", zz=-1)
    poly([(-0.20, 0.42), (-0.38, 0.40), (-0.54, 0.48), (-0.38, 0.56), (-0.20, 0.54)], "#fff9db", ec="none", zz=-1)
    poly([(0.02, 0.34), (0.02, 0.62), (-0.21, 0.69), (-0.21, 0.27)], "#868e96")                  # nozzle
    poly([(0.02, 0.84), (-0.34, 1.07), (-0.20, 0.84), (0.02, 0.66)], "#e8590c")                 # fins
    poly([(0.02, 0.14), (-0.34, -0.09), (-0.20, 0.14), (0.02, 0.32)], "#e8590c")
    body = [(0.0, 0.14), (0.0, 0.80), (0.10, 0.85), (1.40, 0.85), (1.50, 0.81), (1.74, 0.51), (1.88, 0.45),
            (1.93, 0.37), (1.93, 0.17), (1.86, 0.12), (0.05, 0.12)]
    poly(body, "#1f45b5", lw=1.5, zz=1)
    poly([(0.0, 0.12), (1.93, 0.12), (1.93, 0.22), (0.0, 0.22)], "#2e3440", lw=1.0, zz=2)       # skirt
    windows = [(0.12, 0.42), (0.48, 0.78), (0.84, 1.14)]
    hair = ["#1b1b1b", "#3b2416", "#111111", "#5a3825"]; skin = ["#e0b090", "#f1c9a5", "#c68e62", "#d9a074"]
    th = np.linspace(np.deg2rad(5), np.deg2rad(175), 20)
    for i, (a, b) in enumerate(windows):
        poly([(a, 0.46), (b, 0.46), (b, 0.73), (a, 0.73)], "#18202e", lw=1.0, zz=2)
        fx = (a + b) / 2
        circ(fx, 0.565, 0.088, skin[i], lw=0.9, zz=3)
        poly([(fx + 0.093 * np.cos(t), 0.575 + 0.093 * np.sin(t)) for t in th], hair[i], lw=0.8, zz=4)
        for dx in (-0.03, 0.03):
            circ(fx + dx, 0.555, 0.011, INK, ec="none", zz=5)
        ax.plot([a + 0.03, a + 0.12], [0.70, 0.62], color="white", lw=1.0, alpha=0.35, transform=tr, zorder=z + 6)
    poly([(1.21, 0.47), (1.55, 0.47), (1.47, 0.75), (1.21, 0.75)], "#18202e", lw=1.0, zz=2)    # cab window
    circ(1.36, 0.575, 0.088, skin[3], lw=0.9, zz=3)
    poly([(1.36 + 0.093 * np.cos(t), 0.585 + 0.093 * np.sin(t)) for t in th], hair[3], lw=0.8, zz=4)
    for dx in (-0.03, 0.03):
        circ(1.36 + dx, 0.565, 0.011, INK, ec="none", zz=5)
    poly([(1.53, 0.79), (1.61, 0.77), (1.77, 0.53), (1.70, 0.51)], "#18202e", lw=1.0, zz=2)    # windshield
    ax.add_patch(Ellipse((1.87, 0.40), 0.07, 0.06, fc="#fff3bf", ec=INK, lw=0.8, transform=tr, zorder=z + 3))
    for wx in (0.40, 1.50):
        circ(wx, 0.12, 0.13, "#1d1d1d", lw=1.2, zz=4)
        circ(wx, 0.12, 0.055, "#adb5bd", lw=0.8, zz=5)
    for (px, py, s_, fs) in [(0.66, 0.31, "BLUE JAY SHUTTLE", 7.6), (1.36, 0.31, "962", 7.2)]:
        X = T.transform((px, py))
        ax.text(X[0], X[1], s_, rotation=rot, rotation_mode="anchor", ha="center", va="center", fontsize=fs * s,
                family=SANS, weight="bold", color="white", zorder=z + 6)


def professor(ax, px, py, beam_to, z=50):
    """Prof. AJK, drawn from his photo: grey hair, white beard, clear safety glasses, maroon shirt,
    brown tweed jacket. He raises a lantern toward beam_to."""
    skin = "#f0c6a3"; tweed = "#8a6a4b"; tweed_dk = "#6b4f35"; beard = "#e2e3e5"; hair = "#c3c7cc"
    jacket = Polygon([(px - 0.52, py - 1.28), (px + 0.52, py - 1.28), (px + 0.44, py - 0.44), (px + 0.18, py - 0.31),
                      (px - 0.18, py - 0.31), (px - 0.44, py - 0.44)], closed=True, fc=tweed, ec=INK, lw=1.4,
                     zorder=z, joinstyle="round")
    ax.add_patch(jacket)
    for t in np.arange(-0.6, 0.62, 0.085):                                  # tweed weave
        for xs, ys in [((px + t, px + t), (py - 1.3, py - 0.28)), ((px - 0.6, px + 0.6), (py - 0.36 + t, py - 0.36 + t))]:
            ln, = ax.plot(xs, ys, color=tweed_dk, lw=0.6, alpha=0.55, zorder=z + 0.5)
            ln.set_clip_path(jacket)
    ax.add_patch(Polygon([(px - 0.17, py - 0.31), (px + 0.17, py - 0.31), (px, py - 0.78)], closed=True, fc="#7d1f2b",
                         ec=INK, lw=1.1, zorder=z + 1))
    for sgn in (-1, 1):                                                     # lapels
        ax.add_patch(Polygon([(px + sgn * 0.17, py - 0.31), (px + sgn * 0.30, py - 0.40), (px + sgn * 0.06, py - 0.95),
                              (px, py - 0.78)], closed=True, fc=tweed_dk, ec=INK, lw=1.0, zorder=z + 1.5))
    # the raised arm and the lantern
    sh = (px + 0.40, py - 0.50); hand = (px + 0.66, py + 0.30)
    ax.plot([sh[0], hand[0]], [sh[1], hand[1]], color=INK, lw=13, solid_capstyle="round", zorder=z + 2)
    ax.plot([sh[0], hand[0]], [sh[1], hand[1]], color=tweed, lw=10.5, solid_capstyle="round", zorder=z + 2.1)
    ax.add_patch(Circle(hand, 0.075, fc=skin, ec=INK, lw=1.1, zorder=z + 3))
    lx, ly = hand[0] + 0.02, hand[1] - 0.24
    bx, by = beam_to
    v = np.array([bx - lx, by - ly]); v /= np.linalg.norm(v); nrm = np.array([-v[1], v[0]])
    L = np.hypot(bx - lx, by - ly) + 0.5
    ax.add_patch(Polygon([np.array([lx, ly]) + 0.06 * nrm, np.array([lx, ly]) - 0.06 * nrm,
                          np.array([lx, ly]) + L * v - 0.75 * nrm, np.array([lx, ly]) + L * v + 0.75 * nrm],
                         closed=True, fc="#ffe066", ec="none", alpha=0.16, zorder=z - 25))   # the beam
    for rr, a in [(0.34, 0.10), (0.24, 0.16), (0.16, 0.25)]:
        ax.add_patch(Circle((lx, ly), rr, fc="#ffe066", ec="none", alpha=a, zorder=z + 3))
    ax.plot([hand[0] - 0.05, hand[0], hand[0] + 0.05], [ly + 0.13, hand[1] - 0.02, ly + 0.13], color=INK, lw=1.2,
            zorder=z + 3)
    ax.add_patch(Rectangle((lx - 0.085, ly - 0.11), 0.17, 0.22, fc="#ffd43b", ec=INK, lw=1.2, zorder=z + 4))
    ax.add_patch(Rectangle((lx - 0.105, ly + 0.10), 0.21, 0.05, fc="#495057", ec=INK, lw=1.0, zorder=z + 5))
    ax.add_patch(Rectangle((lx - 0.105, ly - 0.15), 0.21, 0.05, fc="#495057", ec=INK, lw=1.0, zorder=z + 5))
    ax.add_patch(Ellipse((lx, ly), 0.07, 0.11, fc="#fff9db", ec="none", zorder=z + 5))
    # head
    ax.add_patch(Rectangle((px - 0.08, py - 0.42), 0.16, 0.14, fc=skin, ec=INK, lw=1.0, zorder=z + 2))
    for sgn in (-1, 1):
        ax.add_patch(Ellipse((px + sgn * 0.29, py - 0.02), 0.09, 0.16, fc=skin, ec=INK, lw=1.0, zorder=z + 3))
    ax.add_patch(Ellipse((px, py), 0.58, 0.68, fc=skin, ec=INK, lw=1.3, zorder=z + 4))
    th = np.linspace(np.deg2rad(12), np.deg2rad(168), 40)
    cap = [(px + 0.30 * np.cos(t) * (1.03 + 0.05 * np.sin(9 * t)), py + 0.04 + 0.33 * np.sin(t) * (1.04 + 0.05 * np.sin(11 * t)))
           for t in th]
    ax.add_patch(Polygon(cap + [(px - 0.20, py + 0.20), (px, py + 0.25), (px + 0.20, py + 0.20)], closed=True, fc=hair,
                         ec=INK, lw=1.1, zorder=z + 5))
    beard_pts = [(px - 0.29, py + 0.0), (px - 0.28, py - 0.22), (px - 0.19, py - 0.40), (px, py - 0.47),
                 (px + 0.19, py - 0.40), (px + 0.28, py - 0.22), (px + 0.29, py + 0.0), (px + 0.22, py - 0.06),
                 (px + 0.12, py - 0.13), (px - 0.12, py - 0.13), (px - 0.22, py - 0.06)]
    ax.add_patch(Polygon(beard_pts, closed=True, fc=beard, ec=INK, lw=1.1, zorder=z + 6))
    ax.add_patch(Ellipse((px, py - 0.155), 0.30, 0.095, fc="#cfd3d8", ec=INK, lw=0.9, zorder=z + 7))   # moustache
    ax.plot(px + np.linspace(-0.06, 0.06, 12), py - 0.235 - 0.018 * np.cos(np.linspace(-1.4, 1.4, 12)),
            color="#7a3b2e", lw=1.4, zorder=z + 7)                                                    # smile
    ax.plot([px - 0.005, px + 0.03, px - 0.01], [py + 0.04, py - 0.07, py - 0.08], color="#b07c5e", lw=1.2,
            zorder=z + 6)                                                                             # nose
    for sgn in (-1, 1):
        ax.add_patch(Circle((px + sgn * 0.11, py + 0.02), 0.022, fc=INK, ec="none", zorder=z + 6))
        ax.plot([px + sgn * 0.05, px + sgn * 0.17], [py + 0.11, py + 0.125], color="#5c5f66", lw=2.6,
                solid_capstyle="round", zorder=z + 7)                                                 # brows
        ax.add_patch(FancyBboxPatch((px + sgn * 0.11 - 0.085, py - 0.045), 0.17, 0.13,
                                    boxstyle="round,pad=0.0,rounding_size=0.04", fc="#d0ebff", ec="#343a40", lw=0.9,
                                    alpha=0.45, zorder=z + 8))                                        # lenses
    ax.plot([px - 0.215, px + 0.215], [py + 0.085, py + 0.085], color="#212529", lw=2.6, solid_capstyle="round",
            zorder=z + 9)                                                                             # top bar
    ax.plot([px - 0.215, px - 0.29], [py + 0.08, py + 0.06], color="#212529", lw=1.4, zorder=z + 9)
    ax.plot([px + 0.215, px + 0.29], [py + 0.08, py + 0.06], color="#212529", lw=1.4, zorder=z + 9)
    label(ax, px, py - 1.48, "Prof. AJK", size=14, weight="bold", ha="center", alpha=0.85)


# ------------------------------------------------------------------ the figure
def build():
    fig = plt.figure(figsize=(W, H), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")

    x = np.linspace(0, W, 500); y = np.linspace(0, H, 625); X, Y = np.meshgrid(x, y); Z = -D(X, Y)
    lev = np.linspace(Z.min(), Z.max(), 26)
    ax.contourf(X, Y, Z, lev, cmap=LAND, zorder=1)
    ax.contour(X, Y, Z, lev, colors="#c9f7c0", linewidths=0.55, alpha=0.20, zorder=2)
    rng = np.random.default_rng(11)                                         # stars over the dark ground
    sx, sy = rng.uniform(0, W, 520), rng.uniform(0, H, 520)
    keep = D(sx, sy) < 0.32
    ax.scatter(sx[keep], sy[keep], s=rng.uniform(0.3, 3.5, keep.sum()), c="white", alpha=0.5, lw=0, zorder=3)
    ax.contour(X, Y, D(X, Y, old=True) - D(X, Y), [0.2, 0.55], colors=A0, linewidths=1.0, linestyles="--",
               alpha=0.38, zorder=4)                                        # ghost of the old peak
    fog(ax, 2.0, 7.35, 1.95, 1.45)

    # ---- the initial scope (abandoned) and the restart
    ax.plot(*LINE0.T, color=A0, lw=2.6, ls=(0, (6, 4)), zorder=15)
    ax.plot(*S, marker="o", ms=12, mfc=A0, mec=BG, mew=2, zorder=16)
    xe, ye = LINE0[-1]
    portal(ax, xe, ye, r=0.24, z=13)
    ax.plot(xe, ye, marker="X", ms=19, mfc="#ff6b6b", mec=BG, mew=1.6, zorder=17)
    label(ax, S[0] + 0.32, S[1] - 0.42, "15 Sep · initial plan:\nreplay April trip by trip", size=13, color=TXT2)
    label(ax, xe - 0.38, ye + 0.05, "trip-level data\nnever came", size=13, color="#ffc9c9", ha="right")
    portal(ax, *R, r=0.36, z=13)
    t = np.linspace(0, 1, 60)
    arc = np.c_[xe + (R[0] - xe) * t + 0.55 * np.sin(np.pi * t), ye + (R[1] - ye) * t]
    ax.plot(*arc.T, color=PORTAL, lw=2.0, ls=(0, (1, 2.6)), zorder=14)
    label(ax, R[0] + 0.52, R[1] - 0.55, "29 Sep · restart on\naggregate data", size=13, color=TXT2)

    # ---- the step (done)
    ax.annotate("", xy=F, xytext=R, zorder=22,
                arrowprops=dict(arrowstyle="-|>,head_length=0.9,head_width=0.45", color="white", lw=3.4,
                                shrinkA=16, shrinkB=11))
    mid = R + 0.55 * (F - R)
    label(ax, mid[0] + 0.32, mid[1] - 0.45, "one step: charts digitized,\ndata mined", size=13, color=TXT)
    u = (F - R) / np.linalg.norm(F - R); nrm = np.array([-u[1], u[0]])
    ang = np.degrees(np.arctan2(u[1], u[0]))
    gpos = R + 0.50 * (F - R) + 0.55 * nrm
    ax.text(*gpos, "$\\nabla D$", fontsize=26, color="white", ha="center",
            va="center", zorder=31, path_effects=halo(4))
    # the angle of the step, measured from the horizontal at the restart point
    r0 = 0.95
    ax.plot([R[0] + 0.30, R[0] + 1.35], [R[1], R[1]], color=TXT2, lw=1.4, ls=(0, (3, 2)), zorder=21)
    th = np.linspace(0, np.radians(ang), 40)
    ax.plot(R[0] + r0 * np.cos(th), R[1] + r0 * np.sin(th), color=TXT, lw=1.8, zorder=21)
    ax.annotate("", xy=(R[0] + r0 * np.cos(th[-1]), R[1] + r0 * np.sin(th[-1])),
                xytext=(R[0] + r0 * np.cos(th[-4]), R[1] + r0 * np.sin(th[-4])), zorder=21,
                arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.25", color=TXT, lw=1.6))
    tm = np.radians(ang / 2)
    ax.text(R[0] + (r0 + 0.32) * np.cos(tm), R[1] + (r0 + 0.32) * np.sin(tm), f"{ang:.0f}°", fontsize=14,
            family=SANS, weight="bold", color=TXT, ha="center", va="center", zorder=31, path_effects=halo(3))
    ax.plot(*F, marker="o", ms=14, mfc="white", mec=BG, mew=2.4, zorder=34)
    label(ax, F[0] + 0.30, F[1] - 0.40, "1 Oct", size=13.5, color=TXT, weight="bold")

    # ---- the three approaches (ahead): dotted flows with evenly spaced steps
    P1, P2, P3 = PATHS[1], PATHS[2], PATHS[3]
    VAN_AT = 0.45
    iv = arclen_index(P1, VAN_AT)
    ax.plot(*P1[: iv + 1].T, color=A1, lw=4.2, zorder=24, solid_capstyle="round")       # climbed so far
    ax.plot(*P1[iv:].T, color=A1, lw=3.6, ls=(0, (1.2, 2.2)), zorder=24, dash_capstyle="round")
    ax.scatter(*resample(P1[iv:], 8)[1:].T, s=40, c=A1, edgecolors=BG, linewidths=1.7, zorder=25)
    ax.plot(*P2.T, color=A2, lw=3.0, ls=(0, (5, 2.2, 1.2, 2.2)), zorder=24)
    ax.scatter(*resample(P2, 10)[1:].T, s=36, c=A2, edgecolors=BG, linewidths=1.6, zorder=25)
    Q3 = P3[: arclen_index(P3, 0.66)]
    ax.plot(*Q3.T, color=A3, lw=3.0, ls=(0, (1, 2.6)), zorder=24, dash_capstyle="round")
    ax.scatter(*resample(Q3, 7)[1:].T, s=36, c=A3, edgecolors=BG, linewidths=1.6, zorder=25)
    for f, sz in [(0.72, 22), (0.83, 26), (0.94, 30)]:
        ax.text(*along(P3, f), "?", fontsize=sz, family=HAND, weight="bold", color=A3, ha="center", va="center",
                zorder=26, path_effects=halo(3.5, "#c9d3de"))
    portal(ax, *P1[-1], r=0.50, z=18)
    portal(ax, *P2[-1], r=0.38, z=18)

    # number badges beside each path
    b1 = along(P1, 0.62, (0.55, 0.0))
    badge(ax, *b1, 1, A1)
    label(ax, b1[0] + 0.32, b1[1], "Simulation + dispatch", size=15, color=A1, weight="bold")
    b2 = along(P2, 0.62, (-0.55, 0.62))
    badge(ax, *b2, 2, A2)
    label(ax, b2[0] + 0.32, b2[1], "Events, zones\nand traffic", size=15, color=A2, weight="bold")
    badge(ax, *along(P3, 0.36, (-0.50, -0.10)), 3, A3)
    q = along(P3, 0.83)
    ax.annotate("What's in plain sight\nthat we don't see?", xy=(q[0] + 0.25, q[1] + 0.30), xytext=(2.45, 9.25),
                fontsize=16, family=HAND, weight="bold", color=INK, ha="center", va="center", zorder=70,
                linespacing=1.2, bbox=dict(boxstyle="round,pad=0.55", fc="white", ec=INK, lw=2.0),
                arrowprops=dict(arrowstyle="wedge,tail_width=0.7,shrink_factor=0.5", fc="white", ec=INK, lw=1.8,
                                shrinkA=0, shrinkB=4))

    # the van, climbing approach 1
    van(ax, *P1[iv], tangent_deg(P1, VAN_AT), s=0.72)

    # Prof. AJK with the lantern, lighting the fog over approach 3
    professor(ax, 0.95, 5.05, beam_to=(1.9, 7.2))

    # ---- legend band (top)
    ax.add_patch(FancyBboxPatch((0.18, 10.42), 9.64, 1.94, boxstyle="round,pad=0.02,rounding_size=0.14", fc=BG,
                                ec="#2a3550", lw=1.0, alpha=0.88, zorder=80))
    ax.text(0.42, 12.08, "Blue Jay Night Ride  ·  Team FourSight", fontsize=13, family=SANS, weight="bold",
            color=TXT2, ha="left", va="center", zorder=81)
    keys = [(A1, "-", 4.0, "Approach 1 · Simulation + dispatch"),
            (A2, (0, (5, 2.2, 1.2, 2.2)), 3.0, "Approach 2 · Events, zones and traffic"),
            (A3, (0, (1, 2.6)), 3.0, "Approach 3 · What's in plain sight that we don't see"),
            (A0, (0, (6, 4)), 2.6, "Initial scope (abandoned)")]
    for i, (c, ls, lw, s_) in enumerate(keys):
        yy = 11.66 - 0.33 * i
        ax.plot([0.45, 1.05], [yy, yy], color=c, lw=lw, ls=ls, zorder=81, solid_capstyle="round")
        ax.text(1.2, yy, s_, fontsize=14, family=SANS, color=TXT, ha="left", va="center", zorder=81)
    cb = fig.add_axes([0.672, 0.902, 0.29, 0.016])
    cb.imshow(np.linspace(1, 0, 256)[None, :], aspect="auto", cmap=LAND, extent=(0, 1, 0, 1))
    cb.set_xticks([]); cb.set_yticks([])
    for sp in cb.spines.values():
        sp.set_edgecolor(TXT3)
    ax.text(6.72, 11.0, "non-defensible", fontsize=14, family=SANS, color=TXT, ha="left", va="center", zorder=81)
    ax.text(9.62, 11.0, "defensible", fontsize=14, family=SANS, weight="bold", color=PORTAL_HI, ha="right",
            va="center", zorder=81)
    return fig


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig = build()
    png = OUT / "FourSight_three_approaches.png"; pdf = OUT / "FourSight_three_approaches.pdf"
    fig.savefig(png, dpi=180, facecolor=BG)
    fig.savefig(pdf, facecolor=BG)
    print(png, pdf, f"step angle error {STEP_ANGLE_ERR:.2f} deg", f"D(R)={D(*R):.3f} D(F)={D(*F):.3f}",
          "F", F.round(2), sep="\n")
