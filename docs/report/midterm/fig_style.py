"""Shared figure standard for the midterm report (v3 onward).

Every report figure is drawn at its final printed size and included in the .tex at natural size
(\\includegraphics{...} with no width=), so the font sizes set here are the sizes on the page.
Body text is 10 pt and captions 9 pt, so figure text stays within 7 to 9 pt.

Use:  from fig_style import FS, COLW, TEXTW, apply_style, save
      apply_style()            # once, after importing make_figures (it sets its own rcParams)
      save(fig, "name")        # writes figures/name.pdf and runs the checks below
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.text import Text

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

COLW = 3.25    # inches, one ICML column  (figure)
TEXTW = 6.75   # inches, ICML \textwidth   (figure*)

FS = {
    "title": 8.5,   # panel titles, bold box titles
    "body": 8.0,    # box text, axis labels, legends, direct labels
    "small": 7.0,   # tick labels, arrow labels, source notes (the floor)
}
FS_MIN, FS_MAX = 7.0, 9.0


def apply_style():
    # make_figures selects the pdf backend, which has no renderer for check(); output is still PDF
    plt.switch_backend("Agg")
    plt.rcParams.update({
        "font.family": ["Arial", "DejaVu Sans"],
        "font.size": FS["body"],
        "axes.titlesize": FS["title"],
        "axes.labelsize": FS["body"],
        "xtick.labelsize": FS["small"],
        "ytick.labelsize": FS["small"],
        "legend.fontsize": FS["small"],
        "mathtext.fontset": "stix",
        "pdf.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "lines.linewidth": 1.2,
    })


def _texts(fig):
    return [t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]


def check(fig, name, max_width=TEXTW, pad_pt=1.0):
    """Return a list of problems: font sizes outside 7-9 pt, figure too wide, text boxes that overlap."""
    problems = []
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    w, _ = fig.get_size_inches()
    if w > max_width + 1e-6:
        problems.append(f"{name}: width {w:.2f} in > {max_width} in")
    texts = _texts(fig)
    for t in texts:
        fs = t.get_fontsize()
        if not FS_MIN - 1e-6 <= fs <= FS_MAX + 1e-6:
            problems.append(f"{name}: font {fs:.1f} pt outside {FS_MIN}-{FS_MAX}: {t.get_text()[:40]!r}")
    pad = pad_pt * fig.dpi / 72
    boxes = [(t, t.get_window_extent(r).expanded(1, 1).padded(pad)) for t in texts]
    for (a, ba), (b, bb) in itertools.combinations(boxes, 2):
        if ba.overlaps(bb):
            problems.append(f"{name}: text overlap {a.get_text()[:30]!r} / {b.get_text()[:30]!r}")
    return problems


def save(fig, name, max_width=TEXTW, strict=False):
    """Save at natural size (no tight-bbox rescale beyond a small pad) and print any check problems."""
    problems = check(fig, name, max_width)
    for p in problems:
        print("CHECK", p, file=sys.stderr)
    if strict and problems:
        raise SystemExit(f"{name}: {len(problems)} figure check problem(s)")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return problems
