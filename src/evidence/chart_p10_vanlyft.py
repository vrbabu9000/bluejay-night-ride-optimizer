"""
p10 - April 2026 Ridership, BJS Vans + Lyft (two PowerBI panels in one raster).

Left  panel "Homewood BJS Ridership": 30 daily stacked columns, Van (dark blue, bottom) + Lyft (pink, top).
Right panel "Average HW BJS Ridership by Day of Week": 7 stacked columns of mean daily riders, in the printed
order Sunday, Monday, Tuesday, Wednesd..., Friday, Thursday, Saturday (Friday and Thursday are out of calendar
order). Printed data labels (1.2K, 0.4K, ...) and the printed total "44,374" are used as anchors, not as inputs.

Method (all pixel geometry is measured on the original 776 x 232 raster; tick VALUES 0K/1K/2K are read by eye
from the axis labels and passed in below):
  1. Colours: Van and Lyft colours are the modal blue / pink pixels of the image.
  2. Each panel has its own y scale: the three dotted gridlines (0K, 1K, 2K) are located to sub-pixel
     precision from the ink centroid of their dots in the columns between bars, then Axis.fit (least squares).
  3. Bars: runs of Van colour just above the baseline (30 in the left panel, 7 in the right).
  4. Segment tops: first row of Lyft colour = top of the stack (total), first row of Van colour = Van top,
     read in the bar's 3 centre columns (right panel: also in side columns, clear of the printed labels).
     Bar edges are crisp integer pixels, so the edge is the UPPER BOUNDARY of that row: row - 0.5 in the same
     pixel-centre coordinates as the gridline centroids. Lyft = total - Van.
  5. Interval: +/-1.5 px of the panel's y scale on every value (about +/-28 riders left, +/-27 right); crisp
     edges are only quantised to +/-0.5 px, so this is a conservative bound.
Checks: sum of daily totals vs the printed 44,374 (+/-2 %); DOW segments vs printed labels (+/-0.05K);
DOW panel vs day-of-week means recomputed from the daily reads (April 1, 2026 is a Wednesday), including which
assignment of the printed "Friday" / "Thursday" bars fits.

Run: .venv/bin/python src/evidence/chart_p10_vanlyft.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import digitize as dg

PAGE = 10
CHART_DAILY = "p10_vanlyft_daily"
CHART_DOW = "p10_vanlyft_dow"
PERIOD = "2026-04-01/2026-04-30"
TICKS = [0, 1000, 2000]          # y-axis labels 0K, 1K, 2K, bottom to top (riders)
ERR_PX = 1.5                     # half-width of the reading interval, in pixels
TOL = 30                         # L1 colour tolerance for the segment masks
PRINTED_TOTAL = 44374            # "Total HW BJS Ridership : 44,374" (printed under the left panel)
TOTAL_TOL_PCT = 2.0              # acceptance band for the sum of the daily reads
LABEL_TOL_K = 0.05               # acceptance band for DOW segments vs printed data labels (0.1K rounding)
N_DAYS = 30
DOW_PRINTED = ["Sunday", "Monday", "Tuesday", "Wednesday", "Friday", "Thursday", "Saturday"]  # left to right
DOW_AXIS_TEXT = ["Sunday", "Monday", "Tuesday", "Wednesd...", "Friday", "Thursday", "Saturday"]
VAN_LABELS = [1.2, 1.1, 1.2, 1.0, 1.0, 1.0, 1.2]       # printed data labels, K
LYFT_LABELS = [None, 0.4, 0.3, 0.4, 0.5, 0.3, 0.4]      # Sunday Lyft has no printed label
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]  # date.weekday()
# plot regions (x0, x1, y0, y1) exclude titles, legends, tick labels; grid = rough rows of the 0K, 1K, 2K lines
LEFT = dict(x0=56, x1=400, y0=52, y1=172, grid=(167, 114, 60), bars=N_DAYS, name="left")
RIGHT = dict(x0=440, x1=776, y0=52, y1=180, grid=(173, 117, 61), bars=7, name="right")


# ---------------------------------------------------------------- local helpers
def modal_colour(img, sel):
    """Most frequent exact RGB among the pixels chosen by the boolean mask `sel`."""
    vals, counts = np.unique(img[sel], axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])


def measure_palette(img):
    blue = (img[..., 0] < 60) & (img[..., 2] > 150)
    pink = (img[..., 0] > 200) & (img[..., 1] < 190) & (img[..., 2] > 170)
    return modal_colour(img, blue), modal_colour(img, pink)


def runs_1d(row, x0, x1):
    """(first, last) column of each run of True values of a 1-D mask within [x0, x1)."""
    xs = np.where(row[x0:x1])[0] + x0
    if not len(xs):
        return []
    return [(int(g[0]), int(g[-1])) for g in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)]


def first_row(mask, cols):
    rows = np.where(mask[:, list(cols)].any(axis=1))[0]
    return int(rows.min()) if len(rows) else None


def last_row(mask, cols):
    rows = np.where(mask[:, list(cols)].any(axis=1))[0]
    return int(rows.max()) if len(rows) else None


def gridline_center(img, cols, y_guess, bar_pixels, half=3, min_ink=20, max_ink=90):
    """Sub-pixel row (pixel-centre coordinates) of a faint dotted horizontal gridline: median over the
    usable columns of the ink-weighted mean row in a +/-`half` row window around `y_guess`. A column is
    usable if it contains no bar pixels and no heavy ink (text) in the window and a dot is present."""
    ink = np.clip(255 - img.mean(axis=2), 0, None)
    ys = np.arange(y_guess - half, y_guess + half + 1)
    cs = []
    for x in cols:
        w = ink[ys, x]
        if bar_pixels[ys, x].any() or w.max() > max_ink or w.sum() < min_ink:
            continue
        cs.append(float((ys * w).sum() / w.sum()))
    return float(np.median(cs)), len(cs), float(np.std(cs))


def read_panel(img, spec, van_rgb, lyft_rgb, side_cols):
    """Locate bars, calibrate the y axis, and read every bar's Van top and stack top."""
    plot = np.zeros(img.shape[:2], bool)
    plot[spec["y0"]:spec["y1"], spec["x0"]:spec["x1"]] = True
    vm = dg.color_mask(img, van_rgb, TOL) & plot
    lm = dg.color_mask(img, lyft_rgb, TOL) & plot

    runs = runs_1d(vm[spec["grid"][0] - 3], spec["x0"], spec["x1"])
    assert len(runs) == spec["bars"], f"{spec['name']}: expected {spec['bars']} bars, found {len(runs)}: {runs}"
    covered = np.zeros(img.shape[1], bool)
    for a, b in runs:
        covered[a:b + 1] = True
    gap_cols = [x for x in range(spec["x0"] + 12, spec["x1"]) if not covered[x]]  # skip the y tick labels
    grid = [gridline_center(img, gap_cols, g, vm | lm) for g in spec["grid"]]
    axis = dg.Axis.fit([g[0] for g in grid], TICKS)

    bars = []
    for i, (a, b) in enumerate(runs):
        mid = (a + b) // 2
        centre = [mid - 1, mid, mid + 1]
        sides = [a + 2, a + 3, b - 3, b - 2] if side_cols else []
        v_row, l_row = first_row(vm, centre), first_row(lm, centre)
        base = last_row(vm, centre)
        # flat-top check across the whole bar width (and the side columns for the labelled panel)
        v_tops = {first_row(vm, [x]) for x in range(a, b + 1)}
        l_tops = {first_row(lm, [x]) for x in range(a, b + 1)}
        flags = []
        if len(v_tops) != 1 or len(l_tops) != 1:
            flags.append(f"top not flat across bar (van rows {sorted(v_tops)}, lyft rows {sorted(l_tops)})")
        if side_cols and (first_row(vm, sides) != v_row or first_row(lm, sides) != l_row):
            flags.append("side columns disagree with centre columns")
        # contiguity: the Lyft segment ends on the row just above the Van top
        l_bot = last_row(lm, centre if not side_cols else sides)
        if l_bot != v_row - 1:
            flags.append(f"segments not contiguous (lyft ends row {l_bot}, van starts row {v_row})")
        # independent recount: rows of colour in a text-free column equals the scanned extent
        cnt_col = mid if not side_cols else a + 2
        n_van, n_lyft = int(vm[:, cnt_col].sum()), int(lm[:, cnt_col].sum())
        if n_van != base - v_row + 1 or n_lyft != v_row - l_row:
            flags.append(f"pixel recount disagrees (van {n_van} vs {base - v_row + 1}, lyft {n_lyft} vs {v_row - l_row})")
        van_px, tot_px = v_row - 0.5, l_row - 0.5          # upper boundary of the first coloured row
        van, total = float(axis.value(van_px)), float(axis.value(tot_px))
        bars.append(dict(idx=i + 1, a=a, b=b, x=(a + b) / 2, v_row=v_row, l_row=l_row, base=base,
                         van_px=van_px, tot_px=tot_px, van=van, total=total, lyft=total - van,
                         n_van=n_van, n_lyft=n_lyft, flags=flags))
    return dict(spec=spec, axis=axis, grid=grid, bars=bars, vm=vm, lm=lm)


def second_read(img, panel, van_rgb, lyft_rgb, side_cols):
    """Independent re-read (guide step 3): classify every pixel of one text-free column per bar to the nearest of
    {white, Lyft pink, Van blue} instead of using the tolerance masks, and take the first pink / first blue row.
    Returns the list of bars whose rows disagree with the primary read."""
    s = panel["spec"]
    palette = np.array([(255, 255, 255), lyft_rgb, van_rgb], float)
    bad = []
    for b in panel["bars"]:
        col = (b["a"] + 2) if side_cols else (b["a"] + b["b"]) // 2
        seg = img[s["y0"]:s["y1"], col].astype(float)
        cls = np.abs(seg[:, None, :] - palette[None, :, :]).sum(axis=2).argmin(axis=1)   # 0 white, 1 pink, 2 blue
        l_row = s["y0"] + int(np.argmax(cls == 1))
        v_row = s["y0"] + int(np.argmax(cls == 2))
        if (l_row, v_row) != (b["l_row"], b["v_row"]):
            bad.append((b["idx"], (l_row, v_row), (b["l_row"], b["v_row"])))
    return bad


def rider_stats(rows):
    return sum(r["van"] for r in rows), sum(r["lyft"] for r in rows), sum(r["total"] for r in rows)


# ---------------------------------------------------------------- QA figures
def make_overlay(img, left, right, out_path):
    """3x nearest-neighbour upscale of the source with the measured geometry drawn on it: green = fitted
    0K/1K/2K gridline rows, red = stack top (Lyft top), yellow = Van top, numbers = day / weekday reads."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    H, W = img.shape[:2]
    fig = plt.figure(figsize=(W * 3 / 100, H * 3 / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img.astype(np.uint8), extent=(0, W, H, 0), interpolation="nearest")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    E = 0.5  # pixel-centre coordinates -> edge coordinates used by imshow

    for panel in (left, right):
        s = panel["spec"]
        for (yc, _, _), tick in zip(panel["grid"], ("0K", "1K", "2K")):
            ax.plot([s["x0"] + 4, s["x1"] - 2], [yc + E, yc + E], color="#00b050", lw=0.8, alpha=0.9, zorder=3)
        yc2 = panel["grid"][2][0]                     # only the 2K row has clear space for its label
        ax.text(s["x1"] - 3, yc2 + E - 1.5, f"2K row {yc2:.2f}", color="#00802f", fontsize=6.5, ha="right",
                va="bottom", zorder=4)
        for b in panel["bars"]:
            ax.plot([b["a"], b["b"] + 1], [b["tot_px"] + E] * 2, color="#e00000", lw=1.6, zorder=5,
                    solid_capstyle="butt")
            ax.plot([b["a"], b["b"] + 1], [b["van_px"] + E] * 2, color="#ffd400", lw=1.6, zorder=5,
                    solid_capstyle="butt")
    for b in left["bars"]:
        ax.text(b["x"] + E, left["spec"]["grid"][0] - 4, str(b["idx"]), color="white", fontsize=6.5, ha="center",
                va="bottom", zorder=6)
    for b, name in zip(right["bars"], DOW_PRINTED):
        ax.text(b["x"] + E, right["spec"]["grid"][0] - 4, f"{name[:3]}\nvan {b['van']:.0f}\nLyft {b['lyft']:.0f}",
                color="white", fontsize=6.5, ha="center", va="bottom", linespacing=1.15, zorder=6)
    g_l = [g[0] for g in left["grid"]]
    g_r = [g[0] for g in right["grid"]]
    ax.text(214, 207, f"green: fitted 0K/1K/2K rows (left {g_l[0]:.2f} / {g_l[1]:.2f} / {g_l[2]:.2f}, "
            f"right {g_r[0]:.2f} / {g_r[1]:.2f} / {g_r[2]:.2f})", fontsize=7.5, color="#333333", va="center",
            zorder=6)
    ax.text(214, 219, "red: stack top (Lyft top)   yellow: Van top   edge = first colour row - 0.5 px   "
            "white numbers: day / weekday reads (riders)", fontsize=7.5, color="#333333", va="center", zorder=6)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100)
    plt.close(fig)


def make_recreation(left, right, van_rgb, lyft_rgb, sum_total, out_path):
    """Clean redraw of both panels from the extracted values (not from the pixels)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    ink, ink2, muted, grid, axis_c = "#1a1a19", "#52514e", "#8a8985", "#e6e5e1", "#c9c8c3"
    c_van = "#%02x%02x%02x" % van_rgb
    c_lyft = "#%02x%02x%02x" % lyft_rgb
    gap = 6  # riders: a ~2 px surface gap between the stacked segments

    days = np.arange(1, N_DAYS + 1)
    van = np.array([b["van"] for b in left["bars"]])
    lyft = np.array([b["lyft"] for b in left["bars"]])
    van_avg = np.array([b["van"] for b in right["bars"]])
    lyft_avg = np.array([b["lyft"] for b in right["bars"]])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.9), dpi=200, sharey=True,
                                   gridspec_kw=dict(width_ratios=[1.45, 1], wspace=0.05))
    for ax in (ax1, ax2):
        ax.set_facecolor("white")
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=grid, lw=0.8, ls="-")
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(axis_c)
        ax.tick_params(axis="both", length=0, labelsize=9, labelcolor=ink2)
        ax.set_ylim(0, 2150)
    ax1.set_yticks([0, 500, 1000, 1500, 2000])
    ax1.set_yticklabels(["0", "500", "1,000", "1,500", "2,000"])
    ax1.set_ylabel("riders per day", fontsize=9, color=muted)

    ax1.bar(days, van, width=0.8, color=c_van, lw=0)
    ax1.bar(days, lyft - gap, bottom=van + gap, width=0.8, color=c_lyft, lw=0)
    ax1.set_xlim(0.2, N_DAYS + 0.8)
    ax1.set_xticks([1, 5, 10, 15, 20, 25, 30])
    ax1.set_xlabel("April 2026, day of month", fontsize=9, color=muted)
    i17 = 16   # April 17: the Van minimum and the Lyft maximum of the month
    assert van[i17] == van.min() and lyft[i17] == lyft.max()
    ax1.annotate(f"Apr 17: Van {van[i17]:.0f}, Lyft {lyft[i17]:.0f}", xy=(17, van[i17] + lyft[i17] + 25),
                 xytext=(14.4, 1790), fontsize=8.5, color=ink2, ha="center",
                 arrowprops=dict(arrowstyle="-", color=muted, lw=0.8, shrinkA=0, shrinkB=0))

    x = np.arange(7)
    ax2.bar(x, van_avg, width=0.74, color=c_van, lw=0)
    ax2.bar(x, lyft_avg - gap, bottom=van_avg + gap, width=0.74, color=c_lyft, lw=0)
    for xi, v, l in zip(x, van_avg, lyft_avg):
        ax2.text(xi, v / 2, f"{v / 1000:.2f}K", ha="center", va="center", fontsize=9, color="white")
        ax2.text(xi, v + gap + (l - gap) / 2, f"{l / 1000:.2f}K", ha="center", va="center", fontsize=9, color=ink)
    ax2.set_xticks(x)
    ax2.set_xticklabels([n[:3] for n in DOW_PRINTED])
    ax2.set_xlim(-0.6, 6.6)
    ax2.set_xlabel("weekday, categories in printed order (Friday precedes Thursday)", fontsize=9, color=muted)

    ax1.set_title("Homewood BJS riders per day, April 2026", loc="left", fontsize=11.5, color=ink, pad=30,
                  fontweight="semibold")
    ax2.set_title("Average riders per day by weekday, April 2026", loc="left", fontsize=11.5, color=ink, pad=30,
                  fontweight="semibold")
    ax1.legend(handles=[Patch(color=c_van, label="Van"), Patch(color=c_lyft, label="Lyft")], loc="lower left",
               bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False, fontsize=9.5, labelcolor=ink2,
               handlelength=1.0, handleheight=1.0, borderaxespad=0.2)
    fig.text(0.075, 0.015,
             f"Re-drawn from digitized values (p10 raster, ~62 ppi). Each value is read to ±{ERR_PX} px "
             f"(±{ERR_PX * left['axis'].per_pixel():.0f} riders daily, ±{ERR_PX * right['axis'].per_pixel():.0f} "
             f"weekday averages). Sum of daily reads {sum_total:,.0f} vs printed total {PRINTED_TOTAL:,} "
             f"({100 * (sum_total - PRINTED_TOTAL) / PRINTED_TOTAL:+.1f}%).",
             fontsize=8, color=muted, ha="left", va="bottom")
    fig.subplots_adjust(left=0.075, right=0.985, top=0.80, bottom=0.17)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    import datetime as dt

    img = dg.load(PAGE)
    van_rgb, lyft_rgb = measure_palette(img)
    print(f"measured colours: van {van_rgb}, lyft {lyft_rgb}; image {img.shape[1]} x {img.shape[0]} px")

    left = read_panel(img, LEFT, van_rgb, lyft_rgb, side_cols=False)
    right = read_panel(img, RIGHT, van_rgb, lyft_rgb, side_cols=True)
    ok = True

    for p in (left, right):
        ax_, g = p["axis"], p["grid"]
        print(f"\n[{p['spec']['name']} panel] gridline rows 0K/1K/2K = "
              f"{g[0][0]:.2f} / {g[1][0]:.2f} / {g[2][0]:.2f} (usable columns {g[0][1]}/{g[1][1]}/{g[2][1]}, "
              f"spread {g[0][2]:.2f}/{g[1][2]:.2f}/{g[2][2]:.2f} px); spacing {g[0][0] - g[1][0]:.2f} & "
              f"{g[1][0] - g[2][0]:.2f} px per 1K")
        print(f"   axis: {1000 / ax_.per_pixel():.2f} px per 1K = {ax_.per_pixel():.2f} riders/px, fit residual "
              f"{ax_.max_residual:.2f} riders; interval +/-{ERR_PX} px = +/-{ERR_PX * ax_.per_pixel():.1f} riders")
        bases = {b["base"] for b in p["bars"]}
        off = p["bars"][0]["base"] + 0.5 - g[0][0]
        print(f"   {len(p['bars'])} bars; baseline row(s) {sorted(bases)} (bar bottom edge {off:+.2f} px below the "
              f"0K gridline centre); bar width {sorted({b['b'] - b['a'] + 1 for b in p['bars']})} px")
        bad = [(b["idx"], b["flags"]) for b in p["bars"] if b["flags"]]
        print("   structural checks (flat tops, contiguity, pixel recount):", "all pass" if not bad else bad)
        second = second_read(img, p, van_rgb, lyft_rgb, side_cols=p is right)
        print(f"   second reader (nearest-palette pixel classes, other column): "
              f"{'agrees on all ' + str(len(p['bars'])) + ' bars' if not second else 'DISAGREES ' + str(second)}")
        ok &= not bad and len(bases) == 1 and not second

    # ---- x alignment: bar i <-> day i (tick labels 10/20/30 and the dotted vertical gridlines sit on bars 10/20/30)
    ink = np.clip(255 - img.mean(axis=2), 0, None)
    lab = ink[172:186, 140:400]
    cols = np.where((lab > 60).any(axis=0))[0] + 140
    groups = np.split(cols, np.where(np.diff(cols) > 4)[0] + 1)
    bx = {b["idx"]: b["x"] for b in left["bars"]}
    print("\n[x axis] tick label centres (ink centroid) vs bar centres:")
    for g, day in zip([g for g in groups if len(g) > 4], (10, 20, 30)):
        w = ink[172:186, g[0]:g[-1] + 1].sum(axis=0)
        c = float((np.arange(g[0], g[-1] + 1) * w).sum() / w.sum())
        print(f"   label '{day}' at x={c:.1f}; bar {day} centre x={bx[day]:.1f} (offset {c - bx[day]:+.1f} px; "
              f"bar pitch {(bx[30] - bx[1]) / 29:.2f} px)")
        ok &= abs(c - bx[day]) <= 2.5

    # ---- daily table
    dates = [dt.date(2026, 4, d) for d in range(1, N_DAYS + 1)]
    wk = [WEEKDAYS[d.weekday()] for d in dates]
    assert wk[0] == "Wednesday", "April 1, 2026 should be a Wednesday"
    ax_l, ax_r = left["axis"], right["axis"]
    err_l, err_r = ERR_PX * ax_l.per_pixel(), ERR_PX * ax_r.per_pixel()
    recs = []
    for metric, key in (("van_riders", "van"), ("lyft_riders", "lyft"), ("total_riders", "total")):
        for b, d in zip(left["bars"], dates):
            v = b[key]
            y = {"van": b["van_px"], "lyft": b["tot_px"], "total": b["tot_px"]}[key]
            note = ""
            if key == "lyft" and b["v_row"] - b["l_row"] <= 10:
                note = (f"thin Lyft segment ({b['v_row'] - b['l_row']} px): +/-{ERR_PX} px is "
                        f"{100 * err_l / v:.0f}% of the value")
            recs.append(dict(metric=metric, date_or_hour=d.isoformat(), value=v, lower=v - err_l, upper=v + err_l,
                             px_x=round(b["x"], 1), px_y=round(y, 1), notes=note))
    daily = pd.DataFrame(recs)
    pop_d = "Homewood BJS ridership, Van and Lyft riders per day (#HWvan / #HWlyft not defined on the slide)"
    method_d = (f"stacked-bar segment tops by colour mask; y-axis fit to 0K/1K/2K gridlines, max resid "
                f"{ax_l.max_residual:.2f} riders; edge = first colour row - 0.5 px; interval +/-{ERR_PX} px")
    daily["chart_id"], daily["page"], daily["period"] = CHART_DAILY, PAGE, PERIOD
    daily["unit"], daily["population"] = "riders", pop_d
    daily["evidence_status"] = "OBSERVED"
    lyft_tag = "; Lyft = stack top - Van top (two crisp edges, quantisation <= 1 px, inside the interval)"
    daily["method"] = np.where(daily.metric == "lyft_riders", method_d + lyft_tag, method_d)
    daily["obs_id"] = [f"{CHART_DAILY}_{m}_{d}" for m, d in zip(daily.metric, daily.date_or_hour)]
    for c in ("value", "lower", "upper"):
        daily[c] = daily[c].round(1)
    daily = daily[dg.OBS_COLUMNS]

    van_sum, lyft_sum, tot_sum = rider_stats(left["bars"])
    err = tot_sum - PRINTED_TOTAL
    pct = 100 * err / PRINTED_TOTAL
    ok_total = abs(pct) <= TOTAL_TOL_PCT
    ok &= ok_total
    # sensitivity: heights measured from each bar's own base instead of the 0K gridline
    off_l = left["bars"][0]["base"] + 0.5 - left["grid"][0][0]
    alt_sum = tot_sum + off_l * ax_l.per_pixel() * N_DAYS
    print(f"\n[acceptance] sum of daily (van + Lyft) = {tot_sum:,.0f} vs printed {PRINTED_TOTAL:,}: "
          f"{err:+,.0f} riders ({pct:+.2f}%) -> {'PASS' if ok_total else 'FAIL'} (+/-{TOTAL_TOL_PCT}% band)")
    print(f"   worst case if every read were {ERR_PX} px off the same way: +/-{ERR_PX * ax_l.per_pixel() * N_DAYS:,.0f} "
          f"riders; heights from each bar's own base instead of the gridline would give {alt_sum:,.0f} "
          f"({100 * (alt_sum - PRINTED_TOTAL) / PRINTED_TOTAL:+.2f}%)")
    print(f"   monthly van {van_sum:,.0f}, Lyft {lyft_sum:,.0f}, Lyft share of riders {100 * lyft_sum / tot_sum:.2f}% "
          f"(scaled to printed total: van {van_sum * PRINTED_TOTAL / tot_sum:,.0f}, Lyft "
          f"{lyft_sum * PRINTED_TOTAL / tot_sum:,.0f})")
    lyft_by_day = {d.isoformat(): b["lyft"] for b, d in zip(left["bars"], dates)}
    van_by_day = {d.isoformat(): b["van"] for b, d in zip(left["bars"], dates)}
    tot_by_day = {d.isoformat(): b["total"] for b, d in zip(left["bars"], dates)}
    for name, dct in (("Lyft", lyft_by_day), ("van", van_by_day), ("total", tot_by_day)):
        lo, hi = min(dct, key=dct.get), max(dct, key=dct.get)
        print(f"   daily {name}: min {dct[lo]:.0f} on {lo}, max {dct[hi]:.0f} on {hi}, mean {np.mean(list(dct.values())):.0f}")

    # ---- DOW panel: rows in printed order
    recs = []
    for metric, key, labels in (("van_avg", "van", VAN_LABELS), ("lyft_avg", "lyft", LYFT_LABELS)):
        for pos, (b, name, txt, lab_k) in enumerate(zip(right["bars"], DOW_PRINTED, DOW_AXIS_TEXT, labels), 1):
            v = b[key]
            y = b["van_px"] if key == "van" else b["tot_px"]
            note = f"printed position {pos}/7; " + (f"printed data label {lab_k:.1f}K" if lab_k is not None
                                                     else "no printed data label")
            if txt != name:
                note += f"; axis label truncated as '{txt}'"
            if name in ("Friday", "Thursday"):
                note += "; printed order has Friday before Thursday (labels follow their own data, see brief)"
            recs.append(dict(metric=metric, date_or_hour=name, value=v, lower=v - err_r, upper=v + err_r,
                             px_x=round(b["x"], 1), px_y=round(y, 1), notes=note))
    dow = pd.DataFrame(recs)
    method_w = (f"stacked-bar segment tops by colour mask (side columns clear of labels); y-axis fit to 0K/1K/2K "
                f"gridlines, max resid {ax_r.max_residual:.2f} riders; edge = first colour row - 0.5 px; "
                f"interval +/-{ERR_PX} px")
    dow["chart_id"], dow["page"], dow["period"] = CHART_DOW, PAGE, PERIOD
    dow["unit"] = "riders"
    dow["population"] = ("Homewood BJS ridership, mean riders per day for that weekday over April 2026 "
                         "(Average of #HWvan / #HWlyft, not defined on the slide)")
    dow["evidence_status"] = "OBSERVED"
    dow["method"] = np.where(dow.metric == "lyft_avg", method_w + lyft_tag, method_w)
    dow["obs_id"] = [f"{CHART_DOW}_{m}_{d}" for m, d in zip(dow.metric, dow.date_or_hour)]
    for c in ("value", "lower", "upper"):
        dow[c] = dow[c].round(1)
    dow = dow[dg.OBS_COLUMNS]

    # ---- DOW segments vs printed data labels
    quant_k = 0.5 * ax_r.per_pixel() / 1000  # half-pixel quantisation of a crisp bar edge, in K
    print(f"\n[anchors] DOW segment reads vs printed data labels (band +/-{LABEL_TOL_K}K; label rounding is 0.1K, "
          f"edge quantisation adds up to {quant_k:.3f}K):")
    n_lab = n_strict = n_quant = 0
    for b, name in zip(right["bars"], DOW_PRINTED):
        pos = DOW_PRINTED.index(name)
        for seg, lab_k in (("van", VAN_LABELS[pos]), ("lyft", LYFT_LABELS[pos])):
            read_k = b[seg] / 1000
            if lab_k is None:
                print(f"   {name:<9} {seg:<4} read {read_k:.3f}K   (no printed label)")
                continue
            d = round(read_k - lab_k, 3)          # labels have 1 decimal, reads are compared at 0.001K
            n_lab += 1
            s_ok, q_ok = abs(d) <= LABEL_TOL_K, abs(d) <= LABEL_TOL_K + quant_k
            n_strict += s_ok
            n_quant += q_ok
            over_k = abs(d) - LABEL_TOL_K
            status = "ok" if s_ok else (
                f"outside the band by {over_k:.3f}K = {over_k * 1000 / ax_r.per_pixel():.1f} px "
                f"({'inside' if q_ok else 'beyond'} the half-pixel edge quantisation)")
            print(f"   {name:<9} {seg:<4} read {read_k:.3f}K vs label {lab_k:.1f}K  diff {d:+.3f}K  {status}")
    print(f"   {n_strict}/{n_lab} within +/-{LABEL_TOL_K}K strictly; {n_quant}/{n_lab} within +/-{LABEL_TOL_K}K "
          f"plus the half-pixel edge quantisation")
    ok &= n_quant == n_lab

    # ---- cross-check: DOW means recomputed from the daily reads (Wed = 1, 8, 15, 22, 29 ...)
    dd = pd.DataFrame(dict(wk=wk, van=[b["van"] for b in left["bars"]], lyft=[b["lyft"] for b in left["bars"]]))
    means = dd.groupby("wk").agg(n=("van", "size"), van=("van", "mean"), lyft=("lyft", "mean"))
    print("\n[cross-check] day-of-week means from the daily reads vs the DOW panel (riders per day):")
    print(f"   {'printed bar':<11}{'n':>2}  {'van daily':>9}{'van panel':>10}{'diff':>7}  {'lyft daily':>10}"
          f"{'lyft panel':>11}{'diff':>7}")
    panel = {name: (b["van"], b["lyft"]) for b, name in zip(right["bars"], DOW_PRINTED)}
    sq = []
    for name in DOW_PRINTED:
        m, (pv, pl) = means.loc[name], panel[name]
        sq += [pv - m.van, pl - m.lyft]
        print(f"   {name:<11}{int(m.n):>2}  {m.van:>9.1f}{pv:>10.1f}{pv - m.van:>+7.1f}  {m.lyft:>10.1f}{pl:>11.1f}"
              f"{pl - m.lyft:>+7.1f}")
    print(f"   RMS difference over 14 numbers: {np.sqrt(np.mean(np.square(sq))):.1f} riders "
          f"(one pixel = {ax_r.per_pixel():.1f} riders)")

    def rms_pair(bar_a, wk_a, bar_b, wk_b):
        d = [panel[bar_a][0] - means.loc[wk_a].van, panel[bar_a][1] - means.loc[wk_a].lyft,
             panel[bar_b][0] - means.loc[wk_b].van, panel[bar_b][1] - means.loc[wk_b].lyft]
        return float(np.sqrt(np.mean(np.square(d)))), d

    r_print, d_print = rms_pair("Friday", "Friday", "Thursday", "Thursday")
    r_swap, d_swap = rms_pair("Friday", "Thursday", "Thursday", "Friday")
    print("   two out-of-order bars: RMS over (van, Lyft) x 2 bars")
    print(f"     as printed (bar 'Friday' = Fridays, bar 'Thursday' = Thursdays): {r_print:6.1f} riders "
          f"(diffs {', '.join(f'{x:+.0f}' for x in d_print)})")
    print(f"     swapped    (bar 'Friday' = Thursdays, bar 'Thursday' = Fridays): {r_swap:6.1f} riders "
          f"(diffs {', '.join(f'{x:+.0f}' for x in d_swap)})")
    verdict = "as printed" if r_print < r_swap else "swapped"
    print(f"     -> assignment that fits: {verdict} (RMS ratio {max(r_print, r_swap) / min(r_print, r_swap):.1f}x). "
          f"A finding, not a pass/fail criterion; the order of the printed categories is what is non-chronological.")

    # robustness: would any other calendar alignment (weekday of day 1) fit the panel better?
    fits = []
    for shift in range(7):
        names = [WEEKDAYS[(2 + shift + d) % 7] for d in range(N_DAYS)]   # day 1 = Wednesday when shift = 0
        mm = dd.assign(wk=names).groupby("wk").agg(van=("van", "mean"), lyft=("lyft", "mean"))
        e = [panel[n][0] - mm.loc[n].van for n in DOW_PRINTED] + [panel[n][1] - mm.loc[n].lyft for n in DOW_PRINTED]
        fits.append((float(np.sqrt(np.mean(np.square(e)))), shift))
    print("   calendar-alignment test (RMS vs panel if day 1 were a different weekday): "
          + ", ".join(f"{WEEKDAYS[(2 + s) % 7][:3]}={r:.0f}" for r, s in sorted(fits, key=lambda t: t[1]))
          + f"  -> best: day 1 = {WEEKDAYS[(2 + min(fits)[1]) % 7]}")
    ok &= min(fits)[1] == 0

    # month total implied by the DOW panel: sum over weekdays of n_days x (van + Lyft)
    def implied(assign):
        return sum(means.loc[assign[n]].n * (panel[n][0] + panel[n][1]) for n in DOW_PRINTED)
    imp_print = implied({n: n for n in DOW_PRINTED})
    imp_swap = implied({**{n: n for n in DOW_PRINTED}, "Friday": "Thursday", "Thursday": "Friday"})
    off_r = right["bars"][0]["base"] + 0.5 - right["grid"][0][0]
    print(f"   month total implied by the DOW panel (sum of n_days x (van + Lyft)): {imp_print:,.0f} as printed "
          f"({100 * (imp_print / PRINTED_TOTAL - 1):+.2f}%), {imp_swap:,.0f} if the two bars were swapped "
          f"({100 * (imp_swap / PRINTED_TOTAL - 1):+.2f}%).")
    print(f"   caveat: the {imp_swap - imp_print:,.0f}-rider gap between those two is about a "
          f"{(imp_swap - imp_print) / (N_DAYS * ax_r.per_pixel()):.1f} px offset of every bar top in this panel "
          f"(30 days x {ax_r.per_pixel():.1f} riders/px), comparable to the {off_r:+.2f} px bar-base offset, so this "
          f"identity cannot decide the assignment; the day-by-day comparison above separates the two by "
          f"{max(r_print, r_swap) / min(r_print, r_swap):.0f}x in RMS")

    # ---- derived summary (DERIVED label in the brief)
    share = {d.isoformat(): 100 * b["lyft"] / b["total"] for b, d in zip(left["bars"], dates)}
    lo, hi = min(share, key=share.get), max(share, key=share.get)
    print(f"\n[summary] Lyft share of daily riders: min {share[lo]:.1f}% on {lo}, max {share[hi]:.1f}% on {hi}, "
          f"mean of daily shares {np.mean(list(share.values())):.1f}%")
    v_arr = np.array([b["van"] for b in left["bars"]])
    l_arr = np.array([b["lyft"] for b in left["bars"]])
    print(f"   daily std: van {v_arr.std(ddof=1):.0f} (CV {v_arr.std(ddof=1) / v_arr.mean():.2f}), Lyft "
          f"{l_arr.std(ddof=1):.0f} (CV {l_arr.std(ddof=1) / l_arr.mean():.2f}); corr(van, Lyft) "
          f"{np.corrcoef(v_arr, l_arr)[0, 1]:+.2f}")
    sig_edge = ax_l.per_pixel() / np.sqrt(12)      # one crisp edge, uniform +/-0.5 px quantisation
    print(f"   sum uncertainty (independent +/-0.5 px edge quantisation, 1 sigma): total +/-{sig_edge * np.sqrt(N_DAYS):.0f}"
          f" riders, Lyft +/-{sig_edge * np.sqrt(2 * N_DAYS):.0f}; systematic offsets up to ~0.3% (see sensitivity above)")

    # ---- write outputs
    dg.PROCESSED.mkdir(parents=True, exist_ok=True)
    daily.to_csv(dg.PROCESSED / f"obs_{CHART_DAILY}.csv", index=False)
    dow.to_csv(dg.PROCESSED / f"obs_{CHART_DOW}.csv", index=False)
    make_overlay(img, left, right, dg.EVIDENCE_OUT / "p10_vanlyft_overlay.png")
    make_recreation(left, right, van_rgb, lyft_rgb, tot_sum, dg.EVIDENCE_OUT / "p10_vanlyft_recreated.png")
    print(f"\nwrote {len(daily)} daily rows, {len(dow)} DOW rows, overlay and recreation; all checks "
          f"{'PASS' if ok else 'NEED ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
