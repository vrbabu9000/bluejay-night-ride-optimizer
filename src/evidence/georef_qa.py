"""
Visual QA for the map georeference: re-project OpenStreetMap tiles into each
screenshot's pixel grid with the fitted transform and blend them. Aligned
streets mean the fit is right; doubled streets show the size of the error.

Tiles are cached under data/raw/osm_tiles/ (light use, per the OSM tile policy).
Run: .venv/bin/python src/evidence/georef_qa.py
"""
import io
import json
import math
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

from georef import PROCESSED, RAW, ROOT, VIEWS, inv_mercator

TILES = ROOT / "data" / "raw" / "osm_tiles"
OUT = ROOT / "outputs" / "evidence"
UA = {"User-Agent": "bluejay-course-project-digitizer/0.1"}
ZOOM = {"city": 14, "campus": 16}


def tile(z, x, y):
    path = TILES / f"{z}_{x}_{y}.png"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            path.write_bytes(r.read())
        time.sleep(0.2)
    return Image.open(path).convert("RGB")


def world_px(lat, lon, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def main():
    fits = json.load(open(PROCESSED / "georef_fit.json"))
    for view, spec in VIEWS.items():
        f, z = fits[view], ZOOM[view]
        base = Image.open(RAW / f"p{spec['base']:02d}.png").convert("RGB")
        w, h = base.size
        s = f["scale_px_per_merc_m"]
        # lat/lon of every screenshot pixel (row/col separable in Web Mercator)
        cols = [inv_mercator(c / s + f["X0"], f["Y0"])[1] for c in range(w)]
        rows = [inv_mercator(f["X0"], f["Y0"] - r / s)[0] for r in range(h)]
        wx = np.array([world_px(rows[0], lon, z)[0] for lon in cols])
        wy = np.array([world_px(lat, cols[0], z)[1] for lat in rows])
        tx0, tx1 = int(wx.min() // 256), int(wx.max() // 256)
        ty0, ty1 = int(wy.min() // 256), int(wy.max() // 256)
        mosaic = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                mosaic.paste(tile(z, tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
        m = np.array(mosaic)
        xi = np.clip((wx - tx0 * 256).astype(int), 0, m.shape[1] - 1)
        yi = np.clip((wy - ty0 * 256).astype(int), 0, m.shape[0] - 1)
        osm = m[yi][:, xi]
        blend = (0.55 * np.array(base, float) + 0.45 * osm).astype(np.uint8)
        blend[:104] = np.array(base)[:104]
        OUT.mkdir(parents=True, exist_ok=True)
        Image.fromarray(blend).save(OUT / f"georef_qa_{view}.png")
        print(view, "tiles", (tx1 - tx0 + 1) * (ty1 - ty0 + 1), "->", OUT / f"georef_qa_{view}.png")


if __name__ == "__main__":
    main()
