"""
T2: How big is cancellation?

Daily cancelled share = canceled / (completed + canceled + no_show + denied), from the p07
"Rides by Status" chart. Denied is read as 0: its +3.3 rides/day reading is a calibration
offset, not data (p07 brief). Requests are therefore the sum of the four statuses, which is
an upper bound on distinct demand because rebookings and Lyft hand-offs are counted as
cancellations.

Reported: month pooled share (sum of cancellations / sum of requests), mean and median of the
daily shares, extremes with dates, the number of days on which cancellations exceed completions,
the mean by weekday (April 1, 2026 is a Wednesday), and requests per completed ride (the
multiplier behind the base scenario's "as requested" load).

The script reads obs_p07_status.csv directly, so it does not rewrite data/processed/observations.csv.

Outputs: outputs/insights/t02_cancellation.png, t02_cancellation_table.csv, docs/evidence/insights/t02.md
"""
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from common import (BLUE, FIGS, GRAY, INK2, MUTED, ORANGE, PROCESSED, marker_kw, save, series, source, style,
                    subtitle, write_brief)

STATUSES = ("completed", "canceled", "no_show", "denied")
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HIGHLIGHT = "2026-04-17"


def day_label(iso, weekday=True):
    d = dt.date.fromisoformat(iso)
    return f"{d:%a} {d:%b} {d.day}" if weekday else f"{d:%b} {d.day}"


def day_axis(ax, iso_dates):
    """One tick per calendar day: day number, with the weekday initials in a quieter row below."""
    days = [int(i[-2:]) for i in iso_dates]
    ax.set_xticks(days, [str(k) for k in days])
    ax.tick_params(axis="x", labelsize=9.5)
    for k, i in zip(days, iso_dates):
        wd = dt.date.fromisoformat(i).strftime("%a")[:2]
        ax.text(k, -0.085, wd, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7.5,
                color=INK2 if wd in ("Sa", "Su") else MUTED)
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("April 2026 (weekends in darker type)", labelpad=17)


def main():
    style()
    obs = pd.read_csv(PROCESSED / "obs_p07_status.csv")
    s = {m: series(obs, "p07_status", m) for m in STATUSES}
    c, comp, ns = s["canceled"], s["completed"], s["no_show"]

    d = pd.DataFrame({m: s[m].value for m in STATUSES})
    off = d.denied.mean()                       # the +3.3 rides/day reading of Denied
    d["denied"] = 0.0                           # read as 0 (p07 brief)
    d["requests"] = d[list(STATUSES)].sum(axis=1)
    d["cancel_share"] = d.canceled / d.requests
    # conservative reading interval of the share: cancellations low and the others high, and the reverse
    d["share_lo"] = c.lower / (c.lower + comp.upper + ns.upper)
    d["share_hi"] = c.upper / (c.upper + comp.lower + ns.lower)
    d["weekday"] = [dt.date.fromisoformat(i).strftime("%a") for i in d.index]
    d["cancel_exceeds_completed"] = d.canceled > d.completed

    # --- month, daily distribution, extremes ---
    tot = d[list(STATUSES)].sum()
    req = tot.sum()
    pooled = tot.canceled / req
    p_lo = c.lower.sum() / (c.lower.sum() + comp.upper.sum() + ns.upper.sum())     # all reading errors lined up
    p_hi = c.upper.sum() / (c.upper.sum() + comp.lower.sum() + ns.lower.sum())
    pooled_off = (tot.canceled - 30 * off) / (req - 3 * 30 * off)                   # if +off is a common offset
    share = d.cancel_share
    i_min, i_max = share.idxmin(), share.idxmax()
    hw = (d.share_hi - d.share_lo) / 2
    mult, mult_ns = req / tot.completed, (tot.completed + tot.canceled) / tot.completed
    unserved = (tot.canceled + tot.no_show) / req          # ceiling for the share of distinct riders left unserved
    r_req = np.corrcoef(d.requests, share)[0, 1]

    # --- days on which cancellations exceed completions ---
    n_gt = int(d.cancel_exceeds_completed.sum())
    certain, possible = c.lower > comp.upper, c.upper > comp.lower
    ties = [i for i in d.index if possible[i] and not certain[i]]
    tie_txt = (f" ({' and '.join(day_label(i, False) for i in ties)} are too close to call within the reading "
               f"interval)") if ties else ""

    # --- weekday ---
    by = d.groupby("weekday").cancel_share.agg(["mean", "count"]).reindex(WEEKDAYS)
    ex = d.drop(HIGHLIGHT)
    anova_p = stats.f_oneway(*[d.cancel_share[d.weekday == w] for w in WEEKDAYS]).pvalue
    anova_p_ex = stats.f_oneway(*[ex.cancel_share[ex.weekday == w] for w in WEEKDAYS]).pvalue
    fri_ex = ex.cancel_share[ex.weekday == "Fri"].mean()
    wd_txt = ", ".join(f"{w} {by.loc[w, 'mean']:.1%}" for w in WEEKDAYS)
    a = d.loc[HIGHLIGHT]

    # --- CSV twin: the plotted numbers ---
    FIGS.mkdir(parents=True, exist_ok=True)
    out = d[["weekday", "completed", "canceled", "no_show", "denied", "requests", "cancel_share", "share_lo",
             "share_hi", "cancel_exceeds_completed"]].copy()
    out["pooled_share"] = pooled
    out.index.name = "date"
    out.round({"completed": 1, "canceled": 1, "no_show": 1, "requests": 1, "cancel_share": 4, "share_lo": 4,
               "share_hi": 4, "pooled_share": 4}).to_csv(FIGS / "t02_cancellation_table.csv")

    # --- figure ---
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    x = np.array([int(i[-2:]) for i in d.index])
    ax.plot([0.4, 30.5], [pooled, pooled], color=GRAY, lw=1.5, zorder=1)
    ax.text(30.85, pooled, f"Month pooled\n{pooled:.1%}", ha="left", va="center", fontsize=9.5, color=INK2)
    ax.plot(x, share, color=BLUE, **marker_kw(BLUE, 8), zorder=3)
    hl = np.array([i == HIGHLIGHT for i in d.index])
    ax.plot(x[hl], share[hl], color=ORANGE, lw=0, **marker_kw(ORANGE, 11), zorder=4)
    for i, off_pts, va in ((i_max, 11, "bottom"), (i_min, -11, "top")):
        ax.annotate(f"{day_label(i)}: {share[i]:.0%}", (int(i[-2:]), share[i]), xytext=(0, off_pts),
                    textcoords="offset points", ha="center", va=va, fontsize=9.5, color=INK2)
    day_axis(ax, list(d.index))
    ax.set_xlim(0.4, 33.6)
    ax.set_ylim(0, 0.78)
    ax.set_yticks(np.arange(0, 0.71, 0.1))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylabel("Cancelled share of requests")
    ax.set_title(f"Nearly half of April's requests were cancelled, from {share.min():.0%} to {share.max():.0%} by day")
    subtitle(ax, f"Cancelled / all requests each day; cancellations outnumbered completed rides on {n_gt} of 30 days")
    fig.subplots_adjust(bottom=0.2)
    source(fig, "Source: TransLoc April 2026 p07 (rides by status), digitized. Requests = completed + cancelled + "
                f"no-show, denied read as 0. Reading interval about ±{hw.mean() * 100:.1f} points per day.")
    save(fig, "t02_cancellation")

    # --- brief ---
    body = f"""
**Question.** How big is cancellation? What share of ride requests is cancelled, how much does it swing from day to day, and how often do cancellations outnumber completed rides?

**Answer (DERIVED from the OBSERVED p07 daily counts; Denied read as 0): cancellation is about as large as completion.**
- **Month.** {tot.canceled:,.0f} requests were canceled, against {tot.completed:,.0f} completed rides and {tot.no_show:,.0f} no-shows: **{pooled:.1%} of the {req:,.0f} requests** (month pooled). Completed rides are {tot.completed / req:.1%} of requests and no-shows {tot.no_show / req:.1%}.
- **By day.** The daily cancelled share has mean {share.mean():.1%}, median {share.median():.1%} and sd {100 * share.std():.1f} percentage points, from {share.min():.1%} ({day_label(i_min)}) to {share.max():.1%} ({day_label(i_max)}). The pooled share is above the mean because busy days both carry more requests and cancel more (r = {r_req:+.2f} between daily requests and share).
- **Cancellations outnumber completed rides on {n_gt} of 30 days**{tie_txt}.
- **By weekday** (mean of the daily shares, 4-5 days each): {wd_txt}. Apr 17 alone lifts the Friday mean from {fri_ex:.1%} to {by.loc['Fri', 'mean']:.1%}. The pattern is suggestive, not established: one-way ANOVA p = {anova_p:.2f} ({anova_p_ex:.2f} without Apr 17).
- **Apr 17** is the extreme day: {a.canceled:,.0f} canceled against {a.completed:.0f} completed ({a.cancel_share:.1%} of requests). T3 treats it as a supply-side outlier.
- **Precision.** Each daily share is read to about ±{hw.mean() * 100:.1f} points (at most ±{hw.max() * 100:.1f}), smaller than the plotted markers. The pooled share stays within {p_lo:.1%}-{p_hi:.1%} even if every reading error lined up. If the +{off:.1f} rides/day of the Denied reading were a common offset on every series (p07 brief), it would be {pooled_off:.1%}. The p07 brief's 47.3% keeps that raw Denied reading in the denominator. The reading is not the uncertainty that matters; the meaning of "canceled" is.
- **Load multiplier.** Requests per completed ride = {mult:.2f} ({mult_ns:.2f} if no-shows are left out). At about 6 completed rides per van-hour at 6 pm (T1), 30 requests "as served" for 5 vans correspond to {30 * mult_ns:.0f}-{30 * mult:.0f} requests "as requested", consistent with D-06's 60.

**Caveats.**
- "Canceled" is not defined on the page. It may include rebookings (the same rider cancelling and re-requesting) and requests handed to Lyft (the slide title says "many cancelled become Lyfts"). So it overstates distinct unserved riders.
- Requests = completed + canceled + no-show + denied is a sum of status counts, not a printed total, and an upper bound on distinct demand: a rebooking adds a request without adding a rider. For the same reason, the share of distinct riders left unserved is at most (canceled + no-show + denied) / requests = {unserved:.1%}, and could be far lower. These charts give no lower bound.
- Days are calendar dates, but a service night crosses midnight (D-03), so the late-night requests of a Friday night are counted on Saturday. This blurs the weekday means.
- The p07 brief notes that the page does not say whether the four statuses are exclusive, or whether Completed includes rides served by Lyft. The sums above assume they are exclusive and that Completed counts van rides.

**What it cannot tell us.**
- Cancellations by hour of night. The page is daily, so the share at 6 pm (the base-scenario hour) is unknown, and the multiplier above is a daily average.
- Why requests were cancelled (rider, timeout, Lyft hand-off) or how many were repeats, and hence how many distinct riders are involved.
- How long a rider waited before cancelling. T3 gives only the day-level association with waits.

**Used by.**
- **Base-scenario stress load (D-06):** 30 requests "as served" against about 60 "as requested". The 60 counts rebookings and hand-offs, so it is the upper end of distinct demand, not its level. D-06's load grid (4, 6, 9, 12 requests per van-hour) already spans both ends.
- **T3** (cancel share vs wait) and **T7** (cancellations vs Lyft riders) use the daily shares in the table.
- **Rider-patience model:** {pooled:.0%} is a level to compare against, not a calibration target. Fitting simulated abandonment to it would overstate abandonment if rebookings are common. Check the shape against T3's slope, and at the "as requested" load check that the simulated unserved share (abandoned plus overflow) stays under {unserved:.0%}.

Figure: `outputs/insights/t02_cancellation.png`. Table: `outputs/insights/t02_cancellation_table.csv`.
"""
    write_brief("t02", "How big is cancellation?", body)

    print(f"month: canceled {tot.canceled:,.1f} completed {tot.completed:,.1f} no_show {tot.no_show:,.1f} requests {req:,.1f}")
    print(f"pooled {pooled:.4f} (worst-case {p_lo:.4f}-{p_hi:.4f}; common-offset {pooled_off:.4f}); "
          f"mean {share.mean():.4f} median {share.median():.4f} sd {share.std():.4f}")
    print(f"min {i_min} {share.min():.4f}; max {i_max} {share.max():.4f}; cancel>completed days {n_gt} (certain {int(certain.sum())}, possible {int(possible.sum())}, ties {ties})")
    print("weekday means:", by["mean"].round(4).to_dict(), "fri ex Apr17", round(fri_ex, 4), "anova p", round(anova_p, 3), round(anova_p_ex, 3))
    print(f"requests/completed {mult:.3f} ({mult_ns:.3f} w/o no-shows); unserved ceiling {unserved:.4f}; r(requests, share) {r_req:.3f}")
    print(f"reading half-width on share: mean {hw.mean():.4f} max {hw.max():.4f}")


if __name__ == "__main__":
    main()
