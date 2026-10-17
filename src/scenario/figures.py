"""
Phase 3, step 3.8: the two Phase 3 figures (layout and wording confirmed with the team, 1 Oct 2026).

  (a) scenario_a_zone_shares.png   synthetic vs April zone shares (dot pairs, origins | destinations)
  (b) scenario_b_M_card.png        scenario M: map of the 30 requests, arrival strip, parameter card

Inputs: outputs/scenario/zone_shares_synthetic_vs_april.csv (from validate.py), data/scenarios/ladder/M/.
Run: .venv/bin/python src/scenario/figures.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "insights"))

import matplotlib.pyplot as plt                       # noqa: E402
import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D                    # noqa: E402

import basemap                                         # noqa: E402
from common import (AXIS, BLUE, GRID, INK, INK2, MUTED, ORANGE, SURFACE,  # noqa: E402
                    source, style)

OUT = ROOT / "outputs" / "scenario"
SHORT = {"Z01": "Remington", "Z02": "Charles Village", "Z03": "Mount Vernon", "Z04": "Midtown / Penn Station",
         "Z05": "University Pkwy", "Z06": "Hampden (W 38th St)", "Z07": "Station North", "Z08": "Homewood campus",
         "Z09": "Inner Harbor", "Z10": "Hampden north", "Z11": "Downtown", "Z12": "Charles Village south",
         "Z13": "Hampden (Roland Ave)", "Z14": "Woodberry", "Z15": "Wyman Park", "Z16": "Abell / Waverly"}


def fig_a():
    s = pd.read_csv(OUT / "zone_shares_synthetic_vs_april.csv")
    gap = (s.synthetic_share - s.april_share).abs().max() * 100
    assert round(gap, 1) == 0.4, f"footnote says 0.4 points; data say {gap:.2f}"
    order = s.groupby("zone_id").april_share.sum().sort_values().index      # largest at the top
    y = {z: i for i, z in enumerate(order)}
    fig, axes = plt.subplots(1, 2, figsize=(9, 6.6), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, (e, name) in zip(axes, (("O", "Origins"), ("D", "Destinations"))):
        d = s[s.endpoint == e]
        yy = d.zone_id.map(y)
        ax.scatter(d.april_share * 100, yy, s=110, facecolors="none", edgecolors=INK2, linewidths=1.6, zorder=3)
        ax.scatter(d.synthetic_share * 100, yy, s=34, color=BLUE, edgecolors=SURFACE, linewidths=1, zorder=4)
        ax.set_title(name, fontsize=11.5, pad=6)
        ax.set_xlim(-0.5, 27)
        ax.set_xticks([0, 5, 10, 15, 20, 25], ["0%", "5%", "10%", "15%", "20%", "25%"])
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Share of trips")
    axes[0].set_yticks(range(len(order)), [SHORT[z] for z in order])
    axes[0].set_ylim(-0.7, len(order) - 0.3)
    fig.suptitle("Where riders start and end: synthetic nights vs April", x=0.02, ha="left",
                 fontsize=13.5, fontweight="bold", y=1.0)
    handles = [Line2D([], [], ls="", marker="o", ms=10, mfc="none", mec=INK2, mew=1.6,
                      label="April (completed rides, from the maps)"),
               Line2D([], [], ls="", marker="o", ms=6.5, mfc=BLUE, mec=SURFACE, label="Synthetic (1,000 nights of scenario M)")]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.012, 0.965), ncol=2, handletextpad=0.4, columnspacing=1.6)
    fig.subplots_adjust(top=0.86, bottom=0.14, left=0.2, right=0.98)
    source(fig, "Largest gap: 0.4 percentage points. The maps count completed rides; synthetic trips are fitted to those totals.")
    path = OUT / "scenario_a_zone_shares.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_b():
    M = ROOT / "data" / "scenarios" / "ladder" / "M"
    req, fleet = pd.read_csv(M / "requests.csv"), pd.read_csv(M / "fleet.csv")
    sc = json.loads((M / "scenario.json").read_text())
    p, summ = sc["params"], sc["summary"]
    cmap = LinearSegmentedColormap.from_list("t", ["#a9c9f2", BLUE, "#0d3a73"])
    tmin = req.t_request_s / 60

    lat = np.r_[req.o_lat, req.d_lat, fleet.lat]
    lon = np.r_[req.o_lon, req.d_lon, fleet.lon]
    pad_lat = 0.004
    south, north = lat.min() - pad_lat, lat.max() + pad_lat
    fig = plt.figure(figsize=(7.6, 11.2))
    box = [0.03, 0.2, 0.94, 0.72]
    # widen the longitude span so the map fills its frame (Web Mercator x is linear in lon)
    (_, y0), (_, y1) = basemap.merc(south, 0), basemap.merc(north, 0)
    half_w = (y1 - y0) * (box[2] * 7.6) / (box[3] * 11.2) / 2
    cx = float(np.mean(basemap.merc(lat, lon)[0][[lon.argmin(), lon.argmax()]]))
    west, east = np.degrees((cx - half_w) / basemap.R), np.degrees((cx + half_w) / basemap.R)
    ax = fig.add_axes(box)
    basemap.draw(ax, south, west, north, east, z=14)
    ox, oy = basemap.merc(req.o_lat, req.o_lon)
    dx, dy = basemap.merc(req.d_lat, req.d_lon)
    # road routes from the local OSRM (travel_times_v2.py); no straight-line fallback
    routes = {f["properties"]["request_id"]: np.array(f["geometry"]["coordinates"])
              for f in json.loads((ROOT / "data" / "processed" / "routes_M_v2.geojson").read_text())["features"]}
    for i in np.argsort(-tmin.to_numpy()):            # late requests first, so early (light) ones stay visible
        c = cmap(tmin.iloc[i] / 60)
        rx, ry = basemap.merc(routes[req.request_id.iloc[i]][:, 1], routes[req.request_id.iloc[i]][:, 0])
        ax.plot(rx, ry, color=c, lw=1.3, alpha=0.75, zorder=2, solid_capstyle="round", solid_joinstyle="round")
        ax.scatter(dx[i], dy[i], s=10, color=c, zorder=2.5, linewidths=0)
        ax.scatter(ox[i], oy[i], s=58, color=c, edgecolors=SURFACE, linewidths=1.5, zorder=3)
    vx, vy = basemap.merc(fleet.lat, fleet.lon)
    ax.scatter(vx, vy, s=120, marker="s", color=ORANGE, edgecolors=SURFACE, linewidths=2, zorder=4)

    handles = [Line2D([0, 1], [0, 0], color=BLUE, lw=1.3, marker="o", ms=7, mfc=BLUE, mec=SURFACE, markevery=[0],
                      label="Request: dot = pickup, line = to drop-off;\ncolor = minutes after 18:00"),
               Line2D([], [], ls="", marker="s", ms=9, mfc=ORANGE, mec=SURFACE, mew=2, label="Van start (5)")]
    leg = ax.legend(handles=handles, loc="lower left", frameon=True, fontsize=9, borderpad=0.7, handlelength=2.4)
    leg.get_frame().set(facecolor=SURFACE, edgecolor=GRID, alpha=0.95)
    cax = ax.inset_axes([0.035, 0.115, 0.3, 0.013])
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 60)), cax=cax, orientation="horizontal")
    cb.set_ticks([0, 30, 60], labels=["0", "30", "60 min"]); cb.outline.set_visible(False)
    cax.tick_params(labelsize=8, colors=MUTED, length=0, labelcolor=INK2)

    st = fig.add_axes([0.09, 0.135, 0.82, 0.035])
    for t in tmin:
        st.axvline(t, ymin=0.1, ymax=0.9, color=cmap(t / 60), lw=2)
    st.set_xlim(0, 60); st.set_ylim(0, 1); st.set_yticks([]); st.grid(False)
    st.set_xticks([0, 60], ["18:00", "19:00"])
    for sname in ("left", "right", "top"):
        st.spines[sname].set_visible(False)
    st.spines["bottom"].set_color(AXIS)
    st.text(30, 1.15, "one tick per request", ha="center", va="bottom", fontsize=8.5, color=MUTED, transform=st.transData)

    card = (f"{summ['vans']} vans  ·  {summ['requests']} requests ({summ['passengers']} riders)  ·  "
            f"{summ['rho_requests_per_van_hour']:g} requests per van-hour  ·  {p['capacity']} seats  ·  seed {p['master_seed']}")
    assert card == "5 vans  ·  30 requests (37 riders)  ·  6 requests per van-hour  ·  4 seats  ·  seed 20261001", card
    fig.text(0.5, 0.075, card, ha="center", fontsize=10, color=INK)
    fig.text(0.03, 0.955, "Scenario M: one synthetic 6 pm hour", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.03, 0.03, "Synthetic, drawn from April's map totals. Not a replay of any real night.", fontsize=8.5, color=MUTED)
    fig.text(0.97, 0.03, "Map data and routes © OpenStreetMap contributors", fontsize=7.5, color=MUTED, ha="right")  # ODbL
    path = OUT / "scenario_b_M_card.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


if __name__ == "__main__":
    style()
    for f in (fig_a, fig_b):
        print(f())
