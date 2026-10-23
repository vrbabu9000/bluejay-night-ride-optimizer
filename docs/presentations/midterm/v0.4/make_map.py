"""Map figure for the v0.4 deck: the first synthetic pilot night, no implementation labels. Reads frozen inputs only; writes v0.4/figures/map_synthetic_hour.png.

    .venv/bin/python docs/presentations/midterm/v0.4/make_map.py
"""
import textwrap
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
z = pd.read_csv(ROOT / "data/processed/zones_v1.csv")
loc = pd.read_csv(ROOT / "data/processed/locations_v1.csv").drop_duplicates("loc_id").set_index("loc_id")
r = pd.read_csv(ROOT / "data/scenarios/v2/L5/r00/requests.csv")
fig, ax = plt.subplots(figsize=(4.2, 4.4), dpi=250)   # drawn at slide size: text stays legible
ax.scatter(loc.lon, loc.lat, s=4, color="#c9c8c2", zorder=1, label="188 April map places")
for _, x in r.iterrows():
    o, d = loc.loc[x.o_loc], loc.loc[x.d_loc]
    ax.plot([o.lon, d.lon], [o.lat, d.lat], color="#a3a29d", lw=0.8, zorder=2)
ax.scatter(loc.loc[r.o_loc].lon, loc.loc[r.o_loc].lat, s=22, color="#2a78d6", edgecolor="white", lw=1, zorder=3, label="pickup")
ax.scatter(loc.loc[r.d_loc].lon, loc.loc[r.d_loc].lat, s=22, marker="s", color="#eb6834", edgecolor="white", lw=1, zorder=3,
           label="drop-off")
names = {"Z08": ("Homewood campus", (34, -14)), "Z02": ("Charles Village", (34, 12)),
         "Z03": ("Mount Vernon\n(Peabody)", (26, 0)), "Z09": ("Inner Harbor", (24, 0))}
for zid, (nm, off) in names.items():
    row = z[z.zone_id == zid].iloc[0]
    ax.annotate(nm, (row.lon, row.lat), xytext=off, textcoords="offset points", fontsize=8.5, color="#333", va="center",
                arrowprops=dict(arrowstyle="-", color="#888", lw=0.6))
ax.set_aspect(1 / 0.773)                              # cos(39.3°): metres east = metres north on the page
ax.set_xlim(loc.lon.min() - 0.004, loc.lon.max() + 0.03)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_color("#d0cfc9")
ax.legend(loc="upper right", frameon=False, fontsize=8, handletextpad=0.2)
ax.set_title("One constructed hour: 28 requests", fontsize=9.5, loc="left", color="#222")
fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02)   # caption is on the slide
fig.savefig(Path(__file__).parent / "figures/map_synthetic_hour.png")
