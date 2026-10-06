"""
Detect the marker-cluster bubbles on the four O/D density maps (pp. 2-5).

The maps are Google Maps screenshots with MarkerClusterer bubbles. Each bubble
has a solid disc in one of four colours that encode the size of the count:
blue (1 digit), yellow (2 digits), red (3 digits), magenta (4 digits). This
script finds the discs, splits touching discs of the same colour, and writes

    data/processed/map_bubbles.csv          one row per bubble (pixel centre, colour, flags)
    outputs/evidence/map_pNN_bubbles.png    the map with bubble ids, for reading and QA
    outputs/evidence/map_pNN_sheet_K.png    contact sheets: enlarged crops, one per bubble id

Counts are read from the contact sheets by eye (two independent readers) and
stored separately; the disc colour is then a check on every reading.
Run: .venv/bin/python src/evidence/map_bubbles.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "april"
OUT = ROOT / "outputs" / "evidence"
PROCESSED = ROOT / "data" / "processed"

MAPS = {2: "origins_city", 3: "destinations_city", 4: "origins_campus", 5: "destinations_campus"}
DIGITS = {"blue": 1, "yellow": 2, "red": 3, "magenta": 4}
MAP_TOP = 104  # rows above this are the report's date pickers, not map


def classes(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return {
        "red": (r >= 200) & (g <= 90) & (b <= 90),
        "magenta": (r >= 200) & (g <= 90) & (b >= 170),
        "yellow": (r >= 200) & (g >= 150) & (g <= 225) & (b <= 90),
        "blue": (r <= 90) & (g >= 100) & (g <= 190) & (b >= 200),
    }


def text_centres(img, cls):
    """Centres of the count labels. The label is printed at the disc centre in dark
    text, so dark pixels enclosed by bubble colour mark the centre even when two
    discs touch or overlap."""
    anyd = np.zeros(img.shape[:2], bool)
    for m in cls.values():
        anyd |= m
    anyd[:MAP_TOP] = False
    filled = ndimage.binary_fill_holes(ndimage.binary_closing(anyd, structure=np.ones((3, 3))))
    text = filled & ~anyd & (img.max(axis=2) < 150)
    labels, _ = ndimage.label(ndimage.binary_dilation(text, structure=np.ones((3, 7))))
    out = []
    for sl in ndimage.find_objects(labels):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if text[sl].sum() >= 6 and 7 <= h <= 20 and 6 <= w <= 50:
            x, y = (sl[1].start + sl[1].stop - 1) / 2, (sl[0].start + sl[0].stop - 1) / 2
            out.append((x, y, w))
    return out


def ring_colour(cls, x, y, r=12):
    """Bubble colour = the class with most pixels within r of the label centre."""
    yy, xx = np.ogrid[:cls["red"].shape[0], :cls["red"].shape[1]]
    disk = (yy - y) ** 2 + (xx - x) ** 2 <= r * r
    counts = {c: int((m & disk).sum()) for c, m in cls.items()}
    return max(counts, key=counts.get), counts


def discs_without_text(cls, centres, min_area=40):
    """Disc components that contain no count label: bubbles whose count is hidden
    under another bubble or cut off by the map edge."""
    out = []
    for colour, mask in cls.items():
        mask = mask.copy()
        mask[:MAP_TOP] = False
        filled = ndimage.binary_fill_holes(ndimage.binary_closing(mask, structure=np.ones((3, 3))))
        labels, _ = ndimage.label(filled)
        labelled = {labels[int(round(ty)), int(round(tx))] for tx, ty, _ in centres}
        for i, sl in enumerate(ndimage.find_objects(labels), start=1):
            comp = labels[sl] == i
            if i in labelled or comp.sum() < min_area:
                continue
            cy, cx = ndimage.center_of_mass(comp)
            out.append((colour, sl[1].start + cx, sl[0].start + cy, int(comp.sum())))
    return out


def main():
    rows = []
    for page, name in MAPS.items():
        img = np.array(Image.open(RAW / f"p{page:02d}.png").convert("RGB")).astype(int)
        h, w, _ = img.shape
        cls = classes(img)
        centres = text_centres(img, cls)
        found = []
        for x, y, _tw in centres:
            colour, counts = ring_colour(cls, x, y)
            found.append((colour, x, y, counts[colour], "count label visible"))
        for colour, x, y, area in discs_without_text(cls, centres):
            found.append((colour, x, y, area, "no visible label (hidden or cut off)"))
        found.sort(key=lambda f: (round(f[2] / 40), f[1]))  # rough reading order: bands top to bottom
        for k, (colour, x, y, area, source) in enumerate(found, start=1):
            edge = x < 14 or x > w - 14 or y < MAP_TOP + 10 or y > h - 12
            rows.append(dict(map_page=page, map_name=name, bubble_id=f"p{page:02d}_b{k:03d}", colour=colour,
                             digits_expected=DIGITS[colour], px_x=round(x, 1), px_y=round(y, 1), disc_px_near=area,
                             source=source, near_edge=edge))
        annotate(img, [r for r in rows if r["map_page"] == page], OUT / f"map_p{page:02d}_bubbles.png")
        sheets(img, [r for r in rows if r["map_page"] == page], page)
    df = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "map_bubbles.csv", index=False)
    print(df.groupby(["map_name", "colour"]).size().unstack(fill_value=0))
    print(df.groupby(["map_name", "source"]).size().unstack(fill_value=0))
    print("near edge:", int(df.near_edge.sum()))


def annotate(img, rows, path):
    im = Image.fromarray(img.astype(np.uint8)).resize((img.shape[1] * 2, img.shape[0] * 2), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for r in rows:
        x, y = r["px_x"] * 2, r["px_y"] * 2
        d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(0, 90, 255), width=2)
        d.text((x + 22, y - 22), r["bubble_id"][-3:], fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def sheets(img, rows, page, per_sheet=24, half=26, scale=4, cols=6):
    base = Image.fromarray(img.astype(np.uint8))
    for s in range(0, len(rows), per_sheet):
        chunk = rows[s:s + per_sheet]
        cell = 2 * half * scale
        sheet = Image.new("RGB", (cols * cell, ((len(chunk) - 1) // cols + 1) * (cell + 24)), "white")
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            x, y = int(round(r["px_x"])), int(round(r["px_y"]))
            crop = base.crop((x - half, y - half, x + half, y + half)).resize((cell, cell), Image.LANCZOS)
            cx, cy = (i % cols) * cell, (i // cols) * (cell + 24)
            sheet.paste(crop, (cx, cy + 24))
            d.text((cx + 6, cy + 4), f"{r['bubble_id']}  ({r['colour']})", fill=(0, 0, 0))
            d.line([(cx + cell // 2 - 6, cy + 24 + cell // 2), (cx + cell // 2 + 6, cy + 24 + cell // 2)], fill=(0, 200, 255))
        sheet.save(OUT / f"map_p{page:02d}_sheet_{s // per_sheet + 1}.png")


if __name__ == "__main__":
    main()
