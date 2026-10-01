"""
T8: O-D structure. Where do April's completed rides start and end, and which
zones are net sources (more pickups) or net sinks (more drop-offs)?

Input: data/processed/zones_v0.csv (zone margins built from the digitized
maps, scaled to the ~24,056 completed-ride city-map fence).
Outputs: outputs/insights/t08a_od_by_zone.png, t08b_net_flow_map.png,
         outputs/insights/t08_zone_table.csv, docs/evidence/insights/t08.md
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import basemap
from common import (BLUE, GRAY, INK, INK2, MUTED, ORANGE, PROCESSED, FIGS, SURFACE, marker_kw, save,
                    source, style, subtitle, write_brief)

CORRIDOR = {"Z03", "Z04", "Z07", "Z09", "Z11"}  # Mount Vernon, Midtown, Station North, Inner Harbor, Downtown


def main():
    style()
    z = pd.read_csv(PROCESSED / "zones_v0.csv")
    z["total"] = z.origins + z.destinations
    z["group"] = np.where(z.zone_id.isin(CORRIDOR), "Charles St corridor / downtown", "Homewood area")
    z = z.sort_values("total")
    z.to_csv(FIGS / "t08_zone_table.csv", index=False) if FIGS.exists() else None

    # --- T8a: dumbbell, origins vs destinations per zone
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    y = np.arange(len(z))
    for yi, r in zip(y, z.itertuples()):
        ax.plot([r.origins, r.destinations], [yi, yi], color=GRAY, lw=2, zorder=1)
    ax.plot(z.origins, y, ls="none", zorder=3, **marker_kw(BLUE, 9))
    ax.plot(z.destinations, y, ls="none", zorder=3, **marker_kw(ORANGE, 9))
    ax.set_yticks(y, z.zone_name)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Completed rides, April 2026")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_title("Campus is a net source; University Pkwy and Remington are net sinks")
    subtitle(ax, "Pickups (origins) vs drop-offs (destinations) per zone, from the digitized density maps")
    for r, yi in zip(z.itertuples(), y):
        if abs(r.net_d_minus_o) >= 1000:
            x = max(r.origins, r.destinations)
            ax.text(x + 120, yi, f"{r.net_d_minus_o:+,}", va="center", fontsize=9, color=INK2)
    ax.legend(handles=[Line2D([], [], ls="none", **marker_kw(BLUE, 9), label="Origins (pickups)"),
                       Line2D([], [], ls="none", **marker_kw(ORANGE, 9), label="Destinations (drop-offs)")],
              loc="lower right")
    source(fig, "Source: TransLoc April 2026 origin/destination density maps (pp. 2-5), digitized; zones v0 (16), "
                "margins scaled to ~24,056 completed rides. Labels: net drop-offs minus pickups.")
    save(fig, "t08a_od_by_zone")

    # --- T8b: net-flow map, circle area = total volume, colour = net source/sink
    fig, ax = plt.subplots(figsize=(6.4, 8.2))
    basemap.draw(ax, 39.282, -76.652, 39.343, -76.596, z=14)
    mx, my = basemap.merc(z.lat.values, z.lon.values)
    lim = 2100
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#2a78d6"])
    sc = ax.scatter(mx, my, s=z.total / 12, c=z.net_d_minus_o, cmap=cmap, vmin=-lim, vmax=lim,
                    edgecolors=SURFACE, linewidths=2, zorder=3, alpha=0.95)
    for r, xx, yy in zip(z.itertuples(), mx, my):
        if r.total >= 2400 or abs(r.net_d_minus_o) >= 1000:
            off, ha = {"Z08": ((-12, -4), "right"), "Z02": ((14, 8), "left")}.get(r.zone_id, ((9, 6), "left"))
            ax.annotate(r.zone_name.split(" (")[0], (xx, yy), xytext=off, textcoords="offset points",
                        fontsize=8.5, color=INK, zorder=4, ha=ha)
    ax.set_title("Net flow by zone: blue = more drop-offs, red = more pickups")
    cb = fig.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.035, pad=0.02)
    cb.set_label("Drop-offs minus pickups (April)", color=INK2); cb.outline.set_visible(False)
    for v in (1000, 5000, 10000):
        ax.scatter([], [], s=v / 12, color=GRAY, edgecolors=SURFACE, label=f"{v:,} rides")
    ax.legend(loc="lower left", title="Circle area = pickups + drop-offs", title_fontsize=8.5, fontsize=8.5,
              labelspacing=1.4, borderpad=1.0)
    source(fig, "Basemap © OpenStreetMap contributors. Zones v0 from digitized TransLoc maps.")
    save(fig, "t08b_net_flow_map")

    homewood = z[z.group == "Homewood area"]
    corridor = z[z.group != "Homewood area"]
    fence = z.origins.sum()
    body = f"""
**Question.** Where do April's completed rides start and end, and which zones are net sources or sinks?

**Answer (DERIVED from OBSERVED map counts).**
- About **{homewood.origins.sum() / fence:.0%} of pickups and {homewood.destinations.sum() / fence:.0%} of drop-offs** are in the Homewood area. The rest are on the Charles St corridor down to downtown (Mount Vernon, Midtown/Penn Station, Station North, Inner Harbor, downtown). That corridor is almost balanced ({corridor.origins.sum():,} pickups vs {corridor.destinations.sum():,} drop-offs).
- **Net sources** (more pickups than drop-offs): the Homewood campus core ({int(z.set_index('zone_id').loc['Z08','net_d_minus_o']):+,}) and the Charles St / E 33rd St corner of Charles Village ({int(z.set_index('zone_id').loc['Z02','net_d_minus_o']):+,}).
- **Net sinks**: Tuscany-Canterbury / University Pkwy ({int(z.set_index('zone_id').loc['Z05','net_d_minus_o']):+,}) and Remington ({int(z.set_index('zone_id').loc['Z01','net_d_minus_o']):+,}).
- **Reading:** the van is used mostly one way, from campus and the library corner toward residential areas. A plausible reason is that riders walk or take other modes in the other direction during the day. That reason is a hypothesis; the data cannot show it.

**Evidence.** Every bubble on the four maps was read (city maps: O 24,056 and D 24,057, two independent readers agreeing on 214 of 215 bubbles; campus maps reconcile with the city bubbles inside the campus frame to within about 2-4%). Zones are count-weighted clusters of bubble positions (16 zones, v0). Margins are scaled to the 24,057 fence (factors: O 1.020, D 0.986).

**What it cannot tell us.**
- Direction by hour. The maps are monthly totals, so a 6 PM campus-outbound pattern is ASSUMED, not shown.
- Where the ~24k cancelled requests came from. The maps show served trips only.
- Individual O-D pairs. Only the margins are observed, and the joint table comes from the generator (Phase 3).
- Exact locations: bubble positions are cluster centres (±15-60 m georeference error, plus clustering), so the conclusions hold at zone level only.

**Used by.** Scenario generator margins (Phase 3), the base-scenario hotspots (A4), T6.

Figures: `outputs/insights/t08a_od_by_zone.png`, `outputs/insights/t08b_net_flow_map.png`. Table: `outputs/insights/t08_zone_table.csv`.
"""
    write_brief("t08", "O-D structure", body)
    z.to_csv(FIGS / "t08_zone_table.csv", index=False)
    print(z[["zone_id", "zone_name", "origins", "destinations", "net_d_minus_o", "group"]].to_string(index=False))
    print(body)


if __name__ == "__main__":
    main()
