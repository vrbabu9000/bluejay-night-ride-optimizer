"""
Digital version of the four O/D density maps: every bubble placed at its
georeferenced position, sized by its count, with the original screenshots as
georeferenced overlays (opacity slider) for visual QA.

Inputs:  data/processed/map_bubbles_geo.csv, data/processed/map_counts_final.csv
         (falls back to map_counts_readerA.csv), data/processed/georef_fit.json
Outputs: data/processed/map_clusters.csv, data/processed/map_clusters.geojson,
         outputs/evidence/od_maps.html
Run: .venv/bin/python src/evidence/od_maps.py
"""
import base64
import io
import json
from pathlib import Path

import folium
import pandas as pd
from branca.element import Element
from PIL import Image

from georef import PROCESSED, RAW, ROOT, VIEWS, inv_mercator

OUT = ROOT / "outputs" / "evidence"
MAP_TOP = 104
LAYERS = {
    "origins_city": ("Origins, city view (p2)", "#1f5fbf"),
    "destinations_city": ("Destinations, city view (p3)", "#d9480f"),
    "origins_campus": ("Origins, campus view (p4)", "#1f5fbf"),
    "destinations_campus": ("Destinations, campus view (p5)", "#d9480f"),
}


def load_clusters():
    geo = pd.read_csv(PROCESSED / "map_bubbles_geo.csv")
    final = PROCESSED / "map_counts_final.csv"
    counts = pd.read_csv(final if final.exists() else PROCESSED / "map_counts_readerA.csv")
    df = geo.merge(counts, on="bubble_id", how="left")
    df = df[df.status != "not_a_bubble"].copy()
    df["count_best"] = df.count_read.fillna((df.lower + df.upper) / 2)
    df["count_source"] = df.status.map(lambda s: "read" if s == "ok" else "partial/bounds")
    return df


def screenshot_overlay(page, fits):
    view = "city" if page in (2, 3) else "campus"
    f = fits[view]
    dx, dy = VIEWS[view]["offsets"][page]
    img = Image.open(RAW / f"p{page:02d}.png").convert("RGB")
    w, h = img.size
    img = img.crop((0, MAP_TOP, w, h))
    s = f["scale_px_per_merc_m"]
    (x0, y0), (x1, y1) = (0 - dx, MAP_TOP - dy), (w - dx, h - dy)
    north, west = inv_mercator(x0 / s + f["X0"], f["Y0"] - y0 / s)
    south, east = inv_mercator(x1 / s + f["X0"], f["Y0"] - y1 / s)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), [[south, west], [north, east]]


def main():
    fits = json.load(open(PROCESSED / "georef_fit.json"))
    df = load_clusters()
    cols = ["bubble_id", "map_page", "map_name", "view", "colour", "digits_expected", "px_x", "px_y", "lat", "lon",
            "pos_uncertainty_m", "count_read", "lower", "upper", "count_best", "count_source", "confidence", "status", "notes"]
    df[cols].to_csv(PROCESSED / "map_clusters.csv", index=False)
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
              "properties": {c: (None if pd.isna(getattr(r, c)) else getattr(r, c)) for c in cols if c not in ("lat", "lon")}}
             for r in df[cols].itertuples()]
    json.dump({"type": "FeatureCollection", "features": feats}, open(PROCESSED / "map_clusters.geojson", "w"), default=str)

    m = folium.Map(location=[39.318, -76.620], zoom_start=13, tiles="OpenStreetMap", control_scale=True)
    for page in (2, 3, 4, 5):
        uri, bounds = screenshot_overlay(page, fits)
        name = f"Original screenshot p{page}"
        folium.raster_layers.ImageOverlay(uri, bounds=bounds, opacity=0.55, name=name, show=(page == 4),
                                          class_name="shot").add_to(m)
    for key, (label, colour) in LAYERS.items():
        fg = folium.FeatureGroup(name=f"{label}: {int(df[df.map_name == key].count_best.sum()):,} rides",
                                 show=key in ("origins_campus",))
        for r in df[df.map_name == key].itertuples():
            radius = 3 + 0.9 * r.count_best ** 0.5 * (0.5 if r.view == "city" else 1.0)
            dash = None if r.status == "ok" else "4 3"
            tip = (f"<b>{r.bubble_id}</b><br>count: {'' if pd.isna(r.count_read) else int(r.count_read)} "
                   f"[{'' if pd.isna(r.lower) else int(r.lower)}-{'' if pd.isna(r.upper) else int(r.upper)}]"
                   f"<br>status: {r.status} ({r.confidence})<br>±{int(r.pos_uncertainty_m)} m"
                   + (f"<br>{r.notes}" if isinstance(r.notes, str) and r.notes else ""))
            folium.CircleMarker([r.lat, r.lon], radius=radius, color=colour, weight=1.5, dash_array=dash,
                                fill=True, fill_opacity=0.35, tooltip=tip).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(Element("""
<div style="position:fixed;bottom:18px;left:12px;z-index:9999;background:white;padding:8px 10px;border-radius:6px;
font:12px sans-serif;box-shadow:0 1px 4px rgba(0,0,0,.3)">
<b>April 2026 O/D density maps, digitized</b><br>Circle area ~ monthly completed rides; dashed = partial/cut bubble<br>
Screenshot opacity <input type="range" min="0" max="100" value="55"
 oninput="document.querySelectorAll('.shot').forEach(e=>e.style.opacity=this.value/100)">
</div>"""))
    OUT.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT / "od_maps.html"))
    print(df.groupby("map_name").agg(bubbles=("bubble_id", "size"), rides=("count_best", "sum")).round(0))
    print("wrote", OUT / "od_maps.html")


if __name__ == "__main__":
    main()
