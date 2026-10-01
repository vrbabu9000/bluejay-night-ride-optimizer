"""
Static recreation of the four O/D density maps (pp. 2-5) from the digitized
bubbles: circle area proportional to the count, drawn at the georeferenced
position on a quiet OpenStreetMap basemap. Cut or hidden bubbles are dashed.

Output: outputs/evidence/p02_p05_recreated.png
Run: .venv/bin/python src/evidence/maps_recreated.py
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "insights"))
import basemap  # noqa: E402
from common import BLUE, INK, INK2, ORANGE, SURFACE, save, source, style  # noqa: E402

VIEWS = {
    "city": dict(bbox=(39.281, -76.700, 39.352, -76.575), z=14, scale=0.30),
    "campus": dict(bbox=(39.3216, -76.6440, 39.3384, -76.5995), z=16, scale=1.0),
}


def main():
    style()
    c = pd.read_csv(ROOT / "data" / "processed" / "map_clusters.csv")
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.2))
    for row, view in enumerate(("city", "campus")):
        spec = VIEWS[view]
        for col, (kind, colour) in enumerate((("origins", BLUE), ("destinations", ORANGE))):
            ax = axes[row, col]
            s, w, n, e = spec["bbox"]
            basemap.draw(ax, s, w, n, e, z=spec["z"])
            d = c[c.map_name == f"{kind}_{view}"]
            x, y = basemap.merc(d.lat.values, d.lon.values)
            solid = (d.status == "ok").values
            size = d.count_best.values * spec["scale"]
            ax.scatter(x[solid], y[solid], s=size[solid], color=colour, alpha=0.55, edgecolors=SURFACE, linewidths=1.5, zorder=3)
            ax.scatter(x[~solid], y[~solid], s=size[~solid], facecolors="none", edgecolors=colour, linewidths=1.2,
                       linestyles="--", zorder=3)
            top = d.nlargest(6 if view == "city" else 8, "count_best")
            tx, ty = basemap.merc(top.lat.values, top.lon.values)
            for r, xx, yy in zip(top.itertuples(), tx, ty):
                ax.annotate(f"{int(r.count_best):,}", (xx, yy), ha="center", va="center", fontsize=8, color=INK, zorder=4)
            read = int(d.count_read.sum())
            cut = int((d.status != "ok").sum()) if view == "campus" else 0
            extra = f" ({cut} edge or partial bubbles dashed)" if cut else ""
            ax.set_title(f"{kind.capitalize()}, {view} view (p{int(d.map_page.iloc[0])}): {read:,} rides read{extra}", fontsize=11)
    fig.suptitle("April 2026 origin and destination density maps, digitized (circle area = completed rides)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", color=INK)
    source(fig, "Every bubble read and georeferenced (campus view ±17 m, city view ±57 m). Dashed = cut or hidden bubble at bound midpoint. "
                "Basemap © OpenStreetMap contributors.")
    fig.subplots_adjust(hspace=0.16, wspace=0.04, top=0.88)
    out = ROOT / "outputs" / "evidence" / "p02_p05_recreated.png"
    fig.savefig(out, dpi=170, bbox_inches="tight"); plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
