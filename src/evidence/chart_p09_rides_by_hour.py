"""
p09 - Rides by Hour (Homewood Night Ride, 1-30 Apr 2026): completed rides per hour of day.

Highcharts column chart, 24 hour-of-day categories (12 am ... 11 pm). Tick values
(0-6k, step 1k) are read from the y-axis labels. Anchor: the hover tooltip on the
6 pm bar, "Rides by Hour (30 days): 5 098".

Bar geometry (measured, see brief): Highcharts draws every column with a 1-px white
border. The border row is the row the value is rounded to (same convention as the
gridline rows), so bar top = first fill row - 1. Reading the first fill row itself
would sit 1 px (19 rides) low; both readings are printed for the 6 pm anchor.

Run: .venv/bin/python src/evidence/chart_p09_rides_by_hour.py
(prints the DERIVED rides per van-hour table when data/processed/obs_p06_vehicles.csv exists)
"""
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage

import digitize as dg

PAGE = 9
CHART = "p09_rides_by_hour"
METRIC = "completed_rides"
UNIT = "rides"
PERIOD = "2026-04-01/2026-04-30"
POPULATION = "Homewood Night Ride (filter as printed); completed rides summed by hour of day over 30 days (tooltip label)"
TITLE = "Rides by Hour"
SUBTITLE = "This report shows the total number of completed rides per hour."
SERIES = "Rides by Hour (30 days)"
YLABEL = "# Rides"
TICKS = [0, 1000, 2000, 3000, 4000, 5000, 6000]    # y-axis labels 0, 1k ... 6k, bottom to top
N_CAT = 24
EXPECTED_BARS = [0, 1, 18, 19, 20, 21, 22, 23]      # 12 am, 1 am, 6 pm ... 11 pm (as seen on the page)
DAYS = 30                                          # from the tooltip / legend label "(30 days)"
ANCHOR_HOUR, ANCHOR_LABEL, ANCHOR_VALUE = 18, "6 pm", 5098   # tooltip header "6 pm", value "5 098"
ACCEPT_REL = 0.01                       # acceptance: anchor within +-1 %
ERR_PX = 1.5                            # half-width of the reading interval, in pixels
BORDER_PX = 1                           # white border row above the first fill row

# search windows (measured from the image): rows 195-535 hold the plot; columns 180-900
# contain neither a bar nor the tooltip, so gridlines are found there
ROWS = (195, 535)
CLEAN_X = (180, 900)
# translucent tooltip: Highcharts default fill rgba(247,247,247,0.85)
TT_BG, TT_ALPHA = 247, 0.85


def hour_label(h):
    return f"{(h % 12) or 12} {'am' if h < 12 else 'pm'}"


def tick_columns(img, axis_row):
    """Columns of the small tick marks drawn under the x axis (category boundaries)."""
    m = dg.color_mask(img, dg.AXIS_LINE, 8)
    return np.where(m[axis_row + 2:axis_row + 6].all(axis=0))[0]


def tooltip_outline(img, y_lo, y_hi, x_lo=100, x_hi=1325, min_run=60):
    """Border rectangle (xl, yt, xr, yb) of the tooltip, from its 1-px #7cb5ec border.
    dg.tooltip_box() only finds the largest patch of the fill that lies over white paper:
    the translucent fill changes colour over bars and the hover band, so it returns a
    partial box (here x 1055-1139 of the real 928-1138). The border is opaque, so it
    gives the whole box."""
    m = dg.color_mask(img, dg.HC_BLUE, 6)
    rows = []
    for y in range(y_lo, y_hi):
        lab, n = ndimage.label(m[y, x_lo:x_hi])
        if n and ndimage.sum(m[y, x_lo:x_hi], lab, range(1, n + 1)).max() > min_run:
            rows.append(y)          # bars are 25 px wide; only the border has runs > 60 px
    assert len(rows) == 2, f"expected top and bottom tooltip border rows, got {rows}"
    yt, yb = rows
    cols = [x for x in range(x_lo, x_hi) if m[yt + 6:yb - 5, x].all()]
    assert len(cols) == 2, f"expected left and right tooltip border columns, got {cols}"
    return cols[0], yt, cols[1], yb


def series_box(outline):
    """Outline -> the box convention of dg.series_mask (tooltip_box: fill bbox grown by 2 px)."""
    xl, yt, xr, yb = outline
    return (xl - 1, yt - 1, xr + 2, yb + 2)


def measure_bar_colours(img, axis_row, x_lo, x_hi):
    """Distinct saturated-blue colours on the fill row next to the axis (inside the plot:
    axis labels have blue-tinted anti-aliasing), with pixel counts."""
    row = img[axis_row - 1, x_lo:x_hi]
    blue = (row[:, 2] - row[:, 0]) >= 40
    cols, counts = np.unique(row[blue], axis=0, return_counts=True)
    return {tuple(int(v) for v in c): int(n) for c, n in zip(cols, counts)}


def find_bars(img, axis_row, colours, min_len=15):
    """Fill runs on the row next to the axis: (x_start, x_end, colour name)."""
    row = img[axis_row - 1][None]
    bars = []
    for name, rgb in colours.items():
        lab, n = ndimage.label(dg.color_mask(row, rgb, 6)[0])
        for k in range(1, n + 1):
            xs = np.where(lab == k)[0]
            if len(xs) >= min_len:
                bars.append((int(xs[0]), int(xs[-1]), name))
    return sorted(bars)


def fill_top(mask, x0, x1, axis_row, min_share=0.5):
    """First fill row of a bar: per column the first masked row, then the most common
    value over the interior fill columns [x0+1, x1-1]. Also returns the share of columns
    that agree, and the answer from the centre columns alone (xc-3 .. xc+3)."""
    tops = []
    for x in range(x0 + 1, x1):
        rows = np.where(mask[:axis_row, x])[0]
        tops.append(int(rows[0]) if len(rows) else -1)
    (top, n), = Counter(tops).most_common(1)
    assert n / len(tops) >= min_share, f"bar top not unanimous: {Counter(tops)}"
    xc = (x0 + x1) // 2
    centre = Counter(tops[xc - 3 - (x0 + 1):xc + 4 - (x0 + 1)]).most_common(1)[0][0]
    return top, n / len(tops), centre


def chroma_reread(img, bars, outline, axis_row, top_row, min_share=0.6, min_run=8):
    """Independent second read of the bar tops by a different method: the row profile of
    blue chroma (B - R >= 10) across each bar's fill columns. It needs neither series_mask nor
    un-blending: a bar seen through the tooltip still has B - R = 16 where the tooltip over white
    has 0. The tooltip's opaque border rows are bridged from their neighbours. Returns the first
    fill row of each bar."""
    xl, yt, xr, yb = outline
    chroma = img[:, :, 2] - img[:, :, 0]
    out = []
    for x0, x1, _ in bars:
        prof = (chroma[top_row:axis_row, x0 + 1:x1] >= 10).mean(axis=1)
        if x0 >= xl - 3 and x1 <= xr + 3:
            for r in (yt, yb):
                i = r - top_row
                if 0 < i < len(prof) - 1:
                    prof[i] = min(prof[i - 1], prof[i + 1])
        ok = set(np.where(prof >= min_share)[0].tolist())
        out.append(next(r + top_row for r in sorted(ok) if all(r + k in ok for k in range(min_run))))
    return out


def occlusion(outline, x, top):
    """Relation between a bar's first fill row and the tooltip: '', 'adjacent', 'shadow', 'hidden'."""
    xl, yt, xr, yb = outline
    if not (xl - 3 <= x <= xr + 3):
        return ""
    if yt < top <= yb:
        return "hidden"                  # top lies under the translucent tooltip
    if yb < top <= yb + 3 or top == yt - 1:
        return "shadow"                  # top lies in the tooltip's drop shadow
    if yt - 6 <= top < yt - 1:
        return "adjacent"                # top is just above the tooltip border
    return ""


def main():
    img = dg.load(PAGE)

    # ---- y axis: 6 gridlines + the axis line = 7 reference lines for 7 tick labels
    grid = dg.line_rows(img, dg.GRID_GRAY, *CLEAN_X, *ROWS, frac=0.9)
    axis0 = dg.line_rows(img, dg.AXIS_LINE, *CLEAN_X, *ROWS, frac=0.9)
    rows = sorted(axis0 + grid, reverse=True)      # bottom (0) to top (6k)
    assert len(rows) == len(TICKS), f"expected {len(TICKS)} reference lines, got {rows}"
    yaxis = dg.Axis.fit(rows, TICKS)
    axis_row = int(round(axis0[0]))

    # ---- categories: 25 tick marks bound 24 categories
    ticks = tick_columns(img, axis_row)
    assert len(ticks) == N_CAT + 1, f"expected {N_CAT + 1} ticks, got {len(ticks)}"
    tick_mid = (ticks[:-1] + ticks[1:]) / 2

    # ---- bar colours (measured, not assumed) and bar detection
    found = measure_bar_colours(img, axis_row, int(ticks[0]), int(ticks[-1]) + 1)
    assert dg.HC_BLUE in found and len(found) == 2, f"expected #7cb5ec plus one hover colour, got {found}"
    hover = next(c for c in found if c != dg.HC_BLUE)
    brightened = tuple(min(255, c + int(0.1 * 255)) for c in dg.HC_BLUE)   # Highcharts hover = brighten(0.1), pInt(25.5) = 25
    print(f"bar colours on the fill row above the axis: {found}; hover colour {hover} "
          f"(brighten(#7cb5ec, 0.1) = {brightened})")
    bars = find_bars(img, axis_row, {"normal": dg.HC_BLUE, "hover": hover})
    centres = [(b[0] + b[1]) / 2 for b in bars]
    cat_of = [int(np.searchsorted(ticks, x) - 1) for x in centres]       # category from the tick marks
    cats, dx = dg.category_positions(centres, N_CAT)                     # equally spaced fit through the bars
    assert cat_of[0] == 0, "first bar should be 12 am"
    assert cat_of == [int(round((x - cats[0]) / dx)) for x in centres], "tick and fitted category indices disagree"
    assert cat_of == EXPECTED_BARS, f"bars found in categories {cat_of}, expected {EXPECTED_BARS}"
    print(f"bars found in categories: {[hour_label(c) for c in cat_of]}")
    print(f"category centres: x0={cats[0]:.2f}, dx={dx:.2f}px; tick midpoints differ from bar centres by "
          f"{np.mean(cats - tick_mid):+.2f}px (max |dev| {np.abs(cats - tick_mid - np.mean(cats - tick_mid)).max():.2f})")

    # ---- tooltip, translucent fill un-blended (series_mask), border removed from the masks
    outline = tooltip_outline(img, ROWS[0], axis_row)
    xl, yt, xr, yb = outline
    box = series_box(outline)
    print(f"tooltip border box: x {xl}-{xr}, y {yt}-{yb}")
    plot = np.zeros(img.shape[:2], bool)
    plot[int(round(min(grid))):axis_row, int(ticks[0]):int(ticks[-1]) + 1] = True
    masks = {}
    for name, rgb in (("normal", dg.HC_BLUE), ("hover", hover)):
        m = dg.series_mask(img, rgb, box, alpha=TT_ALPHA, bg=TT_BG) & plot
        m[yt, xl:xr + 1] = m[yb, xl:xr + 1] = False
        m[yt:yb + 1, xl] = m[yt:yb + 1, xr] = False
        masks[name] = m

    # ---- read every bar
    recs, pts = [], []
    primary_tops = []
    by_cat = {c: b for c, b in zip(cat_of, bars)}
    for h in range(N_CAT):
        date = f"{h:02d}:00"
        if h not in by_cat:
            # no fill on the row next to the axis (any bar must touch the axis), also not under the tooltip
            lo, hi = int(ticks[h]) + 8, int(ticks[h + 1]) - 8
            blank = not (masks["normal"][axis_row - 1, lo:hi].any() or masks["hover"][axis_row - 1, lo:hi].any())
            assert blank, f"{hour_label(h)}: unexpected fill next to the axis"
            err = ERR_PX * yaxis.per_pixel()
            recs.append(dict(metric=METRIC, date_or_hour=date, value=0.0, lower=0.0, upper=err,
                             px_x=round(float(cats[h]), 1), px_y=float(axis_row), notes="no bar visible"))
            pts.append((cats[h], axis_row))
            continue
        x0, x1, name = by_cat[h]
        xc = (x0 + x1) / 2
        top, share, centre = fill_top(masks[name], x0, x1, axis_row)
        primary_tops.append(top)
        y = top - BORDER_PX                      # white border row = the row the value is rounded to
        v = float(yaxis.value(y))
        flags = []
        if name == "hover":
            flags.append(f"highlighted hover-state bar ({'#%02x%02x%02x' % hover}); tooltip pointer covers the centre "
                         f"columns, top read from the {round(share * (x1 - x0 - 1))} of {x1 - x0 - 1} fill columns it does not cover")
        occ = occlusion(outline, xc, top)
        if occ == "hidden":
            flags.append("recovered from under the tooltip (top hidden under its translucent fill; un-blended, alpha 0.85)")
        elif occ == "shadow":
            flags.append(f"partly hidden by the tooltip: top edge sits on its bottom border (border row {yb}, white bar-border row "
                         f"{y} shadowed, first fill row {top} shadowed); found by chromaticity, nothing shows through the "
                         f"tooltip above it")
        elif occ == "adjacent" and name != "hover":
            flags.append(f"top edge {yt - top} px above the tooltip border; read directly, not under the tooltip")
        if centre != top and name != "hover":
            flags.append(f"centre columns disagree (row {centre} vs {top})")
        if h == ANCHOR_HOUR:
            flags.append(f"ANCHOR: tooltip reads {ANCHOR_VALUE:,}")
        err = ERR_PX * yaxis.per_pixel() * (2 if occ in ("hidden", "shadow") else 1)
        if occ in ("hidden", "shadow"):
            flags.append("interval doubled (+-3 px)")
        recs.append(dict(metric=METRIC, date_or_hour=date, value=v, lower=max(0.0, v - err), upper=v + err,
                         px_x=round(float(xc), 1), px_y=float(y), notes="; ".join(flags)))
        pts.append((xc, y))

    second = chroma_reread(img, bars, outline, axis_row, int(round(min(grid))))
    agree = second == primary_tops
    print(f"second read (blue-chroma row profile, no series_mask): {'all ' + str(len(bars)) + ' bar tops agree' if agree else 'DISAGREES: ' + str(list(zip(primary_tops, second)))}")
    df = pd.DataFrame(recs)
    df["chart_id"] = CHART; df["page"] = PAGE; df["period"] = PERIOD
    df["unit"] = UNIT; df["population"] = POPULATION; df["evidence_status"] = "OBSERVED"
    df["method"] = (f"colour-mask column tops (fill row - {BORDER_PX} = white border row); y-axis fit max resid "
                    f"{yaxis.max_residual:.1f} {UNIT}; +-{ERR_PX} px = +-{ERR_PX * yaxis.per_pixel():.1f} {UNIT}")
    df["obs_id"] = [f"{CHART}_{m}_{d[:2]}" for m, d in zip(df.metric, df.date_or_hour)]
    df = df[dg.OBS_COLUMNS]

    # ---- anchor check against the 6 pm tooltip
    anchor_row = df[df.date_or_hour == f"{ANCHOR_HOUR:02d}:00"].iloc[0]
    got = anchor_row.value
    literal = float(yaxis.value(anchor_row.px_y + BORDER_PX))   # reading the first fill row itself
    rel = (got - ANCHOR_VALUE) / ANCHOR_VALUE
    ok = abs(rel) <= ACCEPT_REL and hour_label(cat_of[[b[2] for b in bars].index("hover")]) == ANCHOR_LABEL
    print(f"anchor {ANCHOR_LABEL}: read {got:,.0f} vs tooltip {ANCHOR_VALUE:,} ({got - ANCHOR_VALUE:+,.0f} rides, "
          f"{rel:+.2%}; acceptance +-{ACCEPT_REL:.0%}) -> {'PASS' if ok else 'FAIL'}; "
          f"literal first-fill-row reading would be {literal:,.0f} ({(literal - ANCHOR_VALUE) / ANCHOR_VALUE:+.2%})")
    print(f"y-axis: {yaxis.per_pixel():.2f} rides/px ({1 / yaxis.per_pixel():.4f} px/ride), "
          f"fit residual {yaxis.max_residual:.2f} rides; reference rows {rows}")
    print(df[["date_or_hour", "value", "lower", "upper", "px_x", "px_y"]].round(1).to_string(index=False))
    blank = df[df.notes == "no bar visible"].date_or_hour
    print(f"no bar visible ({len(blank)} hours, read as 0): {', '.join(blank)}")
    for _, r in df[(df.notes != "") & (df.notes != "no bar visible")].iterrows():
        print(f"flag {r.date_or_hour}: {r.notes}")
    total = df.value.sum()
    half_width = ((df.upper - df.lower) / 2)[df.value > 0]
    print(f"DERIVED: sum over the 24 hours = {total:,.0f} completed rides in {DAYS} days "
          f"(+-{np.sqrt((half_width ** 2).sum()):,.0f} rss of the interval half-widths of the 8 bars; +-{half_width.sum():,.0f} if all errors align)")

    dg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(dg.PROCESSED / f"obs_{CHART}.csv", index=False)
    dg.overlay(img, pts, dg.EVIDENCE_OUT / f"{CHART}_overlay.png",
               labels=[f"{v:,.0f}" if v > 0 else "" for v in df.value])
    recreate(df, dg.EVIDENCE_OUT / f"{CHART}_recreated.png")
    van_hours_table(df)
    return 0 if ok and agree else 1


def van_hours_table(rides):
    """DERIVED: completed rides per van-hour = (rides per day-hour) / (mean vehicles in service)."""
    path = dg.PROCESSED / "obs_p06_vehicles.csv"
    if not path.exists():
        print(f"(no {path.name}; run chart_p06_vehicles.py to get the rides per van-hour table)")
        return
    veh = pd.read_csv(path, dtype={"date_or_hour": str})
    m = rides.merge(veh, on="date_or_hour", suffixes=("_r", "_v"))
    m = m[(m.value_r > 0) & (m.value_v > 0)]
    m["rpvh"] = m.value_r / DAYS / m.value_v
    m["lo"] = m.lower_r / DAYS / m.upper_v
    m["hi"] = m.upper_r / DAYS / m.lower_v
    print("DERIVED completed rides per van-hour = (p09 rides / 30) / p06 vehicles; interval = min/max over both intervals")
    print(m[["date_or_hour", "value_r", "value_v", "rpvh", "lo", "hi"]].rename(
        columns={"value_r": "rides_30d", "value_v": "vehicles"}).round(2).to_string(index=False))
    both = rides.merge(veh, on="date_or_hour", suffixes=("_r", "_v"))
    only_v = both[(both.value_r == 0) & (both.value_v > 0)].date_or_hour.tolist()
    print(f"hours with vehicles but no ride bar: {only_v}")
    tot = (m.value_r.sum() / DAYS) / m.value_v.sum()
    print(f"DERIVED pooled over the {len(m)} hours with both: {m.value_r.sum() / DAYS:.1f} rides/day over {m.value_v.sum():.1f} van-hours/day = {tot:.2f} rides per van-hour")


def recreate(df, path):
    """Clean matplotlib recreation: same series colour, axes and title, error bars = intervals."""
    ink, grid_c, axis_c = "#333333", "#e6e6e6", "#ccd6eb"
    blue = "#%02x%02x%02x" % dg.HC_BLUE
    h = np.arange(N_CAT)
    v, lo, hi = (df[c].to_numpy() for c in ("value", "lower", "upper"))
    on = v > 0
    fig, ax = plt.subplots(figsize=(12.6, 5.6), dpi=150)
    ax.bar(h[on], v[on], width=0.5, color=blue, zorder=3)
    ax.errorbar(h[on], v[on], yerr=[v[on] - lo[on], hi[on] - v[on]], fmt="none", ecolor=ink,
                elinewidth=1, capsize=3, capthick=1, zorder=4)
    for i in h[on]:
        ax.text(i, hi[i] + 90, f"{round(v[i], -1):,.0f}", ha="center", va="bottom", fontsize=8, color=ink)
    ax.plot([ANCHOR_HOUR + 0.36], [ANCHOR_VALUE], marker="D", markersize=5, color=ink, linestyle="none", zorder=5)
    ax.text(10, 1300, "no bar visible (read as 0): 2 am to 5 pm", ha="center", va="center", fontsize=9, color="#666666")
    ax.set_ylim(0, 6000); ax.set_yticks(TICKS); ax.set_yticklabels(["0"] + [f"{t // 1000}k" for t in TICKS[1:]])
    ax.set_xlim(-0.5, N_CAT - 0.5)
    ax.set_xticks(h); ax.set_xticklabels([hour_label(i) for i in h], fontsize=8, color=ink)
    ax.tick_params(axis="y", labelsize=8, colors=ink, length=0)
    ax.tick_params(axis="x", length=4, color=axis_c)
    ax.set_ylabel(YLABEL, fontsize=9, color=ink)
    ax.yaxis.grid(True, color=grid_c, linewidth=1, zorder=0); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(axis_c)
    fig.suptitle(TITLE, x=0.012, y=0.985, ha="left", fontsize=13, fontweight="bold", color="#111111")
    fig.text(0.012, 0.915, f"{SUBTITLE}  Series: {SERIES}.", fontsize=9, color="#666666")
    fig.text(0.012, 0.012,
             "Recreated from pixel measurements of TransLoc report p09. Service: Homewood Night Ride, 04-01-2026 to 04-30-2026 "
             "(30 days; each bar is a 30-day total for that hour of day). Bars: OBSERVED.\n"
             "Error bars: ±1.5 px in value units (±3 px where the top lies in the tooltip shadow). "
             "Diamond: tooltip value 5,098 at 6 pm (the anchor the 6 pm bar is checked against). Labels rounded to 10 rides.",
             fontsize=7.5, color="#666666", va="bottom")
    fig.subplots_adjust(left=0.06, right=0.995, top=0.87, bottom=0.15)
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
