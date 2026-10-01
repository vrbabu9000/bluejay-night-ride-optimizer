"""
Digitize the raster charts in the April 2026 TransLoc report.

Every chart in the PDF is a screenshot. The Highcharts panels (pp. 6-9, 11-12)
are stored losslessly and drawn in Highcharts' default palette, so a series can
be isolated by exact colour. The pipeline for one chart is:

    load(page) -> Axis.fit(gridline pixels, tick values) -> colour mask
    -> markers()/bar_tops() -> assign to categories -> observation rows
    -> overlay() for visual QA

Pixel geometry is measured, never guessed; tick values are read by eye from
the axis labels and passed in explicitly by the caller.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "april"
PROCESSED = ROOT / "data" / "processed"
EVIDENCE_OUT = ROOT / "outputs" / "evidence"

# Highcharts default series colours (verified by pixel counts on p11).
HC_BLUE = (124, 181, 236)
HC_BLACK = (67, 67, 72)
HC_GREEN = (144, 237, 125)
HC_ORANGE = (247, 163, 92)
GRID_GRAY = (230, 230, 230)
AXIS_LINE = (204, 214, 235)

OBS_COLUMNS = [
    "obs_id", "chart_id", "page", "period", "date_or_hour", "metric", "value",
    "lower", "upper", "unit", "population", "evidence_status", "method",
    "px_x", "px_y", "notes",
]


def load(page):
    """RGB pixels of the chart on a PDF page, as an int array (H, W, 3)."""
    return np.array(Image.open(RAW / f"p{page:02d}.png").convert("RGB")).astype(int)


def color_mask(img, rgb, tol=24):
    """Pixels within an L1 distance `tol` of a palette colour."""
    return np.abs(img - np.array(rgb)).sum(axis=2) <= tol


def line_rows(img, rgb, x0, x1, y0, y1, frac=0.5, tol=6):
    """Rows in [y0, y1) where at least `frac` of columns [x0, x1) match `rgb`.
    Consecutive rows are merged and returned as their mean position."""
    m = color_mask(img[y0:y1, x0:x1], rgb, tol)
    hits = np.where(m.mean(axis=1) >= frac)[0] + y0
    groups = np.split(hits, np.where(np.diff(hits) > 1)[0] + 1) if len(hits) else []
    return [float(g.mean()) for g in groups if len(g)]


@dataclass
class Axis:
    """Linear pixel -> value map fitted by least squares on (pixel, value) pairs."""
    slope: float
    intercept: float
    max_residual: float

    @classmethod
    def fit(cls, pixels, values):
        p, v = np.asarray(pixels, float), np.asarray(values, float)
        slope, intercept = np.polyfit(p, v, 1)
        resid = v - (slope * p + intercept)
        return cls(float(slope), float(intercept), float(np.abs(resid).max()))

    def value(self, pixel):
        return self.slope * np.asarray(pixel, float) + self.intercept

    def per_pixel(self):
        return abs(self.slope)


@dataclass
class Blob:
    cx: float  # bounding-box centre (the data point for symmetric markers)
    cy: float
    w: int
    h: int
    area: int


def markers(mask, open_px=3, min_area=12):
    """Marker blobs in a series mask. A morphological opening removes the
    ~2 px connecting line so only the wider marker symbols survive."""
    opened = ndimage.binary_opening(mask, structure=np.ones((open_px, open_px)))
    labels, n = ndimage.label(opened)
    blobs = []
    for sl in ndimage.find_objects(labels):
        ys, xs = sl
        area = int(opened[sl].sum())
        if area < min_area:
            continue
        blobs.append(Blob(cx=(xs.start + xs.stop - 1) / 2, cy=(ys.start + ys.stop - 1) / 2,
                          w=xs.stop - xs.start, h=ys.stop - ys.start, area=area))
    return blobs


def tooltip_box(img, rgb=(248, 248, 248), tol=3, min_area=2000):
    """Bounding box (x0, y0, x1, y1) of the hover tooltip, found as the largest
    region of the tooltip's light-gray fill; None if the chart has no tooltip."""
    fill = ndimage.binary_closing(color_mask(img, rgb, tol), structure=np.ones((9, 9)))
    labels, n = ndimage.label(fill)
    if n == 0:
        return None
    sizes = ndimage.sum(np.ones_like(labels), labels, index=range(1, n + 1))
    k = int(np.argmax(sizes))
    if sizes[k] < min_area:
        return None
    ys, xs = ndimage.find_objects(labels)[k]
    return (xs.start - 2, ys.start - 2, xs.stop + 2, ys.stop + 2)  # include the 1-2 px border


def inside(box, x, y):
    return box is not None and box[0] <= x <= box[2] and box[1] <= y <= box[3]


def column_runs(mask, x, half=1, gap=1):
    """Row runs (top, bottom) where any of columns [x-half, x+half] is masked.
    Runs separated by fewer than `gap` empty rows are merged (e.g. a tooltip
    border drawn across a marker)."""
    xi = int(round(x))
    rows = np.where(mask[:, xi - half:xi + half + 1].any(axis=1))[0]
    if not len(rows):
        return []
    groups = np.split(rows, np.where(np.diff(rows) > gap)[0] + 1)
    return [(int(g[0]), int(g[-1])) for g in groups]


def series_mask(img, rgb, box=None, tol=24, alpha=0.84, bg=248, shadow_px=4):
    """Pixels of one series, including parts hidden under a translucent tooltip.

    Inside the tooltip the chart shows through at (1 - alpha); un-blending
    c' = (c - alpha*bg) / (1 - alpha) recovers the original colour (alpha ~0.84
    was measured on p11 from the orange series). Just below the tooltip its
    drop shadow darkens pixels multiplicatively, which preserves chromaticity,
    so those are matched on chromaticity instead of exact colour."""
    mask = color_mask(img, rgb, tol)
    if box is None:
        return mask
    x0, y0, x1, y1 = box
    target = np.array(rgb, float)
    inner = img[y0 + 3:y1 - 1, x0 + 3:x1 - 3].astype(float)
    un = (inner - alpha * bg) / (1 - alpha)
    faint = inner.min(axis=2) >= alpha * bg - 5  # see-through tints only; excludes text and its colour fringes
    mask[y0 + 3:y1 - 1, x0 + 3:x1 - 3] |= faint & (np.abs(un - target).sum(axis=2) <= 2 * tol)
    band = img[y1 - 3:y1 + shadow_px, x0:x1 + shadow_px].astype(float)
    chroma = band / np.maximum(band.sum(axis=2, keepdims=True), 1)
    tchroma = target / target.sum()
    bright = band.sum(axis=2) / target.sum()
    mask[y1 - 3:y1 + shadow_px, x0:x1 + shadow_px] |= (
        (np.abs(chroma - tchroma).sum(axis=2) <= 0.03) & (bright >= 0.5) & (bright <= 1.1))
    return mask


def marker_at(mask, x, typical_len, box=None):
    """Vertical centre of the marker at category x, read from its centre columns.

    For Highcharts' square, diamond and triangle symbols the marker's vertical
    extent in its own centre columns is symmetric about the data point, and the
    connecting line stays inside that extent. Returns (y, flag)."""
    runs = column_runs(mask, x, gap=3)
    if not runs:
        return None, "marker not found"
    # prefer the run whose length is closest to a marker's; ignore 1-2 px slivers
    top, bot = min(runs, key=lambda r: abs((r[1] - r[0] + 1) - typical_len))
    length = bot - top + 1
    flag = ""
    if box is not None and box[0] - 2 <= x <= box[2] + 2 and top <= box[3] + 4 and bot >= box[1] - 4:
        flag = "recovered from under the tooltip"
    if length > typical_len + 3:
        flag = (flag + "; " if flag else "") + "enlarged (hover-state) marker"
    elif length < typical_len - 2:
        flag = (flag + "; " if flag else "") + "short run; check overlay"
    return (top + bot) / 2, flag


def category_positions(xs_detected, n, spacing_hint=None):
    """Equally spaced category centres x0 + i*dx fitted to detected x's.
    Each detection is assigned the nearest integer index."""
    xs = np.sort(np.asarray(xs_detected, float))
    dx = spacing_hint or float(np.median(np.diff(xs)))
    idx = np.round((xs - xs[0]) / dx)
    slope, x0 = np.polyfit(idx, xs, 1)
    return x0 + slope * np.arange(n), float(slope)


def assign(blobs, cats, tol):
    """For each category x, the blob whose centre is nearest (within tol), else None."""
    out = []
    for x in cats:
        near = [b for b in blobs if abs(b.cx - x) <= tol]
        out.append(min(near, key=lambda b: abs(b.cx - x)) if near else None)
    return out


def bar_tops(mask, cats, half_width=3, y_floor=None):
    """Top edge (first masked row) of the bar centred at each category x."""
    tops = []
    for x in cats:
        band = mask[:, int(round(x)) - half_width:int(round(x)) + half_width + 1]
        rows = np.where(band.any(axis=1))[0]
        if y_floor is not None:
            rows = rows[rows < y_floor]
        tops.append(float(rows.min()) if len(rows) else None)
    return tops


def overlay(img, points, out_path, labels=None):
    """Draw a red crosshair (and optional label) at each (x, y) for QA."""
    im = Image.fromarray(img.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate(points):
        if x is None or y is None:
            continue
        d.line([(x - 6, y), (x + 6, y)], fill=(220, 0, 0), width=1)
        d.line([(x, y - 6), (x, y + 6)], fill=(220, 0, 0), width=1)
        if labels:
            d.text((x + 4, y - 14), str(labels[i]), fill=(220, 0, 0))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path)


def seconds_to_mmss(minutes):
    s = int(round(minutes * 60))
    return f"{s // 60}m {s % 60:02d}s"
