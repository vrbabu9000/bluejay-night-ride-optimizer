"""
p08 - Total Passengers (Homewood Night Ride, 1-30 Apr 2026): daily passengers who boarded and completed rides.

Highcharts column chart, 30 daily bars. Tick values (0-1500, step 250) are read from the y-axis labels; gridline and
bar pixels are measured. Anchor: the hover tooltip on Monday, Apr 27, 2026 prints "Passengers: 1 388"; that bar is
drawn in the lighter hover colour. The tooltip is translucent and hides the tops of the Apr 26 and Apr 28 bars, which
are recovered from the bar tint that shows through it (digitize.series_mask un-blends the tooltip).

Bar geometry: Highcharts draws every column with a 1-px white border (checked below: the gridlines stop one pixel
short of each bar). The border row is the row the value is rounded to, the same convention as the gridline rows, so
the value row is the first fill row - 1. Reading the first fill row itself sits about 1 px (4.8 passengers) low;
both readings are printed for the anchor.

Run: .venv/bin/python src/evidence/chart_p08_passengers.py
"""
import datetime as dt
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage

import digitize as dg

PAGE = 8
CHART = "p08_passengers"
TICKS = [0, 250, 500, 750, 1000, 1250, 1500]   # passengers, bottom to top
N_BAR = 30
HOVER_RGB = (149, 206, 255)                     # Highcharts hover state = brighten(#7cb5ec, 0.1)
ANCHORS = {27: 1388}                            # tooltip: "Monday, Apr 27, 2026 - Passengers: 1 388"
ACCEPT_REL = 0.01                               # acceptance: anchor within +-1 %
ERR_PX = 1.5                                    # half-width of the reading interval, in pixels
WIDE_PX = 3.0                                   # doubled where the top lies under the tooltip
BORDER_PX = 1                                   # white border row above the first fill row
TT_BG, TT_ALPHA = 247, 0.85                     # translucent tooltip fill, Highcharts default rgba(247,247,247,0.85)
ROWS = (200, 536)                               # rows that hold the plot (top gridline ... axis line ... tick marks)
CLEAN_X = (1330, 1330)                          # placeholder, gridlines are searched over the plot width below
X_PLOT = (90, 1300)


def tooltip_outline(img, y_lo, y_hi, x_lo=100, x_hi=1320, min_run=60):
    """Border rectangle (xl, yt, xr, yb) of the tooltip, from its opaque 1-px #7cb5ec border (pattern of
    chart_p06_vehicles.py). dg.tooltip_box() returns only the piece of the fill to the right of the bars that
    show through it, so it cannot be used on this page."""
    m = dg.color_mask(img, dg.HC_BLUE, 6)
    rows = []
    for y in range(y_lo, y_hi):
        lab, n = ndimage.label(m[y, x_lo:x_hi])
        if n and ndimage.sum(m[y, x_lo:x_hi], lab, range(1, n + 1)).max() > min_run:
            rows.append(y)          # bars are 19 px wide; only the border has runs > 60 px
    assert len(rows) == 2, f"expected top and bottom tooltip border rows, got {rows}"
    yt, yb = rows
    cols = [x for x in range(x_lo, x_hi) if m[yt + 6:yb - 5, x].all()]
    # a bar taller than the tooltip (Apr 5) also fills these rows, but its columns come in a 19-px block: the border
    # columns are the isolated single-pixel ones
    cols = [x for x in cols if x - 1 not in cols and x + 1 not in cols]
    assert len(cols) == 2, f"expected left and right tooltip border columns, got {cols}"
    return cols[0], yt, cols[1], yb


def series_box(outline):
    """Outline -> the box convention of dg.series_mask (tooltip_box: fill bbox grown by 2 px)."""
    xl, yt, xr, yb = outline
    return (xl - 1, yt - 1, xr + 2, yb + 2)


def bar_extents(img, row):
    """(x_first, x_last) of every bar on a row below the tooltip where all bars are fully visible."""
    m = dg.color_mask(img[row:row + 1], dg.HC_BLUE, 6)[0] | dg.color_mask(img[row:row + 1], HOVER_RGB, 6)[0]
    xs = np.where(m[X_PLOT[0]:X_PLOT[1]])[0] + X_PLOT[0]
    groups = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
    return [(int(g[0]), int(g[-1])) for g in groups]


def fill_top(mask, cols, y_start, y_end, frac):
    """First row from y_start at which at least `frac` of `cols` are in the mask (robust to stray text-fringe pixels),
    and the first masked row of every single column, for QA."""
    sub = mask[y_start:y_end, cols]
    hit = sub.mean(axis=1) >= frac
    row = int(np.argmax(hit)) + y_start if hit.any() else None
    per_col = [int(np.argmax(sub[:, k])) + y_start for k in range(sub.shape[1]) if sub[:, k].any()]
    return row, per_col


def chroma_reread(img, extents, outline, y_start, axis_row, min_share=0.3, window=20, need=10):
    """Independent second read of the bar tops by a different method: the row profile of blue chroma (B - R) across
    each bar's fill columns. It needs neither series_mask nor un-blending: a bar seen through the tooltip has
    B - R = 16 where the tooltip over white has 0, and solid fill has B - R = 106-112. Only those two narrow bands
    count, so the tooltip's text (random chroma) rarely does. Rows crossed by dense glyphs may fall below the share,
    so the top is the first qualifying row followed by at least `need` qualifying rows within the next `window`.
    The tooltip's opaque border rows are bridged from their neighbours. Returns the first fill row of each bar."""
    xl, yt, xr, yb = outline
    chroma = img[:, :, 2] - img[:, :, 0]
    band = ((chroma >= 12) & (chroma <= 20)) | ((chroma >= 100) & (chroma <= 125))
    out = []
    for x0, x1 in extents:
        prof = band[y_start:axis_row, x0 + 1:x1].mean(axis=1)
        if x0 >= xl - 3 and x1 <= xr + 3:
            for r in (yt, yb):
                i = r - y_start
                if 0 < i < len(prof) - 1:
                    prof[i] = min(prof[i - 1], prof[i + 1])
        ok = prof >= min_share
        out.append(next(r + y_start for r in range(len(ok)) if ok[r] and ok[r:r + window].sum() >= need))
    return out


def main():
    img = dg.load(PAGE)

    # ---- y axis: 6 gridlines (bars hide about half of each) + the axis line = 7 reference lines for 7 tick labels
    grid = dg.line_rows(img, dg.GRID_GRAY, X_PLOT[0], X_PLOT[1], ROWS[0], ROWS[1], frac=0.3)
    axis0 = dg.line_rows(img, dg.AXIS_LINE, X_PLOT[0], X_PLOT[1], ROWS[0], ROWS[1], frac=0.5)
    rows = sorted(axis0 + grid, reverse=True)
    assert len(rows) == len(TICKS), f"expected {len(TICKS)} reference lines, got {rows}"
    yaxis = dg.Axis.fit(rows, TICKS)
    per_px = yaxis.per_pixel()
    axis_row = int(round(axis0[0]))
    print(f"y-axis: reference rows {[int(r) for r in rows]}; {per_px:.4f} passengers/px; fit residual max "
          f"{yaxis.max_residual:.2f} passengers ({yaxis.max_residual / per_px:.2f} px; gridlines are snapped to whole pixels)")

    # ---- bars and categories
    ext = bar_extents(img, row=axis_row - 21)
    assert len(ext) == N_BAR and {b - a + 1 for a, b in ext} == {19}, "expected 30 bars, each 19 px wide"
    xc = np.array([(a + b) / 2 for a, b in ext])
    tick_x = np.where(dg.color_mask(img[axis_row + 5:axis_row + 6, X_PLOT[0]:X_PLOT[1]], dg.AXIS_LINE, 6)[0])[0] + X_PLOT[0]
    tdiff = xc[0:N_BAR:2] - tick_x
    ok = len(tick_x) == 15 and np.abs(tdiff).max() <= 1.0
    print(f"bars: 30 x 19 px fill, pitch {np.diff(xc).mean():.2f} px; 15 tick marks (Apr 1,3,...,29) vs bar centres: "
          f"max |diff| {np.abs(tdiff).max():.1f} px")
    hov = [i for i in range(N_BAR) if tuple(img[axis_row - 21, int(xc[i])]) == HOVER_RGB]
    assert hov == [d - 1 for d in ANCHORS], f"hover-colour bar {hov} is not the anchored date"
    # white border check: on a gridline row the line must stop one pixel short of a bar (border column, fill starts next)
    gr = int(rows[1])
    a0, b0 = ext[0]
    edge_ok = all(tuple(img[gr, x]) == (255, 255, 255) for x in (a0 - 1, b0 + 1)) and \
        tuple(img[gr, a0 - 2]) == (230, 230, 230)
    print(f"1-px white border around bars: gridline row {gr} is white at x={a0 - 1} and {b0 + 1} (fill {a0}-{b0}) "
          f"and gray at x={a0 - 2}: {'confirmed' if edge_ok else 'NOT confirmed'}")
    ok &= edge_ok

    # ---- tooltip and masks (translucent fill un-blended by series_mask; opaque border removed)
    outline = tooltip_outline(img, ROWS[0], axis_row)
    xl, yt, xr, yb = outline
    box = series_box(outline)
    under = [i + 1 for i in range(N_BAR) if xl <= xc[i] + 9 and xc[i] - 9 <= xr]
    print(f"tooltip border box: x {xl}-{xr}, y {yt}-{yb}; bars overlapping it: {['Apr %d' % d for d in under]}")
    plot = np.zeros(img.shape[:2], bool)
    plot[int(round(min(grid))) - 2:axis_row, X_PLOT[0]:X_PLOT[1]] = True
    masks = {}
    for name, rgb in (("normal", dg.HC_BLUE), ("hover", HOVER_RGB)):
        m = dg.series_mask(img, rgb, box, alpha=TT_ALPHA, bg=TT_BG) & plot
        m[yt - 1:yt + 2, xl - 1:xr + 2] = False                      # border rows and columns are never bar edges
        m[yb - 1:yb + 2, xl - 1:xr + 2] = False
        m[yt - 1:yb + 2, xl - 1:xl + 2] = False
        m[yt - 1:yb + 2, xr - 1:xr + 2] = False
        masks[name] = m

    # ---- read every bar
    recs, pts, info = [], [], {}
    for i in range(N_BAR):
        date = dt.date(2026, 4, i + 1).isoformat()
        c = int(xc[i])
        anchor_bar = i + 1 in ANCHORS
        hidden = (i + 1) in under and not anchor_bar
        if anchor_bar:        # the tooltip pointer covers the centre columns: read the two edge bands beside it
            cols = list(range(c - 9, c - 4)) + list(range(c + 5, c + 10))
            top, per_col = fill_top(masks["hover"], cols, ROWS[0], axis_row, frac=0.8)
            flag = ("highlighted hover-state bar (#%02x%02x%02x); top read on either side of the tooltip pointer"
                    % HOVER_RGB)
        elif hidden:          # top lies under the translucent tooltip: start the search below its top border
            cols = list(range(c - 6, c + 7))
            top, per_col = fill_top(masks["normal"], cols, yt + 3, axis_row, frac=0.6)
            flag = "recovered from under the tooltip (top hidden under its translucent fill; un-blended, alpha 0.85)"
        else:
            cols = list(range(c - 6, c + 7))
            top, per_col = fill_top(masks["normal"], cols, ROWS[0], axis_row, frac=0.6)
            flag = ""
        assert top is not None, f"no bar top found for Apr {i + 1}"
        info[i] = dict(top=top, cols=(min(per_col), max(per_col)), hidden=hidden, flag=flag)
        y = top - BORDER_PX                          # white border row = the row the value is rounded to
        v = float(yaxis.value(y))
        err = (WIDE_PX if hidden else ERR_PX) * per_px
        notes = flag
        if hidden:
            notes += "; interval doubled (+-3 px)"
        if anchor_bar:
            notes += f"; ANCHOR: tooltip prints {ANCHORS[i + 1]:,}"
        recs.append(dict(metric="passengers", date_or_hour=date, value=round(v, 1), lower=round(v - err, 1),
                         upper=round(v + err, 1), px_x=float(xc[i]), px_y=float(y), notes=notes))
        pts.append((xc[i], float(y)))

    df = pd.DataFrame(recs)
    df["chart_id"] = CHART
    df["page"] = PAGE
    df["period"] = "2026-04-01/2026-04-30"
    df["unit"] = "passengers"
    df["population"] = "Homewood Night Ride; passengers who boarded and completed rides in a day (per chart subtitle)"
    df["evidence_status"] = "OBSERVED"
    df["method"] = (f"colour-mask column tops (fill row - {BORDER_PX} = white border row); y-axis fit max resid "
                    f"{yaxis.max_residual:.2f} passengers; +-{ERR_PX} px = +-{ERR_PX * per_px:.1f} passengers")
    df["obs_id"] = [f"{CHART}_{m}_{d}" for m, d in zip(df.metric, df.date_or_hour)]
    df = df[dg.OBS_COLUMNS]
    dg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(dg.PROCESSED / f"obs_{CHART}.csv", index=False)
    dg.overlay(img, pts, dg.EVIDENCE_OUT / f"{CHART}_overlay.png")

    # ---- anchor check
    for day, truth in ANCHORS.items():
        r = df.iloc[day - 1]
        got = float(r.value)
        literal = float(yaxis.value(r.px_y + BORDER_PX))          # reading the first fill row itself
        rel = (got - truth) / truth
        good = abs(rel) <= ACCEPT_REL
        ok &= good
        print(f"anchor Apr {day}: read {got:.1f} vs tooltip {truth:,} ({got - truth:+.1f} passengers, {rel:+.2%}; acceptance "
              f"+-{ACCEPT_REL:.0%}) -> {'PASS' if good else 'FAIL'}; interval [{r.lower:.1f}, {r.upper:.1f}] "
              f"{'contains' if r.lower <= truth <= r.upper else 'does NOT contain'} the tooltip value")
        print(f"   first fill row {info[day - 1]['top']}, value row {int(r.px_y)}; literal first-fill-row reading would be "
              f"{literal:.1f} ({(literal - truth) / truth:+.2%})")

    # ---- second read (blue chroma, no series_mask) and comparison with the shared helper on un-obstructed bars
    second = chroma_reread(img, ext, outline, int(round(min(grid))) - 2, axis_row)
    primary = [info[i]["top"] for i in range(N_BAR)]
    agree = second == primary
    ok &= agree
    print(f"second read (blue-chroma row profile, no series_mask): "
          f"{'all 30 bar tops agree' if agree else 'DISAGREES: ' + str([(i + 1, a, b) for i, (a, b) in enumerate(zip(primary, second)) if a != b])}")
    plain = [i for i in range(N_BAR) if i + 1 not in under]
    helper = dg.bar_tops(masks["normal"], xc[plain], half_width=6, y_floor=axis_row)
    hd = [int(h) - primary[i] for h, i in zip(helper, plain)]
    print(f"digitize.bar_tops on the {len(plain)} bars clear of the tooltip: identical tops on {sum(d == 0 for d in hd)}")
    ok &= all(d == 0 for d in hd)
    for i in sorted(set(d - 1 for d in under)):
        d = info[i]
        print(f"  Apr {i + 1}: first fill row {d['top']} ({'hover' if not d['hidden'] else 'under the tooltip'}); "
              f"single-column first rows range {d['cols'][0]}-{d['cols'][1]}")

    summary_report(df, info)
    recreate(df, dg.EVIDENCE_OUT / f"{CHART}_recreated.png")
    print("files: data/processed/obs_p08_passengers.csv, outputs/evidence/p08_passengers_overlay.png, _recreated.png")
    return 0 if ok else 1


def summary_report(df, info):
    v = df.set_index("date_or_hour").value
    print(f"\nMONTHLY SUM (DERIVED): {v.sum():.0f} passengers; mean/day {v.mean():.1f}; min {v.min():.1f} ({v.idxmin()}); "
          f"max {v.max():.1f} ({v.idxmax()})")
    wk = pd.to_datetime(v.index).dayofweek
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    by = v.groupby(wk).agg(["mean", "count"])
    print("mean by weekday:", {names[k]: f"{r['mean']:.0f} (n={int(r['count'])})" for k, r in by.iterrows()})
    for d in ("2026-04-17", "2026-04-30"):
        print(f"  {d}: {v[d]:.1f}")
    # cross-chart checks, run only if the other charts' observation files exist (DERIVED, not part of this chart's evidence)
    p07, p10 = dg.PROCESSED / "obs_p07_status.csv", dg.PROCESSED / "obs_p10_vanlyft_daily.csv"
    if p07.exists():
        c = pd.read_csv(p07).query("metric == 'completed'").set_index("date_or_hour").value
        r = v / c
        print(f"DERIVED passengers / completed rides (p07), per day: mean {r.mean():.3f}, min {r.min():.3f} ({r.idxmin()}), "
              f"max {r.max():.3f} ({r.idxmax()}); month pooled {v.sum() / c.sum():.3f}")
    if p10.exists():
        van = pd.read_csv(p10).query("metric == 'van_riders'").set_index("date_or_hour").value
        r = v / van
        print(f"DERIVED agreement with p10 van riders (independent read of another page): correlation "
              f"{np.corrcoef(v, van.loc[v.index])[0, 1]:.4f}; daily ratio mean {r.mean():.3f}, min {r.min():.3f} "
              f"({r.idxmin()}), max {r.max():.3f} ({r.idxmax()}); sums {v.sum():.0f} vs {van.sum():.0f} ({v.sum() / van.sum() - 1:+.2%}); "
              f"tooltip-hidden days Apr 26/28: {v['2026-04-26']:.0f} vs {van['2026-04-26']:.0f}, {v['2026-04-28']:.0f} vs {van['2026-04-28']:.0f}")
    print("FLAGGED POINTS:")
    for _, r in df[df.notes != ""].iterrows():
        print(f"  {r.date_or_hour}  value {r.value:7.1f} [{r.lower:.1f}, {r.upper:.1f}]  {r.notes}")


def recreate(df, path):
    """Clean matplotlib recreation: same series colour, axes and title, error bars = intervals."""
    ink, muted, grid_c, axis_c = "#2b2b2b", "#666666", "#e6e6e6", "#ccd6eb"
    blue = tuple(c / 255 for c in dg.HC_BLUE)
    hover = tuple(c / 255 for c in HOVER_RGB)
    fig, ax = plt.subplots(figsize=(13.2, 6.4), dpi=100)
    x = np.arange(1, N_BAR + 1)
    y, lo, hi = df.value.to_numpy(), df.lower.to_numpy(), df.upper.to_numpy()
    wide = df.notes.str.startswith("recovered").to_numpy()
    cols = [hover if d == "2026-04-27" else blue for d in df.date_or_hour]
    ax.bar(x, y, width=0.47, color=cols, zorder=2)
    ax.errorbar(x[~wide], y[~wide], yerr=[(y - lo)[~wide], (hi - y)[~wide]], fmt="none", ecolor=ink, elinewidth=1.0,
                capsize=2.5, capthick=1.0, zorder=3)
    ax.errorbar(x[wide], y[wide], yerr=[(y - lo)[wide], (hi - y)[wide]], fmt="none", ecolor=ink, elinewidth=1.8,
                capsize=4.5, capthick=1.8, zorder=3)
    for day, truth in ANCHORS.items():
        ax.plot([day + 0.36], [truth], marker="D", ms=6.5, mfc="white", mec=ink, mew=1.4, ls="none", zorder=4)
        ax.annotate(f"Apr {day} tooltip: {truth:,}", (day + 0.36, truth), xytext=(-10, 14), textcoords="offset points",
                    ha="right", fontsize=9.5, color=ink)
    ax.set_xlim(0.4, 30.6)
    ax.set_ylim(0, 1500)
    ax.set_yticks(TICKS)
    ax.set_xticks(x[::2])
    ax.set_xticklabels([f"{d}. Apr" for d in x[::2]])
    ax.grid(axis="y", color=grid_c, lw=1)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(axis_c)
    ax.tick_params(colors=muted, length=3, labelsize=9)
    ax.tick_params(axis="y", length=0)
    ax.set_ylabel("Total Passengers", color=muted, fontsize=9)
    fig.suptitle("Total Passengers", x=0.06, y=0.985, ha="left", fontsize=20, color=ink)
    fig.text(0.06, 0.915, "Recreated from the April 2026 report, page 8 (Homewood Night Ride, 04-01-2026 to 04-30-2026). "
             "The lighter bar is the hover-state bar (Apr 27); the diamond is the printed tooltip value, 1,388.\n"
             "Error bars: reading interval, +-1.5 px = about +-7 passengers; heavier bars, +-3 px, for Apr 26 and Apr 28, "
             "whose tops are hidden under the tooltip.",
             color=muted, fontsize=9, ha="left", va="top", linespacing=1.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=blue), plt.Line2D([], [], color=ink, lw=1.0, marker="_", ms=8),
               plt.Line2D([], [], color="none", marker="D", mfc="white", mec=ink, mew=1.4, ms=6.5)]
    ax.legend(handles, ["Passengers (read from bar top)", "Reading interval", "Tooltip value (exact)"],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False, fontsize=10, labelcolor=ink)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.86, bottom=0.17)
    dg.EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
