"""
p07 - Rides by Status (Homewood Night Ride, 1-30 Apr 2026): daily Completed / Canceled / No Show / Denied.

Four line series with markers. The page shows NO tooltip, so there is no printed anchor. The read is
therefore checked two independent ways:
  M1 (reported)  edge-aware vertical run of solid marker pixels in the 3 centre columns (pattern of p11),
                 with reconstruction from the visible edge where another series hides the marker or a steep
                 connecting line lengthens the run.
  M2 (check)     bounding-box centre of morphologically opened marker blobs (digitize.markers).
  M3 (check)     sub-pixel fit of the exact Highcharts marker shape (radius 4 px) to the anti-aliased pixels,
                 ignoring pixels that belong to connecting lines or to other series.
Tick values (0-1500, step 250) are read from the y-axis labels; the gridline pixels are measured.

Run: .venv/bin/python src/evidence/chart_p07_status.py
"""
import datetime as dt
import sys

import numpy as np
import pandas as pd
from scipy import ndimage

import digitize as dg

PAGE = 7
CHART = "p07_status"
PLOT = dict(x0=85, x1=1335, y0=205, y1=545)   # plot area incl. axis line; excludes title, filters, legend
TICKS = [0, 250, 500, 750, 1000, 1250, 1500]  # rides, bottom to top
N_CAT = 30
# Series in drawing order: later series are painted over earlier ones.
# clean_len = solid-run length (rows) of an unobstructed marker in its 3 centre columns (7-8 rows for the 8 px
# circle/square, 5-6 for the diamond, 6 for the triangle); checked against the data in main().
SERIES = {
    "completed": dict(rgb=dg.HC_BLUE, shape="circle", clean_len=(7, 8), label="Completed", mpl="o"),
    "canceled": dict(rgb=dg.HC_BLACK, shape="diamond", clean_len=(5, 6), label="Canceled", mpl="D"),
    "no_show": dict(rgb=dg.HC_GREEN, shape="square", clean_len=(7, 8), label="No Show", mpl="s"),
    "denied": dict(rgb=dg.HC_ORANGE, shape="triangle", clean_len=(6, 6), label="Denied", mpl="^"),
}
# The two apex rows of the triangle are anti-aliased, so the solid-pixel run misses them and its centre sits
# ~1 px below the marker's bounding-box centre (p11 P90 anchor: -0.83 px; here confirmed by M3 on all 30 points).
TRIANGLE_RUN_OFFSET = -1.0
ERR_PX = 1.5    # half-width of the reading interval, in pixels
WIDE_PX = 3.0   # doubled for points that are partly hidden or reconstructed
STEEP_PX = 3.0  # a neighbour this many px higher/lower counts as a rise/fall for the line-poke logic
S = 8           # sub-pixel steps per pixel in the template fit
NCAN = 16       # template canvas (px)


# ----------------------------------------------------------------------------- axis and categories
def reference_lines(img):
    grid = dg.line_rows(img, dg.GRID_GRAY, 100, 1320, PLOT["y0"], PLOT["y1"], frac=0.5)
    axis0 = dg.line_rows(img, dg.AXIS_LINE, 100, 1320, PLOT["y0"], PLOT["y1"], frac=0.5)
    return sorted(axis0 + grid, reverse=True)  # bottom (0) to top (1500)


def tick_marks(img):
    """x of the 1 px tick marks under the axis (one per labelled date: Apr 1, 3, ..., 29)."""
    band = dg.color_mask(img[538:539, PLOT["x0"]:PLOT["x1"]], dg.AXIS_LINE, 6)[0]
    return np.where(band)[0] + PLOT["x0"]


# ----------------------------------------------------------------------------- M1: solid runs
def first_runs(masks, cats):
    """Run (top, bottom) of solid pixels in the 3 centre columns of every marker; the run whose length is
    nearest the series' typical marker length is taken when a category has several."""
    runs, n_multi = {}, {}
    for name, m in masks.items():
        lens = [r[1] - r[0] + 1 for x in cats for r in dg.column_runs(m, x, half=1, gap=3)[:1]]
        typical = int(np.median(lens))
        out, multi = [], 0
        for x in cats:
            rr = dg.column_runs(m, x, half=1, gap=3)
            multi += len(rr) > 1
            out.append(min(rr, key=lambda r: abs((r[1] - r[0] + 1) - typical)) if rr else None)
        runs[name], n_multi[name] = out, multi
    return runs, n_multi


def touches(mask, x, r0, r1, half=2):
    xi = int(round(x))
    return bool(mask[max(r0, 0):r1 + 1, xi - half:xi + half + 1].any())


def centre_from_run(name, i, runs, raw, cats, occluders, half_len):
    """(y_centre, flag) for marker i of series `name`, in pixel-index units (rows)."""
    spec = SERIES[name]
    run = runs[name][i]
    if run is None:
        return None, "marker not found"
    t, b = run
    length = b - t + 1
    lo, hi = spec["clean_len"]
    flag = ""
    if lo <= length <= hi:
        y = (t + b) / 2                              # complete, unobstructed run: symmetric marker
    elif length < lo:                                # truncated: a series drawn later hides one end
        occ_top = touches(occluders[name], cats[i], t - 3, t - 1)
        occ_bot = touches(occluders[name], cats[i], b + 1, b + 3)
        if occ_top and not occ_bot:
            y, flag = b - half_len[name], "partly hidden by another series: centre from the visible bottom edge"
        elif occ_bot and not occ_top:
            y, flag = t + half_len[name], "partly hidden by another series: centre from the visible top edge"
        else:
            y, flag = (t + b) / 2, "short run, cause unclear: centre = run midpoint"
    else:                                            # longer than a marker: a steep connecting line adds rows
        dirs = []
        for j in (i - 1, i + 1):
            if 0 <= j < N_CAT and raw[name][j] is not None:
                d = raw[name][j] - raw[name][i]
                dirs.append(0 if abs(d) < STEEP_PX else (1 if d > 0 else -1))
        if dirs and all(d >= 0 for d in dirs) and any(d > 0 for d in dirs):      # peak: lines leave downwards
            y, flag = t + half_len[name], "steep line(s) lengthen the run downwards: centre from the free top edge"
        elif dirs and all(d <= 0 for d in dirs) and any(d < 0 for d in dirs):    # trough: lines leave upwards
            y, flag = b - half_len[name], "steep line(s) lengthen the run upwards: centre from the free bottom edge"
        else:
            y, flag = (t + b) / 2, "steep lines lengthen the run on both sides: centre = run midpoint (about +-1 px)"
    if spec["shape"] == "triangle":
        y += TRIANGLE_RUN_OFFSET
    return y, flag


# ----------------------------------------------------------------------------- M3: template fit
def phase_templates(shape):
    """Exact (16x supersampled) pixel coverage of a marker of radius 4 px for every 1/S-pixel phase."""
    ss = 16
    coords = (np.arange(NCAN * ss) + 0.5) / ss
    X, Y = np.meshgrid(coords, coords)
    out = {}
    for ky in range(S):
        for kx in range(S):
            dx, dy = X - (NCAN / 2 + kx / S), Y - (NCAN / 2 + ky / S)
            if shape == "circle":
                m = dx * dx + dy * dy <= 16
            elif shape == "square":
                m = (np.abs(dx) <= 4) & (np.abs(dy) <= 4)
            elif shape == "diamond":
                m = np.abs(dx) + np.abs(dy) <= 4
            else:  # triangle: apex up, base down, bounding box 8 x 8
                m = (dy >= -4) & (dy <= 4) & (np.abs(dx) <= (dy + 4) / 2)
            out[(kx, ky)] = m.reshape(NCAN, ss, NCAN, ss).mean(axis=(1, 3))
    return out


def coverage_map(img, rgb, bg_rows):
    """Fraction of `rgb` in each pixel, assuming a blend of the local background and the series colour."""
    c = np.asarray(rgb, float)
    bg = np.full(img.shape, 255.0)
    for r, col in bg_rows.items():
        bg[r] = col
    d, v = bg - c, bg - img
    a = (v * d).sum(2) / (d * d).sum(2)
    resid = np.sqrt(((v - a[..., None] * d) ** 2).sum(2))
    return np.clip(a, 0, 1), (resid <= 14.0) & (a > -0.06) & (a < 1.06)


def seg_dist(px, py, p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def fit_marker(cov, valid, other, templates, cx0, cy0, neighbours):
    """Best sub-pixel marker centre (continuous coordinates), rms residual over the marker footprint, and a
    sensitivity: the smaller rise in the squared-error cost when the marker is moved 0.5 px up or down from the best
    fit. A well-constrained marker has sensitivity of about 1.5-3; a marker whose free edges were masked away
    (lines, other series) has a flat cost and a sensitivity near 0, so its fit says little.
    Pixels within 2.4 px of the connecting lines, pixels of other series (+1 px) and invalid colours are ignored."""
    W = 24
    ix0, iy0 = int(np.floor(cx0)) - 12, int(np.floor(cy0)) - 12
    ys, xs = np.mgrid[iy0:iy0 + W, ix0:ix0 + W]
    px, py = xs + 0.5, ys + 0.5
    excl = np.zeros((W, W), bool)
    for nb in neighbours:
        excl |= seg_dist(px, py, (cx0, cy0), nb) <= 2.4
    use = valid[iy0:iy0 + W, ix0:ix0 + W] & ~excl & ~other[iy0:iy0 + W, ix0:ix0 + W]
    obs = cov[iy0:iy0 + W, ix0:ix0 + W]
    if use.sum() < 15:
        return np.nan, np.nan, np.nan, 0.0

    def render(cx, cy):
        qx, qy = round(cx * S) / S, round(cy * S) / S
        ix, kx = int(np.floor(qx)), int(round((qx - np.floor(qx)) * S)) % S
        iy, ky = int(np.floor(qy)), int(round((qy - np.floor(qy)) * S)) % S
        full = np.zeros((W, W))
        r0, c0 = iy - NCAN // 2 - iy0, ix - NCAN // 2 - ix0
        full[r0:r0 + NCAN, c0:c0 + NCAN] = templates[(kx, ky)]
        return qx, qy, full, float((((obs - full) ** 2) * use).sum())

    best = None
    for cy in np.arange(cy0 - 3, cy0 + 3.001, 1 / S):
        for cx in np.arange(cx0 - 1.6, cx0 + 1.601, 1 / S):
            qx, qy, full, err = render(cx, cy)
            if best is None or err < best[0]:
                best = (err, qx, qy, full)
    err, qx, qy, full = best
    sens = min(render(qx, qy + d)[3] - err for d in (-0.5, 0.5))
    foot = use & ((full > 0.02) | (obs > 0.02))
    rms = float(np.sqrt((((obs - full) ** 2) * foot).sum() / max(int(foot.sum()), 1)))
    return qx, qy, rms, float(sens)


# ----------------------------------------------------------------------------- main
def main():
    img = dg.load(PAGE)
    fimg = img.astype(float)
    ok = True

    # y axis: 6 gridlines + axis line -> 7 reference rows for 7 tick values
    rows = reference_lines(img)
    assert len(rows) == len(TICKS), f"expected {len(TICKS)} reference lines, got {rows}"
    yaxis = dg.Axis.fit(rows, TICKS)
    per_px = yaxis.per_pixel()
    print(f"y-axis: reference rows {[int(r) for r in rows]}; {per_px:.4f} rides/px; fit residual max "
          f"{yaxis.max_residual:.2f} rides ({yaxis.max_residual / per_px:.2f} px; gridlines are snapped to whole pixels)")

    plot = np.zeros(img.shape[:2], bool)
    plot[PLOT["y0"]:PLOT["y1"], PLOT["x0"]:PLOT["x1"]] = True
    masks = {n: dg.series_mask(img, s["rgb"], None) & plot for n, s in SERIES.items()}

    # category centres from the square No Show markers (unaffected by steep lines), checked against tick marks
    sq = dg.markers(masks["no_show"])
    assert len(sq) == N_CAT, f"expected {N_CAT} square markers, got {len(sq)}"
    cats, dx = dg.category_positions([b.cx for b in sq], N_CAT)
    ticks = tick_marks(img)
    tick_diff = cats[0:N_CAT:2] - ticks
    ok &= len(ticks) == 15 and np.abs(tick_diff).max() <= 1.0
    print(f"categories: dx = {dx:.3f} px; 15 tick marks (Apr 1,3,...,29) vs marker centres: "
          f"max |diff| {np.abs(tick_diff).max():.2f} px")

    # ---- M1
    runs, n_multi = first_runs(masks, cats)
    print("categories with more than one run in the centre columns (0 = unambiguous):", n_multi)
    assert all(r is not None for rr in runs.values() for r in rr), "a marker was not found"
    raw = {n: [(r[0] + r[1]) / 2 for r in rr] for n, rr in runs.items()}           # plain run centres
    later = list(SERIES)
    occluders = {}
    for k, n in enumerate(SERIES):                                                  # masks of series drawn on top
        m = np.zeros_like(plot)
        for o in later[k + 1:]:
            m |= masks[o]
        occluders[n] = ndimage.binary_dilation(m, structure=np.ones((3, 3)))
    half_len = {}
    for n, spec in SERIES.items():
        lens = [r[1] - r[0] + 1 for r in runs[n]]
        clean = [L for L in lens if spec["clean_len"][0] <= L <= spec["clean_len"][1]]
        half_len[n] = (np.mean(clean) - 1) / 2
        hist = {L: lens.count(L) for L in sorted(set(lens))}
        print(f"  {n:9s} run lengths {hist}; clean mean {np.mean(clean):.2f} rows over {len(clean)} markers "
              f"-> half-length {half_len[n]:.2f}")

    cy1 = {n: [] for n in SERIES}
    flags = {n: [] for n in SERIES}
    for n in SERIES:
        for i in range(N_CAT):
            y, f = centre_from_run(n, i, runs, raw, cats, occluders, half_len)
            cy1[n].append(y)
            flags[n].append(f)

    # ---- M2: opened-blob bounding-box centre (not meaningful for triangles: the opening removes the apex)
    cy2 = {}
    for n, spec in SERIES.items():
        if spec["shape"] == "triangle":
            continue
        asg = dg.assign(dg.markers(masks[n]), cats, tol=4)
        cy2[n] = [b.cy if b is not None else np.nan for b in asg]

    # ---- M3: sub-pixel template fit
    grid_rows = {int(r): (230, 230, 230) for r in rows[1:]}
    grid_rows[int(rows[0])] = tuple(dg.AXIS_LINE)
    templates = {sh: phase_templates(sh) for sh in {s["shape"] for s in SERIES.values()}}
    cy3, cx3, rms3, sens3 = {}, {}, {}, {}
    for n, spec in SERIES.items():
        cov, valid = coverage_map(fimg, spec["rgb"], grid_rows)
        other = np.zeros_like(plot)
        for o in SERIES:
            if o != n:
                other |= masks[o]
        other = ndimage.binary_dilation(other, structure=np.ones((3, 3)))
        cy3[n], cx3[n], rms3[n], sens3[n] = [], [], [], []
        for i in range(N_CAT):
            nbs = [(cats[j] + 0.5, cy1[n][j] + 0.5) for j in (i - 1, i + 1) if 0 <= j < N_CAT]
            cx, cy, rms, sens = fit_marker(cov, valid, other, templates[spec["shape"]],
                                           cats[i] + 0.5, cy1[n][i] + 0.5, nbs)
            cy3[n].append(cy - 0.5 if not np.isnan(cy) else np.nan)
            cx3[n].append(cx - 0.5 if not np.isnan(cx) else np.nan)
            rms3[n].append(rms)
            sens3[n].append(sens)

    # ---- observation rows
    recs, pts = [], []
    for n, spec in SERIES.items():
        for i in range(N_CAT):
            date = dt.date(2026, 4, i + 1).isoformat()
            y, flag = cy1[n][i], flags[n][i]
            v = float(yaxis.value(y))
            err = (WIDE_PX if flag else ERR_PX) * per_px
            notes = flag
            if n == "denied":
                notes = ("on the zero line on every day (identical marker position on all 30 days); indistinguishable "
                         "from 0 at this resolution; lower bound clipped at 0")
            recs.append(dict(metric=n, date_or_hour=date, value=round(v, 1), lower=round(max(v - err, 0.0), 1),
                             upper=round(v + err, 1), px_x=round(float(cats[i]), 1), px_y=round(float(y), 1),
                             notes=notes))
            pts.append((cats[i], y))
    df = pd.DataFrame(recs)
    df["chart_id"] = CHART
    df["page"] = PAGE
    df["period"] = "2026-04-01/2026-04-30"
    df["unit"] = "rides"
    df["population"] = "Homewood Night Ride; rides grouped by status (definition per chart subtitle)"
    df["evidence_status"] = "OBSERVED"
    df["method"] = (f"colour-mask marker runs, edge-aware (M1); y-axis fit on 7 reference lines, "
                    f"{per_px:.2f} rides/px, max resid {yaxis.max_residual:.1f} rides")
    df["obs_id"] = [f"{CHART}_{m}_{d}" for m, d in zip(df.metric, df.date_or_hour)]
    df = df[dg.OBS_COLUMNS]
    dg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(dg.PROCESSED / f"obs_{CHART}.csv", index=False)
    dg.overlay(img, pts, dg.EVIDENCE_OUT / f"{CHART}_overlay.png")

    # ---- checks
    ok &= second_method_report(df, cy1, cy2, cy3, rms3, sens3, yaxis)
    ok &= summary_report(df)
    recreate(df, dg.EVIDENCE_OUT / f"{CHART}_recreated.png")
    print("files: data/processed/obs_p07_status.csv, outputs/evidence/p07_status_overlay.png, _recreated.png")
    return 0 if ok else 1


# ----------------------------------------------------------------------------- reports
NAMED = [("completed", 5), ("completed", 21), ("completed", 30), ("canceled", 1), ("canceled", 17),
         ("canceled", 19), ("canceled", 25), ("no_show", 13), ("no_show", 27)]


MIN_SENS = 0.5  # min cost rise for a 0.5 px vertical shift, else the fit is too weakly constrained to check a point


def second_method_report(df, cy1, cy2, cy3, rms3, sens3, yaxis):
    per_px = yaxis.per_pixel()
    ok = True
    flagged = {(n, i) for n in cy1 for i in range(N_CAT) if df[(df.metric == n)].notes.iloc[i]
               and n != "denied"}
    print("\nSECOND-METHOD CHECKS (differences in pixels; 1 px = %.2f rides)" % per_px)
    # M2 vs M1
    d2 = []
    for n, vals in cy2.items():
        for i, v in enumerate(vals):
            if not np.isnan(v):
                d2.append((n, i, v - cy1[n][i], (n, i) in flagged))
    clean2 = [d for d in d2 if not d[3]]
    a = np.array([d[2] for d in clean2])
    print(f"M2 (opened-blob bbox centre) - M1, unflagged points: n={len(a)}, mean {a.mean():+.2f} px, "
          f"mean|d| {np.abs(a).mean():.2f}, max|d| {np.abs(a).max():.2f} px "
          f"({np.abs(a).max() * per_px:.1f} rides); share within 0.5 px: {(np.abs(a) <= 0.5).mean():.0%}")
    worst = sorted(clean2, key=lambda d: -abs(d[2]))[:3]
    print("  largest:", "; ".join(f"{n} Apr {i + 1}: {d:+.1f}" for n, i, d, _ in worst))
    fl2 = [d for d in d2 if d[3]]
    print("  flagged points with a blob:", "; ".join(f"{n} Apr {i + 1}: {d:+.1f}" for n, i, d, _ in fl2),
          "(blob of a partly hidden marker is not comparable)")
    ok &= np.abs(a).max() <= 1.0
    # M3 vs M1
    d3, thin = [], []
    for n in cy3:
        for i in range(N_CAT):
            v = cy3[n][i]
            if np.isnan(v) or sens3[n][i] < MIN_SENS:
                thin.append((n, i, sens3[n][i]))          # too little unmasked edge to check the point
            else:
                d3.append((n, i, v - cy1[n][i], (n, i) in flagged))
    print(f"M3 could check {len(d3)} of {len(d3) + len(thin)} markers; too weakly constrained after masking lines and other "
          f"series (cost rise for a 0.5 px shift < {MIN_SENS}): " + ("; ".join(f"{n} Apr {i + 1} ({e:.2f})" for n, i, e in thin) or "none"))
    for label, sel in (("unflagged", [d for d in d3 if not d[3]]), ("flagged", [d for d in d3 if d[3]])):
        if not sel:
            continue
        a3 = np.array([d[2] for d in sel])
        print(f"M3 (sub-pixel template fit) - M1, {label}: n={len(a3)}, mean {a3.mean():+.2f} px, mean|d| "
              f"{np.abs(a3).mean():.2f}, max|d| {np.abs(a3).max():.2f} px ({np.abs(a3).max() * per_px:.1f} rides)")
        if label == "unflagged":
            ok &= np.abs(a3).max() <= 1.0
            for n in cy3:
                an = np.array([d[2] for d in sel if d[0] == n])
                if len(an):
                    print(f"    {n:9s} n={len(an):2d} mean {an.mean():+.2f}, max|d| {np.abs(an).max():.2f}")
        else:
            print("  ", "; ".join(f"{n} Apr {i + 1}: {d:+.2f}" for n, i, d, _ in sel))
            ok &= np.abs(a3).max() <= 1.5
    good = [(n, i) for n, i, _, _ in d3]
    print("  fit quality on the checked markers: median footprint rms %.3f (coverage units), sensitivity median %.2f, min %.2f" % (
        np.median([rms3[n][i] for n, i in good]), np.median([sens3[n][i] for n, i in good]),
        min(sens3[n][i] for n, i in good)))
    print("\nNAMED POINTS (value in rides; M2 = blob, M3 = template fit; * = M3 weakly constrained at this point):")
    print(f"  {'series':9s} {'date':7s} {'M1':>8s} {'M2':>8s} {'M3':>8s} {'M2-M1':>7s} {'M3-M1':>7s}   (px: M2-M1, M3-M1)")
    for n, day in NAMED:
        i = day - 1
        v1 = float(yaxis.value(cy1[n][i]))
        v2 = float(yaxis.value(cy2[n][i])) if n in cy2 and not np.isnan(cy2[n][i]) else np.nan
        v3 = float(yaxis.value(cy3[n][i]))
        p2 = cy2[n][i] - cy1[n][i] if n in cy2 else np.nan
        p3 = cy3[n][i] - cy1[n][i]
        weak = "*" if sens3[n][i] < MIN_SENS else " "
        print(f"  {n:9s} Apr {day:2d}  {v1:8.1f} {v2:8.1f} {v3:8.1f}{weak} {v2 - v1:+7.1f} {v3 - v1:+7.1f}   ({p2:+.2f}, {p3:+.2f} px)")
    return ok


def summary_report(df):
    w = df.pivot(index="date_or_hour", columns="metric", values="value")
    tot = w[["completed", "canceled", "no_show", "denied"]].sum()
    print("\nMONTHLY SUMS (DERIVED, rides):", {k: round(float(v), 0) for k, v in tot.items()})
    sanity = abs(tot["completed"] - 24000) / 24000
    print(f"sanity: sum of Completed = {tot['completed']:.0f} vs ~24,000 -> {sanity:+.1%} "
          f"({'within' if sanity <= 0.03 else 'OUTSIDE'} +-3%; reported, not forced)")
    denom = w[["completed", "canceled", "no_show", "denied"]].sum(axis=1)
    share = w["canceled"] / denom
    print(f"daily cancel share = canceled / (completed+canceled+no_show+denied): mean {share.mean():.3f}, "
          f"min {share.min():.3f} ({share.idxmin()}), max {share.max():.3f} ({share.idxmax()}); "
          f"month pooled {tot['canceled'] / tot[['completed', 'canceled', 'no_show', 'denied']].sum():.3f}")
    for d in ("2026-04-17", "2026-04-30"):
        print(f"  {d}:", {k: float(w.loc[d, k]) for k in w.columns})
    print(f"  days with Canceled above Completed: {int((w['canceled'] > w['completed']).sum())} of {len(w)}")
    # cross-page checks, run only if the other charts' observation files exist (DERIVED; different pages, different readers)
    p09, p10 = dg.PROCESSED / "obs_p09_rides_by_hour.csv", dg.PROCESSED / "obs_p10_vanlyft_daily.csv"
    if p09.exists():
        h = pd.read_csv(p09)
        half9 = float(np.sqrt((((h.upper - h.lower) / 2) ** 2).sum()))
        c = df[df.metric == "completed"]
        half7 = float(np.sqrt((((c.upper - c.lower) / 2) ** 2).sum()))
        print(f"  cross-check p09 (completed rides summed by hour of day, 30 days): {h.value.sum():.0f} vs p07 Completed "
              f"{tot['completed']:.0f} ({tot['completed'] / h.value.sum() - 1:+.2%}); reading noise rss +-{half9:.0f} (p09) and "
              f"+-{half7:.0f} (p07), combined +-{np.hypot(half9, half7):.0f} rides")
    if p10.exists():
        lyft = pd.read_csv(p10).query("metric == 'lyft_riders'").set_index("date_or_hour").value
        print(f"  cross-check p10: correlation of daily Canceled (p07) with daily Lyft riders (p10) = "
              f"{np.corrcoef(w['canceled'], lyft.loc[w.index])[0, 1]:.2f}; Lyft riders {lyft.sum():.0f} in the month")
    fl = df[(df.notes != "") & (df.metric != "denied")]
    print("\nFLAGGED POINTS:")
    for _, r in fl.iterrows():
        print(f"  {r.metric:9s} {r.date_or_hour}  value {r.value:7.1f} [{r.lower:.1f}, {r.upper:.1f}]  {r.notes}")
    return True


# ----------------------------------------------------------------------------- recreated chart
def recreate(df, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, gridc = "#2b2b2b", "#666666", "#e6e6e6"
    fig, ax = plt.subplots(figsize=(13.4, 6.4), dpi=100)
    x = np.arange(1, N_CAT + 1)
    for n, spec in SERIES.items():
        d = df[df.metric == n].sort_values("date_or_hour")
        col = tuple(c / 255 for c in spec["rgb"])
        y, lo, hi = d.value.values, d.lower.values, d.upper.values
        wide = (d.notes != "").values & (n != "denied")
        ax.plot(x, y, color=col, lw=1.8, marker=spec["mpl"], ms=6.5, mec=col, mfc=col, zorder=3,
                solid_joinstyle="round")
        ax.errorbar(x[~wide], y[~wide], yerr=[(y - lo)[~wide], (hi - y)[~wide]], fmt="none", ecolor=col,
                    elinewidth=1.0, capsize=2.5, capthick=1.0, zorder=2, alpha=0.9)
        if wide.any():
            ax.errorbar(x[wide], y[wide], yerr=[(y - lo)[wide], (hi - y)[wide]], fmt="none", ecolor=col,
                        elinewidth=1.6, capsize=4, capthick=1.6, zorder=2)
            ax.plot(x[wide], y[wide], ls="none", marker="o", ms=11, mfc="none", mec=ink, mew=0.9, zorder=4)
    ax.set_xlim(0.4, 31.6)
    ax.set_ylim(0, 1500)
    ax.set_yticks(TICKS)
    ax.set_xticks(x[::2])
    ax.set_xticklabels([f"{d}. Apr" for d in x[::2]])
    ax.grid(axis="y", color=gridc, lw=1)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#ccd6eb")
    ax.tick_params(colors=muted, length=3, labelsize=9)
    ax.tick_params(axis="y", length=0)
    ax.set_ylabel("Rides by Status", color=muted, fontsize=9)
    # direct labels at the right end (Denied and No Show are close: nudge)
    last = {n: df[(df.metric == n)].sort_values("date_or_hour").value.values[-1] for n in SERIES}
    nudge = {"completed": 0, "canceled": 0, "no_show": 16, "denied": 0}
    for n, spec in SERIES.items():
        ax.annotate(spec["label"], (30.35, last[n] + nudge[n]), xytext=(6, 0), textcoords="offset points",
                    color=ink, fontsize=9.5, va="center", annotation_clip=False)
    fig.suptitle("Rides by Status", x=0.06, y=0.985, ha="left", fontsize=20, color=ink)
    fig.text(0.06, 0.915, "Recreated from the April 2026 report, page 7 (Homewood Night Ride, 04-01-2026 to 04-30-2026). "
             "Denied plots on the zero line on every day.\n"
             "Error bars: reading interval, +-1.5 px = about +-7 rides. Rings: point partly hidden by another series or "
             "lengthened by a steep line (interval doubled to +-3 px).",
             color=muted, fontsize=9, ha="left", va="top", linespacing=1.5)
    handles = [plt.Line2D([], [], color=tuple(c / 255 for c in s["rgb"]), lw=1.8, marker=s["mpl"], ms=6.5)
               for s in SERIES.values()]
    ax.legend(handles, [s["label"] for s in SERIES.values()], loc="upper center", bbox_to_anchor=(0.5, -0.09),
              ncol=4, frameon=False, fontsize=10, labelcolor=ink)
    fig.subplots_adjust(left=0.06, right=0.93, top=0.86, bottom=0.17)
    dg.EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
