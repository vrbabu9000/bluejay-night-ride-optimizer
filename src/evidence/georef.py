"""
Georeference the four O/D map screenshots (pp. 2-5) and place every bubble in lat/lon.

The screenshots come in two views. p02/p03 share one city-wide view, with p03
offset by (+4, -5) px. p04/p05 share one campus view, with p05 offset by
(-2, +1) px. Both offsets were measured by aligning the map backgrounds with the
bubbles masked out. Google Maps is Web Mercator and north-up at a fixed zoom, so
pixel = s * (mercator - origin) with one scale s and two offsets. That fit uses
ground-control points: the tips of labelled POI pins, geocoded with OpenStreetMap
Nominatim (cached in data/processed/gcp_geocode_cache.json).

Outputs: data/processed/georef_fit.json (fit, residuals) and
data/processed/map_bubbles_geo.csv (bubble lat/lon with position uncertainty).
Run: .venv/bin/python src/evidence/georef.py
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "april"
PROCESSED = ROOT / "data" / "processed"
R_EARTH = 6378137.0

VIEWS = {"city": {"base": 2, "offsets": {2: (0, 0), 3: (4, -5)}},
         "campus": {"base": 4, "offsets": {4: (0, 0), 5: (-2, 1)}}}

# Approximate pin-circle centres in base-page pixels, measured on zoomed crops.
# kind: 'gray' POI pin or 'green' place pin; occluded: pin tip hidden by a bubble.
# Corrections from the two-reader reconciliation (docs/evidence/map_count_reconciliation.md):
# p04_b075's detection spanned two touching discs; its own disc ("222") sits at (494, 601),
# and the second, edge-cut disc is added as p04_extra_1.
POSITION_FIX = {"p04_b075": (494.0, 601.0)}
EXTRA_BUBBLES = [dict(map_page=4, map_name="origins_campus", bubble_id="p04_extra_1", colour="red", digits_expected=3,
                      px_x=536.0, px_y=605.0, disc_px_near=0, source="extra (reader reconciliation)", near_edge=True)]

GCPS = {
    "city": [
        ("shoprite_howard_park", (238.5, 221.5), "gray", False),
        ("md_zoo", (504.5, 279.5), "gray", False),
        ("mondawmin_mall", (476.5, 321.5), "gray", False),
        ("oriole_park", (667.5, 574.5), "gray", False),
        ("clifton_golf", (865.5, 286.5), "gray", False),
        ("coppin_state", (457.0, 356.0), "gray", False),
        ("morgan_state", (886.0, 121.0), "gray", False),
    ],
    "campus": [
        ("wicked_sisters", (188.0, 190.0), "gray", True),
        ("cosima", (312.5, 560.5), "gray", False),
        ("red_emmas", (796.0, 442.0), "gray", False),
        ("weinberg_ymca", (968.0, 387.0), "green", False),
        ("peabody_heights_brewery", (782.0, 517.0), "gray", True),
    ],
}


def mercator(lat, lon):
    x = R_EARTH * math.radians(lon)
    y = R_EARTH * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def inv_mercator(x, y):
    lon = math.degrees(x / R_EARTH)
    lat = math.degrees(2 * math.atan(math.exp(y / R_EARTH)) - math.pi / 2)
    return lat, lon


def pin_tip(img, approx, kind, occluded, tip_offset=None, win=16):
    """Pin tip (the pin's geographic anchor) near an approximate circle centre."""
    x0, y0 = int(approx[0]) - win, int(approx[1]) - win
    patch = img[y0:y0 + 2 * win + 14, x0:x0 + 2 * win].astype(int)
    r, g, b = patch[..., 0], patch[..., 1], patch[..., 2]
    if kind == "green":
        fill = (g > r + 30) & (g > b + 40)
    else:
        fill = (np.abs(r - g) < 20) & (np.abs(g - b) < 22) & (r >= 95) & (r <= 175)
    labels, n = ndimage.label(fill)
    if n == 0:
        return None
    cy, cx = win, win
    k = min(range(1, n + 1), key=lambda i: np.hypot(*(np.array(ndimage.center_of_mass(labels == i)) - (cy, cx))))
    ys, xs = np.where(labels == k)
    width = xs.max() - xs.min() + 1
    top = ys.min()
    xc = (xs.min() + xs.max()) / 2
    if occluded:
        centre_y = top + width / 2
        return x0 + xc, y0 + centre_y + tip_offset, width, "tip = circle centre + measured offset"
    return x0 + xc, y0 + ys.max() + 1, width, "tip = lowest fill pixel"


def fit_offsets(points, s, weights):
    """Offsets only, for a known scale s (weighted means of X - px/s and Y + py/s)."""
    w = np.asarray(weights, float)
    X0 = float(np.average([X - px / s for (px, py), (X, Y) in points], weights=w))
    Y0 = float(np.average([Y + py / s for (px, py), (X, Y) in points], weights=w))
    return s, X0, Y0


def geocode_sigma_m(result):
    """Rough 1-sigma of a geocoded point as a pin anchor: a quarter of the OSM
    feature's bounding-box diagonal (large parks and campuses geocode to a
    centroid, not to where Google puts the pin), with a 30 m floor."""
    bb = [float(v) for v in result.get("boundingbox") or []]
    if len(bb) != 4:
        return 30.0
    dy = (bb[1] - bb[0]) * 111_320
    dx = (bb[3] - bb[2]) * 111_320 * math.cos(math.radians((bb[0] + bb[1]) / 2))
    return max(30.0, math.hypot(dx, dy) / 4)


def fit(points):
    """Least squares for px = s*(X - X0), py = s*(Y0 - Y) (north-up Web Mercator)."""
    A, rhs = [], []
    for (px, py), (X, Y) in points:
        A.append([X, -1, 0]); rhs.append(px)      # px = s*X - s*X0
        A.append([-Y, 0, 1]); rhs.append(py)      # py = -s*Y + s*Y0
    sol, *_ = np.linalg.lstsq(np.array(A, float), np.array(rhs, float), rcond=None)
    s, sX0, sY0 = sol
    return s, sX0 / s, sY0 / s


def main():
    cache = json.load(open(PROCESSED / "gcp_geocode_cache.json"))
    fits = {}
    for view in ("campus", "city"):  # campus first: its scale fixes the city scale
        spec = VIEWS[view]
        img = np.array(Image.open(RAW / f"p{spec['base']:02d}.png").convert("RGB"))
        # measured tip offset below the circle centre for unoccluded gray pins in this view
        offs = []
        for name, approx, kind, occ in GCPS[view]:
            if not occ and kind == "gray":
                tx, ty, w, _ = pin_tip(img, approx, kind, False)
                top_centre = ty - 1 - (approx[1] - (approx[1] - w / 2))  # placeholder, refined below
                offs.append((name, tx, ty, w))
        tip_offset = None
        rows = []
        for name, approx, kind, occ in GCPS[view]:
            if occ and tip_offset is None:
                # offset = tip - circle centre, averaged over unoccluded gray pins
                deltas = []
                for n2, a2, k2, o2 in GCPS[view]:
                    if o2 or k2 != "gray":
                        continue
                    x0, y0 = int(a2[0]) - 16, int(a2[1]) - 16
                    patch = img[y0:y0 + 46, x0:x0 + 32].astype(int)
                    r, g, b = patch[..., 0], patch[..., 1], patch[..., 2]
                    fill = (np.abs(r - g) < 20) & (np.abs(g - b) < 22) & (r >= 95) & (r <= 175)
                    lab, n = ndimage.label(fill)
                    k = min(range(1, n + 1), key=lambda i: np.hypot(*(np.array(ndimage.center_of_mass(lab == i)) - (16, 16))))
                    ys, xs = np.where(lab == k)
                    width = xs.max() - xs.min() + 1
                    deltas.append((ys.max() + 1) - (ys.min() + width / 2))
                tip_offset = float(np.median(deltas))
            tip = pin_tip(img, approx, kind, occ, tip_offset)
            geo = cache[name]["results"][0]
            lat, lon = float(geo["lat"]), float(geo["lon"])
            rows.append(dict(view=view, gcp=name, px=tip[0], py=tip[1], pin_width=tip[2], how=tip[3], lat=lat, lon=lon,
                             sigma_m=round(geocode_sigma_m(geo), 0),
                             osm_type=geo.get("type"), osm_name=geo.get("display_name", "")[:60]))
        df = pd.DataFrame(rows)
        pts = [((r.px, r.py), mercator(r.lat, r.lon)) for r in df.itertuples()]
        s_free, _, _ = fit(pts)
        if view == "city":
            # The city view is two Google zoom levels out from the campus view (free fits
            # give a scale ratio of 4.04), so the scale is fixed at campus/4 and only the
            # offsets are fitted; this limits the damage from large-area POIs.
            s, X0, Y0 = fit_offsets(pts, fits["campus"]["scale_px_per_merc_m"] / 4, 1 / df.sigma_m ** 2)
        else:
            s, X0, Y0 = fit(pts)
        cos_lat = math.cos(math.radians(df.lat.mean()))
        df["resid_x_m"] = [(r.px - s * (X - X0)) / s * cos_lat for r, (_, (X, Y)) in zip(df.itertuples(), pts)]
        df["resid_y_m"] = [(r.py - s * (Y0 - Y)) / s * cos_lat for r, (_, (X, Y)) in zip(df.itertuples(), pts)]
        df["resid_m"] = np.hypot(df.resid_x_m, df.resid_y_m)
        wrms = float(np.sqrt(np.average(df.resid_m ** 2, weights=1 / df.sigma_m ** 2)))
        fits[view] = dict(scale_px_per_merc_m=s, free_fit_scale=s_free, weighted_rms_resid_m=wrms, X0=X0, Y0=Y0, ground_m_per_px=cos_lat / s, tip_offset_px=tip_offset,
                          rms_resid_m=float(np.sqrt((df.resid_m ** 2).mean())), gcps=df.round(6).to_dict("records"))
        print(f"\n[{view}] ground {cos_lat / s:.2f} m/px; RMS residual {fits[view]['rms_resid_m']:.0f} m "
              f"(weighted {wrms:.0f} m); tip offset {tip_offset}")
        print(df[["gcp", "px", "py", "osm_type", "sigma_m", "resid_x_m", "resid_y_m", "resid_m"]].round(1).to_string(index=False))
    json.dump(fits, open(PROCESSED / "georef_fit.json", "w"), indent=1)

    bub = pd.read_csv(PROCESSED / "map_bubbles.csv")
    for bid, (x, y) in POSITION_FIX.items():
        bub.loc[bub.bubble_id == bid, ["px_x", "px_y"]] = (x, y)
    bub = pd.concat([bub, pd.DataFrame(EXTRA_BUBBLES)], ignore_index=True)
    out = []
    for r in bub.itertuples():
        view = "city" if r.map_page in (2, 3) else "campus"
        f = fits[view]
        dx, dy = VIEWS[view]["offsets"][r.map_page]
        bx, by = r.px_x - dx, r.px_y - dy  # into base-page pixels
        lat, lon = inv_mercator(bx / f["scale_px_per_merc_m"] + f["X0"], f["Y0"] - by / f["scale_px_per_merc_m"])
        out.append(dict(bubble_id=r.bubble_id, view=view, lat=round(lat, 6), lon=round(lon, 6),
                        pos_uncertainty_m=round(f["weighted_rms_resid_m"] + 3 * f["ground_m_per_px"], 0)))
    geo = bub.merge(pd.DataFrame(out), on="bubble_id")
    geo.to_csv(PROCESSED / "map_bubbles_geo.csv", index=False)
    print("\nwrote", PROCESSED / "map_bubbles_geo.csv", len(geo))


if __name__ == "__main__":
    main()
