"""
Quiet OpenStreetMap basemap for static figures, in Web Mercator metres.
Tiles are cached in data/raw/osm_tiles (shared with the georeference QA).
"""
import math
import time
import urllib.request

import numpy as np
from PIL import Image

from common import ROOT

TILES = ROOT / "data" / "raw" / "osm_tiles"
UA = {"User-Agent": "bluejay-course-project/0.1"}
R = 6378137.0


def merc(lat, lon):
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    return R * np.radians(lon), R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def _tile(z, x, y):
    path = TILES / f"{z}_{x}_{y}.png"
    if not path.exists():
        TILES.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            path.write_bytes(r.read())
        time.sleep(0.2)
    return Image.open(path).convert("RGB")


def draw(ax, south, west, north, east, z=14, fade=0.62):
    """Draw faded, desaturated tiles covering the bbox; axes in Web Mercator metres."""
    n = 2 ** z
    def tx(lon): return int((lon + 180) / 360 * n)
    def ty(lat): return int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    x0, x1, y0, y1 = tx(west), tx(east), ty(north), ty(south)
    mosaic = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            mosaic.paste(_tile(z, x, y), ((x - x0) * 256, (y - y0) * 256))
    a = np.asarray(mosaic, float)
    gray = a.mean(axis=2, keepdims=True)
    a = (0.35 * a + 0.65 * gray)            # desaturate
    a = a + (255 - a) * fade                  # fade toward white
    span = 2 * math.pi * R / n
    left, top = -math.pi * R + x0 * span, math.pi * R - y0 * span
    ax.imshow(a.astype(np.uint8), extent=[left, left + (x1 - x0 + 1) * span, top - (y1 - y0 + 1) * span, top],
              interpolation="bilinear", zorder=0)
    (xa, ya), (xb, yb) = merc(south, west), merc(north, east)
    ax.set_xlim(float(xa), float(xb)); ax.set_ylim(float(ya), float(yb))
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
