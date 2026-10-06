"""
Zones v0: a coarse zone system built from the digitized O/D bubbles.

Point set: campus-view bubbles (finer; inside the campus frame) plus city-view
bubbles outside the campus frame, so no ride is counted twice. Zones are formed
by count-weighted k-means on origin and destination points together (so O and D
share zones), seeded deterministically from the heaviest points. Each zone gets
its April origin and destination margins (completed rides, with bounds from
partial/cut bubbles).

Outputs: data/processed/zones_v0.csv, data/processed/zone_points_v0.csv
Run: .venv/bin/python src/scenario/zones.py
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
K = 16
LAT0 = 39.32
# Readable names from reverse-geocoding the centroids (OSM Nominatim, 2026-09-29) plus local knowledge.
# The seeding is deterministic, so ids are stable across reruns; names are re-checked by hand if the ids move.
NAMES = {"Z01": "Remington (W 28th St)", "Z02": "Charles Village (E 33rd St)", "Z03": "Mount Vernon",
         "Z04": "Midtown-Belvedere / Penn Station", "Z05": "Tuscany-Canterbury (University Pkwy)",
         "Z06": "Hampden (W 38th St)", "Z07": "Charles North / Station North", "Z08": "Homewood campus (Bowman Dr)",
         "Z09": "Inner Harbor", "Z10": "Hampden north (W 41st St)", "Z11": "Downtown (W Baltimore St)",
         "Z12": "Charles Village south (Calvert St)", "Z13": "Hampden (Roland Ave)", "Z14": "Woodberry / Hampden west",
         "Z15": "Wyman Park / Keswick Rd", "Z16": "Abell / Waverly (E 33rd St)"}


def to_xy(lat, lon):
    return (np.asarray(lon) + 76.62) * 111_320 * math.cos(math.radians(LAT0)), (np.asarray(lat) - LAT0) * 111_320


def campus_frame():
    import sys
    sys.path.insert(0, str(ROOT / "src" / "evidence"))
    from georef import inv_mercator
    f = json.load(open(PROCESSED / "georef_fit.json"))["campus"]
    s = f["scale_px_per_merc_m"]
    north, west = inv_mercator(2 / s + f["X0"], f["Y0"] - 105 / s)
    south, east = inv_mercator(1040 / s + f["X0"], f["Y0"] - 610 / s)
    return south, north, west, east


def point_set():
    c = pd.read_csv(PROCESSED / "map_clusters.csv")
    south, north, west, east = campus_frame()
    inside = c.lat.between(south, north) & c.lon.between(west, east)
    keep = (c.view == "campus") | ((c.view == "city") & ~inside)
    pts = c[keep].copy()
    pts["endpoint"] = np.where(pts.map_name.str.startswith("origins"), "O", "D")
    pts["lower"] = pts.lower.fillna(pts.count_best)
    pts["upper"] = pts.upper.fillna(pts.count_best)
    # Cut/hidden bubbles enter at their lower bound, then each endpoint is scaled so
    # that O and D each sum to the reconciled city total (the city-map "fence", ~24,056).
    pts["count_used"] = pts.count_read.fillna(pts.lower).astype(float)
    fence = c[c.map_name == "origins_city"].count_best.sum()
    for ep in ("O", "D"):
        sel = pts.endpoint == ep
        pts.loc[sel, "scale_to_fence"] = fence / pts.loc[sel, "count_used"].sum()
        pts.loc[sel, "count_used"] *= pts.loc[sel, "scale_to_fence"]
    return pts


def weighted_kmeans(x, y, w, k, iters=100):
    order = np.argsort(-w)
    cx, cy = [x[order[0]]], [y[order[0]]]
    for i in order[1:]:  # heaviest points that are >= 500 m from existing seeds
        if len(cx) == k:
            break
        if min(math.hypot(x[i] - a, y[i] - b) for a, b in zip(cx, cy)) >= 500:
            cx.append(x[i]); cy.append(y[i])
    cx, cy = np.array(cx), np.array(cy)
    for _ in range(iters):
        d = (x[:, None] - cx[None]) ** 2 + (y[:, None] - cy[None]) ** 2
        lab = d.argmin(1)
        nx = np.array([np.average(x[lab == j], weights=w[lab == j]) for j in range(len(cx))])
        ny = np.array([np.average(y[lab == j], weights=w[lab == j]) for j in range(len(cx))])
        if np.allclose(nx, cx) and np.allclose(ny, cy):
            break
        cx, cy = nx, ny
    return lab, cx, cy


def main():
    pts = point_set()
    x, y = to_xy(pts.lat.values, pts.lon.values)
    lab, cx, cy = weighted_kmeans(x, y, pts.count_used.values, K)
    print("scale to fence: O %.4f, D %.4f" % tuple(pts.groupby("endpoint").scale_to_fence.first()[["O", "D"]]))
    pts["zone_id"] = [f"Z{j + 1:02d}" for j in lab]
    pts.to_csv(PROCESSED / "zone_points_v0.csv", index=False)
    rows = []
    for j in range(len(cx)):
        z = pts[lab == j]
        lat = LAT0 + cy[j] / 111_320
        lon = -76.62 + cx[j] / (111_320 * math.cos(math.radians(LAT0)))
        spread = float(np.sqrt(np.average((x[lab == j] - cx[j]) ** 2 + (y[lab == j] - cy[j]) ** 2, weights=z.count_used)))
        o, d = z[z.endpoint == "O"], z[z.endpoint == "D"]
        rows.append(dict(zone_id=f"Z{j + 1:02d}", lat=round(lat, 6), lon=round(lon, 6), radius_m=round(spread),
                         n_points=len(z), origins=round(o.count_used.sum()), origins_lower=int(o.lower.sum()),
                         origins_upper=int(o.upper.sum()), destinations=round(d.count_used.sum()),
                         destinations_lower=int(d.lower.sum()), destinations_upper=int(d.upper.sum())))
    zones = pd.DataFrame(rows)
    zones["net_d_minus_o"] = zones.destinations - zones.origins
    zones.insert(1, "zone_name", zones.zone_id.map(NAMES))
    zones = zones.sort_values("origins", ascending=False)
    zones.to_csv(PROCESSED / "zones_v0.csv", index=False)
    print(zones.to_string(index=False))
    print("totals: O", zones.origins.sum(), "D", zones.destinations.sum())


if __name__ == "__main__":
    main()
