"""
p12 - Ride Duration (Homewood Night Ride, 1-30 Apr 2026): daily P10 / median / P90.

Structurally the p11 wait-time chart (chart_p11_wait.py): colour-mask markers, y-axis fitted to the
gridlines, category positions from the median squares. Tick values (0-35 min, step 5) are read from
the y-axis labels. Anchor: the Apr 17 tooltip (P10 4m04s, median 12m28s, P90 29m24s).

Three chart-specific refinements, all local to this script (digitize.py is shared and unchanged):
  1. P90 triangles. The apex is too thin to survive the colour mask, so the mask-run midpoint reads
     ~0.7 px (~5 s) low. The data point is placed from the flat base instead (sub-pixel), half a
     marker height above it.
  2. Hover-state markers (Apr 17, all three series). The enlarged marker sits on a translucent halo
     disc that is centred on the data point; the disc centre is used.
  3. A marker hidden by the tooltip (P90, Apr 16). The line segment to the next marker is straight,
     so it is measured through the translucent tooltip and the hidden vertex is one category step
     back from the Apr 17 halo centre. Flagged, interval doubled.

Run: .venv/bin/python src/evidence/chart_p12_ride.py            extract; write CSV, overlay, recreated chart
     .venv/bin/python src/evidence/chart_p12_ride.py --check    also cross-check every vertex
                                                               against the drawn polyline
"""
import datetime as dt
import sys

import numpy as np
import pandas as pd

import digitize as dg

PAGE = 12
CHART = "p12_ride"
# Plot area measured on this image: the gridlines span x = 71..1321 and rows 216 (35 min) .. 527
# (0 min, the axis line). The window is padded a little above the top gridline and below the axis
# but stops short of the x-axis labels and legend (rows >= 571) and the controls above row 200.
PLOT = dict(x0=71, x1=1322, y0=205, y1=533)
TICKS = [0, 5, 10, 15, 20, 25, 30, 35]  # minutes, bottom to top (8 reference lines)
SERIES = {"ride_p10": dg.HC_BLACK, "ride_median": dg.HC_GREEN, "ride_p90": dg.HC_ORANGE}
TRIANGLE = "ride_p90"                    # the only triangle-symbol series
ANCHORS = {("ride_p10", 17): 4 + 4 / 60, ("ride_median", 17): 12 + 28 / 60, ("ride_p90", 17): 29 + 24 / 60}
HOVER_DAY = 17                           # the date named in the tooltip; its markers are in hover state
ERR_PX = 1.5                             # half-width of the reading interval, in pixels
TRI_HALF = 4.0                           # triangle half height, px (8 x 8 marker; apex-to-base 8.0 measured)
HALO_ALPHA = 0.25                        # opacity of the hover halo disc (Highcharts default)
TIP_ALPHA, TIP_FILL = 0.85, 247.0        # tooltip fill rgba(247,247,247,0.85) (Highcharts default)


def row_background(img, cols, lo=225):
    """Per-row background colour, (H, 3): the median of each row's near-gray pixels over `cols`.
    White on plain rows, gridline gray on a gridline row; a row with too few gray pixels is white."""
    px = img[:, cols].astype(float)
    gray = (np.abs(px[..., 0] - px[..., 1]) <= 2) & (np.abs(px[..., 1] - px[..., 2]) <= 2) & (px[..., 0] >= lo)
    out = np.full((img.shape[0], 3), 255.0)
    for y in range(img.shape[0]):
        if gray[y].sum() >= 20:
            out[y] = np.median(px[y][gray[y]], axis=0)
    return out


def coverage(img, xs, y, rgb, bg, tip=False):
    """Fraction (0..1) of row y, columns xs (mean), covered by series colour `rgb` over background `bg`.
    tip=True: the chart is seen through the translucent tooltip (pass the tooltip-tinted `bg`)."""
    target = np.asarray(rgb, float)
    if tip:
        target = TIP_ALPHA * TIP_FILL + (1 - TIP_ALPHA) * target
    t = bg - target
    return float(np.mean((bg - img[y, xs].astype(float)) @ t) / (t @ t))


def triangle_centre(img, x, y_run, bg):
    """Data-point row (pixel-index units) of a triangle marker, read from its flat base. The base's lower
    edge, as a continuous coordinate, is the last fully covered row + 1 + the partial coverage of the row
    below; the data point is TRI_HALF above it, less 0.5 to convert to pixel-index units. -> (y, flag)."""
    xs = [int(round(x)) + d for d in (-1, 0, 1)]
    rows = range(int(y_run), int(y_run) + 9)
    cov = {y: coverage(img, xs, y, dg.HC_ORANGE, bg[y]) for y in rows}
    full = [y for y in rows if cov[y] >= 0.97 and y <= y_run + 5]
    if not full:
        return None, "base edge not found"
    last = max(full)
    base = last + 1 + min(max(cov[last + 1], 0.0), 1.0)
    flag = "" if cov[last + 2] < 0.25 else "base edge unclear; check overlay"
    return base - TRI_HALF - 0.5, flag


def halo_centre(img, x, y_guess, rgb, bg, reach=14):
    """Data-point row (pixel-index units) of a hover-state marker, from the translucent halo disc that is
    centred on it. The disc's top and bottom edges are read in the two columns beside the crosshair,
    sub-pixel from the partial edge rows."""
    xs = [int(round(x)) - 1, int(round(x)) + 1]
    ys = np.arange(int(y_guess) - reach, int(y_guess) + reach + 1)
    cov = np.array([coverage(img, xs, y, rgb, bg[y]) for y in ys])
    on = np.where(cov >= 0.02)[0]
    top = ys[on[0]] + 1 - min(cov[on[0]] / HALO_ALPHA, 1.0)
    bottom = ys[on[-1]] + min(cov[on[-1]] / HALO_ALPHA, 1.0)
    return (top + bottom) / 2 - 0.5


def line_centres(img, rgb, cols, y_expect, bg, tip=False, half=4):
    """Vertical centre (pixel-index units) of a drawn line in each column of `cols`: the coverage-weighted
    mean row in a +-half window around `y_expect(x)`. -> (columns, centres)."""
    xs, cy = [], []
    for x in cols:
        y0 = int(y_expect(x))
        ys = np.arange(y0 - half, y0 + half + 1)
        c = np.clip([coverage(img, [x], y, rgb, bg[y], tip) for y in ys], 0, 1)
        if c.sum() >= 0.5:
            xs.append(x)
            cy.append(float((ys * c).sum() / c.sum()))
    return np.array(xs, float), np.array(cy)


def hidden_vertex(img, box, rgb, bg_tip, x_hid, y_hid_guess, x_next, y_next, dx):
    """Data-point row of a marker hidden under the tooltip, given its right-hand neighbour (x_next, y_next).
    The segment between them is straight: its slope is measured through the translucent fill on the columns
    between the markers that lie inside the tooltip, and the hidden vertex is one category step (dx) back
    along it. -> (y, slope, residual sd of the line fit, columns used)."""
    guess = lambda x: y_hid_guess + (y_next - y_hid_guess) * (x - x_hid) / (x_next - x_hid)
    xs, cy = line_centres(img, rgb, range(int(round(x_hid)) + 7, box[2] - 3), guess, bg_tip, tip=True)
    slope, icpt = np.polyfit(xs, cy, 1)
    sd = float(np.std(cy - (icpt + slope * xs)))
    return y_next - slope * dx, float(slope), sd, len(xs)


def vertex_check(img, bg, cats, ys):
    """QA (--check): compare every marker-based read with the polyline the chart draws between markers.
    The two line segments meeting at a vertex are fitted separately and evaluated at the vertex; the
    vertices sit a constant ~0.5 px right of the marker-box centres (measured on the sharp P90 corners).
    Vertices next to the tooltip and the hover halo (Apr 15-18) are skipped."""
    skip = {HOVER_DAY - 3, HOVER_DAY - 2, HOVER_DAY - 1, HOVER_DAY}  # 0-based indices of Apr 15-18

    def seg(rgb, i, j, y):
        xs, cy = line_centres(img, rgb, range(int(np.ceil(cats[i] + 8)), int(np.floor(cats[j] - 8)) + 1),
                              lambda x: y[i] + (y[j] - y[i]) * (x - cats[i]) / (cats[j] - cats[i]), bg, half=5)
        slope, icpt = np.polyfit(xs, cy, 1)
        return icpt, slope

    verts = [i for i in range(1, 29) if i not in skip]
    corner_dx = []  # corner x from the intersection of the two segments, minus the marker x (P90 corners are sharp)
    for i in verts:
        (a1, b1), (a2, b2) = seg(SERIES[TRIANGLE], i - 1, i, ys[TRIANGLE]), seg(SERIES[TRIANGLE], i, i + 1, ys[TRIANGLE])
        corner_dx.append((a2 - a1) / (b1 - b2) - cats[i])
    off = float(np.median(corner_dx))
    print(f"vertex check: polyline corners sit {off:+.2f} px (sd {np.std(corner_dx):.2f}, n={len(verts)}) right of marker centres")
    for name, rgb in SERIES.items():
        d = []
        for i in verts:
            (a1, b1), (a2, b2) = seg(rgb, i - 1, i, ys[name]), seg(rgb, i, i + 1, ys[name])
            x = cats[i] + off
            d.append((a1 + b1 * x + a2 + b2 * x) / 2 - ys[name][i])
        print(f"  {name:12s} polyline vertex - marker read: mean {np.mean(d):+.2f} px, sd {np.std(d):.2f}, max |d| {np.max(np.abs(d)):.2f}")


def recreate(df, path, yaxis):
    """Clean matplotlib recreation of the chart from the extracted observations. Error bars are the reading
    intervals (+-1.5 px = +-0.17 min, doubled for the point read from under the tooltip); they are smaller
    than the markers, so only their caps show. Series colours are validated categorical slots (blue, aqua,
    orange; dataviz validator: all hard checks pass, aqua's 2.7:1 contrast is relieved by the legend and the
    direct labels), not the source's Highcharts colours; marker shapes are the source's."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    surface, ink, ink2, muted, grid, axis_c = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
    style = {  # metric: (label, colour, marker, marker size)
        "ride_p10": ("P10", "#2a78d6", "D", 5.2),
        "ride_median": ("Median", "#1baf7a", "s", 5.6),
        "ride_p90": ("P90", "#eb6834", "^", 6.6),
    }
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=160, facecolor=surface)
    ax.set_facecolor(surface)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=grid, linewidth=0.8, linestyle="-")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(axis_c)
    ax.tick_params(axis="both", length=0, colors=muted, labelsize=9.5)
    ax.tick_params(axis="x", pad=6)

    handles = []
    for metric, (label, colour, marker, ms) in style.items():
        d = df[df.metric == metric].sort_values("date_or_hour")
        x = np.arange(1, len(d) + 1)
        y, err = d.value.to_numpy(), ((d.upper - d.lower) / 2).to_numpy()
        ax.errorbar(x, y, yerr=err, fmt="none", ecolor=colour, elinewidth=1.1, capsize=4.5, capthick=1.1, zorder=2)
        (line,) = ax.plot(x, y, color=colour, linewidth=1.7, solid_capstyle="round", solid_joinstyle="round",
                          marker=marker, markersize=ms, markerfacecolor=colour, markeredgecolor=surface,
                          markeredgewidth=1.0, zorder=3, label=label)
        handles.append(line)
        ax.text(30.75, y[-1], label, color=ink2, fontsize=10, va="center", ha="left")  # direct label at the line end
        hidden = d.notes.str.contains("tooltip").to_numpy()
        if hidden.any():  # open marker: this point was read from under the tooltip
            ax.plot(x[hidden], y[hidden], linestyle="none", marker=marker, markersize=ms + 0.6,
                    markerfacecolor=surface, markeredgecolor=colour, markeredgewidth=1.6, zorder=4)
    for (metric, day), truth in ANCHORS.items():  # the printed tooltip values, for the eye
        ax.plot([day], [truth], linestyle="none", marker="x", markersize=5.5, markeredgewidth=1.3,
                color=ink, zorder=5)

    handles += [
        Line2D([], [], linestyle="none", marker="x", markersize=5.5, markeredgewidth=1.3, color=ink),
        Line2D([], [], linestyle="none", marker="^", markersize=6.2, markerfacecolor=surface,
               markeredgecolor=ink2, markeredgewidth=1.5),
    ]
    ax.legend(handles, ["P10", "Median", "P90", "Apr 17 tooltip value", "Read from under the tooltip"],
              loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=5, frameon=False, fontsize=9.5,
              labelcolor=ink2, handlelength=1.6, columnspacing=1.8)

    ax.set_ylim(0, 35)
    ax.set_yticks(range(0, 36, 5))
    ax.set_xlim(0.4, 32.4)
    ax.set_xticks(range(1, 30, 2))
    ax.set_xticklabels([f"{d}. Apr" for d in range(1, 30, 2)])
    ax.set_ylabel("Ride Duration (Minutes)", color=ink2, fontsize=10, labelpad=8)

    fig.text(0.07, 0.945, "Ride Duration, Homewood Night Ride", color=ink, fontsize=14.5, fontweight="semibold", ha="left")
    fig.text(0.07, 0.895, "Daily P10, median and P90 of time on vehicle, 1-30 Apr 2026. Recreated from the p12 "
             "screenshot (marker shapes as in the source, colours not).", color=ink2, fontsize=9.5, ha="left")
    half = ERR_PX * yaxis.per_pixel()
    fig.text(0.07, 0.018, f"Error bars: reading interval of +-1.5 px (+-{half:.2f} min), doubled (+-{2 * half:.2f} min) for the point "
             f"read from under the tooltip. Values: data/processed/obs_{CHART}.csv (OBSERVED).",
             color=muted, fontsize=8.3, ha="left")
    fig.subplots_adjust(left=0.07, right=0.975, top=0.84, bottom=0.2)
    dg.EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=surface)
    plt.close(fig)


def main():
    img = dg.load(PAGE)
    grid = dg.line_rows(img, dg.GRID_GRAY, 100, 1320, PLOT["y0"], PLOT["y1"], frac=0.5)
    axis0 = dg.line_rows(img, dg.AXIS_LINE, 100, 1320, PLOT["y0"], PLOT["y1"] + 5, frac=0.9)
    rows = sorted(axis0 + grid, reverse=True)  # bottom (0) to top (35)
    assert len(rows) == len(TICKS), f"expected {len(TICKS)} reference lines, got {rows}"
    yaxis = dg.Axis.fit(rows, TICKS)

    box = dg.tooltip_box(img)
    plot = np.zeros(img.shape[:2], bool)
    plot[PLOT["y0"]:PLOT["y1"], PLOT["x0"]:PLOT["x1"]] = True
    masks = {name: dg.series_mask(img, rgb, box) & plot for name, rgb in SERIES.items()}

    # category centres from the square median markers, ignoring the tooltip's legend dots
    ref = [b for b in dg.markers(masks["ride_median"]) if not dg.inside(box, b.cx, b.cy)]
    cats, dx = dg.category_positions([b.cx for b in ref], 30)
    hover = HOVER_DAY - 1

    bg = row_background(img, np.r_[75:610, 750:1318])            # white, or gridline gray on a gridline row
    bg_tip = TIP_ALPHA * TIP_FILL + (1 - TIP_ALPHA) * bg          # the same rows seen through the tooltip
    inner = img[box[3] - 12:box[3] - 4, box[0] + 10:box[0] + 80].astype(float)  # blank tooltip fill (below its text)
    assert abs(np.median(inner) - bg_tip[box[3] - 8, 0]) < 1.5, "tooltip fill does not match TIP_ALPHA / TIP_FILL"

    # first pass: the p11 read (mask-run midpoint) for every marker
    run = {}
    for name, mask in masks.items():
        lens = [r[1] - r[0] + 1 for x in cats for r in dg.column_runs(mask, x)[:1]]
        typical = int(np.median(lens))
        for i, x in enumerate(cats):
            run[name, i] = dg.marker_at(mask, x, typical, box)

    # second pass: the refinements
    est = {}  # (metric, day index) -> (row, flag, method)
    for name, rgb in SERIES.items():  # hover-state markers first: they anchor the hidden one
        y0, _ = run[name, hover]
        est[name, hover] = (halo_centre(img, cats[hover], y0, rgb, bg), "enlarged (hover-state) marker", "hover halo disc centre")
    for (name, i), (y0, flag) in run.items():
        if i == hover:
            continue
        if y0 is None:
            est[name, i] = (None, flag, "")
        elif "tooltip" in flag:
            assert i == hover - 1, f"{name} day {i + 1}: hidden marker not adjacent to the hover marker"
            y, slope, sd, n = hidden_vertex(img, box, SERIES[name], bg_tip, cats[i], y0, cats[hover], est[name, hover][0], dx)
            assert sd < 0.1, f"tooltip line fit is noisy (sd {sd:.3f} px); check overlay"
            est[name, i] = (y, flag, f"line segment through tooltip (slope {slope:.3f}, {n} cols), one step back from hover halo")
        elif name == TRIANGLE:
            y, tflag = triangle_centre(img, cats[i], y0, bg)
            est[name, i] = (y, flag or tflag, "triangle base edge (sub-pixel)")
        else:
            est[name, i] = (y0, flag, "marker run midpoint")

    recs, pts, labels = [], [], []
    for name in SERIES:
        for i, x in enumerate(cats):
            y, flag, how = est[name, i]
            date = dt.date(2026, 4, i + 1).isoformat()
            if y is None:
                recs.append(dict(metric=name, date_or_hour=date, value=np.nan, lower=np.nan, upper=np.nan,
                                 px_x=round(x, 1), px_y=np.nan, notes=flag, method=""))
                continue
            v = float(yaxis.value(y))
            err = ERR_PX * yaxis.per_pixel() * (2 if "tooltip" in flag else 1)
            recs.append(dict(metric=name, date_or_hour=date, value=v, lower=v - err, upper=v + err,
                             px_x=round(x, 1), px_y=round(y, 2), notes=flag,
                             method=f"{how}; y-axis fit max resid {yaxis.max_residual:.3f} min"))
            pts.append((x, y))
            labels.append("hidden" if "tooltip" in flag else "hover" if i == hover else "")

    df = pd.DataFrame(recs)
    df["chart_id"] = CHART; df["page"] = PAGE; df["period"] = "2026-04-01/2026-04-30"
    df["unit"] = "min"; df["population"] = "Homewood Night Ride; passengers on vehicle (definition per chart subtitle)"
    df["evidence_status"] = "OBSERVED"
    df["obs_id"] = [f"{CHART}_{m}_{d}" for m, d in zip(df.metric, df.date_or_hour)]
    df = df[dg.OBS_COLUMNS]

    # anchor check against the Apr 17 tooltip (also shown for the unrefined p11-style mask-run read)
    ok = True
    for (metric, day), truth in ANCHORS.items():
        got = df[(df.metric == metric) & (df.date_or_hour == f"2026-04-{day:02d}")].value.iloc[0]
        base = float(yaxis.value(run[metric, day - 1][0]))
        err_s = (got - truth) * 60
        ok &= abs(err_s) <= 10
        print(f"anchor {metric} Apr {day}: read {dg.seconds_to_mmss(got)} vs tooltip {dg.seconds_to_mmss(truth)} "
              f"({err_s:+.1f} s); unrefined mask-run read {(base - truth) * 60:+.1f} s")
    print(f"y-axis: {yaxis.per_pixel() * 60:.2f} s/px, fit residual {yaxis.max_residual:.4f} min; categories dx={dx:.2f}px")
    print("reference rows:", rows)
    p90_shift = np.mean([(yaxis.value(est[TRIANGLE, i][0]) - yaxis.value(run[TRIANGLE, i][0])) * 60
                         for i in range(30) if i not in (hover, hover - 1)])
    print(f"P90 triangle refinement vs mask-run midpoint (normal markers): mean {p90_shift:+.1f} s")
    print(df.groupby("metric").value.describe().round(2))
    print("flags:", df[df.notes != ""][["metric", "date_or_hour", "notes"]].to_string(index=False) or "none")

    dg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(dg.PROCESSED / f"obs_{CHART}.csv", index=False)
    dg.overlay(img, pts, dg.EVIDENCE_OUT / f"{CHART}_overlay.png", labels)
    recreate(df, dg.EVIDENCE_OUT / f"{CHART}_recreated.png", yaxis)
    print("tooltip box:", box)
    if "--check" in sys.argv:
        vertex_check(img, bg, cats, {n: [est[n, i][0] for i in range(30)] for n in SERIES})
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
