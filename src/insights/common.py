"""
Shared loading and figure style for the insight tasks T1-T10.

Style follows the project's data-viz rules: a light surface, hairline grid,
2 px lines, >= 8 px markers with a surface ring, thin bars, one y axis per
chart, a legend for >= 2 series, and selective direct labels. Palette slots
come in a fixed order (blue, orange, aqua), validated for colour-vision
deficiency; gray is the de-emphasis colour. Figures are PNGs for the deck and
report; every figure has its numbers in a CSV twin.
"""
import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
FIGS = ROOT / "outputs" / "insights"
BRIEFS = ROOT / "docs" / "evidence" / "insights"

SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRAY = "#b9b7ae"          # de-emphasis marks
BLUE_LIGHT = "#86b6ef"    # sequential step 250


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10.5, "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 26, "axes.labelcolor": INK2, "axes.labelsize": 10,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False, "legend.fontsize": 9.5,
        "lines.linewidth": 2, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
    })


def marker_kw(color, size=7):
    """Filled marker with a 2 px surface-coloured ring."""
    return dict(marker="o", markersize=size, markerfacecolor=color, markeredgecolor=SURFACE, markeredgewidth=2)


def subtitle(ax, text):
    ax.text(0, 1.015, text, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")


def source(fig, text):
    fig.text(0.01, 0.005, text, fontsize=8, color=MUTED, ha="left", va="bottom")


def save(fig, name):
    FIGS.mkdir(parents=True, exist_ok=True)
    path = FIGS / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def observations(refresh=True):
    """All digitized chart observations, merged into data/processed/observations.csv."""
    if refresh:
        frames = [pd.read_csv(f) for f in sorted(glob.glob(str(PROCESSED / "obs_*.csv")))]
        obs = pd.concat(frames, ignore_index=True)
        obs.to_csv(PROCESSED / "observations.csv", index=False)
        return obs
    return pd.read_csv(PROCESSED / "observations.csv")


def series(obs, chart_id, metric):
    s = obs[(obs.chart_id == chart_id) & (obs.metric == metric)].copy()
    return s.set_index("date_or_hour")[["value", "lower", "upper"]]


def write_brief(task, title, body):
    BRIEFS.mkdir(parents=True, exist_ok=True)
    (BRIEFS / f"{task}.md").write_text(f"# {task.upper()}: {title}\n\n{body.strip()}\n")
