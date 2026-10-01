"""
p11 - Ride Wait Time (Homewood Night Ride, 1-30 Apr 2026): daily P10 / median / P90.

Worked example for the digitizer. Tick values (0-25 min, step 5) are read from
the y-axis labels. Anchor: the Apr 17 tooltip (P10 2m41s, median 12m56s,
P90 21m17s). Run: .venv/bin/python src/evidence/chart_p11_wait.py
"""
import datetime as dt
import sys

import numpy as np
import pandas as pd

import digitize as dg

PAGE = 11
CHART = "p11_wait"
PLOT = dict(x0=70, x1=1330, y0=200, y1=532)  # plot area; excludes title and legend
TICKS = [0, 5, 10, 15, 20, 25]                  # minutes, bottom to top
SERIES = {"wait_p10": dg.HC_BLACK, "wait_median": dg.HC_GREEN, "wait_p90": dg.HC_ORANGE}
ANCHORS = {("wait_p10", 17): 2 + 41 / 60, ("wait_median", 17): 12 + 56 / 60, ("wait_p90", 17): 21 + 17 / 60}
ERR_PX = 1.5  # half-width of the reading interval, in pixels


def main():
    img = dg.load(PAGE)
    grid = dg.line_rows(img, dg.GRID_GRAY, 100, 1320, PLOT["y0"], PLOT["y1"], frac=0.5)
    axis0 = dg.line_rows(img, dg.AXIS_LINE, 100, 1320, PLOT["y0"], PLOT["y1"] + 5, frac=0.9)
    rows = sorted(axis0 + grid, reverse=True)  # bottom (0) to top (25)
    assert len(rows) == len(TICKS), f"expected {len(TICKS)} reference lines, got {rows}"
    yaxis = dg.Axis.fit(rows, TICKS)

    box = dg.tooltip_box(img)
    plot = np.zeros(img.shape[:2], bool)
    plot[PLOT["y0"]:PLOT["y1"], PLOT["x0"]:PLOT["x1"]] = True
    masks = {name: dg.series_mask(img, rgb, box) & plot for name, rgb in SERIES.items()}

    # category centres from the square median markers, ignoring the tooltip's legend dots
    ref = [b for b in dg.markers(masks["wait_median"]) if not dg.inside(box, b.cx, b.cy)]
    cats, dx = dg.category_positions([b.cx for b in ref], 30)

    recs, pts = [], []
    for name, mask in masks.items():
        lens = [r[1] - r[0] + 1 for x in cats for r in dg.column_runs(mask, x)[:1]]
        typical = int(np.median(lens))
        for i, x in enumerate(cats):
            date = dt.date(2026, 4, i + 1).isoformat()
            y, flag = dg.marker_at(mask, x, typical, box)
            if y is None:
                recs.append(dict(metric=name, date_or_hour=date, value=np.nan, lower=np.nan, upper=np.nan,
                                 px_x=round(x, 1), px_y=np.nan, notes=flag))
                continue
            v = float(yaxis.value(y))
            err = ERR_PX * yaxis.per_pixel() * (2 if "tooltip" in flag else 1)
            recs.append(dict(metric=name, date_or_hour=date, value=v, lower=v - err, upper=v + err,
                             px_x=round(x, 1), px_y=round(y, 1), notes=flag))
            pts.append((x, y))

    df = pd.DataFrame(recs)
    df["chart_id"] = CHART; df["page"] = PAGE; df["period"] = "2026-04-01/2026-04-30"
    df["unit"] = "min"; df["population"] = "Homewood Night Ride; riders picked up (definition per chart subtitle)"
    df["evidence_status"] = "OBSERVED"; df["method"] = f"colour-mask markers; y-axis fit max resid {yaxis.max_residual:.3f} min"
    df["obs_id"] = [f"{CHART}_{m}_{d}" for m, d in zip(df.metric, df.date_or_hour)]
    df = df[dg.OBS_COLUMNS]

    # anchor check against the Apr 17 tooltip
    ok = True
    for (metric, day), truth in ANCHORS.items():
        got = df[(df.metric == metric) & (df.date_or_hour == f"2026-04-{day:02d}")].value.iloc[0]
        err_s = (got - truth) * 60
        ok &= abs(err_s) <= 10
        print(f"anchor {metric} Apr {day}: read {dg.seconds_to_mmss(got)} vs tooltip {dg.seconds_to_mmss(truth)} ({err_s:+.1f} s)")
    print(f"y-axis: {yaxis.per_pixel() * 60:.2f} s/px, fit residual {yaxis.max_residual:.4f} min; categories dx={dx:.2f}px")
    print(df.groupby("metric").value.describe().round(2))
    print("flags:", df[df.notes != ""][["metric", "date_or_hour", "notes"]].to_string(index=False) or "none")

    dg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(dg.PROCESSED / f"obs_{CHART}.csv", index=False)
    dg.overlay(img, pts, dg.EVIDENCE_OUT / f"{CHART}_overlay.png")
    print("tooltip box:", box)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
